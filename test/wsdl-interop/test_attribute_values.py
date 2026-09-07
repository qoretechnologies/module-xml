#!/usr/bin/env python3
"""Independent SOAP request/response checks for attribute value constraints.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

from pathlib import Path
import json
import subprocess
import tempfile
import unittest

from lxml import etree

import survey
from independent import SchemaJob, run as run_independent


XSD = "http://www.w3.org/2001/XMLSchema"
WSDL = "http://schemas.xmlsoap.org/wsdl/"
NS = "urn:qore:attribute-values"


def schema():
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
      <xs:complexType name="Record">
        <xs:attribute name="flag" type="xs:boolean" default="false"/>
        <xs:attribute name="count" type="xs:int" default="7"/>
        <xs:attribute name="unit" type="xs:string" fixed="EUR"/>
      </xs:complexType>
      <xs:element name="Submit" type="t:Record"/>
      <xs:element name="Reply" type="t:Record"/>
    </xs:schema>'''


def description(version, schema_text=None):
    soap = "http://schemas.xmlsoap.org/wsdl/soap" + ("12" if version == "12" else "") + "/"
    return f'''<w:definitions xmlns:w="{WSDL}" xmlns:t="{NS}" xmlns:s="{soap}" targetNamespace="{NS}">
      <w:types>{schema() if schema_text is None else schema_text}</w:types>
      <w:message name="Request"><w:part name="body" element="t:Submit"/></w:message>
      <w:message name="Response"><w:part name="body" element="t:Reply"/></w:message>
      <w:portType name="Port"><w:operation name="submit"><w:input message="t:Request"/>
        <w:output message="t:Response"/></w:operation></w:portType>
      <w:binding name="Soap{version}" type="t:Port"><s:binding style="document"
        transport="http://schemas.xmlsoap.org/soap/http"/><w:operation name="submit">
        <s:operation soapAction="urn:submit"/><w:input><s:body use="literal"/></w:input>
        <w:output><s:body use="literal"/></w:output></w:operation></w:binding>
      <w:service name="Values"><w:port name="Port{version}" binding="t:Soap{version}">
        <s:address location="http://example.invalid/values"/></w:port></w:service>
    </w:definitions>'''


class AttributeValuesTest(unittest.TestCase):
    def test_provider_values_and_generated_examples_in_actual_bindings(self):
        attributes = '''<xs:attribute name="code" fixed="EUR" use="required"/>
          <xs:attribute name="flag" type="xs:boolean" fixed="false"/>
          <xs:attribute name="count" type="xs:int" default="0"/>
          <xs:attribute name="text" default=""/>
          <xs:attribute name="unit" type="xs:string" fixed="kg" form="qualified"/>'''
        models = {
            "empty": attributes,
            "sequence": '<xs:sequence><xs:element name="child" type="xs:int"/></xs:sequence>' + attributes,
            "simple": '<xs:simpleContent><xs:extension base="xs:string">' + attributes
                      + '</xs:extension></xs:simpleContent>',
        }
        jobs = []
        with tempfile.TemporaryDirectory(prefix="wsdl-attribute-consumers-") as temporary:
            for kind, content in models.items():
                source = f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
                  <xs:complexType name="Record">{content}</xs:complexType>
                  <xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/>
                </xs:schema>'''
                compiled = etree.XMLSchema(etree.fromstring(source.encode()))
                documents = {}
                for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                    path = Path(temporary) / f"{kind}-{version}.wsdl"
                    path.write_text(description(version, source))
                    process = subprocess.run(
                        ["qore", "--enable-debug", str(Path(__file__).with_name("attribute-consumers.qr")),
                         str(path), "Soap" + version], text=True, capture_output=True, timeout=30, check=True)
                    self.assertEqual("", process.stderr)
                    rows = [json.loads(line) for line in process.stdout.splitlines()]
                    self.assertEqual(["request", "response"], [r["direction"] for r in rows])
                    for row in rows:
                        self.assertEqual({"code": "EUR", "flag": False, "count": 0, "text": "", "unit": "kg"},
                                         row["value"]["^attributes^"])
                        self.assertIs(False, row["value"]["^attributes^"]["flag"])
                        self.assertIs(int, type(row["value"]["^attributes^"]["count"]))
                        envelope = etree.fromstring(row["body"].encode())
                        self.assertEqual(f"{{{envelope_ns}}}Envelope", envelope.tag)
                        payload = envelope.find("{*}Body")[0]
                        self.assertEqual(f"{{{NS}}}" + ("Submit" if row["direction"] == "request" else "Reply"),
                                         payload.tag)
                        self.assertEqual({"code": "EUR", "flag": "false", "count": "0", "text": "",
                                          f"{{{NS}}}unit": "kg"}, dict(payload.attrib))
                        if kind == "simple":
                            self.assertEqual("abc", payload.text)
                        elif kind == "sequence":
                            self.assertEqual([("child", "123")], [(c.tag, c.text) for c in payload])
                        self.assertTrue(compiled.validate(payload), str(compiled.error_log))
                        documents[f"{kind}/{version}/{row['direction']}"] = etree.tostring(payload)
                jobs.append(SchemaJob(kind, f"http://example.invalid/{kind}.xsd", source.encode(), documents))
        oracle = run_independent(jobs)
        self.assertEqual(12, len(oracle["documents"]))
        for name, result in oracle["documents"].items():
            self.assertTrue(result["ok"], (name, result))

    def test_qualified_collisions_in_actual_bindings_and_both_directions(self):
        source_schema = f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
          <xs:complexType name="Record">
            <xs:attribute name="code" type="xs:int" use="required"/>
            <xs:attribute name="code" type="xs:boolean" form="qualified" use="required"/>
          </xs:complexType><xs:element name="Submit" type="t:Record"/>
          <xs:element name="Reply" type="t:Record"/></xs:schema>'''
        compiled = etree.XMLSchema(etree.fromstring(source_schema.encode()))
        cases, documents, expected = [], {}, {}
        with tempfile.TemporaryDirectory(prefix="wsdl-qualified-attributes-") as temporary:
            root = Path(temporary)
            for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                wsdl = root / f"soap{version}.wsdl"
                wsdl.write_text(description(version, source_schema))
                messages = []
                for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                    for variant, attributes in (("valid", 'code="7" p:code="false"'),
                                                ("missing", 'code="7"'),
                                                ("wrong-namespace", 'code="7" q:code="false"')):
                        name = f"{version}/{direction}/{variant}"
                        source = f'''<s:Envelope xmlns:s="{envelope_ns}" xmlns:t="{NS}" xmlns:p="urn:shadowed"
                            xmlns:q="urn:wrong"><s:Body xmlns:p="{NS}"><t:{wrapper} {attributes}/></s:Body></s:Envelope>'''
                        path = root / name.replace("/", "-")
                        path.write_text(source)
                        payload = etree.fromstring(source.encode()).find("{*}Body")[0]
                        valid = variant == "valid"
                        self.assertEqual(valid, compiled.validate(payload), str(compiled.error_log))
                        documents[name], expected[name] = etree.tostring(payload), valid
                        messages.append({"file": name, "path": str(path), "direction": direction})
                cases.append({"name": "Qualified" + version, "wsdl": str(wsdl), "base": "http://example.invalid/",
                              "operation": "submit", "binding": "Soap" + version, "messages": messages})
            rows = survey.run_worker(cases, {})
        accounting = survey.stage_accounting(cases, rows)["counts"]
        self.assertEqual(4, accounting["serialize"]["ok"], rows)
        self.assertEqual(8, accounting["deserialize"]["failed"], rows)
        for row in rows:
            if row["stage"] == "parse":
                self.assertTrue(row["ok"], row)
            elif not expected[row["file"]]:
                self.assertFalse(row["ok"], row)
                self.assertEqual("SOAP-DESERIALIZATION-ERROR", row["err"])
            elif row["stage"] == "serialize":
                version, direction, _ = row["file"].split("/")
                envelope = etree.fromstring(row["body"].encode())
                self.assertEqual(f"{{{survey.SOAP_NAMESPACES[int(version == '12')]}}}Envelope", envelope.tag)
                payload = envelope.find("{*}Body")[0]
                self.assertEqual(f"{{{NS}}}" + ("Submit" if direction == "request" else "Reply"), payload.tag)
                self.assertEqual({"code": "7", f"{{{NS}}}code": "false"}, dict(payload.attrib))
                self.assertTrue(compiled.validate(payload), str(compiled.error_log))
                documents[row["file"] + "/output"] = etree.tostring(payload)
                expected[row["file"] + "/output"] = True
            else:
                self.assertTrue(row["ok"], row)
        oracle = run_independent([SchemaJob("qualified", "http://example.invalid/qualified.xsd",
                                           source_schema.encode(), documents)])
        self.assertEqual(16, len(oracle["documents"]))
        for name, valid in expected.items():
            self.assertEqual(valid, oracle["documents"][name]["ok"], (name, oracle["documents"][name]))

    def test_defaults_fixed_and_explicit_values_in_both_directions(self):
        compiled = etree.XMLSchema(etree.fromstring(schema().encode()))
        cases, documents, expected = [], {}, {}
        with tempfile.TemporaryDirectory(prefix="wsdl-attribute-values-") as temporary:
            root = Path(temporary)
            for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                wsdl = root / f"soap{version}.wsdl"
                wsdl.write_text(description(version))
                messages = []
                for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                    for variant, attributes in (("defaults", ""), ("explicit", 'flag="0" count="0" unit="EUR"'),
                                                ("wrong-fixed", 'unit="USD"')):
                        name = f"{version}/{direction}/{variant}"
                        body = f'<t:{wrapper} xmlns:t="{NS}" {attributes}/>'
                        source = f'<s:Envelope xmlns:s="{envelope_ns}"><s:Body>{body}</s:Body></s:Envelope>'
                        path = root / name.replace("/", "-")
                        path.write_text(source)
                        payload = etree.fromstring(body.encode())
                        valid = variant != "wrong-fixed"
                        self.assertEqual(valid, compiled.validate(payload), str(compiled.error_log))
                        documents[name] = etree.tostring(payload)
                        expected[name] = valid
                        messages.append({"file": name, "path": str(path), "direction": direction})
                cases.append({"name": "Values" + version, "wsdl": str(wsdl), "base": "http://example.invalid/",
                              "operation": "submit", "binding": "Soap" + version, "messages": messages})
            rows = survey.run_worker(cases, {})
        self.assertEqual(8, survey.stage_accounting(cases, rows)["counts"]["serialize"]["ok"], rows)
        for row in rows:
            if row["stage"] == "parse":
                self.assertTrue(row["ok"], row)
                continue
            if not expected[row["file"]]:
                self.assertEqual("deserialize", row["stage"])
                self.assertEqual("SOAP-DESERIALIZATION-ERROR", row["err"])
                self.assertFalse(row["ok"], row)
                continue
            self.assertTrue(row["ok"], row)
            if row["stage"] != "serialize":
                continue
            version, direction, variant = row["file"].split("/")
            envelope = etree.fromstring(row["body"].encode())
            self.assertEqual(f"{{{survey.SOAP_NAMESPACES[int(version == '12')]}}}Envelope", envelope.tag)
            payload = envelope.find("{*}Body")[0]
            self.assertEqual(f"{{{NS}}}" + ("Submit" if direction == "request" else "Reply"), payload.tag)
            self.assertEqual({"flag": "false", "count": "7" if variant == "defaults" else "0", "unit": "EUR"},
                             dict(payload.attrib))
            self.assertTrue(compiled.validate(payload), str(compiled.error_log))
            name = row["file"] + "/output"
            documents[name], expected[name] = etree.tostring(payload), True
        oracle = run_independent([SchemaJob("values", "http://example.invalid/values.xsd", schema().encode(), documents)])
        self.assertEqual(20, len(oracle["documents"]))
        for name, valid in expected.items():
            self.assertEqual(valid, oracle["documents"][name]["ok"], (name, oracle["documents"][name]))

    def test_attribute_defaults_reject_invalid_schema_constraints(self):
        cases, jobs = [], []
        examples = {
            "bad-bound": '<xs:attribute name="count" default="2"><xs:simpleType><xs:restriction base="xs:int">'
                         '<xs:maxInclusive value="1"/></xs:restriction></xs:simpleType></xs:attribute>',
            "bad-fixed-override": '<xs:attribute ref="t:unit" fixed="USD"/>',
            "default-over-fixed": '<xs:attribute ref="t:unit" default="EUR"/>',
        }
        with tempfile.TemporaryDirectory(prefix="wsdl-invalid-attribute-values-") as temporary:
            for name, declaration in examples.items():
                source = f'<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">'
                source += '<xs:attribute name="unit" type="xs:string" fixed="EUR"/>'
                source += f'<xs:complexType name="Record">{declaration}</xs:complexType></xs:schema>'
                try:
                    etree.XMLSchema(etree.fromstring(source.encode()))
                except etree.XMLSchemaParseError:
                    pass
                else:
                    # libxml2 accepts a different local fixed value; au-props-correct.2 forbids it.
                    # Qore and pinned Xerces must reject below. See the attribute-value oracle notes.
                    self.assertEqual("bad-fixed-override", name)
                path = Path(temporary) / (name + ".xsd")
                path.write_text(source)
                cases.append({"name": name, "wsdl": str(path), "base": "http://example.invalid/",
                              "schema_only": True, "messages": []})
                jobs.append(SchemaJob(name, "http://example.invalid/" + path.name, source.encode()))
            rows = survey.run_worker(cases, {})
        self.assertEqual(3, len(rows))
        for row in rows:
            self.assertFalse(row["ok"], row)
            self.assertEqual("WSDL-ERROR", row["err"])
        oracle = run_independent(jobs)
        for name in examples:
            self.assertFalse(oracle["schemas"][name]["ok"], (name, oracle["schemas"][name]))


if __name__ == "__main__":
    unittest.main()
