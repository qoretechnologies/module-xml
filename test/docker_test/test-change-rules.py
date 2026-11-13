#!/usr/bin/env python3
"""Checks that a partial pipeline cannot skip test-valgrind for a change that its tests depend on.

Copyright (C) 2026 Qore Technologies, s.r.o.

In a branch pipeline, test-valgrind runs only when a file matching the valgrind paths of .gitlab/ci/module-xml.yml
(&valgrind-paths, matched as GitLab's rules:changes does) changes. This fails unless those globs cover, for every
test file that run-valgrind-qtests.sh selects:
- the test file itself;
- every in-repo module it loads by name (%requires, %try-module, %try-reexport-module, load_module() or
  loadModule(), also in the sub-programs it parses), and every in-repo module those load, each with all of its files
  (qlib/NAME.qm, qlib/NAME/, qlib/NAME.i18n/); the tests find them through the module path, which the CI job sets
  to the checkout's qlib first (QORE_MODULE_DIR) and some tests prepend themselves;
- every existing file or directory it names relative to its own directory (get_script_dir() + "/PATH"; other names
  are labels, such as the label of a parsed sub-program), and in turn the in-repo modules that a Qore source among
  them loads and the files that an XSD or WSDL document among them imports by a relative location.
A load it cannot resolve fails the check: a module loaded by path or by a computed name, a module path other than
"${SCRIPT_DIR}/../qlib", or an %include. A use of get_script_dir() that builds a path at run time must be listed in
DYNAMIC with its expression and how it is covered. Modules that a system module loads on demand (DataProvider
factories such as "sax" or "soap", connection schemes) are not followed: no selected test uses them.

It needs only python3 and runs in the Qore test jobs, which every pipeline runs (about 1 s), after a self-test of
the check on a stand-in tree. Exits nonzero with the uncovered paths.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CI_FILE = ROOT / ".gitlab" / "ci" / "module-xml.yml"
SELECTOR = ROOT / "test" / "docker_test" / "run-valgrind-qtests.sh"

# get_script_dir() uses that build a path at run time: test file -> [(a regular expression that the line of the use
# matches, the glob that every such path matches or None for an exemption, why)]
DYNAMIC = {
    "test/wsdl-schema-whitespace.qtest": [
        (r'get_script_dir\(\) \+ "/" \+ name \+ "\.wsdl"', "test/*.wsdl", "reads test/<name>.wsdl"),
    ],
    "test/listener-addresses.qtest": [
        (r"ListenerScanner::scanDirectory\(get_script_dir\(\)\)", None,
         "a source lint: scans every Qore source under test/ for listener addresses; the Qore test jobs, which run "
         "in every pipeline, run it over the same sources, so valgrind would only run the same lexer over other "
         "text"),
    ],
}

NAME = r"[A-Za-z_][A-Za-z0-9_]*"
LOAD_DIRECTIVE = re.compile(r"%(?:requires|try-module|try-reexport-module)(?:\([a-z]+\))?[ \t]+(\S+)")
LOAD_CALL = re.compile(r"\b(?:load_module|loadModule)\(\s*(\"(" + NAME + r")\"|[^)\s]*)")
MODULE_PATH = re.compile(r"%(?:prepend|append)-module-path[ \t]+([^\n]*)")
QLIB_PATH = '"${SCRIPT_DIR}/../qlib"'
INCLUDE = re.compile(r"%include\b")
SCRIPT_DIR_USE = re.compile(r"get_script_dir\(\)(\s*\+\s*\"([^\"]*)\"(\s*\+)?)?")
QORE_SOURCES = (".q", ".qr", ".qc", ".qm", ".ql", ".qtest")
DOCUMENTS = (".xsd", ".wsdl")
# a relative import, include or redefine of an XSD or WSDL document
LOCATION = re.compile(r"\b(?:schemaLocation|location)\s*=\s*[\"']([^\"']+)[\"']")


def globs(anchor):
    """The paths of a list anchor in the CI file (``  name: &anchor`` followed by ``    - glob`` lines)."""
    text = CI_FILE.read_text()
    block = re.search(rf"(?m)^  [a-z]+: &{re.escape(anchor)}\n((?:    - .*\n)+)", text)
    if block is None:
        raise SystemExit(f"test-change-rules.py: no &{anchor} list in {CI_FILE}")
    return [line.strip()[2:] for line in block.group(1).splitlines()]


def pattern(glob):
    """A glob as GitLab matches it: File.fnmatch with FNM_PATHNAME, "*" within a directory, "**/" any directories.
    Braces, brackets, escapes and a "**" inside a path segment are refused, as they would match differently (a
    trailing "**" matches as "*" does)."""
    if re.search(r"[{}\[\]\\]", glob) or re.search(r"[^/]\*\*|\*\*[^/]", glob):
        raise ValueError(f"unsupported glob syntax: {glob}")
    parts = re.split(r"(\*\*/|\*|\?)", glob)
    return re.compile("".join({"**/": "(?:[^/]+/)*", "*": "[^/]*", "?": "[^/]"}.get(part, re.escape(part))
                              for part in parts))


def module_files(name, root):
    """The files of an in-repo module, or None if NAME is not one."""
    files = []
    for path in (root / "qlib" / f"{name}.qm", root / "qlib" / name, root / "qlib" / f"{name}.i18n"):
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files += [file for file in sorted(path.rglob("*")) if file.is_file()]
    return files or None


def loaded_modules(text, where=None, problems=None):
    """The module names a Qore source loads; with WHERE, appends the loads it cannot resolve to PROBLEMS."""
    names = set()
    for match in LOAD_DIRECTIVE.finditer(text):
        # in a parsed sub-program the directive ends at the string's "\n" or quote
        argument = match.group(1)
        name = None if argument.startswith('"') else re.split(r'[\\"]', argument)[0]
        if name and re.fullmatch(NAME, name):
            names.add(name)
        elif where is not None:
            problems.append(f"{where}: loads a module by path ({match.group(0).strip()!r})")
    for match in LOAD_CALL.finditer(text):
        if match.group(2):
            names.add(match.group(2))
        elif where is not None:
            problems.append(f"{where}: loads a module by a computed name ({match.group(0)!r})")
    if where is not None:
        for match in MODULE_PATH.finditer(text):
            if match.group(1).strip() != QLIB_PATH:
                problems.append(f"{where}: sets a module path other than {QLIB_PATH} ({match.group(0).strip()!r})")
        if INCLUDE.search(text):
            problems.append(f"{where}: uses %include")
    return names


def check(selected, patterns, problems, root=ROOT, dynamic=None):
    """Appends the uncovered dependencies of the selected tests to problems; returns the modules found."""
    dynamic = DYNAMIC if dynamic is None else dynamic
    root = root.resolve()

    def covered(path):
        return any(regex.fullmatch(path) for regex in patterns)

    def relative(path):
        return path.resolve().relative_to(root).as_posix()

    def read(path):
        return path.read_text(encoding="utf-8", errors="replace")

    modules = {}
    used = set()
    for test in selected:
        if not covered(test):
            problems.append(f"{test}: the test file is not covered")
        text = read(root / test)
        names = loaded_modules(text, test, problems)
        # the files it names relative to its directory, and what they import or load in turn
        pending_files = []
        for match in SCRIPT_DIR_USE.finditer(text):
            literal, more = match.group(2), match.group(3)
            if literal is None or more or literal.endswith("/"):
                line = text[text.rfind("\n", 0, match.start()) + 1:text.find("\n", match.end())]
                entries = [index for index, (expression, _, _) in enumerate(dynamic.get(test, []))
                           if re.search(expression, line)]
                if not entries:
                    problems.append(f"{test}: builds a path from get_script_dir() at run time "
                                    f"({line.strip()!r}); list it in DYNAMIC")
                used.update((test, index) for index in entries)
                continue
            target = (root / test).parent / literal.lstrip("/")
            if not target.exists():
                # not a file it reads, such as the label of a parsed sub-program ("cancellation.qr")
                continue
            pending_files += [target] if target.is_file() else sorted(file for file in target.rglob("*")
                                                                      if file.is_file())
        seen_files = set()
        while pending_files:
            file = pending_files.pop()
            if file in seen_files:
                continue
            seen_files.add(file)
            try:
                path = relative(file)
            except ValueError:
                problems.append(f"{test}: reads {file}, which is outside the repository")
                continue
            if not covered(path):
                problems.append(f"{test}: reads {path}, which is not covered")
            if file.suffix in QORE_SOURCES:
                names |= loaded_modules(read(file), f"{test} (through {path})", problems)
            elif file.suffix in DOCUMENTS:
                for location in LOCATION.findall(read(file)):
                    if not re.match(r"[a-z][a-z0-9+.-]*:", location):
                        imported = file.parent / location
                        if imported.is_file():
                            pending_files.append(imported)
        # the in-repo modules it loads, and those they load
        pending = sorted(names)
        seen = set()
        while pending:
            name = pending.pop()
            if name in seen:
                continue
            seen.add(name)
            files = module_files(name, root)
            if files is None:
                continue
            modules.setdefault(name, set()).add(test)
            for file in files:
                if not covered(relative(file)):
                    problems.append(f"{test}: loads module {name}, whose file {relative(file)} is not covered")
                if file.suffix in (".qm", ".qc"):
                    pending += sorted(loaded_modules(read(file)) - seen)
    for test, entries in dynamic.items():
        if test not in selected:
            problems.append(f"DYNAMIC lists {test}, which run-valgrind-qtests.sh does not select")
            continue
        for index, (expression, glob, _) in enumerate(entries):
            if (test, index) not in used:
                problems.append(f"DYNAMIC lists {expression!r} for {test}, which no longer uses it")
            elif glob is not None and not any(regex.pattern == pattern(glob).pattern for regex in patterns):
                problems.append(f"{test}: its run-time paths match {glob}, which is not a valgrind path")
    return modules


def self_test():
    """Checks check() itself on a stand-in tree; returns the failures."""
    failures = []
    with tempfile.TemporaryDirectory(prefix="test-change-rules-") as temp:
        root = Path(temp)
        for path, text in {
                "qlib/Mod.qm": "%requires(reexport) Dep\n%requires xml\n",
                "qlib/Dep/Dep.qm": "%requires qore\n",
                "qlib/Dep/Part.qc": "",
                "qlib/Other.qm": "",
                "qlib/Called.qm": "",
                "qlib/Sub.qm": "",
                "test/a.qtest": "%prepend-module-path \"${SCRIPT_DIR}/../qlib\"\n%requires Mod\n"
                                "string f = get_script_dir() + \"/data/x.json\";\n"
                                "program.parse(code, get_script_dir() + \"/label.qr\");\n"
                                "p.loadModule(\"Called\");\n"
                                "string s = get_script_dir() + \"/sub.qr\";\n"
                                "string d = get_script_dir() + \"/main.xsd\";\n",
                "test/b.qtest": "program.parse(\"%try-module Other\\n\");\n"
                                "string g = get_script_dir() + \"/\" + name;\n",
                "test/sub.qr": "%requires Sub\n",
                "test/main.xsd": "<xs:import schemaLocation=\"schemas/shared.xsd\"/>"
                                 "<xs:import schemaLocation=\"http://example.com/remote.xsd\"/>",
                "test/schemas/shared.xsd": "<xs:schema/>",
                "test/data/x.json": "{}",
        }.items():
            (root / path).parent.mkdir(parents=True, exist_ok=True)
            (root / path).write_text(text)
        everything = ["test/*.qtest", "test/*.qr", "test/*.xsd", "test/schemas/**/*", "test/data/**/*",
                      "qlib/Mod.qm", "qlib/Dep/**/*", "qlib/Other.qm", "qlib/Called.qm", "qlib/Sub.qm"]
        tests = ["test/a.qtest", "test/b.qtest"]
        dynamic = {"test/b.qtest": [(r'get_script_dir\(\) \+ "/" \+ name', None, "stand-in")]}

        def problems(globs, dynamic=dynamic, tests=tests):
            found = []
            check(tests, [pattern(glob) for glob in globs], found, root, dynamic)
            return sorted(found)

        def without(glob):
            return [other for other in everything if other != glob]
        cases = [
            (everything, []),
            (without("test/*.qtest"),
             ["test/a.qtest: the test file is not covered", "test/b.qtest: the test file is not covered"]),
            # a module loaded through another in-repo module, with all of its files
            (without("qlib/Dep/**/*"),
             ["test/a.qtest: loads module Dep, whose file qlib/Dep/Dep.qm is not covered",
              "test/a.qtest: loads module Dep, whose file qlib/Dep/Part.qc is not covered"]),
            # a module loaded by a parsed sub-program, by loadModule() and by a Qore source the test reads
            (without("qlib/Other.qm"), ["test/b.qtest: loads module Other, whose file qlib/Other.qm is not covered"]),
            (without("qlib/Called.qm"),
             ["test/a.qtest: loads module Called, whose file qlib/Called.qm is not covered"]),
            (without("qlib/Sub.qm"), ["test/a.qtest: loads module Sub, whose file qlib/Sub.qm is not covered"]),
            (without("test/data/**/*"), ["test/a.qtest: reads test/data/x.json, which is not covered"]),
            (without("test/*.qr"), ["test/a.qtest: reads test/sub.qr, which is not covered"]),
            # a schema imported by a schema the test reads; the remote import is not followed
            (without("test/schemas/**/*"), ["test/a.qtest: reads test/schemas/shared.xsd, which is not covered"]),
        ]
        for globs, expected in cases:
            if problems(globs) != sorted(expected):
                failures.append(f"self-test: with {globs}: {problems(globs)}, expected {sorted(expected)}")
        unlisted = problems(everything, {})
        if len(unlisted) != 1 or "builds a path from get_script_dir() at run time" not in unlisted[0]:
            failures.append(f"self-test: an unlisted run-time path gave {unlisted}")
        stale = problems(everything, dict(dynamic, **{"test/a.qtest": [("never", None, "stale")]}))
        if stale != ["DYNAMIC lists 'never' for test/a.qtest, which no longer uses it"]:
            failures.append(f"self-test: a stale DYNAMIC entry gave {stale}")
        # loads that cannot be resolved, and a second run-time path in a listed test
        for text, expected in (
                ("%requires ./Local.qm\n", "loads a module by path"),
                ("%requires \"${SCRIPT_DIR}/Helper.qm\"\n", "loads a module by path"),
                ("load_module(name);\n", "loads a module by a computed name"),
                ("%prepend-module-path \"${SCRIPT_DIR}\"\n", "sets a module path other than"),
                ("%include helper.q\n", "uses %include"),
                ("string h = get_script_dir() + \"/other/\" + x;\n", "list it in DYNAMIC")):
            (root / "test" / "c.qtest").write_text(text)
            found = problems(everything + ["test/c.qtest"], dict(dynamic, **{"test/c.qtest": dynamic["test/b.qtest"]})
                             if "DYNAMIC" in expected else dynamic, tests + ["test/c.qtest"])
            found = [problem for problem in found if not problem.startswith("DYNAMIC lists")]
            if len(found) != 1 or expected not in found[0]:
                failures.append(f"self-test: {text.strip()!r} gave {found}, expected {expected!r}")
        for glob in ("qlib/{A,B}.qm", "qlib/[AB].qm", "qlib/Soap**/x", "qlib/**x", "a\\b"):
            try:
                pattern(glob)
                failures.append(f"self-test: the glob {glob} was accepted")
            except ValueError:
                pass
    return failures


def main():
    failures = self_test()
    for failure in failures:
        print(f"test-change-rules.py: FAILED: {failure}", file=sys.stderr)
    if failures:
        return 1
    selected = subprocess.run([str(SELECTOR), "--list"], check=True, capture_output=True,
                              text=True).stdout.split()
    if not selected:
        print("test-change-rules.py: run-valgrind-qtests.sh selected no test file", file=sys.stderr)
        return 1
    patterns = [pattern(glob) for glob in globs("valgrind-paths")]
    problems = []
    modules = check(selected, patterns, problems)
    for problem in problems:
        print(f"test-change-rules.py: FAILED: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"test-change-rules.py: the valgrind paths cover the {len(selected)} selected test files and the in-repo "
          f"modules they load ({', '.join(sorted(modules))})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
