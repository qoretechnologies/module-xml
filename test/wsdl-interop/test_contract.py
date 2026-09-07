#!/usr/bin/env python3
"""Namespace and WSDL reference inventory regressions.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

from pathlib import Path
import unittest

from lxml import etree

import contract


ROOT = Path(__file__).resolve().parent


class ContractTest(unittest.TestCase):
    def test_qname_context_and_invalid_names(self):
        doc = etree.fromstring(b'<root xmlns="urn:outer" xmlns:p="urn:first">'
                               b'<child xmlns="" xmlns:p="urn:second"/></root>')
        self.assertEqual("{urn:first}value", contract.qname(doc, "p:value"))
        self.assertEqual("{urn:second}value", contract.qname(doc[0], "p:value"))
        self.assertEqual("{urn:outer}value", contract.qname(doc, "value"))
        self.assertEqual("value", contract.qname(doc[0], "value"))
        for name in (None, "", "missing:value", "a:b:c", ":value", "p:", "a b", "1name", "{urn:a}b"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                contract.qname(doc, name)

    def test_real_echo_request_and_response_components(self):
        doc = etree.parse(str(ROOT / "w3c/BooleanElement/echoBooleanElement.wsdl")).getroot()
        value = contract.describe(doc)
        ns = "{http://www.w3.org/2002/ws/databinding/examples/6/09/}"
        self.assertEqual([], value["errors"])
        self.assertEqual([], value["imports"])
        binding = value["bindings"][ns + "SoapBinding"]
        self.assertEqual("11", binding["soap_version"])
        self.assertEqual(ns + "BooleanElementPortType", binding["port_type"])
        op = value["port_types"][binding["port_type"]]["operations"][0]
        self.assertEqual(ns + "echoBooleanElementRequest", op["input"]["message"])
        self.assertEqual(ns + "echoBooleanElementResponse", op["output"]["message"])
        for direction in ("input", "output"):
            part = value["messages"][op[direction]["message"]]["parts"][0]
            self.assertEqual(ns + "echoBooleanElement", part["element"])
            self.assertTrue(part["declared_inline"])
        self.assertEqual(ns + "SoapBinding", value["ports"][0]["binding"])
        self.assertEqual(ns + "BooleanElementService", value["ports"][0]["service"])

    def test_soap12_and_mime_binding_inventory(self):
        doc = etree.parse(str(ROOT / "cxf/hello_world_soap12.wsdl")).getroot()
        value = contract.describe(doc)
        self.assertIn("12", [b["soap_version"] for b in value["bindings"].values()])
        self.assertEqual([], value["errors"])
        doc = etree.parse(str(ROOT / "cxf/no_body_parts.wsdl")).getroot()
        value = contract.describe(doc)
        extensions = [extension for b in value["bindings"].values() for op in b["operations"]
                      for direction in ("input", "output") for extension in op.get(direction, {}).get("extensions", [])]
        self.assertEqual(2, len(extensions))
        for extension in extensions:
            self.assertEqual("{http://schemas.xmlsoap.org/wsdl/mime/}multipartRelated", extension["element"])
            body = extension["children"][0]["children"][0]
            self.assertEqual("{http://schemas.xmlsoap.org/wsdl/soap/}body", body["element"])
            self.assertNotIn("parts", body["attributes"])
            self.assertEqual("mimeAttachment", extension["children"][1]["children"][0]["attributes"]["part"])

    def test_explicit_empty_parts(self):
        wire = b'''<definitions xmlns="http://schemas.xmlsoap.org/wsdl/" xmlns:t="urn:test"
          xmlns:s="http://schemas.xmlsoap.org/wsdl/soap/" targetNamespace="urn:test">
          <portType name="p"/><binding name="b" type="t:p"><s:binding/>
            <operation name="o"><input><s:body parts="" use="literal"/></input>
              <output><s:body use="literal"/></output></operation>
          </binding></definitions>'''
        value = contract.describe(etree.fromstring(wire))
        op = value["bindings"]["{urn:test}b"]["operations"][0]
        self.assertEqual("", op["input"]["extensions"][0]["attributes"]["parts"])
        self.assertNotIn("parts", op["output"]["extensions"][0]["attributes"])

    def test_unresolved_and_duplicate_components_are_reported(self):
        wire = b'''<definitions xmlns="http://schemas.xmlsoap.org/wsdl/" xmlns:t="urn:test"
             targetNamespace="urn:test">
          <message name="m"><part name="p"/><part name="p" type="missing:int"/></message>
          <message name="m"/>
          <portType name="p"><operation name="o"><input message="t:unknown"/></operation></portType>
          <binding name="b" type="t:unknown"/>
          <service name="s"><port name="p" binding="t:unknown"/></service>
        </definitions>'''
        value = contract.describe(etree.fromstring(wire))
        self.assertEqual({"WSDL-COMPONENT-NAME", "WSDL-PART-NAME", "WSDL-PART-TYPE", "WSDL-QNAME",
                          "WSDL-UNRESOLVED-MESSAGE", "WSDL-UNRESOLVED-PORT-TYPE", "WSDL-UNRESOLVED-BINDING"},
                         {e["err"] for e in value["errors"]})
        with self.assertRaisesRegex(ValueError, "not a WSDL 1.1"):
            contract.describe(etree.fromstring(b"<schema/>"))

    def test_missing_wrappers_are_visible(self):
        wire = b'''<definitions xmlns="http://schemas.xmlsoap.org/wsdl/" xmlns:t="urn:test"
          targetNamespace="urn:test"><message name="m"><part name="p" element="t:missing"/></message>
        </definitions>'''
        value = contract.describe(etree.fromstring(wire))
        part = value["messages"]["{urn:test}m"]["parts"][0]
        self.assertEqual("{urn:test}missing", part["element"])
        self.assertFalse(part["declared_inline"])
        # An import may supply this declaration: absence inline alone is not a schema error.
        self.assertEqual([], value["errors"])


if __name__ == "__main__":
    unittest.main()
