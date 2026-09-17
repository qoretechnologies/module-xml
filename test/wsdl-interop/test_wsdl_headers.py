#!/usr/bin/env python3
"""Observe imported header identities with the pinned WSDL4J implementation.

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
SOAP11 = "http://schemas.xmlsoap.org/wsdl/soap/"
SOAP12 = "http://schemas.xmlsoap.org/wsdl/soap12/"


class HeaderIdentitiesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = json.loads((ORACLE / "wsdl4j-manifest.json").read_text())
        if (manifest["implementation"], manifest["version"]) != ("WSDL4J", "1.6.3"):
            raise ValueError("unexpected oracle version")
        for artifact in manifest["artifacts"]:
            data = (ORACLE / artifact["path"]).read_bytes()
            if len(data) != artifact["size"] or hashlib.sha256(data).hexdigest() != artifact["sha256"]:
                raise ValueError("modified oracle artifact: " + artifact["path"])
        cls.directory = tempfile.TemporaryDirectory(prefix="wsdl-header-oracle-")
        cls.addClassCleanup(cls.directory.cleanup)
        cls.classes = Path(cls.directory.name) / "classes"
        cls.classes.mkdir()
        cls.jar = ORACLE / "wsdl4j-1.6.3.jar"
        result = subprocess.run(["javac", "-Xlint:all", "-Werror", "-cp", str(cls.jar), "-d", str(cls.classes),
                                 str(ORACLE / "WsdlHeadersOracle.java")], capture_output=True, text=True,
                                timeout=60, check=True)
        if result.stdout or result.stderr:
            raise RuntimeError("unexpected compiler diagnostics")

    def test_imported_header_message_identities(self):
        fixtures = ROOT / "regressions/header-identities"
        for name in ("a.wsdl", "b.wsdl"):
            (Path(self.directory.name) / name).write_bytes((fixtures / name).read_bytes())
        for soap12 in (False, True):
            with self.subTest(soap12=soap12):
                raw = (fixtures / "root.wsdl").read_bytes()
                if soap12:
                    raw = raw.replace(SOAP11.encode(), SOAP12.encode())
                path = Path(self.directory.name) / "root.wsdl"
                path.write_bytes(raw)
                result = subprocess.run(["java", "-cp", str(self.classes) + os.pathsep + str(self.jar),
                                         "WsdlHeadersOracle", str(path)], capture_output=True, text=True, timeout=30)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("", result.stderr)
                self.assertEqual([direction + "\t{urn:header:" + namespace + "}H\ttoken"
                                  for direction in ("input", "output") for namespace in ("a", "b")],
                                 result.stdout.splitlines())


if __name__ == "__main__":
    unittest.main()
