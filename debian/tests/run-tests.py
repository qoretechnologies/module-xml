#!/usr/bin/python3
# Copyright (C) 2026 David Nichols
# SPDX-License-Identifier: MIT
"""Exercise built or installed XML modules without falling back to qlib sources."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
mode = parser.add_mutually_exclusive_group(required=True)
mode.add_argument('--build-dir', type=Path)
mode.add_argument('--installed', action='store_true')
args = parser.parse_args()
source = Path(__file__).resolve().parents[2]
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
env.update(QORE_MODULE_DIR=':'.join(paths), QORE_MODULE_DIR_ONLY='1',
           QORE_XML_REQUIRE_LITMUS='1', LC_ALL='C.UTF-8', TZ='UTC')
# No Salesforce credentials are supplied by package qualification.
for key in list(env):
    if key.startswith('SALESFORCE_'):
        env.pop(key)
command = ['/usr/bin/qore', '-l', str(native), '-p', 'enable-debug']
with tempfile.TemporaryDirectory(prefix='qore-xml-package-', dir=os.environ.get('AUTOPKGTEST_TMP')) as name:
    work = Path(name)
    shutil.copytree(source / 'test', work / 'test',
                    ignore=shutil.ignore_patterns('*.jar', '__pycache__', '.venv', 'ci-results', '*.aot.qtest'))
    # Some tests consume documentation examples as input; no source modules are copied.
    shutil.copytree(source / 'docs', work / 'docs')
    lines = ['%modern'] + ['%requires ' + module for module in modules]
    for module in modules:
        lines += [f'if (!get_module_hash().{json.dumps(module)}.filename.equalPartial('
                  f'{json.dumps(str(module_dir) + "/")})) {{',
                  f'    throw "PACKAGE-TEST-ERROR", {json.dumps("Wrong artifact for " + module)};', '}']
    preflight = work / 'preflight.q'
    preflight.write_text('\n'.join(lines) + '\n')
    subprocess.run([*command, str(preflight)], cwd=work, env=env, check=True, timeout=180)
    print(f'Preflight: all {len(modules)} modules resolve to compiled artifacts in {module_dir}', flush=True)
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
        subprocess.run([*command, str(suite.relative_to(work)), '-v'],
                       cwd=work, env=env, check=True, timeout=300)
    print(f'Package test suites passed: {len(suites)}', flush=True)
    cli = source / 'bin/webdav-server' if args.build_dir else Path('/usr/bin/webdav-server')
    subprocess.run(['/usr/bin/python3', str(source / 'debian/tests/webdav-cli.py'), str(cli)],
                   cwd=work, env=env, check=True, timeout=120)
