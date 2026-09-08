#!/usr/bin/env python3
"""Independent checks for colliding element declaration and public field names.

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


ELEMENTS = ('<xs:element name="item" type="xs:boolean" form="unqualified"/>'
            '<xs:element name="item" type="xs:int" form="qualified"/>')


def schema(model):
    declarations = ""
    if model in ("sequence", "all", "choice"):
        content = f"<xs:{model}>{ELEMENTS}</xs:{model}>"
    elif model == "anonymous":
        content = ('<xs:sequence><xs:element name="payload"><xs:complexType><xs:sequence>'
                   + ELEMENTS + '</xs:sequence></xs:complexType></xs:element></xs:sequence>')
    elif model == "extension":
        declarations = ('<xs:complexType name="Base"><xs:sequence><xs:element name="item" '
                        'type="xs:boolean"/></xs:sequence></xs:complexType>')
        content = ('<xs:complexContent><xs:extension base="t:Base"><xs:sequence>'
                   '<xs:element name="item" type="xs:int" form="qualified"/></xs:sequence>'
                   '</xs:extension></xs:complexContent>')
    elif model == "group":
        declarations = f'<xs:group name="Fields"><xs:sequence>{ELEMENTS}</xs:sequence></xs:group>'
        content = '<xs:group ref="t:Fields"/>'
    else:
        raise ValueError(model)
    return (f'<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">{declarations}'
            f'<xs:complexType name="Record">{content}</xs:complexType>'
            '<xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/>'
            '</xs:schema>')


class ElementCollisionsTest(unittest.TestCase):
    def test_distinct_element_identities_in_actual_bindings(self):
        jobs = []
        document_count = 0
        for model in ("sequence", "all", "choice", "anonymous", "extension", "group"):
            source = schema(model)
            compiled = etree.XMLSchema(etree.fromstring(source.encode()))
            variants = {
                "both": '<item>false</item><t:item>0</t:item>',
                "plain": '<item>false</item>',
                "qualified": '<t:item>0</t:item>',
                "wrong": '<item>false</item><q:item xmlns:q="urn:wrong">0</q:item>',
            }
            documents, expected, expected_values, cases = {}, {}, {}, []
            with tempfile.TemporaryDirectory(prefix="wsdl-element-collisions-") as temporary:
                root = Path(temporary)
                for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                    wsdl = root / f"{model}-{version}.wsdl"
                    wsdl.write_text(description(version, source))
                    messages = []
                    for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                        for variant, children in variants.items():
                            valid = variant in ("plain", "qualified") if model == "choice" else variant == "both"
                            if model == "anonymous":
                                children = '<payload>' + children + '</payload>'
                            name = f"{model}/{version}/{direction}/{variant}"
                            text = (f'<s:Envelope xmlns:s="{envelope_ns}" xmlns:t="{NS}"><s:Body>'
                                    f'<t:{wrapper}>{children}</t:{wrapper}></s:Body></s:Envelope>')
                            path = root / name.replace("/", "-")
                            path.write_text(text)
                            payload = etree.fromstring(text.encode()).find("{*}Body")[0]
                            self.assertEqual(valid, compiled.validate(payload), (name, str(compiled.error_log)))
                            documents[name], expected[name] = etree.tostring(payload), valid
                            content = payload[0] if model == "anonymous" else payload
                            expected_values[name] = [(child.tag, child.text) for child in content]
                            messages.append({"file": name, "path": str(path), "direction": direction})
                    cases.append({"name": model + version, "wsdl": str(wsdl), "base": "http://example.invalid/",
                                  "operation": "submit", "binding": "Soap" + version, "messages": messages})
                rows = survey.run_worker(cases, {})
            counts = survey.stage_accounting(cases, rows)["counts"]
            self.assertEqual(8 if model == "choice" else 4, counts["serialize"]["ok"], rows)
            self.assertEqual(8 if model == "choice" else 12, counts["deserialize"]["failed"], rows)
            for row in rows:
                if row["stage"] == "parse":
                    self.assertTrue(row["ok"], row)
                elif not expected[row["file"]]:
                    self.assertFalse(row["ok"], row)
                    self.assertEqual("SOAP-DESERIALIZATION-ERROR", row["err"])
                elif row["stage"] == "serialize":
                    _, version, direction, _ = row["file"].split("/")
                    envelope = etree.fromstring(row["body"].encode())
                    self.assertEqual(f"{{{survey.SOAP_NAMESPACES[int(version == '12')]}}}Envelope", envelope.tag)
                    payload = envelope.find("{*}Body")[0]
                    self.assertEqual(f"{{{NS}}}" + ("Submit" if direction == "request" else "Reply"), payload.tag)
                    content = payload[0] if model == "anonymous" else payload
                    self.assertEqual(expected_values[row["file"]], [(child.tag, child.text) for child in content])
                    self.assertTrue(compiled.validate(payload), str(compiled.error_log))
                    name = row["file"] + "/output"
                    documents[name], expected[name] = etree.tostring(payload), True
                else:
                    self.assertTrue(row["ok"], row)
            jobs.append(SchemaJob(model, f"http://example.invalid/{model}.xsd", source.encode(), documents))
            document_count += len(documents)
            oracle = run_independent([jobs[-1]])
            self.assertEqual(len(documents), len(oracle["documents"]))
            for name, valid in expected.items():
                self.assertEqual(valid, oracle["documents"][name]["ok"], (name, oracle["documents"][name]))
        self.assertEqual(124, document_count)

    def test_reconstructed_provider_and_generated_examples(self):
        jobs = []
        with tempfile.TemporaryDirectory(prefix="wsdl-collision-examples-") as temporary:
            for model in ("sequence", "choice", "anonymous"):
                source, documents = schema(model), {}
                for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                    wsdl = Path(temporary) / f"{model}-{version}.wsdl"
                    wsdl.write_text(description(version, source))
                    process = subprocess.run(
                        ["qore", "--enable-debug", str(Path(__file__).with_name("element-collision-values.qr")),
                         str(wsdl), "Soap" + version], text=True, capture_output=True, check=True, timeout=30)
                    self.assertEqual("", process.stderr)
                    rows = [json.loads(line) for line in process.stdout.splitlines()]
                    self.assertEqual(["request", "response"], [row["direction"] for row in rows])
                    for row in rows:
                        value = row["value"]["payload"] if model == "anonymous" else row["value"]
                        self.assertEqual(["{}item"] if model == "choice" else ["{}item", f"{{{NS}}}item"], list(value))
                        self.assertIs(bool, type(value["{}item"]))
                        if model != "choice":
                            self.assertIs(int, type(value[f"{{{NS}}}item"]))
                            self.assertEqual(123, value[f"{{{NS}}}item"])
                        envelope = etree.fromstring(row["body"].encode())
                        self.assertEqual(f"{{{envelope_ns}}}Envelope", envelope.tag)
                        payload = envelope.find("{*}Body")[0]
                        content = payload[0] if model == "anonymous" else payload
                        expected_values = [("item", "true" if value["{}item"] else "false")]
                        if model != "choice":
                            expected_values.append((f"{{{NS}}}item", "123"))
                        self.assertEqual(expected_values, [(child.tag, child.text) for child in content])
                        documents[f"{model}/{version}/{row['direction']}"] = etree.tostring(payload)
                jobs.append(SchemaJob(model, f"http://example.invalid/{model}.xsd", source.encode(), documents))
        oracle = run_independent(jobs)
        self.assertEqual(12, len(oracle["documents"]))
        for name, result in oracle["documents"].items():
            self.assertTrue(result["ok"], (name, result))


if __name__ == "__main__":
    unittest.main()
