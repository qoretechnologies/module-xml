#!/usr/bin/env python3
"""Independently observe explicit and omitted SOAP body parts with WSDL4J.

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
from independent import SchemaJob, run
import jvm

ROOT = Path(__file__).resolve().parent
ORACLE = ROOT / "oracle"
WSDL = "http://schemas.xmlsoap.org/wsdl/"
SOAP11 = "http://schemas.xmlsoap.org/wsdl/soap/"
SOAP12 = "http://schemas.xmlsoap.org/wsdl/soap12/"


class WsdlBodyPartsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = json.loads((ORACLE / "wsdl4j-manifest.json").read_text())
        if (manifest["implementation"], manifest["version"]) != ("WSDL4J", "1.6.3"):
            raise ValueError("unexpected oracle version")
        for artifact in manifest["artifacts"]:
            data = (ORACLE / artifact["path"]).read_bytes()
            if len(data) != artifact["size"] or hashlib.sha256(data).hexdigest() != artifact["sha256"]:
                raise ValueError("modified oracle artifact: " + artifact["path"])
        cls.directory = tempfile.TemporaryDirectory(prefix="wsdl-body-parts-oracle-")
        cls.addClassCleanup(cls.directory.cleanup)
        cls.classes = Path(cls.directory.name) / "classes"
        cls.classes.mkdir()
        cls.jar = ORACLE / "wsdl4j-1.6.3.jar"
        result = subprocess.run(["javac", "-Xlint:all", "-Werror", "-cp", str(cls.jar),
                                 "-d", str(cls.classes), str(ORACLE / "WsdlBodyPartsOracle.java")],
                                capture_output=True, text=True, timeout=60, check=True, env=jvm.environment())
        if result.stdout or result.stderr:
            raise RuntimeError("unexpected compiler diagnostics")

    def observe(self, selection, soap12=False, rpc=False):
        tree = etree.parse(str(ROOT / "regressions/body-parts/document.wsdl"))
        for body in tree.iter(f"{{{SOAP11}}}body"):
            if selection is None:
                del body.attrib["parts"]
            else:
                body.set("parts", selection)
        if rpc:
            tree.find(f".//{{{SOAP11}}}binding").set("style", "rpc")
            for part in tree.find(f"{{{WSDL}}}message").iter(f"{{{WSDL}}}part"):
                del part.attrib["element"]
                part.set("type", "xs:int")
        raw = etree.tostring(tree)
        if soap12:
            raw = raw.replace(SOAP11.encode(), SOAP12.encode())
        path = Path(self.directory.name) / "input.wsdl"
        path.write_bytes(raw)
        result = subprocess.run(["java", "-cp", str(self.classes) + os.pathsep + str(self.jar),
                                 "WsdlBodyPartsOracle", str(path)], capture_output=True, text=True, timeout=30,
                                 env=jvm.environment())
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        return result.stdout.splitlines()

    def check(self, selection, label, parts):
        expected = []
        for direction in ("input", "output"):
            expected += [direction + "\t" + label] + ["part\t" + part for part in parts]
        for soap12 in (False, True):
            for rpc in (False, True):
                with self.subTest(soap12=soap12, rpc=rpc):
                    self.assertEqual(expected, self.observe(selection, soap12, rpc))

    def test_omitted_selects_all_parts(self):
        self.check(None, "omitted", ["left", "right"])

    def test_explicit_empty_selects_no_parts(self):
        self.check("", "[]", [])

    def test_wsdl4j_whitespace_only_limitation(self):
        # WSDL4J splits on SPACE alone; character-reference TAB/CR/LF remains one unknown token.
        self.check(" \t\r\n ", "[\\t\\r\\n]", [])

    def test_subset_preserves_explicit_order(self):
        self.check("right left", "[right, left]", ["right", "left"])

    def test_wsdl4j_tab_separator_limitation(self):
        self.check("right\tleft", "[right\\tleft]", [])

    def test_independent_xml_list_whitespace_normalization(self):
        # A list permits the empty value required by the SOAP literal profile.
        # Enumeration tests the normalized list value, not merely lexical validity.
        schema = b'''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
          <xs:simpleType name="Names"><xs:list itemType="xs:NCName"/></xs:simpleType>
          <xs:simpleType name="Selection"><xs:restriction base="Names">
            <xs:enumeration value=""/><xs:enumeration value="right left"/>
          </xs:restriction></xs:simpleType>
          <xs:element name="selection"><xs:complexType>
            <xs:attribute name="parts" type="Selection" use="required"/>
          </xs:complexType></xs:element></xs:schema>'''
        values = {"tab": ("right&#9;left", True), "line": ("right&#10;left", True),
                  "cr": ("right&#13;left", True), "empty": ("", True),
                  "blank": (" &#9;&#13;&#10; ", True), "order": ("left right", False),
                  "nbsp": ("right&#160;left", False), "unknown": ("right missing", False)}
        documents = {name: ('<selection parts="' + value + '"/>').encode()
                     for name, (value, valid) in values.items()}
        report = run([SchemaJob("body-parts", "urn:qore:body-parts", schema, documents)])
        self.assertTrue(report["schemas"]["body-parts"]["ok"], report)
        self.assertEqual([], report["schemas"]["body-parts"]["warnings"])
        for name, (value, valid) in values.items():
            with self.subTest(name=name):
                self.assertEqual(valid, report["documents"][name]["ok"], report)
                self.assertEqual([], report["documents"][name]["warnings"])

    def test_single_selected_part(self):
        self.check("left", "[left]", ["left"])


if __name__ == "__main__":
    unittest.main()
