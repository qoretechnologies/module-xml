#!/usr/bin/env python3
"""Adjudicate pinned CXF binding references with the independent WSDL4J model.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
ORACLE = ROOT / "oracle"


class CxfBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = json.loads((ORACLE / "wsdl4j-manifest.json").read_text())
        if (manifest["implementation"], manifest["version"]) != ("WSDL4J", "1.6.3"):
            raise ValueError("unexpected oracle version")
        for artifact in manifest["artifacts"]:
            data = (ORACLE / artifact["path"]).read_bytes()
            if len(data) != artifact["size"] or hashlib.sha256(data).hexdigest() != artifact["sha256"]:
                raise ValueError("modified oracle artifact: " + artifact["path"])
        cls.directory = tempfile.TemporaryDirectory(prefix="wsdl-cxf-bindings-oracle-")
        cls.addClassCleanup(cls.directory.cleanup)
        cls.classes = Path(cls.directory.name) / "classes"
        cls.classes.mkdir()
        cls.jar = ORACLE / "wsdl4j-1.6.3.jar"
        result = subprocess.run(["javac", "-Xlint:all", "-Werror", "-cp", str(cls.jar), "-d", str(cls.classes),
                                 str(ORACLE / "WsdlCxfBindingsOracle.java")], capture_output=True, text=True,
                                timeout=60, check=True)
        if result.stdout or result.stderr:
            raise RuntimeError("unexpected compiler diagnostics")

    def test_body_part_references_in_original_header_contracts(self):
        catalog = json.loads((ROOT / "cxf/catalog.json").read_text())
        for item in catalog["resources"]:
            self.assertEqual(item["sha256"], hashlib.sha256((ROOT / "cxf" / item["path"]).read_bytes()).hexdigest())
        for style in ("doc_lit", "rpc_lit"):
            with self.subTest(style=style):
                fixture = ROOT / "cxf" / ("header_" + style + ".wsdl")
                namespace = "http://apache.org/headers/" + style
                result = subprocess.run(["java", "-cp", str(self.classes) + os.pathsep + str(self.jar),
                                         "WsdlCxfBindingsOracle", str(fixture), namespace], capture_output=True,
                                        text=True, timeout=30)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("", result.stderr)
                rows = [line.split("\t") for line in result.stdout.splitlines()]
                self.assertEqual(4, len(rows))
                self.assertEqual(["inHeader", "outHeader", "inoutHeader", "inoutHeader"], [row[0] for row in rows])
                self.assertEqual(["input", "output", "input", "output"], [row[1] for row in rows])
                self.assertEqual(["in", "out", "in", "out"], [row[3] for row in rows])
                self.assertEqual(["defined", "defined"] + (["undefined"] * 2 if style == "doc_lit"
                                                          else ["defined"] * 2), [row[4] for row in rows])
                for row, message in zip(rows, ("inHeaderRequest", "outHeaderResponse",
                                               "inoutHeaderRequest", "inoutHeaderResponse")):
                    self.assertEqual("{" + namespace + "}" + message, row[2])


if __name__ == "__main__":
    unittest.main()
