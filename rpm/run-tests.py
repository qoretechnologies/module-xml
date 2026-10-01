#!/usr/bin/python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Exercise built XML qmods or installed artifacts, excluding checkout sources."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument('--build-dir', type=Path)
mode.add_argument('--installed', action='store_true')
args = parser.parse_args()
source = Path(__file__).resolve().parents[1]
modules = json.loads((source / 'debian/tests/modules.json').read_text())
env = os.environ.copy()
for key in ('QORE_MODULE_DIR', 'QORE_MODULE_DIR_ONLY', 'QORE_INCLUDE_DIR',
            'LD_LIBRARY_PATH', 'LD_PRELOAD'):
    env.pop(key, None)
base_paths = subprocess.check_output(['/usr/bin/qore', '--module-path'], env=env, text=True).strip().split(':')
if args.build_dir:
    build = args.build_dir.resolve()
    module_dir = build / 'qlib-qmod'
    native, = build.glob('xml-api-*.qmod')
    paths = [str(build), str(module_dir), *base_paths]
else:
    candidates = [Path(p) for p in base_paths if (Path(p) / 'WSDL.qmod').is_file()]
    if len(candidates) != 1:
        raise SystemExit(f'Expected one installed compiled WSDL module, found {candidates}')
    module_dir = candidates[0]
    native, = module_dir.glob('xml-api-*.qmod')
    # --module-path lists configured directories, while Qore's standard lookup
    # prioritizes native paths. Put this package's AOT directory first when
    # constructing an explicit isolated path instead of selecting source files.
    paths = [str(module_dir), *(p for p in base_paths if Path(p) != module_dir)]
for module in modules:
    if not ((module_dir / (module + '.qmod')).is_file()
            or (module_dir / module / (module + '.qmod')).is_file()):
        raise SystemExit(f'Missing compiled module: {module}')
installed_sources = set()
if args.installed:
    # Accept only sources owned by this package, never checkout or user modules.
    installed_sources = {
        Path(p).resolve() for p in subprocess.check_output(
            ['rpm', '-ql', 'qore-xml-module'], text=True).splitlines()
        if p.endswith('.qm')
    }
env.update(QORE_MODULE_DIR=':'.join(paths), QORE_MODULE_DIR_ONLY='1',
           QORE_XML_REQUIRE_LITMUS='1', LC_ALL='C.UTF-8', TZ='UTC')
# No Salesforce credentials are supplied by package qualification.
for key in list(env):
    if key.startswith('SALESFORCE_'):
        env.pop(key)
command = ['/usr/bin/qore', '-b', '-l', str(native), '-p', 'enable-debug']
with tempfile.TemporaryDirectory(prefix='qore-xml-package-', dir=os.environ.get('AUTOPKGTEST_TMP')) as name:
    work = Path(name)
    shutil.copytree(source / 'test', work / 'test',
                    ignore=shutil.ignore_patterns('*.jar', '__pycache__', '.venv', 'ci-results', '*.aot.qtest'))
    # Some tests consume documentation examples as input; no source modules are copied.
    shutil.copytree(source / 'docs', work / 'docs')
    lines = ['%modern'] + ['%requires ' + module for module in modules]
    for module in modules:
        lines += [f'printf("%s\\t%s\\n", {json.dumps(module)}, '
                  f'get_module_hash().{json.dumps(module)}.filename);']
    preflight = work / 'preflight.q'
    preflight.write_text('\n'.join(lines) + '\n')
    result = subprocess.run([*command, str(preflight)], cwd=work, env=env,
                            capture_output=True, text=True, timeout=180)
    # Keep diagnostics visible; a successful fallback is not silent qualification.
    print(result.stderr, end='', file=sys.stderr, flush=True)
    result.check_returncode()
    loaded = [line.split('\t') for line in result.stdout.splitlines()]
    if len(loaded) != len(modules) or any(len(row) != 2 for row in loaded):
        raise SystemExit(f'Invalid preflight output: {result.stdout!r}')
    if [row[0] for row in loaded] != modules:
        raise SystemExit(f'Unexpected preflight module inventory: {loaded!r}')
    for module, filename in loaded:
        artifact = Path(filename).resolve()
        compiled = {(module_dir / (module + '.qmod')).resolve(),
                    (module_dir / module / (module + '.qmod')).resolve()}
        if artifact not in compiled:
            # New optional dependencies invalidate AOT assumptions. Qore must use
            # the installed source in that case; build tests still require qmods.
            stale_optional = any(
                f"for feature '{module}'" in line and 'AOT-MODULE-STALE:' in line
                and 'was compiled when optional module ' in line
                for line in result.stderr.splitlines())
            if (not args.installed or artifact not in installed_sources
                    or artifact.name != module + '.qm' or not stale_optional):
                raise SystemExit(f'Wrong artifact for {module}: {filename}')
        print(f'Preflight: {module}: {artifact}', flush=True)
    suites = sorted((work / 'test').glob('*.qtest'))
    for suite in suites:
        text = suite.read_text()
        text = re.sub(r'^\s*%prepend-module-path "\$\{SCRIPT_DIR\}/\.\./qlib"\s*$', '', text, flags=re.M)
        text = re.sub(r'%requires \.\./qlib/(?:[A-Za-z0-9_]+/)?([A-Za-z0-9_]+)(?:\.qm)?',
                      r'%requires \1', text)
        if '../qlib/' in text:
            raise SystemExit(f'Unconverted source module reference in {suite.name}')
        suite.write_text(text)
        print(f'=== {suite.name} ===', flush=True)
        # SOAP's existing host option avoids dependence on container DNS.
        options = ['--host=127.0.0.1'] if suite.name in ('SoapClient.qtest', 'SoapHandler.qtest') else []
        subprocess.run([*command, str(suite.relative_to(work)), '-v', *options],
                       cwd=work, env=env, check=True, timeout=300)
    print(f'Package test suites passed: {len(suites)}', flush=True)
    cli = source / 'bin/webdav-server' if args.build_dir else Path('/usr/bin/webdav-server')
    subprocess.run(['/usr/bin/python3', str(source / 'debian/tests/webdav-cli.py'), str(cli)],
                   cwd=work, env=env, check=True, timeout=120)
