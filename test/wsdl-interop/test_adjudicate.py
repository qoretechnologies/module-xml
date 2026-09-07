#!/usr/bin/env python3
"""Adjudication accounting and normative disagreement regressions.

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

import adjudicate
import corpus
import survey


ROOT = Path(__file__).resolve().parent


class AdjudicateTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="wsdl-adjudicate-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "w3c/BooleanElement", self.root / "BooleanElement")
        self.decisions = {"format": 1, "schemas": {}, "messages": {}, "historical_outputs": {}, "ownership": {},
            "requirements": {name: {"url": "https://www.w3.org/TR/xmlschema-1/", "reason": "XSD 1.0 validation"}
                             for name in ("XSD10-schema", "XSD10-payload")}}

    def test_valid_both_versions_and_inline_binding_identity(self):
        cases = survey.inventory(self.root, "both")
        result = adjudicate.assess(self.root, cases, corpus.Catalog(), self.decisions, {})
        self.assertEqual([], result["unclassified"])
        self.assertEqual({"wsdl_valid": 1, "messages_valid": 8}, result["counts"])
        record = result["cases"][0]
        self.assertEqual({"11"}, {v["soap_version"] for v in record["contract"]["bindings"].values()})
        self.assertEqual(8, len(record["messages"]))
        for value in record["messages"].values():
            for source in ("inline", "echo"):
                self.assertTrue(value[source]["lxml"]["ok"])
                self.assertTrue(value[source]["xerces"]["ok"])

    def test_unclassified_invalid_input_and_documented_rejection(self):
        original = self.root / "BooleanElement/echoBooleanElement-BooleanElement01-soap11.xml"
        file = "BooleanElement/invalid-soap11.xml"
        (self.root / file).write_text(original.read_text().replace(">false<", ">invalid<"))
        cases = survey.inventory(self.root, "both")
        result = adjudicate.assess(self.root, cases, corpus.Catalog(), self.decisions, {})
        self.assertEqual([file], result["unclassified"])
        self.assertEqual(1, result["counts"]["messages_unclassified"])
        self.decisions["messages"][file] = {"valid": False, "requirements": ["XSD10-payload"]}
        result = adjudicate.assess(self.root, cases, corpus.Catalog(), self.decisions, {})
        self.assertEqual([], result["unclassified"])
        self.assertEqual(1, result["counts"]["messages_invalid_source"])

    def test_duplicate_and_stale_cases_fail(self):
        cases = survey.inventory(self.root, "both")
        with self.assertRaisesRegex(ValueError, "duplicate case"):
            adjudicate.assess(self.root, cases * 2, corpus.Catalog(), self.decisions, {})
        duplicate = deepcopy(cases)
        duplicate[0]["messages"].append(duplicate[0]["messages"][0])
        with self.assertRaisesRegex(ValueError, "duplicate message"):
            adjudicate.assess(self.root, duplicate, corpus.Catalog(), self.decisions, {})
        self.decisions["messages"]["missing"] = {"valid": False, "requirements": ["XSD10-payload"]}
        with self.assertRaisesRegex(ValueError, "absent messages case"):
            adjudicate.assess(self.root, cases, corpus.Catalog(), self.decisions, {})

    def test_malformed_adjudications(self):
        variants = [[], {}, {"format": True}, {"format": 2}]
        for section, value in (("schemas", []), ("messages", {"a": {"valid": None}}),
                               ("ownership", {"a": "unknown"}), ("requirements", {}),
                               ("schemas", {"a": {"valid": True, "requirements": ["unknown"]}})):
            variant = deepcopy(self.decisions)
            variant[section] = value
            variants.append(variant)
        for variant in variants:
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                adjudicate.validate_decisions(variant)

    def test_full_pinned_corpus_strict_classification(self):
        directory = self.root / "full-corpus"
        path = corpus.extract(directory)
        output = self.root / "report.json"
        result = subprocess.run([sys.executable, str(ROOT / "adjudicate.py"), str(path), "--strict",
                                 "--output", str(output)], text=True, capture_output=True, check=True, timeout=60)
        self.assertEqual("", result.stderr)
        report = json.loads(output.read_text())
        self.assertEqual([], report["unclassified"])
        self.assertEqual(293, len(report["cases"]))
        self.assertEqual(1136, sum(len(c["messages"]) for c in report["cases"]))
        self.assertEqual(3, report["counts"]["historical_outputs_valid"])
        self.assertEqual(14, report["counts"]["wsdl_invalid_source"])
        self.assertEqual(88, report["counts"]["messages_invalid_source"])
        self.assertEqual(1048, report["counts"]["messages_valid"])
        # Every retained original disagreement has its own current classification.
        historical = json.loads((ROOT / "findings.json").read_text())
        messages = {f: r for c in report["cases"] for f, r in c["messages"].items()}
        for file in historical["input_oracle_disagreements"]:
            self.assertIn(file, messages)
            self.assertIs(type(messages[file]["decision"]["valid"]), bool)
        by_name = {c["case"]: c for c in report["cases"]}
        for name in ("IDREFAttribute", "IDREFElement", "IDREFSAttribute", "IDREFSElement"):
            self.assertEqual("P5", by_name[name]["implementation_phase"])
        (path / "extra.xsd").write_text("<extra/>")
        with self.assertRaisesRegex(ValueError, "differs from pinned inventory"):
            adjudicate.verify_original_corpus(path)


if __name__ == "__main__":
    unittest.main()
