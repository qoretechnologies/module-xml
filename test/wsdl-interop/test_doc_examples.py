#!/usr/bin/env python3
"""Runs the examples of the xml module's documentation pages.

Copyright (C) 2026 Qore Technologies, s.r.o.

Every `@code{.py}` block of the pages in docs/ that begins with `%modern` is a complete script. Each one is run with
the development modules and must succeed without warnings; when the block is followed by a `@verbatim` block
introduced as its output ("This produces", "Giving", "Producing", "Resulting in"), the script must print exactly
that. Blocks that are fragments (without `%modern`) are run with `%modern` and `%requires xml` prepended.
"""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DOCS = REPO / "docs"

BLOCK = re.compile(r"@code\{\.py\}\n(.*?)@endcode(.*?)(?=@code|\Z)", re.S)
OUTPUT = re.compile(r"\s*(?:This produces|Giving|Producing|Resulting)[^@]*?@verbatim\s*\n?(.*?)@endverbatim", re.S)
# pages whose fragments are complete statements; other pages hold API excerpts that are not standalone
RUNNABLE_FRAGMENTS = {"xml-serialization.doxygen.tmpl"}


def examples(page, text=None):
    """Returns (index, code, expected output or None) for each runnable example of a page."""
    text = page.read_text(encoding="utf-8") if text is None else text
    for index, (code, after) in enumerate(BLOCK.findall(text)):
        if not code.lstrip().startswith("%modern"):
            if page.name not in RUNNABLE_FRAGMENTS:
                continue
            code = "%modern\n%requires xml\n" + code
        match = OUTPUT.match(after)
        yield index, code, match.group(1).strip() if match else None


def run(code, temp):
    script = Path(temp) / "example.q"
    script.write_text(code + "\n", encoding="utf-8")
    env = dict(os.environ, QORE_MODULE_DIR=os.pathsep.join(
        (str(REPO / "build-debug"), str(REPO / "qlib"), os.environ.get("QORE_MODULE_DIR", ""))))
    return subprocess.run([os.environ.get("QORE", "qore"), "-b", "--enable-debug", str(script)],
                          capture_output=True, text=True, env=env, timeout=300)


class DocExampleTests(unittest.TestCase):
    def test_pages_have_examples(self):
        # the pages that document usage keep complete examples; losing them silently weakens this test
        counts = {page.name: len(list(examples(page))) for page in DOCS.glob("*.doxygen.tmpl")}
        for name in ("xml-cookbook.doxygen.tmpl", "xml-getting-started.doxygen.tmpl",
                     "xml-serialization.doxygen.tmpl"):
            self.assertGreater(counts.get(name, 0), 2, name)

    def test_examples_run(self):
        with tempfile.TemporaryDirectory(prefix="xml-doc-examples-") as temp:
            for page in sorted(DOCS.glob("*.doxygen.tmpl")):
                for index, code, expected in examples(page):
                    with self.subTest(page=page.name, example=index):
                        result = run(code, temp)
                        self.assertEqual(0, result.returncode, result.stderr)
                        self.assertEqual("", result.stderr)
                        if expected is not None:
                            self.assertEqual(expected, result.stdout.strip())

    def test_documented_outputs_are_compared(self):
        # the serialization guide documents the output of its examples
        outputs = [expected for _, _, expected in examples(DOCS / "xml-serialization.doxygen.tmpl") if expected]
        self.assertGreater(len(outputs), 3)
        # a wrong documented output is paired with its example and differs from the actual output
        page = Path("xml-serialization.doxygen.tmpl")
        text = ("    @code{.py}\nprintf(\"%s\\n\", make_xml({\"a\": 1}));\n    @endcode\n\n"
                "    This produces:\n    @verbatim\n<b>1</b>\n    @endverbatim\n")
        (_, code, expected), = examples(page, text)
        self.assertEqual("<b>1</b>", expected)
        with tempfile.TemporaryDirectory(prefix="xml-doc-examples-") as temp:
            result = run(code, temp)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("<a>1</a>", result.stdout)
        self.assertNotEqual(expected, result.stdout.strip())


if __name__ == "__main__":
    unittest.main()
