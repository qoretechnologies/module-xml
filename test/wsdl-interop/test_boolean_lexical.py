#!/usr/bin/env python3
"""XSD boolean lexical space, typed values, and actual SOAP 1.1/1.2 bindings.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS, XSD
import survey


VALID = ("true", "false", "1", "0", " \ttrue\r\n", " \tfalse\r\n", " 1 ", " 0 ")
INVALID = ("", " ", "TRUE", "False", "yes", "no", "truefalse", "untrue", "false-tail", "2", "-1",
           "+1", "00", "1.0", "t rue", "true\u00a0", "false 0")


def schema(model):
    if model == "record":
        definition = '''<xs:complexType name="Record"><xs:simpleContent><xs:extension base="xs:boolean">
            <xs:attribute name="enabled" type="xs:boolean" use="required"/>
            </xs:extension></xs:simpleContent></xs:complexType>'''
    elif model == "list":
        definition = '<xs:simpleType name="Record"><xs:list itemType="xs:boolean"/></xs:simpleType>'
    else:
        definition = '<xs:simpleType name="Record"><xs:union memberTypes="xs:boolean xs:int"/></xs:simpleType>'
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">{definition}
        <xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/></xs:schema>'''


def boolean_value(text):
    return text.strip(" \t\r\n") in ("true", "1")


class BooleanLexicalTest(unittest.TestCase):
    def test_both_bindings_and_directions(self):
        cases, jobs, validators, expected, values, outputs = [], {}, {}, {}, {}, {}
        with tempfile.TemporaryDirectory(prefix="wsdl-boolean-") as temporary:
            root = Path(temporary)
            for model in ("record", "list", "union"):
                source = schema(model).encode()
                jobs[model] = SchemaJob(model, f"http://example.invalid/{model}.xsd", source)
                validators[model] = etree.XMLSchema(etree.fromstring(source))
                if model == "record":
                    variants = [(v, True) for v in VALID] + [(v, False) for v in INVALID]
                elif model == "list":
                    variants = [(v, True) for v in ("", " \t\r\n", "true false 1 0", "0", "1\t0\nfalse")]
                    variants += [("true " + v, False) for v in INVALID
                                 if v.strip(" \t\r\n") and v != "false 0"]
                    variants.append(("true false0", False))
                else:
                    variants = [(v, True) for v in VALID + ("12", "-2", "+1", "00")]
                    variants += [(v, False) for v in ("", " ", "TRUE", "yes", "no", "truefalse", "1.0")]
                for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                    path = root / f"{model}-{version}.wsdl"
                    path.write_text(description(version, source.decode()))
                    messages = []
                    for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                        for location in (("content", "attribute") if model == "record" else ("content",)):
                            for index, (lexical, valid) in enumerate(variants):
                                name = f"{model}/{version}/{direction}/{location}/{index}"
                                envelope = etree.Element(f"{{{envelope_ns}}}Envelope", nsmap={"s": envelope_ns})
                                body = etree.SubElement(envelope, f"{{{envelope_ns}}}Body")
                                value = etree.SubElement(body, f"{{{NS}}}{wrapper}")
                                value.text = lexical if location == "content" else "false"
                                if location == "content" and index % 2 == 0:
                                    value.text = etree.CDATA(value.text)
                                if model == "record":
                                    value.set("enabled", lexical if location == "attribute" else "1")
                                self.assertEqual(valid, validators[model].validate(value),
                                                 (name, str(validators[model].error_log)))
                                jobs[model].documents[name] = etree.tostring(value)
                                if valid:
                                    if model == "record":
                                        values[name] = boolean_value(value.text), boolean_value(value.get("enabled"))
                                    elif model == "list":
                                        values[name] = [boolean_value(v) for v in lexical.split()]
                                    else:
                                        v = lexical.strip(" \t\r\n")
                                        values[name] = boolean_value(v) if v in ("true", "false", "1", "0") else int(v)
                                message = root / name.replace("/", "-")
                                message.write_bytes(etree.tostring(envelope))
                                messages.append({"file": name, "path": str(message), "direction": direction})
                                expected[name] = valid
                    cases.append({"name": model + version, "wsdl": str(path), "base": "http://example.invalid/",
                                  "operation": "submit", "binding": "Soap" + version, "messages": messages})
            rows = survey.run_worker(cases, {})
        counts = survey.stage_accounting(cases, rows)["counts"]
        self.assertEqual(6, counts["parse"]["ok"])
        self.assertEqual(sum(expected.values()), counts["serialize"]["ok"],
                         [r for r in rows if not r["ok"] and expected.get(r.get("file"))])
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
            model, version, direction, _, _ = name.split("/")
            envelope = etree.fromstring(row["body"].encode())
            self.assertEqual(f"{{{survey.SOAP_NAMESPACES[int(version == '12')]}}}Envelope", envelope.tag)
            value = envelope.find("{*}Body")[0]
            self.assertEqual(f"{{{NS}}}" + ("Submit" if direction == "request" else "Reply"), value.tag)
            self.assertTrue(validators[model].validate(value), (name, str(validators[model].error_log)))
            text = value.text or ""
            if model == "record":
                self.assertEqual(values[name], (boolean_value(text), boolean_value(value.get("enabled"))))
            elif model == "list":
                self.assertEqual(values[name], [boolean_value(v) for v in text.split()])
            else:
                actual = boolean_value(text) if text in ("true", "false", "1", "0") else int(text)
                self.assertEqual(values[name], actual)
            self.assertEqual(0, len(value))
            outputs[name + "/output"] = True
            jobs[model].documents[name + "/output"] = etree.tostring(value)
        self.assertEqual(356, len(expected))
        self.assertEqual(132, len(outputs))
        results = run_independent(list(jobs.values()))
        self.assertEqual(set(expected) | set(outputs), set(results["documents"]))
        for name, valid in (expected | outputs).items():
            self.assertEqual(valid, results["documents"][name]["ok"], (name, results["documents"][name]))

    def test_native_providers_and_examples(self):
        source = schema("record")
        validator = etree.XMLSchema(etree.fromstring(source.encode()))
        job = SchemaJob("consumers", "http://example.invalid/consumers.xsd", source.encode())
        with tempfile.TemporaryDirectory(prefix="wsdl-boolean-consumers-") as temporary:
            for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                path = Path(temporary) / f"{version}.wsdl"
                path.write_text(description(version, source))
                process = subprocess.run(["qore", "--enable-debug", str(Path(__file__).with_name("boolean-consumers.qr")),
                                          str(path), "Soap" + version], text=True, capture_output=True,
                                         timeout=60, check=True)
                self.assertEqual("", process.stderr)
                rows = [json.loads(line) for line in process.stdout.splitlines()]
                self.assertEqual(32, len(rows))
                identities = set()
                for row in rows:
                    key = f"{version}/{row['copy']}/{row['direction']}/{row['index']}"
                    self.assertNotIn(key, identities)
                    identities.add(key)
                    value = row["value"]
                    expected_value = row["index"] % 2 == 1
                    self.assertIs(expected_value, value["^value^"])
                    self.assertIs(expected_value, value["^attributes^"]["enabled"])
                    for kind in ("body", "example"):
                        envelope = etree.fromstring(row[kind].encode())
                        self.assertEqual(f"{{{envelope_ns}}}Envelope", envelope.tag)
                        element = envelope.find("{*}Body")[0]
                        self.assertEqual(f"{{{NS}}}" + ("Submit" if row["direction"] == "request" else "Reply"), element.tag)
                        self.assertTrue(validator.validate(element), str(validator.error_log))
                        if kind == "body":
                            self.assertEqual((expected_value, expected_value),
                                             (boolean_value(element.text), boolean_value(element.get("enabled"))))
                        job.documents[key + "/" + kind] = etree.tostring(element)
        self.assertEqual(128, len(job.documents))
        results = run_independent([job])
        self.assertEqual(set(job.documents), set(results["documents"]))
        for name, result in results["documents"].items():
            self.assertTrue(result["ok"], (name, result))


if __name__ == "__main__":
    unittest.main()
