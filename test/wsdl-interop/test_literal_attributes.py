#!/usr/bin/env python3
"""Literal scalar attributes must not become SOAP encoding references.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

from pathlib import Path
import os
import shlex
import shutil
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
import survey
from test_attribute_values import description, NS, XSD


def schema():
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
      <xs:complexType name="Item"><xs:simpleContent><xs:extension base="xs:string">
        <xs:attribute name="id" type="xs:int" use="required"/>
        <xs:attribute name="href" type="xs:anyURI"/>
      </xs:extension></xs:simpleContent></xs:complexType>
      <xs:complexType name="Record"><xs:sequence>
        <xs:element name="item" type="t:Item" maxOccurs="2"/>
      </xs:sequence><xs:attribute name="id" type="xs:unsignedLong"/>
        <xs:attribute name="href" type="xs:anyURI"/>
        <xs:attribute name="root" type="xs:boolean"/>
        <xs:attribute name="id" type="xs:string" form="qualified"/>
        <xs:attribute name="href" type="xs:string" form="qualified"/>
      </xs:complexType><xs:element name="Submit" type="t:Record"/>
      <xs:element name="Reply" type="t:Record"/>
    </xs:schema>'''


class LiteralAttributesTest(unittest.TestCase):
    def test_literal_attributes_validate_and_retain_values_in_both_directions(self):
        source = schema().encode()
        validator = etree.XMLSchema(etree.fromstring(source))
        expected, documents, output_documents, cases = {}, {}, {}, []
        with tempfile.TemporaryDirectory(prefix="wsdl-literal-attributes-") as temporary:
            root = Path(temporary)
            mode = os.environ.get("QORE_EXEC_MODE", "jit")
            self.assertIn(mode, ("ast", "ir", "jit", "tiered"))
            executable = shutil.which("qore")
            self.assertIsNotNone(executable)
            worker = root / "qore-worker"
            worker.write_text(f'#!/bin/sh\nexec {shlex.quote(executable)} -b --exec-mode={mode} "$@"\n')
            worker.chmod(0o700)
            for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                wsdl = root / f"soap{version}.wsdl"
                wsdl.write_text(description(version, source.decode()))
                messages = []
                for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                    for label, attributes, item_id, valid in (
                        ("id", 'id="18446744073709551615"', "7", True),
                        ("href", 'href="#not-a-reference"', "7", True),
                        ("empty-href", 'href=""', "7", True),
                        ("root", 'root="false"', "7", True),
                        ("collision", 'id="18446744073709551615" href="https://example.invalid/" '
                            't:id="ordinary" t:href="#qualified"', "7", True),
                        ("id-overflow", 'id="18446744073709551616"', "7", False),
                        ("id-negative", 'id="-1"', "7", False),
                        ("nested-id", 'id="1"', "not-an-integer", False),
                    ):
                        name = f"{version}/{direction}/{label}"
                        payload = f'''<t:{wrapper} xmlns:t="{NS}" {attributes}>
                            <item id="{item_id}" href="#nested">first</item>
                            <item id="8" href="">second</item></t:{wrapper}>'''.encode()
                        element = etree.fromstring(payload)
                        self.assertEqual(valid, validator.validate(element), str(validator.error_log))
                        wire = f'<s:Envelope xmlns:s="{envelope_ns}"><s:Body>'.encode() + payload \
                            + b'</s:Body></s:Envelope>'
                        path = root / name.replace("/", "-")
                        path.write_bytes(wire)
                        messages.append({"file": name, "path": str(path), "direction": direction})
                        expected[name] = valid
                        documents[name] = payload
                cases.append({"name": "LiteralAttributes" + version, "wsdl": str(wsdl),
                              "base": "http://example.invalid/", "operation": "submit",
                              "binding": "Soap" + version, "messages": messages})
            oracle = run_independent([SchemaJob("literal", "http://example.invalid/literal.xsd", source, documents)])
            self.assertTrue(oracle["schemas"]["literal"]["ok"])
            self.assertEqual([], oracle["schemas"]["literal"]["warnings"])
            self.assertEqual(set(expected), set(oracle["documents"]))
            for name, result in oracle["documents"].items():
                self.assertEqual(expected[name], result["ok"], (name, result))
                self.assertEqual([], result["warnings"])
            rows = survey.run_worker(cases, {}, qore=str(worker))
            survey.stage_accounting(cases, rows)
            self.assertEqual(2, sum(row["stage"] == "parse" for row in rows))
            self.assertEqual(32, sum(row["stage"] == "deserialize" for row in rows))
            for row in rows:
                with self.subTest(stage=row["stage"], file=row.get("file")):
                    if row["stage"] == "parse":
                        self.assertTrue(row["ok"], row)
                        continue
                    name = row["file"]
                    if not expected[name]:
                        self.assertEqual("deserialize", row["stage"], row)
                        self.assertFalse(row["ok"], row)
                        self.assertEqual("SOAP-DESERIALIZATION-ERROR", row["err"])
                        continue
                    self.assertTrue(row["ok"], row)
                    if row["stage"] != "serialize":
                        continue
                    envelope = etree.fromstring(row["body"].encode())
                    version = name.split("/")[0]
                    self.assertEqual(f'{{{survey.SOAP_NAMESPACES[int(version == "12")]}}}Envelope', envelope.tag)
                    payload = envelope.find("{*}Body")[0]
                    before = etree.fromstring(documents[name])
                    self.assertTrue(validator.validate(payload), str(validator.error_log))
                    self.assertEqual(before.tag, payload.tag)
                    self.assertEqual(dict(before.attrib), dict(payload.attrib))
                    self.assertEqual([(child.tag, child.text, dict(child.attrib)) for child in before],
                                     [(child.tag, child.text, dict(child.attrib)) for child in payload])
                    self.assertNotIn(name, output_documents)
                    output_documents[name] = etree.tostring(payload)
        self.assertEqual({name for name, valid in expected.items() if valid}, set(output_documents))
        oracle = run_independent([SchemaJob("output", "http://example.invalid/literal.xsd", source, output_documents)])
        self.assertTrue(oracle["schemas"]["output"]["ok"])
        self.assertEqual([], oracle["schemas"]["output"]["warnings"])
        self.assertEqual(set(output_documents), set(oracle["documents"]))
        for name, result in oracle["documents"].items():
            self.assertTrue(result["ok"], (name, result))
            self.assertEqual([], result["warnings"])


if __name__ == "__main__":
    unittest.main()
