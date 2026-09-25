#!/usr/bin/env python3
"""Exact XSD 1.0 integer ranges and values in both SOAP bindings and directions.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

from pathlib import Path
import json
import subprocess
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS, XSD
import survey


BOUNDS = {
    "byte": (-128, 127), "short": (-32768, 32767), "int": (-2147483648, 2147483647),
    "long": (-9223372036854775808, 9223372036854775807), "unsignedByte": (0, 255),
    "unsignedShort": (0, 65535), "unsignedInt": (0, 4294967295),
    "unsignedLong": (0, 18446744073709551615), "integer": (None, None),
    "negativeInteger": (None, -1), "nonPositiveInteger": (None, 0),
    "positiveInteger": (1, None), "nonNegativeInteger": (0, None),
}


class IntegerRangeTest(unittest.TestCase):
    def test_simple_content_and_attributes(self):
        cases, jobs, validators, expected, outputs, values = [], {}, {}, {}, {}, {}
        with tempfile.TemporaryDirectory(prefix="wsdl-integer-range-") as temporary:
            root = Path(temporary)
            for datatype, (minimum, maximum) in BOUNDS.items():
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
                valid_values = list(dict.fromkeys((minimum if minimum is not None else -(10**100 + 17),
                                                   maximum if maximum is not None else 10**100 + 17)))
                variants = [(str(v), True) for v in valid_values]
                variants += [("-000" + str(-v) if v < 0 else "000" + str(v), True) for v in valid_values]
                variants += [(str(v), False) for v in (None if minimum is None else minimum - 1,
                                                       None if maximum is None else maximum + 1) if v is not None]
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
                                # The pinned libxml2 (2.14.6) validates arbitrary-precision integers; the P1
                                # precision disagreement belonged to libxml2 2.12.10.
                                self.assertEqual(valid, validators[datatype].validate(value),
                                                 (name, str(validators[datatype].error_log)))
                                if valid:
                                    values[name] = (int(value.text), int(value.attrib["count"]))
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
            self.assertTrue(validators[datatype].validate(value), (name, str(validators[datatype].error_log)))
            content, attribute = values[name]
            self.assertEqual(content, int(value.text))
            self.assertEqual(attribute, int(value.attrib["count"]))
            self.assertEqual(0, len(value))
            outputs[name + "/output"] = True
            jobs[datatype].documents[name + "/output"] = etree.tostring(value)
        self.assertEqual(576, len(expected))
        self.assertEqual(416, len(outputs))
        results = run_independent(list(jobs.values()))
        self.assertEqual(set(expected) | set(outputs), set(results["documents"]))
        for name, valid in (expected | outputs).items():
            self.assertEqual(valid, results["documents"][name]["ok"], (name, results["documents"][name]))

    def test_providers_reconstruction_and_examples(self):
        cases, jobs = [], {}
        with tempfile.TemporaryDirectory(prefix="wsdl-integer-consumers-") as temporary:
            root = Path(temporary)
            for datatype, (minimum, maximum) in BOUNDS.items():
                schema = f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
                  <xs:complexType name="Record"><xs:simpleContent><xs:extension base="xs:{datatype}">
                    <xs:attribute name="count" type="xs:{datatype}" use="required"/>
                  </xs:extension></xs:simpleContent></xs:complexType>
                  <xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/>
                </xs:schema>'''
                jobs[datatype] = SchemaJob(datatype, f"http://example.invalid/{datatype}.xsd", schema.encode())
                for version in ("11", "12"):
                    path = root / f"{datatype}-{version}.wsdl"
                    path.write_text(description(version, schema))
                    value = minimum if maximum is not None and maximum <= 0 else maximum
                    if value is None:
                        value = -(10**100 + 17) if maximum is not None and maximum <= 0 else 10**100 + 17
                    cases.append({"wsdl": str(path), "binding": "Soap" + version, "version": version,
                                  "datatype": datatype, "value": str(value)})
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(cases))
            process = subprocess.run(["qore", "--enable-debug", str(Path(__file__).with_name("integer-consumers.qr")),
                                      str(manifest)], text=True, capture_output=True, timeout=60, check=True)
        self.assertEqual("", process.stderr)
        rows = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(104, len(rows))
        identities = set()
        inputs = {(c["datatype"], c["version"]): int(c["value"]) for c in cases}
        for row in rows:
            key = row["datatype"], row["version"], row["copy"], row["direction"]
            self.assertNotIn(key, identities)
            identities.add(key)
            value = inputs[key[:2]]
            self.assertEqual(value, int(row["value"]["^value^"]))
            self.assertEqual(value, int(row["value"]["^attributes^"]["count"]))
            for kind in ("body", "example"):
                envelope = etree.fromstring(row[kind].encode())
                self.assertEqual(f"{{{survey.SOAP_NAMESPACES[int(row['version'] == '12')]}}}Envelope", envelope.tag)
                element = envelope.find("{*}Body")[0]
                self.assertEqual(f"{{{NS}}}" + ("Submit" if row["direction"] == "request" else "Reply"), element.tag)
                if kind == "body":
                    self.assertEqual(value, int(element.text))
                    self.assertEqual(value, int(element.attrib["count"]))
                name = "/".join(map(str, key)) + "/" + kind
                jobs[row["datatype"]].documents[name] = etree.tostring(element)
        results = run_independent(list(jobs.values()))
        self.assertEqual(208, len(results["documents"]))
        for name, result in results["documents"].items():
            self.assertTrue(result["ok"], (name, result))


if __name__ == "__main__":
    unittest.main()
