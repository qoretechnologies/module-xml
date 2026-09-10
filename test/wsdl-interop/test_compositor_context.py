#!/usr/bin/env python3
"""Independent compositor namespace and nested-choice rejection checks.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

from pathlib import Path
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
import survey
from test_attribute_values import description, NS, XSD


def schema(model):
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
      <xs:complexType name="Record">{model}</xs:complexType>
      <xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/>
    </xs:schema>'''


class CompositorContextTest(unittest.TestCase):
    def check_messages(self, source, content, valid):
        """Verify the independent input verdict before invoking Qore in both directions."""
        compiled = etree.XMLSchema(etree.fromstring(source.encode()))
        cases, documents = [], {}
        with tempfile.TemporaryDirectory(prefix="wsdl-compositor-context-") as temporary:
            root = Path(temporary)
            for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                wsdl = root / f"soap{version}.wsdl"
                wsdl.write_text(description(version, source))
                messages = []
                for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                    name = f"{version}/{direction}"
                    text = f'''<s:Envelope xmlns:s="{envelope_ns}" xmlns:t="{NS}"><s:Body>
                      <t:{wrapper}>{content}</t:{wrapper}></s:Body></s:Envelope>'''
                    path = root / name.replace("/", "-")
                    path.write_text(text)
                    payload = etree.fromstring(text.encode()).find("{*}Body")[0]
                    self.assertEqual(valid, compiled.validate(payload), str(compiled.error_log))
                    documents[name] = etree.tostring(payload)
                    messages.append({"file": name, "path": str(path), "direction": direction})
                cases.append({"name": "Compositor" + version, "wsdl": str(wsdl),
                              "base": "http://example.invalid/", "operation": "submit",
                              "binding": "Soap" + version, "messages": messages})
            oracle = run_independent([SchemaJob("compositor", "http://example.invalid/compositor.xsd",
                                                 source.encode(), documents)])
            self.assertEqual(4, len(oracle["documents"]))
            for name, result in oracle["documents"].items():
                self.assertEqual(valid, result["ok"], (name, result))
            rows = survey.run_worker(cases, {})
        return cases, rows, compiled

    def test_compositor_namespaces_in_actual_bindings_and_both_directions(self):
        models = {name: f'''<xs:{name} xmlns:q="{XSD}">
                    <xs:element name="flag" type="q:boolean"/></xs:{name}>'''
                  for name in ("sequence", "choice", "all")}
        models["nested"] = f'''<xs:choice><xs:choice xmlns:q="{XSD}">
          <xs:sequence><xs:element name="flag" type="q:boolean"/>
          <xs:sequence xmlns="{XSD}"><xs:element name="count" type="int"/></xs:sequence>
          </xs:sequence><xs:element name="text" type="q:string"/>
        </xs:choice></xs:choice>'''
        jobs = []
        for name, model in models.items():
            with self.subTest(model=name):
                source = schema(model)
                cases, rows, compiled = self.check_messages(
                    source, "<flag>false</flag>" + ("<count>0</count>" if name == "nested" else ""), True)
                accounting = survey.stage_accounting(cases, rows)["counts"]
                self.assertEqual(2, accounting["parse"]["ok"], rows)
                self.assertEqual(4, accounting["deserialize"]["ok"], rows)
                self.assertEqual(4, accounting["serialize"]["ok"], rows)
                documents = {}
                for row in rows:
                    self.assertTrue(row["ok"], row)
                    if row["stage"] == "serialize":
                        envelope = etree.fromstring(row["body"].encode())
                        version = row["file"].split("/")[0]
                        self.assertEqual(f"{{{survey.SOAP_NAMESPACES[int(version == '12')]}}}Envelope", envelope.tag)
                        payload = envelope.find("{*}Body")[0]
                        wrapper = "Submit" if row["direction"] == "request" else "Reply"
                        self.assertEqual(f"{{{NS}}}{wrapper}", payload.tag)
                        self.assertEqual([("flag", "false")] + ([("count", "0")] if name == "nested" else []),
                                         [(child.tag, child.text) for child in payload])
                        self.assertTrue(compiled.validate(payload), str(compiled.error_log))
                        documents[f"{name}/{row['file']}"] = etree.tostring(payload)
                self.assertEqual(4, len(documents))
                jobs.append(SchemaJob(name, f"http://example.invalid/{name}.xsd", source.encode(), documents))
        oracle = run_independent(jobs)
        self.assertEqual(16, len(oracle["documents"]))
        for name, result in oracle["documents"].items():
            self.assertTrue(result["ok"], (name, result))

    def test_nested_choice_exclusivity_requirement_p4(self):
        # Whole-particle decoding rejects members from both nested alternatives.
        source = schema('''<xs:choice><xs:choice><xs:sequence>
          <xs:element name="flag" type="xs:boolean"/><xs:element name="count" type="xs:int"/>
          </xs:sequence><xs:element name="text" type="xs:string"/></xs:choice></xs:choice>''')
        cases, rows, _ = self.check_messages(source, "<flag>false</flag><count>0</count><text>extra</text>", False)
        survey.stage_accounting(cases, rows)
        rejected = [row for row in rows if row["stage"] == "deserialize"]
        self.assertEqual(4, len(rejected))
        for row in rejected:
            with self.subTest(file=row["file"], requirement="P4-nested-choice-exclusivity"):
                self.assertFalse(row["ok"], row)
                self.assertEqual("SOAP-DESERIALIZATION-ERROR", row["err"])


if __name__ == "__main__":
    unittest.main()
