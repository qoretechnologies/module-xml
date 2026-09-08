#!/usr/bin/env python3
"""Element declaration consistency before flattened fields merge.

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


def element(type_name="xs:int", extra=""):
    return f'<xs:element name="item" type="{type_name}" {extra}/>'


def record(content, name="Record"):
    return f'<xs:complexType name="{name}">{content}</xs:complexType>'


def schema(body):
    return (f'<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">{body}'
            '<xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/></xs:schema>')


def schema_cases():
    cases = {}
    for model in ("sequence", "choice", "all"):
        cases[model + "-conflict"] = (record(f'<xs:{model}>' + element() + element("xs:string")
                                            + f'</xs:{model}>'), False)
    for model in ("sequence", "choice"):
        cases[model + "-nested"] = (record('<xs:sequence>' + element() + f'<xs:{model} minOccurs="0">'
                                          + element("xs:string") + f'</xs:{model}></xs:sequence>'), False)
    anonymous = ('<xs:element name="item"><xs:simpleType><xs:restriction base="xs:int"/>'
                 '</xs:simpleType></xs:element>')
    cases["anonymous-distinct"] = (record('<xs:sequence>' + anonymous * 2 + '</xs:sequence>'), False)
    cases["alias"] = (record('<xs:sequence>' + element() + element("a:int", f'xmlns:a="{XSD}"')
                             + '</xs:sequence>'), True)
    types = ('<xs:simpleType name="A"><xs:restriction base="xs:int"/></xs:simpleType>'
             '<xs:simpleType name="B"><xs:restriction base="xs:int"/></xs:simpleType>')
    for name, other, valid in (("named-same", "A", True), ("named-distinct", "B", False)):
        cases[name] = (types + record('<xs:sequence>' + element("t:A") + element("t:" + other)
                                      + '</xs:sequence>'), valid)
    for name, other, valid in (("default-same", "xs:anyType", True), ("default-conflict", "xs:int", False)):
        cases[name] = (record('<xs:sequence><xs:element name="item"/>' + element(other) + '</xs:sequence>'), valid)
    cases["different-namespaces"] = (record('<xs:sequence>' + element()
                                            + element("xs:boolean", 'form="qualified"') + '</xs:sequence>'), True)
    cases["different-scopes"] = (record('<xs:sequence>' + element() + '<xs:element name="nested">'
                                        + record('<xs:sequence>' + element("xs:string") + '</xs:sequence>')
                                        .replace(' name="Record"', '') + '</xs:element></xs:sequence>'), True)
    cases["reference-same-anonymous"] = (anonymous + record('<xs:sequence><xs:element ref="t:item"/>'
                                                           '<xs:element ref="t:item"/></xs:sequence>'), True)
    cases["reference-conflict"] = (element() + record('<xs:sequence><xs:element ref="t:item"/>'
                                                     + element("xs:string", 'form="qualified"')
                                                     + '</xs:sequence>'), False)
    group = '<xs:group name="G"><xs:sequence>' + element() + '</xs:sequence></xs:group>'
    cases["group-local-conflict"] = (group + record('<xs:sequence><xs:group ref="t:G"/>'
                                                   + element("xs:string") + '</xs:sequence>'), False)
    cases["group-nested-conflict"] = (group + '<xs:group name="Outer"><xs:sequence><xs:sequence>'
                                     '<xs:group ref="t:G"/>' + element("xs:string")
                                     + '</xs:sequence></xs:sequence></xs:group>' + record(''), False)
    cases["group-unused-conflict"] = ('<xs:group name="Unused"><xs:sequence>' + element()
                                      + '<xs:choice><xs:sequence>' + element("xs:string")
                                      + '</xs:sequence></xs:choice></xs:sequence></xs:group>' + record(''), False)
    cases["group-reuse-anonymous"] = ('<xs:group name="G"><xs:sequence>' + anonymous
                                      + '</xs:sequence></xs:group>' + record('<xs:sequence><xs:group ref="t:G"/>'
                                                                          '<xs:group ref="t:G"/></xs:sequence>'), True)
    base = record('<xs:sequence>' + element() + '</xs:sequence>', "Base")
    for name, method, other, valid in (("extension-conflict", "extension", "xs:string", False),
                                      ("extension-same", "extension", "xs:int", True),
                                      ("restriction", "restriction", "xs:short", True)):
        cases[name] = (base + record(f'<xs:complexContent><xs:{method} base="t:Base"><xs:sequence>'
                                     + element(other) + f'</xs:sequence></xs:{method}></xs:complexContent>'), valid)
    for zero in ("0", "+00", " 0 "):
        occurs = f'minOccurs="{zero}" maxOccurs="{zero}"'
        cases["zero-element-" + zero] = (record('<xs:sequence>' + element() + element("xs:string", occurs)
                                               + '</xs:sequence>'), True)
        cases["zero-group-" + zero] = (record('<xs:sequence>' + element() + f'<xs:sequence {occurs}>'
                                             + element("xs:string") + '</xs:sequence></xs:sequence>'), True)
    cases["zero-root"] = (record('<xs:sequence minOccurs="0" maxOccurs="0">' + element()
                                 + element("xs:string") + '</xs:sequence>'), True)
    cases["zero-reference"] = (group + record('<xs:sequence>' + element("xs:string")
                                              + '<xs:group ref="t:G" minOccurs="0" maxOccurs="0"/>'
                                              '</xs:sequence>'), True)
    return {name: (schema(body), valid) for name, (body, valid) in cases.items()}


class ElementConsistencyTest(unittest.TestCase):
    def test_schema_constraints_in_both_bindings(self):
        sources = schema_cases()
        jobs, cases, lxml_gaps = [], [], set()
        with tempfile.TemporaryDirectory(prefix="wsdl-element-consistency-") as temporary:
            root = Path(temporary)
            for index, (name, (source, expected)) in enumerate(sources.items()):
                try:
                    etree.XMLSchema(etree.fromstring(source.encode()))
                    valid = True
                except etree.XMLSchemaParseError:
                    valid = False
                if valid != expected:
                    lxml_gaps.add(name)
                jobs.append(SchemaJob(name, f"https://example.invalid/consistency/{index}.xsd", source.encode()))
                for version in ("11", "12"):
                    path = root / f"{index}-{version}.wsdl"
                    path.write_text(description(version, source))
                    cases.append({"name": name + "/" + version, "wsdl": str(path), "base": "https://example.invalid/",
                                  "operation": "submit", "binding": "Soap" + version, "messages": []})
            rows = survey.run_worker(cases, {})
        self.assertEqual(30, len(sources))
        self.assertEqual(60, len(rows))
        # libxml2 omits EDC on these deterministic or unused content models. Keep its exact
        # verdicts visible. Its occurrence parser also rejects the valid +00 spelling.
        self.assertEqual({"sequence-conflict", "sequence-nested", "choice-nested", "anonymous-distinct",
                          "named-distinct", "default-conflict", "reference-conflict", "group-local-conflict",
                          "group-nested-conflict", "group-unused-conflict", "extension-conflict", "choice-conflict",
                          "all-conflict", "zero-element-+00", "zero-group-+00"}, lxml_gaps)
        self.assertEqual({case["name"] for case in cases}, {row["case"] for row in rows})
        for row in rows:
            with self.subTest(case=row["case"]):
                self.assertEqual("parse", row["stage"])
                self.assertEqual(sources[row["case"].rsplit("/", 1)[0]][1], row["ok"], row)
                if not row["ok"]:
                    self.assertEqual("WSDL-ERROR", row["err"])
        oracle = run_independent(jobs)
        self.assertEqual(set(sources), set(oracle["schemas"]))
        for name, result in oracle["schemas"].items():
            # Xerces checks EDC only when a complex type consumes these named groups.
            # XSD 1.0 section 3.8.6 applies the constraint to all model groups.
            self.assertEqual(sources[name][1] or name in ("group-nested-conflict", "group-unused-conflict"),
                             result["ok"], (name, result))

    def test_nested_group_fields_in_both_directions(self):
        source = schema('<xs:group name="G"><xs:sequence><xs:sequence>' + element()
                        + '<xs:element name="flag" type="xs:boolean"/></xs:sequence></xs:sequence></xs:group>'
                        + '<xs:group name="Outer"><xs:sequence><xs:sequence><xs:group ref="t:G"/>'
                        '</xs:sequence></xs:sequence></xs:group>' + record('<xs:group ref="t:Outer"/>'))
        compiled = etree.XMLSchema(etree.fromstring(source.encode()))
        cases, documents, expected = [], {}, {}
        with tempfile.TemporaryDirectory(prefix="wsdl-element-consumers-") as temporary:
            root = Path(temporary)
            for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                path = root / f"{version}.wsdl"
                path.write_text(description(version, source))
                messages = []
                for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                    for variant, content in (("valid", '<item>0</item><flag>false</flag>'),
                                              ("namespace", '<t:item>0</t:item><flag>false</flag>'),
                                              ("missing", '<flag>false</flag>')):
                        name = f"{version}/{direction}/{variant}"
                        payload = f'<t:{wrapper} xmlns:t="{NS}">{content}</t:{wrapper}>'
                        expected[name] = variant == "valid"
                        documents[name] = payload.encode()
                        self.assertEqual(expected[name], compiled.validate(etree.fromstring(documents[name])))
                        message = root / name.replace("/", "-")
                        message.write_text(f'<s:Envelope xmlns:s="{envelope_ns}"><s:Body>{payload}'
                                           '</s:Body></s:Envelope>')
                        messages.append({"file": name, "path": str(message), "direction": direction})
                cases.append({"name": version, "wsdl": str(path), "base": "https://example.invalid/",
                              "operation": "submit", "binding": "Soap" + version, "messages": messages})
                process = subprocess.run(["qore", "--enable-debug",
                                          str(Path(__file__).with_name("element-collision-values.qr")), str(path),
                                          "Soap" + version], capture_output=True, text=True, check=True, timeout=30)
                self.assertEqual("", process.stderr)
                samples = [json.loads(line) for line in process.stdout.splitlines()]
                self.assertEqual(2, len(samples))
                for row in samples:
                    self.assertIs(int, type(row["value"]["item"]))
                    self.assertIs(bool, type(row["value"]["flag"]))
                    envelope = etree.fromstring(row["body"].encode())
                    self.assertEqual(f"{{{envelope_ns}}}Envelope", envelope.tag)
                    payload = envelope.find("{*}Body")[0]
                    self.assertEqual([("item", str(row["value"]["item"])),
                                      ("flag", str(row["value"]["flag"]).lower())], [(c.tag, c.text) for c in payload])
                    self.assertTrue(compiled.validate(payload), str(compiled.error_log))
                    name = f"{version}/{row['direction']}/sample"
                    documents[name], expected[name] = etree.tostring(payload), True
            rows = survey.run_worker(cases, {})
        counts = survey.stage_accounting(cases, rows)["counts"]
        self.assertEqual(4, counts["serialize"]["ok"], rows)
        self.assertEqual(8, counts["deserialize"]["failed"], rows)
        for row in rows:
            if row["stage"] == "parse":
                self.assertTrue(row["ok"], row)
            elif not expected[row["file"]]:
                self.assertFalse(row["ok"], row)
                self.assertEqual("SOAP-DESERIALIZATION-ERROR", row["err"])
            elif row["stage"] == "deserialize":
                self.assertTrue(row["ok"], row)
            else:
                self.assertTrue(row["ok"], row)
                envelope = etree.fromstring(row["body"].encode())
                payload = envelope.find("{*}Body")[0]
                self.assertTrue(compiled.validate(payload), str(compiled.error_log))
                self.assertEqual([("item", "0"), ("flag", "false")], [(c.tag, c.text) for c in payload])
                name = row["file"] + "/output"
                documents[name], expected[name] = etree.tostring(payload), True
        self.assertEqual(20, len(documents))
        oracle = run_independent([SchemaJob("wire", "https://example.invalid/consistent.xsd", source.encode(), documents)])
        self.assertTrue(oracle["schemas"]["wire"]["ok"], oracle)
        self.assertEqual(set(documents), set(oracle["documents"]))
        for name, result in oracle["documents"].items():
            self.assertEqual(expected[name], result["ok"], (name, result))


if __name__ == "__main__":
    unittest.main()
