#!/usr/bin/env python3
"""Strict Qore coverage, complete accounting, independent values and real binding tests.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from lxml import etree

import corpus
import coverage
import survey


ROOT = Path(__file__).resolve().parent


class CoverageTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="wsdl-coverage-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "w3c/BooleanElement", self.root / "BooleanElement")
        self.source = json.loads((ROOT / "adjudication-report.json").read_text())
        self.source["cases"] = [c for c in self.source["cases"] if c["case"] == "BooleanElement"]
        self.selection = corpus.read_manifest(ROOT / "strict-selection.json")
        self.selection["cases"] = {"BooleanElement": self.selection["cases"]["BooleanElement"]}

    def test_strict_positive_both_directions_and_value_change_detection(self):
        report = coverage.assess(self.root, self.source, self.selection, corpus.Catalog())
        self.assertEqual([], report["selected_failures"])
        self.assertEqual([], report["failures"])
        self.assertEqual({"wsdls": 1, "message_directions": 16}, report["selected_scope"])
        self.assertEqual(16, report["stage_accounting"]["counts"]["values"]["ok"])
        identity = report["cases"][0]["identity"]
        self.assertNotEqual(identity["directions"]["request"]["message"], identity["directions"]["response"]["message"])
        cases, _ = coverage.prepare(self.root, self.source)
        rows = survey.run_worker(cases, {})
        # A changed boolean is still schema-valid. The strict gate must detect its changed value.
        encoded = next(r for r in rows if r["stage"] == "serialize")
        encoded["body"] = encoded["body"].replace(">false<", ">true<")
        with patch.object(survey, "run_worker", return_value=rows):
            report = coverage.assess(self.root, self.source, self.selection, corpus.Catalog())
        self.assertEqual(["value_preservation"], report["selected_failures"][0]["stages"])
        row = report["cases"][0]["messages"][0]
        self.assertTrue(row["output_xerces"]["ok"])
        self.assertTrue(row["output_lxml"]["ok"])
        self.assertFalse(row["values"]["ok"])

    def test_strict_selection_and_source_integrity(self):
        _, records = coverage.prepare(self.root, self.source)
        variants = [{}, {"format": True, "cases": {}}, {"format": 1, "cases": {"absent": {}}}]
        for value in ({}, {"messages": {}}, {"messages": {"absent": []}},
                      {"messages": {next(iter(records["BooleanElement"]["messages"])): []}}):
            variants.append({"format": 1, "cases": {"BooleanElement": value}})
        for selection in variants:
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                coverage.validate_selection(selection, records)
        for key, value in (("wsdl_sha256", "0" * 64), ("messages", {})):
            source = deepcopy(self.source)
            source["cases"][0][key] = value
            with self.assertRaises(ValueError):
                coverage.prepare(self.root, source)
        duplicate = deepcopy(self.source)
        duplicate["cases"] *= 2
        with self.assertRaises(ValueError):
            coverage.prepare(self.root, duplicate)
        source = deepcopy(self.source)
        source["cases"][0]["source_decision"]["valid"] = None
        with self.assertRaisesRegex(ValueError, "provisional"):
            coverage.prepare(self.root, source)

    def test_missing_worker_stage_cannot_pass(self):
        cases, _ = coverage.prepare(self.root, self.source)
        rows = survey.run_worker(cases, {})
        with patch.object(survey, "run_worker", return_value=rows[:-1]), self.assertRaises(RuntimeError):
            coverage.assess(self.root, self.source, self.selection, corpus.Catalog())

    def test_real_cxf_soap12_binding_distinct_request_response(self):
        ns = "http://apache.org/hello_world_soap12_http/types"
        messages = []
        for direction, body in (("request", f'<sayHi xmlns="{ns}"/>'),
                                ("response", f'<sayHiResponse xmlns="{ns}"><responseType>Hello, world!</responseType>'
                                 '</sayHiResponse>')):
            file = direction + ".xml"
            path = self.root / file
            path.write_text(f'<s:Envelope xmlns:s="{survey.SOAP_NAMESPACES[1]}"><s:Body>{body}</s:Body></s:Envelope>')
            messages.append({"file": file, "path": str(path), "direction": direction})
        wsdl = ROOT / "cxf/hello_world_soap12.wsdl"
        case = {"name": "CxfSoap12", "wsdl": str(wsdl), "base": "http://cxf.invalid/",
                "operation": "sayHi", "binding": "Greeter_SOAPBinding", "messages": messages}
        rows = survey.run_worker([case], {})
        self.assertEqual(2, survey.stage_accounting([case], rows)["counts"]["serialize"]["ok"])
        schema = etree.XMLSchema(etree.parse(str(wsdl)).find(
            "{http://schemas.xmlsoap.org/wsdl/}types/{http://www.w3.org/2001/XMLSchema}schema"))
        for row in rows:
            if row["stage"] == "serialize":
                envelope = etree.fromstring(row["body"].encode())
                self.assertEqual(f"{{{survey.SOAP_NAMESPACES[1]}}}Envelope", envelope.tag)
                body = survey.payload(row["body"].encode(), survey.parser(self.root))
                self.assertTrue(schema.validate(body), str(schema.error_log))
                self.assertEqual(f"{{{ns}}}sayHi" + ("Response" if row["direction"] == "response" else ""), body.tag)
                if row["direction"] == "response":
                    self.assertEqual("Hello, world!", body.find(f"{{{ns}}}responseType").text)

    def test_full_strict_gate_keeps_later_failures_visible(self):
        path = corpus.extract(self.root / "complete")
        output = self.root / "coverage.json"
        process = subprocess.run([sys.executable, str(ROOT / "coverage.py"), str(path), "--strict", "--output",
                                  str(output)], text=True, capture_output=True, timeout=60, check=True)
        self.assertEqual("", process.stderr)
        report = json.loads(output.read_text())
        self.assertEqual([], report["selected_failures"])
        self.assertEqual(293, len(report["cases"]))
        self.assertEqual(2272, sum(len(c["messages"]) for c in report["cases"]))
        for stage, counts in report["stage_accounting"]["counts"].items():
            self.assertEqual(293 if stage == "parse" else 2272, sum(counts.values()))
            self.assertEqual(0, counts["missing"])
            self.assertEqual(0, counts["skipped"])
        # Harness assertions verify retained failures, not conformance passes for broken functionality.
        self.assertGreater(len(report["failures"]), 0)
        by_name = {c["case"]: c for c in report["cases"]}
        for name in ("NegativeIntegerElement", "NonNegativeIntegerElement"):
            failures = [m for m in by_name[name]["messages"] if "value_preservation" in m["failures"]]
            self.assertTrue(failures, name)
            self.assertEqual("P3", by_name[name]["implementation_phase"])
        self.assertTrue(by_name["ImportSchema"]["parse_requirement_passed"])
        self.assertEqual("PARSE-XML-EXCEPTION", by_name["ImportSchema"]["expected_parse"])
        self.assertEqual("WSDL-ERROR", by_name["BlockDefault"]["expected_parse"])
        invalid = [m for m in by_name["GlobalAttribute"]["messages"] if m["source_valid"] is False]
        self.assertTrue(all("wrong_error_category" in m["failures"] for m in invalid))
        disagreements = [m["output_oracle_disagreement"] for c in report["cases"] for m in c["messages"]
                         if "output_oracle_disagreement" in m]
        self.assertEqual(32, len(disagreements))
        self.assertTrue(all(d["adjudicated"] for d in disagreements))


if __name__ == "__main__":
    unittest.main()
