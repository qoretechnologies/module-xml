#!/usr/bin/env python3
"""Independent XSD mixed/emptiable derivation checks and SOAP consumers.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
import survey
from test_attribute_values import description, NS, XSD


def schema(base, extra="", restriction=True, inline=True, attrs=""):
    method = "restriction" if restriction else "extension"
    scalar = '<xs:simpleType><xs:restriction base="xs:int"/></xs:simpleType>' if inline else ""
    facets = '<xs:minInclusive value="0"/>' if restriction and inline else ""
    return (f'<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">{extra}{base}'
            f'<xs:complexType name="Record"><xs:simpleContent><xs:{method} base="t:Base">{scalar}{facets}'
            f'{attrs}</xs:{method}></xs:simpleContent></xs:complexType>'
            '<xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/>'
            '</xs:schema>')


def base(particle="", mixed="true", attrs=""):
    return f'<xs:complexType name="Base" mixed="{mixed}">{particle}{attrs}</xs:complexType>'


OPTIONAL = '<xs:sequence><xs:element name="a" type="xs:int" minOccurs="0"/></xs:sequence>'
REQUIRED = '<xs:sequence><xs:element name="a" type="xs:int"/></xs:sequence>'
ATTR = '<xs:attribute name="unit" type="xs:string" use="required" fixed="kg"/>'


class MixedBaseTest(unittest.TestCase):
    def test_named_mixed_base_schema_matrix(self):
        particles = {
            "absent": ("", True), "empty-sequence": ('<xs:sequence/>', True),
            "empty-choice": ('<xs:choice/>', True), "empty-all": ('<xs:all/>', True),
            "optional-child": (OPTIONAL, True), "required-child": (REQUIRED, False),
            "optional-sequence": (REQUIRED.replace('<xs:sequence>', '<xs:sequence minOccurs="0">'), True),
            "zero-particle": (REQUIRED.replace('<xs:sequence>', '<xs:sequence minOccurs="0" maxOccurs="0">'), True),
            "optional-choice": ('<xs:choice><xs:element name="a" type="xs:int"/>'
                                '<xs:element name="b" type="xs:string" minOccurs="0"/></xs:choice>', True),
            "required-choice": ('<xs:choice><xs:element name="a" type="xs:int"/>'
                                '<xs:element name="b" type="xs:string"/></xs:choice>', False),
            "optional-all": ('<xs:all><xs:element name="a" type="xs:int" minOccurs="0"/>'
                             '<xs:element name="b" type="xs:string" minOccurs="0"/></xs:all>', True),
            "required-all": ('<xs:all><xs:element name="a" type="xs:int" minOccurs="0"/>'
                             '<xs:element name="b" type="xs:string"/></xs:all>', False),
            "nested-empty-choice": ('<xs:sequence><xs:choice><xs:sequence/>'
                                    '<xs:element name="a" type="xs:int"/></xs:choice></xs:sequence>', True),
            "optional-wildcard": ('<xs:sequence><xs:any minOccurs="0" processContents="lax"/></xs:sequence>', True),
            "required-wildcard": ('<xs:sequence><xs:any processContents="lax"/></xs:sequence>', False),
        }
        sources = {name: (schema(base(particle)), valid) for name, (particle, valid) in particles.items()}
        sources["element-only"] = schema(base(OPTIONAL, "false")), False
        sources["missing-inline"] = schema(base(OPTIONAL), inline=False), False
        sources["simple-extension"] = schema(base(OPTIONAL), restriction=False, inline=False), False
        sources["ur-extension"] = schema('<xs:complexType name="Base"><xs:complexContent>'
                                         '<xs:extension base="xs:anyType"/></xs:complexContent>'
                                         '</xs:complexType>'), True
        groups = ('<xs:group name="Optional"><xs:choice><xs:sequence><xs:element name="a" type="xs:int"'
                  ' minOccurs="0"/></xs:sequence><xs:element name="b" type="xs:int"/></xs:choice></xs:group>'
                  '<xs:group name="Required"><xs:sequence><xs:element name="c" type="xs:int"/>'
                  '</xs:sequence></xs:group>')
        for name, particle, valid in (
                ("group-scope", f'<xs:group xmlns:g="{NS}" ref="g:Optional"/>', True),
                ("optional-group", '<xs:group ref="t:Required" minOccurs="0"/>', True),
                ("required-group", '<xs:group ref="t:Required"/>', False),
                ("nested-group-choice", '<xs:sequence><xs:choice><xs:group ref="t:Optional"/>'
                 '<xs:group ref="t:Required"/></xs:choice></xs:sequence>', True)):
            sources[name] = schema(base(particle), groups), valid
        for name, particle, valid in (("optional", OPTIONAL, True), ("required", REQUIRED, False)):
            ancestor = f'<xs:complexType name="Ancestor" mixed="true">{particle}</xs:complexType>'
            for label, content in (("absent", ""), ("sequence", '<xs:sequence/>'),
                                    ("nested", '<xs:sequence><xs:choice/></xs:sequence>')):
                extended = ('<xs:complexType name="Base"><xs:complexContent><xs:extension base="t:Ancestor">'
                            + content + '</xs:extension></xs:complexContent></xs:complexType>')
                sources[f"inherited-{name}-{label}"] = schema(extended, ancestor), valid and label != "nested"
        for mixed, valid in (("true", True), ("1", True), ("false", False), ("0", False)):
            body = (f'<xs:complexType name="Base" mixed="true"><xs:complexContent mixed="{mixed}">'
                    f'<xs:restriction base="xs:anyType">{OPTIONAL}</xs:restriction></xs:complexContent>'
                    '</xs:complexType>')
            sources["content-mixed-" + mixed] = schema(body), valid
        for label, ref in (("cyclic", "t:Bad"), ("undefined", "t:Missing")):
            group = (f'<xs:group name="Bad"><xs:sequence><xs:choice><xs:group ref="{ref}" minOccurs="0"/>'
                     '</xs:choice></xs:sequence></xs:group>')
            sources["nested-" + label] = schema(base(OPTIONAL), group), False
        jobs, cases = [], []
        with tempfile.TemporaryDirectory(prefix="wsdl-mixed-base-schema-") as temporary:
            root = Path(temporary)
            for name, (source, expected) in sources.items():
                try:
                    etree.XMLSchema(etree.fromstring(source.encode()))
                    valid = True
                except etree.XMLSchemaParseError:
                    valid = False
                # libxml2 incorrectly retains outer mixed=true after an inner false/0 override.
                self.assertEqual(expected or name in ("content-mixed-false", "content-mixed-0"), valid, name)
                path = root / (name + ".xsd")
                path.write_text(source)
                cases.append({"name": name, "wsdl": str(path), "schema_only": True,
                              "base": "http://example.invalid/", "messages": []})
                jobs.append(SchemaJob(name, "http://example.invalid/" + path.name, source.encode()))
            rows = survey.run_worker(cases, {})
        self.assertEqual(35, len(sources))
        self.assertEqual(len(sources), len(rows))
        for row in rows:
            self.assertEqual(sources[row["case"]][1], row["ok"], row)
            if not row["ok"]:
                self.assertEqual("WSDL-ERROR", row["err"])
        oracle = run_independent(jobs)
        self.assertEqual(set(sources), set(oracle["schemas"]))
        for name, result in oracle["schemas"].items():
            self.assertEqual(sources[name][1], result["ok"], (name, result))

    def test_real_bindings_values_and_reconstructed_examples(self):
        source = schema(base(OPTIONAL, attrs=ATTR))
        compiled = etree.XMLSchema(etree.fromstring(source.encode()))
        documents, expected, cases = {}, {}, []
        with tempfile.TemporaryDirectory(prefix="wsdl-mixed-base-wire-") as temporary:
            root = Path(temporary)
            for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                path = root / f"{version}.wsdl"
                path.write_text(description(version, source))
                messages = []
                for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                    for variant, attrs, text in (("valid", 'unit="kg"', "0"), ("facet", 'unit="kg"', "-1"),
                                                  ("missing-attribute", "", "0"),
                                                  ("child", 'unit="kg"', '<a>0</a>')):
                        name = f"{version}/{direction}/{variant}"
                        payload_text = f'<t:{wrapper} xmlns:t="{NS}" {attrs}>{text}</t:{wrapper}>'
                        payload = etree.fromstring(payload_text.encode())
                        valid = variant == "valid"
                        # libxml2 drops outer facets on restrictions of mixed bases; the
                        # property mapping requires them and Xerces/Qore enforce them below.
                        self.assertEqual(valid or variant == "facet", compiled.validate(payload),
                                         (name, str(compiled.error_log)))
                        documents[name], expected[name] = etree.tostring(payload), valid
                        message = root / name.replace("/", "-")
                        message.write_text(f'<s:Envelope xmlns:s="{envelope_ns}"><s:Body>{payload_text}'
                                           '</s:Body></s:Envelope>')
                        messages.append({"file": name, "path": str(message), "direction": direction})
                cases.append({"name": version, "wsdl": str(path), "base": "http://example.invalid/",
                              "binding": "Soap" + version, "operation": "submit", "messages": messages})
                process = subprocess.run(["qore", "--enable-debug", str(Path(__file__).with_name("mixed-base.qr")),
                                          str(path), "Soap" + version], capture_output=True, text=True,
                                         check=True, timeout=30)
                self.assertEqual("", process.stderr)
                rows = [json.loads(line) for line in process.stdout.splitlines()]
                self.assertEqual(4, len(rows))
                for row in rows:
                    name = f"{version}/{row['direction']}/{row['kind']}"
                    self.assertIs(int, type(row["value"]["^value^"]))
                    self.assertGreaterEqual(row["value"]["^value^"], 0)
                    self.assertEqual({"unit": "kg"}, row["value"]["^attributes^"])
                    if row["kind"] == "native":
                        self.assertEqual(0, row["value"]["^value^"])
                    envelope = etree.fromstring(row["body"].encode())
                    self.assertEqual(f"{{{envelope_ns}}}Envelope", envelope.tag)
                    payload = envelope.find("{*}Body")[0]
                    self.assertEqual(f"{{{NS}}}" + ("Submit" if row["direction"] == "request" else "Reply"), payload.tag)
                    self.assertEqual(str(row["value"]["^value^"]), payload.text)
                    self.assertTrue(compiled.validate(payload), str(compiled.error_log))
                    documents[name], expected[name] = etree.tostring(payload), True
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
                    version, direction, _ = row["file"].split("/")
                    envelope = etree.fromstring(row["body"].encode())
                    self.assertEqual(f"{{{survey.SOAP_NAMESPACES[int(version == '12')]}}}Envelope", envelope.tag)
                    payload = envelope.find("{*}Body")[0]
                    self.assertEqual(f"{{{NS}}}" + ("Submit" if direction == "request" else "Reply"), payload.tag)
                    self.assertEqual("0", payload.text)
                    self.assertEqual({"unit": "kg"}, dict(payload.attrib))
                    self.assertTrue(compiled.validate(payload), str(compiled.error_log))
                    documents[row["file"] + "/output"] = etree.tostring(payload)
                    expected[row["file"] + "/output"] = True
        self.assertEqual(28, len(documents))
        oracle = run_independent([SchemaJob("mixed", "http://example.invalid/mixed.xsd", source.encode(), documents)])
        self.assertEqual(set(documents), set(oracle["documents"]))
        for name, result in oracle["documents"].items():
            self.assertEqual(expected[name], result["ok"], (name, result))


if __name__ == "__main__":
    unittest.main()
