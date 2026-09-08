#!/usr/bin/env python3
"""Exact numeric restrictions across real SOAP bindings and schema contexts.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from decimal import Decimal
from pathlib import Path
import json
import subprocess
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS, XSD
import survey


CASES = {
    "bounds": ("decimal", '<xs:minInclusive value="1.00000000000000000001"/>'
               '<xs:maxInclusive value="1.00000000000000000003"/>',
               ("1.00000000000000000001", "1.00000000000000000002", "1.00000000000000000003"),
               ("0.9", "1.00000000000000000000", "1.00000000000000000004")),
    "exclusive": ("decimal", '<xs:minExclusive value="-1.00000000000000000003"/>'
                  '<xs:maxExclusive value="-1.00000000000000000001"/>',
                  ("-1.00000000000000000002",),
                  ("-1.00000000000000000003", "-1.00000000000000000001", "-0.9")),
    "integer": ("integer", '<xs:minInclusive value="9223372036854775808123"/>'
                '<xs:maxExclusive value="9223372036854775808125"/>',
                ("9223372036854775808123", "+09223372036854775808124"),
                ("9223372036854775808122", "9223372036854775808125")),
    "digits": ("decimal", '<xs:totalDigits value="4"/><xs:fractionDigits value="4"/>',
               ("0.0012", "+000.001200", "12.3400", "0.0000"), ("0.00001", "12345", "1.2345")),
    "enum": ("decimal", '<xs:enumeration value="+001.2300"/><xs:enumeration value="-0.00"/>',
             ("1.23", "+001.2300", "-0", "+0.0"), ("1.23000000000000000001", "-1.23")),
    "pattern": ("integer", '<xs:pattern value="00[0-9]"/><xs:maxInclusive value="9"/>',
                ("009", "001"), ("9", "09", "010")),
}


def schema(base, facets, model):
    definition = f'<xs:simpleType name="Amount"><xs:restriction base="xs:{base}">{facets}</xs:restriction></xs:simpleType>'
    if model == "record":
        definition += '''<xs:complexType name="Record"><xs:simpleContent><xs:extension base="t:Amount">
            <xs:attribute name="amount" type="t:Amount" use="required"/>
            </xs:extension></xs:simpleContent></xs:complexType>'''
    elif model == "list":
        definition += '<xs:simpleType name="Record"><xs:list itemType="t:Amount"/></xs:simpleType>'
    else:
        definition += '<xs:simpleType name="Record"><xs:union memberTypes="t:Amount xs:boolean"/></xs:simpleType>'
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">{definition}
        <xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/></xs:schema>'''


def value(model, element):
    text = element.text or ""
    if model == "record":
        return Decimal(text), Decimal(element.get("amount"))
    if model == "list":
        return tuple(Decimal(item) for item in text.split())
    return text == "true" if text in ("true", "false") else Decimal(text)


class NumericFacetsTest(unittest.TestCase):
    def test_values_bindings_directions_and_contexts(self):
        cases, jobs, validators, expected, values, outputs = [], {}, {}, {}, {}, {}
        with tempfile.TemporaryDirectory(prefix="wsdl-numeric-facets-") as temporary:
            root = Path(temporary)
            for family, (base, facets, valid, invalid) in CASES.items():
                for model in ("record", "list", "union"):
                    key = family + "-" + model
                    source = schema(base, facets, model).encode()
                    jobs[key] = SchemaJob(key, f"http://example.invalid/{key}.xsd", source)
                    validators[key] = etree.XMLSchema(etree.fromstring(source))
                    variants = [(text, True) for text in valid] + [(text, False) for text in invalid]
                    if model == "list":
                        variants = [(valid[0] + " " + text, ok) for text, ok in variants]
                        variants.append(("", True))
                    if model == "union":
                        # xs:boolean recognizes only these additional literals; numeric negatives are not 0/1.
                        variants.append(("true", True))
                    for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                        wsdl = root / f"{key}-{version}.wsdl"
                        wsdl.write_text(description(version, source.decode()))
                        messages = []
                        for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                            for location in (("content", "attribute") if model == "record" else ("content",)):
                                for index, (text, ok) in enumerate(variants):
                                    name = f"{key}/{version}/{direction}/{location}/{index}"
                                    envelope = etree.Element(f"{{{envelope_ns}}}Envelope", nsmap={"s": envelope_ns})
                                    body = etree.SubElement(envelope, f"{{{envelope_ns}}}Body")
                                    element = etree.SubElement(body, f"{{{NS}}}{wrapper}")
                                    element.text = text if location == "content" else valid[0]
                                    if model == "record":
                                        element.set("amount", text if location == "attribute" else valid[0])
                                    self.assertEqual(ok, validators[key].validate(element),
                                                     (name, str(validators[key].error_log)))
                                    jobs[key].documents[name] = etree.tostring(element)
                                    expected[name] = ok
                                    if ok:
                                        values[name] = value(model, element)
                                    path = root / name.replace("/", "-")
                                    path.write_bytes(etree.tostring(envelope))
                                    messages.append({"file": name, "path": str(path), "direction": direction})
                        cases.append({"name": key + version, "wsdl": str(wsdl), "base": "http://example.invalid/",
                                      "operation": "submit", "binding": "Soap" + version, "messages": messages})
            rows = survey.run_worker(cases, {})
        counts = survey.stage_accounting(cases, rows)["counts"]
        self.assertEqual(36, counts["parse"]["ok"])
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
            key, version, direction, _, _ = name.split("/")
            model = key.split("-")[-1]
            envelope = etree.fromstring(row["body"].encode())
            self.assertEqual(f"{{{survey.SOAP_NAMESPACES[int(version == '12')]}}}Envelope", envelope.tag)
            element = envelope.find("{*}Body")[0]
            self.assertEqual(f"{{{NS}}}" + ("Submit" if direction == "request" else "Reply"), element.tag)
            self.assertTrue(validators[key].validate(element), (name, str(validators[key].error_log)))
            self.assertEqual(values[name], value(model, element), name)
            outputs[name + "/output"] = True
            jobs[key].documents[name + "/output"] = etree.tostring(element)
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(560, len(expected))
        self.assertEqual(304, len(outputs))
        self.assertEqual(set(expected) | set(outputs), set(oracle["documents"]))
        for name, ok in (expected | outputs).items():
            self.assertEqual(ok, oracle["documents"][name]["ok"], (name, oracle["documents"][name]))

    def test_providers_reconstruction_and_generated_examples(self):
        jobs, validators, expectations, definitions = {}, {}, {}, []
        with tempfile.TemporaryDirectory(prefix="wsdl-numeric-facet-consumers-") as temporary:
            root = Path(temporary)
            for family, (base, facets, valid, invalid) in CASES.items():
                variants = [{"text": text, "ok": True} for text in valid]
                variants += [{"text": text, "ok": False} for text in invalid]
                # Native MPFR/binary64 input must reach the same exact restrictions.
                if family == "bounds":
                    variants += [{"text": "1.00000000000000000002", "native": "number", "ok": True},
                                 {"text": "0.9", "native": "float", "ok": False}]
                elif family == "digits":
                    variants += [{"text": "12.34", "native": "float", "ok": True},
                                 {"text": "1.00000000000000000001", "native": "number", "ok": False}]
                for model in ("record", "list", "union"):
                    key = family + "-" + model
                    source = schema(base, facets, model).encode()
                    jobs[key] = SchemaJob(key, f"http://example.invalid/{key}.xsd", source)
                    validators[key] = etree.XMLSchema(etree.fromstring(source))
                    for version in ("11", "12"):
                        name = key + "/" + version
                        path = root / (name.replace("/", "-") + ".wsdl")
                        path.write_text(description(version, source.decode()))
                        definitions.append({"name": name, "wsdl": str(path), "binding": "Soap" + version,
                                            "model": model, "first": valid[0], "values": variants})
                        expectations[name] = (model, valid[0], variants)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(definitions))
            process = subprocess.run(["qore", "--enable-debug",
                                      str(Path(__file__).with_name("numeric-facet-consumers.qr")), str(manifest)],
                                     text=True, capture_output=True, timeout=60)
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual("", process.stderr)
        rows = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(sum(4 * (len(item[2]) + 1) for item in expectations.values()), len(rows))
        seen = set()
        for row in rows:
            name = f"{row['name']}/{row['copy']}/{row['direction']}/{row['index']}"
            self.assertNotIn(name, seen)
            seen.add(name)
            model, first, variants = expectations[row["name"]]
            if row["index"] != "example" and not variants[row["index"]]["ok"]:
                self.assertEqual("RUNTIME-TYPE-ERROR", row.get("err"), row)
                self.assertNotIn("body", row)
                continue
            self.assertNotIn("err", row)
            key, version = row["name"].split("/")
            envelope = etree.fromstring(row["body"].encode())
            self.assertEqual(f"{{{survey.SOAP_NAMESPACES[int(version == '12')]}}}Envelope", envelope.tag)
            element = envelope.find("{*}Body")[0]
            self.assertEqual(f"{{{NS}}}" + ("Submit" if row["direction"] == "request" else "Reply"), element.tag)
            self.assertTrue(validators[key].validate(element), (name, str(validators[key].error_log)))
            if row["index"] != "example":
                expected = Decimal(variants[row["index"]]["text"])
                if model == "record":
                    expected = (expected, expected)
                elif model == "list":
                    expected = (Decimal(first), expected)
                self.assertEqual(expected, value(model, element), name)
            jobs[key].documents[name] = etree.tostring(element)
        oracle = run_independent(list(jobs.values()))
        self.assertEqual({name for job in jobs.values() for name in job.documents}, set(oracle["documents"]))
        self.assertEqual(576, len(oracle["documents"]))
        for name, result in oracle["documents"].items():
            self.assertTrue(result["ok"], (name, result))


if __name__ == "__main__":
    unittest.main()
