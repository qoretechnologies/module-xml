#!/usr/bin/env python3
"""Observe message part identities with the pinned WSDL4J implementation.

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


class MessagePartsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = json.loads((ORACLE / "wsdl4j-manifest.json").read_text())
        if (manifest["implementation"], manifest["version"]) != ("WSDL4J", "1.6.3"):
            raise ValueError("unexpected oracle version")
        for artifact in manifest["artifacts"]:
            data = (ORACLE / artifact["path"]).read_bytes()
            if len(data) != artifact["size"] or hashlib.sha256(data).hexdigest() != artifact["sha256"]:
                raise ValueError("modified oracle artifact: " + artifact["path"])
        cls.directory = tempfile.TemporaryDirectory(prefix="wsdl-message-parts-oracle-")
        cls.addClassCleanup(cls.directory.cleanup)
        cls.classes = Path(cls.directory.name) / "classes"
        cls.classes.mkdir()
        cls.jar = ORACLE / "wsdl4j-1.6.3.jar"
        result = subprocess.run(["javac", "-Xlint:all", "-Werror", "-cp", str(cls.jar), "-d", str(cls.classes),
                                 str(ORACLE / "WsdlMessagePartsOracle.java")], capture_output=True, text=True,
                                timeout=60, check=True)
        if result.stdout or result.stderr:
            raise RuntimeError("unexpected compiler diagnostics")

    def test_distinct_parts_can_reference_the_same_element(self):
        fixture = ROOT / "cxf/swa-mime.wsdl"
        catalog = json.loads((ROOT / "cxf/catalog.json").read_text())
        item = next(item for item in catalog["resources"] if item["path"] == fixture.name)
        self.assertEqual(item["sha256"], hashlib.sha256(fixture.read_bytes()).hexdigest())
        for direction in ("Request", "Response"):
            with self.subTest(direction=direction):
                result = subprocess.run(["java", "-cp", str(self.classes) + os.pathsep + str(self.jar),
                                         "WsdlMessagePartsOracle", str(fixture), "http://cxf.apache.org/swa",
                                         "echoDataWithHeader" + direction], capture_output=True, text=True, timeout=30)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("", result.stderr)
                self.assertEqual([
                    "text\t{http://cxf.apache.org/swa/types}headerText\tnull",
                    "data\tnull\t{http://www.w3.org/2001/XMLSchema}base64Binary",
                    "headerText\t{http://cxf.apache.org/swa/types}headerText\tnull",
                ], result.stdout.splitlines())


if __name__ == "__main__":
    unittest.main()
