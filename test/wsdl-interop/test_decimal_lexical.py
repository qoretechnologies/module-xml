#!/usr/bin/env python3
"""Exact decimals through both SOAP bindings, directions, providers and examples.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS, XSD
import survey


VALID = ("0", "-0", "+001.2300", ".1", "1.", "123.45", " \t123.45\r\n",
         "1.00000000000000000001", "0.123450000000000000000006",
         "+10000000999829292922093443563.32423442",
         "+100000000000000000000000000000000000000000000.00")
INVALID = ("", " ", ".", "+", "-", "+.", "-.", "1e2", "1E-2", "0x10", "1tail",
           "1.2.3", "1 2", "--1", "+-1", "INF", "-INF", "NaN", "true", "١", "1\u00a0")


def schema(model):
    if model == "record":
        definition = '''<xs:complexType name="Record"><xs:simpleContent><xs:extension base="xs:decimal">
            <xs:attribute name="amount" type="xs:decimal" use="required"/>
            </xs:extension></xs:simpleContent></xs:complexType>'''
    elif model == "list":
        definition = '<xs:simpleType name="Record"><xs:list itemType="xs:decimal"/></xs:simpleType>'
    else:
        definition = '<xs:simpleType name="Record"><xs:union memberTypes="xs:decimal xs:boolean"/></xs:simpleType>'
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">{definition}
        <xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/></xs:schema>'''


def typed_value(model, element):
    text = element.text or ""
    if model == "record":
        return Decimal(text), Decimal(element.get("amount"))
    if model == "list":
        return [Decimal(item) for item in text.split()]
    text = text.strip(" \t\r\n")
    return text == "true" if text in ("true", "false") else Decimal(text)


class DecimalLexicalTest(unittest.TestCase):
    def test_both_bindings_and_directions(self):
        cases, jobs, validators, expected, values, outputs = [], {}, {}, {}, {}, {}
        libxml_disagreements = set()
        with tempfile.TemporaryDirectory(prefix="wsdl-decimal-") as temporary:
            root = Path(temporary)
            for model in ("record", "list", "union"):
                source = schema(model).encode()
                jobs[model] = SchemaJob(model, f"http://example.invalid/{model}.xsd", source)
                validators[model] = etree.XMLSchema(etree.fromstring(source))
                if model == "record":
                    variants = [(value, True) for value in VALID] + [(value, False) for value in INVALID]
                elif model == "list":
                    variants = [(value, True) for value in ("", " \t\r\n", "123.45 +001.2300 .5",
                                                          "1.00000000000000000001", "1\t2\n3")]
                    variants += [("1 " + value, False) for value in INVALID
                                 if value.strip(" \t\r\n") and value != "1 2"]
                    variants.append(("1 2tail", False))
                else:
                    variants = [(value, True) for value in VALID + ("true", "false")]
                    variants += [(value, False) for value in ("", " ", "TRUE", "yes", "1e2", "NaN", ".")]
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
                                element = etree.SubElement(body, f"{{{NS}}}{wrapper}")
                                element.text = lexical if location == "content" else "123.45"
                                if location == "content" and index % 2 == 0:
                                    element.text = etree.CDATA(element.text)
                                if model == "record":
                                    element.set("amount", lexical if location == "attribute" else "123.45")
                                oracle_valid = validators[model].validate(element)
                                if valid and not oracle_valid:
                                    # P1's retained libxml2 precision limitation. 2.12's decimal pre-parser
                                    # has a 24-digit buffer (before trimming fractional trailing zeros).
                                    # Xerces and exact Decimal values remain mandatory below.
                                    self.assertGreater(len(lexical.strip(" \t\r\n").lstrip("+-0").replace(".", "")), 24)
                                    libxml_disagreements.add(name)
                                else:
                                    self.assertEqual(valid, oracle_valid, (name, str(validators[model].error_log)))
                                jobs[model].documents[name] = etree.tostring(element)
                                if valid:
                                    values[name] = typed_value(model, element)
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
                         [row for row in rows if not row["ok"] and expected.get(row.get("file"))])
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
            element = envelope.find("{*}Body")[0]
            self.assertEqual(f"{{{NS}}}" + ("Submit" if direction == "request" else "Reply"), element.tag)
            if not validators[model].validate(element):
                self.assertIn(name, libxml_disagreements, (name, str(validators[model].error_log)))
            self.assertEqual(values[name], typed_value(model, element), name)
            self.assertEqual(0, len(element))
            outputs[name + "/output"] = True
            jobs[model].documents[name + "/output"] = etree.tostring(element)
        self.assertEqual(432, len(expected))
        self.assertEqual(160, len(outputs))
        # Newer libxml2 releases have removed this limit; every document is checked in either case.
        self.assertIn(len(libxml_disagreements), (0, 24))
        results = run_independent(list(jobs.values()))
        self.assertEqual(set(expected) | set(outputs), set(results["documents"]))
        for name, valid in (expected | outputs).items():
            self.assertEqual(valid, results["documents"][name]["ok"], (name, results["documents"][name]))

    def test_native_providers_and_examples(self):
        source = schema("record")
        validator = etree.XMLSchema(etree.fromstring(source.encode()))
        job = SchemaJob("consumers", "http://example.invalid/consumers.xsd", source.encode())
        libxml_disagreements = set()
        expected = [Decimal(text) for text in ("123.45", "0.1", "1e100", "5e-324", "1.7976931348623157e308",
                    "123.45", "0.1", "1.00000000000000000001", "0.123450000000000000000006",
                    "9223372036854775807", "+001.2300", "12345678901234567890.123456789")]
        with tempfile.TemporaryDirectory(prefix="wsdl-decimal-consumers-") as temporary:
            for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                path = Path(temporary) / f"{version}.wsdl"
                path.write_text(description(version, source))
                process = subprocess.run(["qore", "--enable-debug", str(Path(__file__).with_name("decimal-consumers.qr")),
                                          str(path), "Soap" + version], text=True, capture_output=True,
                                         timeout=60, check=True)
                self.assertEqual("", process.stderr)
                rows = [json.loads(line) for line in process.stdout.splitlines()]
                self.assertEqual(48, len(rows))
                identities = set()
                for row in rows:
                    key = f"{version}/{row['copy']}/{row['direction']}/{row['index']}"
                    self.assertNotIn(key, identities)
                    identities.add(key)
                    for kind in ("body", "example"):
                        envelope = etree.fromstring(row[kind].encode())
                        self.assertEqual(f"{{{envelope_ns}}}Envelope", envelope.tag)
                        element = envelope.find("{*}Body")[0]
                        self.assertEqual(f"{{{NS}}}" + ("Submit" if row["direction"] == "request" else "Reply"), element.tag)
                        if not validator.validate(element):
                            self.assertEqual("body", kind)
                            self.assertIn(row["index"], (2, 3, 4, 11), str(validator.error_log))
                            self.assertGreater(len(element.text.lstrip("+-0").replace(".", "")), 24)
                            libxml_disagreements.add(key)
                        if kind == "body":
                            self.assertEqual((expected[row["index"]], expected[row["index"]]), typed_value("record", element))
                        job.documents[key + "/" + kind] = etree.tostring(element)
        self.assertEqual(192, len(job.documents))
        self.assertIn(len(libxml_disagreements), (0, 32))
        results = run_independent([job])
        self.assertEqual(set(job.documents), set(results["documents"]))
        for name, result in results["documents"].items():
            self.assertTrue(result["ok"], (name, result))


if __name__ == "__main__":
    unittest.main()
