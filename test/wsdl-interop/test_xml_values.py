#!/usr/bin/env python3
"""Independent validation and information checks for the explicit XML value API.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

from pathlib import Path
import subprocess
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent


SCHEMA = b'''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="urn:r">
  <xs:element name="record"><xs:complexType mixed="true">
    <xs:sequence><xs:element name="item" type="xs:int" maxOccurs="unbounded"/></xs:sequence>
    <xs:attribute name="amount" type="xs:decimal" use="required"/>
    <xs:attribute name="type" type="xs:QName" use="required"/>
    <xs:attribute name="big" type="xs:unsignedLong" use="required"/>
  </xs:complexType></xs:element>
</xs:schema>'''


class XmlValuesTest(unittest.TestCase):
    def test_lexical_qname_mixed_content_and_reconstruction(self):
        compiled = etree.XMLSchema(etree.fromstring(SCHEMA))
        documents, expected = {}, {}
        for value, valid in (("0", True), ("-2147483648", True), ("invalid", False)):
            source = ('<p:record xmlns:p="urn:r" xmlns:t="urn:types" amount="009.00" '
                      'type="t:Special" big="18446744073709551615">before<?route next?>'
                      f'<![CDATA[009]]><!--note--><item>{value}</item> <item>7</item>after</p:record>')
            for mode in ("original", "restored"):
                with self.subTest(value=value, mode=mode):
                    process = subprocess.run(
                        ["qore", "--enable-debug", str(Path(__file__).with_name("xml-value.qr")), source, mode],
                        capture_output=True, text=True, timeout=30)
                    self.assertEqual(0, process.returncode, process.stderr)
                    self.assertEqual("", process.stderr)
                    parent = etree.fromstring(process.stdout.encode(), etree.XMLParser(strip_cdata=False))
                    self.assertEqual("{urn:parent}collection", parent.tag)
                    self.assertEqual(1, len(parent))
                    payload = parent[0]
                    self.assertEqual("{urn:r}record", payload.tag)
                    self.assertEqual({"amount": "009.00", "type": "t:Special",
                                      "big": "18446744073709551615"}, dict(payload.attrib))
                    self.assertEqual("urn:types", payload.nsmap["t"])
                    self.assertEqual([("item", value), ("item", "7")],
                                     [(child.tag, child.text) for child in payload if isinstance(child.tag, str)])
                    self.assertEqual(["before", "009", value, " ", "7", "after"], list(payload.itertext()))
                    self.assertEqual("route", payload[0].target)
                    self.assertEqual("next", payload[0].text)
                    self.assertEqual("note", payload[1].text)
                    self.assertIn(b"<![CDATA[009]]>", etree.tostring(payload))
                    # XML values retain invalid XSD lexical content too: schema validation
                    # belongs to the schema consumer, not this generic XML representation.
                    self.assertEqual(valid, compiled.validate(payload), str(compiled.error_log))
                    name = f"{value}/{mode}"
                    documents[name] = etree.tostring(payload)
                    expected[name] = valid
        results = run_independent([SchemaJob("xml-value", "http://example.invalid/xml-value.xsd",
                                             SCHEMA, documents)])
        self.assertEqual(6, len(results["documents"]))
        for name, result in results["documents"].items():
            self.assertEqual(expected[name], result["ok"], (name, result))


if __name__ == "__main__":
    unittest.main()
