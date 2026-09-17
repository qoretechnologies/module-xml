#!/usr/bin/env python3
"""Observe fault descriptions with the pinned WSDL4J implementation.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree

ROOT = Path(__file__).resolve().parent
ORACLE = ROOT / "oracle"
SOAP11 = "http://schemas.xmlsoap.org/wsdl/soap/"
SOAP12 = "http://schemas.xmlsoap.org/wsdl/soap12/"
ENCODING = "http://schemas.xmlsoap.org/soap/encoding/"


class FaultDescriptionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = json.loads((ORACLE / "wsdl4j-manifest.json").read_text())
        if (manifest["implementation"], manifest["version"]) != ("WSDL4J", "1.6.3"):
            raise ValueError("unexpected oracle version")
        for artifact in manifest["artifacts"]:
            data = (ORACLE / artifact["path"]).read_bytes()
            if len(data) != artifact["size"] or hashlib.sha256(data).hexdigest() != artifact["sha256"]:
                raise ValueError("modified oracle artifact: " + artifact["path"])
        cls.directory = tempfile.TemporaryDirectory(prefix="wsdl-fault-oracle-")
        cls.addClassCleanup(cls.directory.cleanup)
        cls.classes = Path(cls.directory.name) / "classes"
        cls.classes.mkdir()
        cls.jar = ORACLE / "wsdl4j-1.6.3.jar"
        result = subprocess.run(["javac", "-Xlint:all", "-Werror", "-cp", str(cls.jar), "-d", str(cls.classes),
                                 str(ORACLE / "WsdlFaultsOracle.java")], capture_output=True, text=True,
                                timeout=60, check=True)
        if result.stdout or result.stderr:
            raise RuntimeError("unexpected compiler diagnostics")

    def observe(self, encoded, soap12, rpc):
        tree = etree.parse(str(ROOT / "regressions/fault-bindings/literal.wsdl"))
        fault = tree.find(f".//{{{SOAP11}}}fault")
        # Opposite output use makes accidental output/fault metadata reuse observable.
        tree.find(f".//{{http://schemas.xmlsoap.org/wsdl/}}binding/"
                  f"{{http://schemas.xmlsoap.org/wsdl/}}operation/"
                  f"{{http://schemas.xmlsoap.org/wsdl/}}output/{{{SOAP11}}}body").set(
                      "use", "literal" if encoded else "encoded")
        if encoded:
            fault.set("use", "encoded")
            fault.set("namespace", "urn:fault-wire")
            fault.set("encodingStyle", ENCODING)
            part = tree.find("{http://schemas.xmlsoap.org/wsdl/}message[@name='Failure']/"
                             "{http://schemas.xmlsoap.org/wsdl/}part")
            del part.attrib["element"]
            part.set("type", "xs:int")
        if rpc:
            tree.find(f".//{{{SOAP11}}}binding").set("style", "rpc")
        raw = etree.tostring(tree)
        if soap12:
            raw = raw.replace(SOAP11.encode(), SOAP12.encode())
        path = Path(self.directory.name) / "input.wsdl"
        path.write_bytes(raw)
        result = subprocess.run(["java", "-cp", str(self.classes) + os.pathsep + str(self.jar),
                                 "WsdlFaultsOracle", str(path)], capture_output=True, text=True, timeout=30)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        return result.stdout.splitlines()

    def test_literal_fault_independent_of_output_and_operation_style(self):
        for soap12 in (False, True):
            for rpc in (False, True):
                with self.subTest(soap12=soap12, rpc=rpc):
                    self.assertEqual(["Rejected\tRejected\tliteral\tnull\tnull", "parts\t1"],
                                     self.observe(False, soap12, rpc))

    def test_encoded_fault_retains_its_own_namespace_and_style(self):
        for soap12 in (False, True):
            for rpc in (False, True):
                with self.subTest(soap12=soap12, rpc=rpc):
                    self.assertEqual(["Rejected\tRejected\tencoded\turn:fault-wire\t[" + ENCODING + "]",
                                      "parts\t1"], self.observe(True, soap12, rpc))


if __name__ == "__main__":
    unittest.main()
