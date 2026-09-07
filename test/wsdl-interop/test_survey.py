#!/usr/bin/env python3
"""Tests for the offline survey and fixture provenance.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

import hashlib
import json
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from lxml import etree

import survey


ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "w3c"


class SurveyTest(unittest.TestCase):
    def test_inventory_and_provenance(self):
        cases = survey.inventory(FIXTURES, "both")
        self.assertEqual(8, len(cases))
        self.assertEqual(64, sum(len(c["messages"]) for c in cases))
        cases11 = survey.inventory(FIXTURES, "11")
        cases12 = survey.inventory(FIXTURES, "12")
        self.assertEqual(32, sum(len(c["messages"]) for c in cases11))
        self.assertEqual(32, sum(len(c["messages"]) for c in cases12))
        for item in json.loads((FIXTURES / "manifest.json").read_text()):
            self.assertEqual(item["sha256"], hashlib.sha256((FIXTURES / item["path"]).read_bytes()).hexdigest())

    def test_empty_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "no echo WSDL"):
                survey.inventory(Path(directory), "11")

    def test_payload_preserves_qname_context(self):
        schema = etree.XMLSchema(etree.fromstring(b'''
            <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
              <xs:element name="q" type="xs:QName"/>
            </xs:schema>'''))
        xml_parser = survey.parser(FIXTURES)
        for ns in survey.SOAP_NAMESPACES:
            wire = f'<s:Envelope xmlns:s="{ns}" xmlns:t="urn:example"><s:Body><q>t:value</q></s:Body></s:Envelope>'
            element = survey.payload(wire.encode(), xml_parser)
            self.assertEqual("urn:example", element.nsmap["t"])
            self.assertTrue(schema.validate(element))
            invalid = wire.replace(' xmlns:t="urn:example"', "")
            self.assertFalse(survey.validate(schema, invalid.encode(), xml_parser)["ok"])

    def test_invalid_envelopes(self):
        for wire in (b"<not-soap/>", b"<broken", b'''<s:Envelope
                     xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><a/><b/></s:Body></s:Envelope>'''):
            with self.assertRaises((ValueError, etree.XMLSyntaxError)):
                survey.payload(wire, survey.parser(FIXTURES))

    def test_offline_resolution(self):
        resolver = survey.CorpusResolver(FIXTURES)
        for url in ("https://example.invalid/schema.xsd", "file:///etc/passwd",
                    survey.SOURCE + "../outside.xsd", survey.SOURCE + "missing.xsd"):
            with self.assertRaises(OSError):
                resolver.resolve(url, None, None)
        self.assertIsNotNone(resolver.resolve(survey.SOURCE + "BooleanElement/echoBooleanElement.xsd", None, None))

    def test_oracle_disagreement_is_separate(self):
        cases = [c for c in survey.inventory(FIXTURES, "11") if c["name"] == "UnsignedShortElement"]
        original = FIXTURES / "UnsignedShortElement/echoUnsignedShortElement-UnsignedShortElement04-soap11.xml"
        wire = original.read_text().replace(">65535<", ">65536<")
        rows = [{"case": "UnsignedShortElement", "stage": "serialize", "ok": True,
                 "file": original.relative_to(FIXTURES).as_posix(), "body": wire}]
        report = survey.examine(FIXTURES, cases, rows)
        self.assertEqual(1, report["counts"]["valid_input_invalid_output"])
        self.assertTrue(report["rows"][0]["input_validation"]["ok"])
        self.assertFalse(report["rows"][0]["output_validation"]["ok"])
        self.assertIn("body", report["rows"][0])
        # A rejected source is still recorded separately, regardless of the validator's exact reason.
        self.assertEqual(4, len(report["inputs"]))

    def test_cli_with_real_qore(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            run = subprocess.run([sys.executable, str(ROOT / "survey.py"), str(FIXTURES),
                                  "--output", str(output), "--soap-version", "both"],
                                 text=True, capture_output=True, timeout=30, check=True)
            self.assertEqual("", run.stderr)
            result = json.loads(output.read_text())
            self.assertEqual(8, result["counts"]["parse_ok"])
            self.assertEqual(64, result["counts"]["serialize_ok"])
            self.assertEqual(0, result["counts"].get("valid_input_invalid_output", 0))
            self.assertEqual(0, result["counts"].get("deserialize_failed", 0))
            self.assertEqual(80, len(result["source_sha256"]))
            self.assertEqual(False, result["scope"]["network"])

    def test_worker_output_completeness(self):
        cases = [{"name": "A", "messages": [{"file": "A/one.xml"}, {"file": "A/two.xml"}]},
                 {"name": "B", "messages": [{"file": "B/one.xml"}]}]
        rows = [{"case": "A", "stage": "parse", "ok": True},
                {"case": "A", "file": "A/one.xml", "stage": "deserialize", "ok": True},
                {"case": "A", "file": "A/one.xml", "stage": "serialize", "ok": True, "body": "<a/>"},
                {"case": "A", "file": "A/two.xml", "stage": "deserialize", "ok": False,
                 "err": "SOAP-DESERIALIZATION-ERROR", "desc": "rejected input"},
                {"case": "B", "stage": "parse", "ok": False, "err": "WSDL-ERROR", "desc": "bad schema"}]
        survey.check_rows(cases, rows)
        variants = [rows[:-1], rows[:2] + rows[3:], rows + [rows[0]], rows[:1] + rows[2:], rows + [None]]
        for index, key, value in ((0, "case", "unknown"), (1, "file", "A/wrong.xml"), (0, "ok", 1),
                                  (2, "body", None), (3, "err", None), (0, "stage", "serialize")):
            invalid = deepcopy(rows)
            invalid[index][key] = value
            variants.append(invalid)
        for variant in variants:
            with self.subTest(rows=variant), self.assertRaises(RuntimeError):
                survey.check_rows(cases, variant)

    def test_worker_serialization_failure(self):
        cases = [{"name": "A", "messages": [{"file": "A/one.xml"}]}]
        rows = [{"case": "A", "stage": "parse", "ok": True},
                {"case": "A", "file": "A/one.xml", "stage": "deserialize", "ok": True},
                {"case": "A", "file": "A/one.xml", "stage": "serialize", "ok": False,
                 "err": "SOAP-SERIALIZATION-ERROR", "desc": "rejected value"}]
        survey.check_rows(cases, rows)
        with self.assertRaises(RuntimeError):
            survey.check_rows(cases, rows[:-1])


if __name__ == "__main__":
    unittest.main()
