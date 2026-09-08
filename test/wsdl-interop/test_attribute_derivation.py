#!/usr/bin/env python3
"""XSD 1.0 attribute derivation constraints and SOAP consumer integration.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

from pathlib import Path
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
import survey
from test_attribute_values import description, NS, XSD


def attribute(type_name="xs:int", extra=""):
    return f'<xs:attribute name="a" type="{type_name}" {extra}/>'


def schema(base, derived, method="restriction", simple=False, declarations=""):
    if simple:
        base = f'<xs:simpleContent><xs:extension base="xs:int">{base}</xs:extension></xs:simpleContent>'
    kind = "simpleContent" if simple else "complexContent"
    return (f'<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">{declarations}'
            f'<xs:complexType name="Base">{base}</xs:complexType><xs:complexType name="Record">'
            f'<xs:{kind}><xs:{method} base="t:Base">{derived}</xs:{method}></xs:{kind}></xs:complexType>'
            '<xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/>'
            '</xs:schema>')


class AttributeDerivationTest(unittest.TestCase):
    def test_schema_constraint_matrix(self):
        # libxml2 misses fixed-constraint preservation. Keep its exact disagreement visible;
        # normative derivation-ok-restriction.2.1.3 and pinned Xerces determine rejection.
        cases = {
            "required-optional": (attribute(extra='use="required"'), attribute(), False),
            "required-prohibited": (attribute(extra='use="required"'),
                                    attribute(extra='use="prohibited"'), False),
            "optional-required": (attribute(), attribute("xs:short", 'use="required"'), True),
            "omitted-required": (attribute(extra='use="required"'), "", True),
            "optional-prohibited": (attribute(), attribute(extra='use="prohibited"'), True),
            "fixed-absent": (attribute(extra='fixed="1"'), attribute(), False),
            "fixed-default": (attribute(extra='fixed="1"'), attribute(extra='default="1"'), False),
            "fixed-changed": (attribute(extra='fixed="1"'), attribute(extra='fixed="2"'), False),
            "fixed-same": (attribute(extra='fixed="0"'), attribute(extra='fixed="0" use="required"'), True),
            "wrong-type": (attribute(), attribute("xs:string"), False),
            "wider-type": (attribute(), attribute("xs:integer"), False),
            "numeric-ancestry": (attribute("xs:decimal"), attribute("xs:unsignedInt"), True),
            "string-ancestry": (attribute("xs:string"), attribute("xs:NCName"), True),
            "float-double": (attribute("xs:float"), attribute("xs:double"), False),
        }
        sources, expected, lxml_expected = {}, {}, {}
        for simple in (False, True):
            for label, (base, derived, valid) in cases.items():
                name = f"{'simple' if simple else 'complex'}-{label}"
                sources[name] = schema(base, derived, simple=simple)
                expected[name] = valid
                lxml_expected[name] = valid or label in ("fixed-absent", "fixed-default", "fixed-changed")
            for label, derived, valid in (("duplicate", attribute(), False),
                                          ("different-namespace", attribute("xs:boolean", 'form="qualified"'), True)):
                name = f"{'simple' if simple else 'complex'}-extension-{label}"
                sources[name] = schema(attribute(), derived, "extension", simple)
                expected[name] = lxml_expected[name] = valid
        declarations = ('<xs:simpleType name="Value"><xs:restriction base="xs:int"/></xs:simpleType>'
                        '<xs:simpleType name="Sibling"><xs:restriction base="xs:int"/></xs:simpleType>'
                        '<xs:simpleType name="Narrow"><xs:restriction base="t:Value"/></xs:simpleType>'
                        '<xs:simpleType name="Items"><xs:list itemType="xs:int"/></xs:simpleType>'
                        '<xs:simpleType name="OtherItems"><xs:list itemType="xs:int"/></xs:simpleType>'
                        '<xs:simpleType name="TwoItems"><xs:restriction base="t:Items"><xs:length value="2"/>'
                        '</xs:restriction></xs:simpleType>'
                        '<xs:simpleType name="Either"><xs:union memberTypes="xs:boolean t:Value"/></xs:simpleType>')
        for name, base, derived, valid in (
                ("named-restriction", "t:Value", "t:Narrow", True),
                ("named-sibling", "t:Value", "t:Sibling", False),
                ("list-restriction", "t:Items", "t:TwoItems", True),
                ("list-sibling", "t:Items", "t:OtherItems", False),
                ("list-item", "t:Items", "xs:int", False),
                ("union-member", "t:Either", "t:Narrow", True),
                ("union-other", "t:Either", "xs:string", False),
                ("list-ur", "xs:anySimpleType", "t:Items", True),
                ("union-ur", "xs:anySimpleType", "t:Either", True)):
            sources[name] = schema(attribute(base), attribute(derived), declarations=declarations)
            expected[name] = lxml_expected[name] = valid
        for type_name, valid in (("xs:string", False), ("xs:integer", False), ("xs:short", True)):
            name = "inline-" + type_name.split(":")[1]
            sources[name] = schema("", f'<xs:simpleType><xs:restriction base="{type_name}"/></xs:simpleType>',
                                   simple=True)
            expected[name] = lxml_expected[name] = valid
        jobs, worker_cases = [], []
        with tempfile.TemporaryDirectory(prefix="wsdl-attribute-derivation-") as temporary:
            root = Path(temporary)
            for name, source in sources.items():
                try:
                    etree.XMLSchema(etree.fromstring(source.encode()))
                    valid = True
                except etree.XMLSchemaParseError:
                    valid = False
                self.assertEqual(lxml_expected[name], valid, name)
                jobs.append(SchemaJob(name, f"http://example.invalid/{name}.xsd", source.encode()))
                for version in ("11", "12"):
                    path = root / f"{name}-{version}.wsdl"
                    path.write_text(description(version, source))
                    worker_cases.append({"name": name + "/" + version, "wsdl": str(path),
                                         "base": "http://example.invalid/", "operation": "submit",
                                         "binding": "Soap" + version, "messages": []})
            rows = survey.run_worker(worker_cases, {})
        self.assertEqual(44, len(sources))
        self.assertEqual(88, len(rows))
        for row in rows:
            name = row["case"].split("/")[0]
            with self.subTest(name=row["case"]):
                self.assertEqual("parse", row["stage"])
                self.assertEqual(expected[name], row["ok"], row)
                if not expected[name]:
                    self.assertEqual("WSDL-ERROR", row["err"])
        oracle = run_independent(jobs)
        self.assertEqual(set(sources), set(oracle["schemas"]))
        for name, result in oracle["schemas"].items():
            self.assertEqual(expected[name], result["ok"], (name, result))

    def test_requests_and_responses_preserve_restricted_attributes(self):
        jobs = []
        for simple in (False, True):
            source = schema(attribute("xs:int", 'use="required"')
                            + '<xs:attribute name="flag" type="xs:boolean" fixed="false"/>'
                            + '<xs:attribute name="gone" type="xs:string"/>',
                            attribute("xs:short", 'use="required"')
                            + '<xs:attribute name="flag" type="xs:boolean" fixed="false"/>'
                            + '<xs:attribute name="gone" use="prohibited"/>', simple=simple)
            compiled = etree.XMLSchema(etree.fromstring(source.encode()))
            documents, expected, cases = {}, {}, []
            with tempfile.TemporaryDirectory(prefix="wsdl-attribute-derivation-wire-") as temporary:
                root = Path(temporary)
                for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                    path = root / f"{simple}-{version}.wsdl"
                    path.write_text(description(version, source))
                    messages = []
                    for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                        for variant, attrs in (("valid", 'a="0"'), ("missing", ''),
                                               ("fixed", 'a="0" flag="true"'),
                                               ("prohibited", 'a="0" gone="x"')):
                            name = f"{simple}/{version}/{direction}/{variant}"
                            payload_text = f'<t:{wrapper} xmlns:t="{NS}" {attrs}>{"0" if simple else ""}</t:{wrapper}>'
                            payload = etree.fromstring(payload_text.encode())
                            valid = variant == "valid"
                            self.assertEqual(valid, compiled.validate(payload), (name, str(compiled.error_log)))
                            documents[name], expected[name] = etree.tostring(payload), valid
                            message = root / name.replace("/", "-")
                            message.write_text(f'<s:Envelope xmlns:s="{envelope_ns}"><s:Body>{payload_text}'
                                               '</s:Body></s:Envelope>')
                            messages.append({"file": name, "path": str(message), "direction": direction})
                    cases.append({"name": str(simple) + version, "wsdl": str(path),
                                  "base": "http://example.invalid/", "operation": "submit",
                                  "binding": "Soap" + version, "messages": messages})
                rows = survey.run_worker(cases, {})
            counts = survey.stage_accounting(cases, rows)["counts"]
            self.assertEqual(4, counts["serialize"]["ok"], rows)
            self.assertEqual(12, counts["deserialize"]["failed"], rows)
            for row in rows:
                if row["stage"] == "parse":
                    self.assertTrue(row["ok"], row)
                elif not expected[row["file"]]:
                    self.assertFalse(row["ok"], row)
                    self.assertEqual("SOAP-DESERIALIZATION-ERROR", row["err"])
                else:
                    self.assertTrue(row["ok"], row)
                    if row["stage"] == "serialize":
                        _, version, direction, _ = row["file"].split("/")
                        envelope = etree.fromstring(row["body"].encode())
                        self.assertEqual(f"{{{survey.SOAP_NAMESPACES[int(version == '12')]}}}Envelope", envelope.tag)
                        payload = envelope.find("{*}Body")[0]
                        self.assertEqual(f"{{{NS}}}" + ("Submit" if direction == "request" else "Reply"), payload.tag)
                        self.assertEqual({"a": "0", "flag": "false"}, dict(payload.attrib))
                        self.assertEqual("0" if simple else None, payload.text)
                        self.assertTrue(compiled.validate(payload), str(compiled.error_log))
                        documents[row["file"] + "/output"] = etree.tostring(payload)
                        expected[row["file"] + "/output"] = True
            jobs.append(SchemaJob(str(simple), f"http://example.invalid/{simple}.xsd", source.encode(), documents))
            self.assertEqual(20, len(documents))
            oracle = run_independent([jobs[-1]])
            self.assertEqual(set(expected), set(oracle["documents"]))
            for name, result in oracle["documents"].items():
                self.assertEqual(expected[name], result["ok"], (name, result))


if __name__ == "__main__":
    unittest.main()
