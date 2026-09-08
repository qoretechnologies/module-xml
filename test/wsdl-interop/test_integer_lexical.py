#!/usr/bin/env python3
"""XSD 1.0 integer lexical spaces in both SOAP bindings and directions.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

from pathlib import Path
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS, XSD
import survey


TYPES = ("integer", "long", "int", "short", "byte", "unsignedLong", "unsignedInt", "unsignedShort",
         "unsignedByte", "positiveInteger", "negativeInteger", "nonPositiveInteger", "nonNegativeInteger")


class IntegerLexicalTest(unittest.TestCase):
    def test_simple_content_and_attributes(self):
        cases, jobs, validators, expected, outputs = [], {}, {}, {}, {}
        with tempfile.TemporaryDirectory(prefix="wsdl-integer-lexical-") as temporary:
            root = Path(temporary)
            for datatype in TYPES:
                schema = f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
                  <xs:complexType name="Record"><xs:simpleContent><xs:extension base="xs:{datatype}">
                    <xs:attribute name="count" type="xs:{datatype}" use="required"/>
                  </xs:extension></xs:simpleContent></xs:complexType>
                  <xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/>
                </xs:schema>'''.encode()
                jobs[datatype] = SchemaJob(datatype, f"http://example.invalid/{datatype}.xsd", schema)
                validators[datatype] = etree.XMLSchema(etree.fromstring(schema))
                negative = datatype in ("negativeInteger", "nonPositiveInteger")
                ordinary = "-1" if negative else "1"
                variants = [(ordinary, True), (" \t-001\r\n " if negative else " \t001\r\n ", True)]
                variants += [(value, False) for value in ("", "1.0", "1tail", "١", "1\u00a0")]
                for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                    wsdl = root / f"{datatype}-{version}.wsdl"
                    wsdl.write_text(description(version, schema.decode()))
                    messages = []
                    for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                        for location in ("content", "attribute"):
                            for index, (lexical, valid) in enumerate(variants):
                                name = f"{datatype}/{version}/{direction}/{location}/{index}"
                                envelope = etree.Element(f"{{{envelope_ns}}}Envelope", nsmap={"s": envelope_ns, "t": NS})
                                body = etree.SubElement(envelope, f"{{{envelope_ns}}}Body")
                                value = etree.SubElement(body, f"{{{NS}}}{wrapper}")
                                value.text = lexical if location == "content" else ordinary
                                value.set("count", lexical if location == "attribute" else ordinary)
                                self.assertEqual(valid, validators[datatype].validate(value),
                                                 (name, str(validators[datatype].error_log)))
                                jobs[datatype].documents[name] = etree.tostring(value)
                                path = root / name.replace("/", "-")
                                path.write_bytes(etree.tostring(envelope))
                                messages.append({"file": name, "path": str(path), "direction": direction})
                                expected[name] = valid
                    cases.append({"name": datatype + version, "wsdl": str(wsdl), "base": "http://example.invalid/",
                                  "operation": "submit", "binding": "Soap" + version, "messages": messages})
            rows = survey.run_worker(cases, {})
        counts = survey.stage_accounting(cases, rows)["counts"]
        self.assertEqual(26, counts["parse"]["ok"])
        self.assertEqual(sum(expected.values()), counts["serialize"]["ok"])
        for stages in counts.values():
            self.assertEqual(0, stages["missing"])
            self.assertEqual(0, stages["skipped"])
        for row in rows:
            if row["stage"] == "parse":
                self.assertTrue(row["ok"], row)
                continue
            name = row["file"]
            if not expected[name]:
                self.assertEqual("deserialize", row["stage"], row)
                self.assertFalse(row["ok"], row)
                self.assertEqual("SOAP-DESERIALIZATION-ERROR", row["err"], row)
                continue
            self.assertTrue(row["ok"], row)
            if row["stage"] != "serialize":
                continue
            datatype, version, direction, _, _ = name.split("/")
            envelope = etree.fromstring(row["body"].encode())
            self.assertEqual(f"{{{survey.SOAP_NAMESPACES[int(version == '12')]}}}Envelope", envelope.tag)
            value = envelope.find("{*}Body")[0]
            self.assertEqual(f"{{{NS}}}" + ("Submit" if direction == "request" else "Reply"), value.tag)
            self.assertTrue(validators[datatype].validate(value), str(validators[datatype].error_log))
            integer = -1 if datatype in ("negativeInteger", "nonPositiveInteger") else 1
            self.assertEqual(integer, int(value.text))
            self.assertEqual(integer, int(value.attrib["count"]))
            self.assertEqual(0, len(value))
            outputs[name + "/output"] = True
            jobs[datatype].documents[name + "/output"] = etree.tostring(value)
        self.assertEqual(728, len(expected))
        self.assertEqual(208, len(outputs))
        results = run_independent(list(jobs.values()))
        self.assertEqual(set(expected) | set(outputs), set(results["documents"]))
        for name, valid in (expected | outputs).items():
            self.assertEqual(valid, results["documents"][name]["ok"], (name, results["documents"][name]))


if __name__ == "__main__":
    unittest.main()
