#!/usr/bin/env python3
"""The SOAP assertion ledger is checked in every suite run, and its checks reject each kind of drift.

Copyright (C) 2026 Qore Technologies, s.r.o.

verify_ledger.py checks assertion-ledger.json against the pinned specification texts and the actual test suite. It
used to be run only by hand; this test runs it on the real ledger, and on mutated copies to show that each check
fails for the fault it exists to catch.
"""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import verify_ledger

LEDGER = json.loads(verify_ledger.LEDGER.read_text())


def run(ledger):
    """Returns (status, output) of the verifier for a ledger."""
    with tempfile.TemporaryDirectory(prefix="ledger-test-") as temp:
        path = Path(temp) / "assertion-ledger.json"
        path.write_text(json.dumps(ledger))
        output = io.StringIO()
        with mock.patch.object(verify_ledger, "LEDGER", path), contextlib.redirect_stdout(output):
            status = verify_ledger.main()
    return status, output.getvalue()


def row(ledger, predicate):
    """Returns the first ledger row matching a predicate."""
    return next(entry for entry in ledger["assertions"] if predicate(entry))


class LedgerTest(unittest.TestCase):
    def test_current_ledger(self):
        status, output = run(LEDGER)
        self.assertEqual(0, status, output)
        self.assertIn(f"ledger rows: {len(LEDGER['assertions'])}", output)
        self.assertTrue(output.rstrip().endswith("OK"), output)
        # every published requirement is accounted for, and nothing is left open
        coverage = {entry["coverage"] for entry in LEDGER["assertions"]}
        self.assertLessEqual(coverage, {"covered", "not-applicable"})

    def assertRejected(self, ledger, message):
        status, output = run(ledger)
        self.assertEqual(1, status, output)
        self.assertIn(message, output)

    def test_duplicate_and_missing_rows(self):
        ledger = copy.deepcopy(LEDGER)
        ledger["assertions"].append(copy.deepcopy(ledger["assertions"][0]))
        self.assertRejected(ledger, "duplicate ledger rows")
        ledger = copy.deepcopy(LEDGER)
        removed = ledger["assertions"].pop()
        self.assertRejected(ledger, f"{removed['id']}: published requirement is absent from the ledger")
        ledger = copy.deepcopy(LEDGER)
        extra = copy.deepcopy(ledger["assertions"][0])
        extra["id"] = "R99999"
        extra["source"] = "wsi12"
        ledger["assertions"].append(extra)
        self.assertRejected(ledger, "R99999: ledger row is not a published requirement identifier")

    def test_executable_cases_must_exist(self):
        ledger = copy.deepcopy(LEDGER)
        covered = row(ledger, lambda entry: entry["coverage"] == "covered")
        covered["tests"][0]["case"] = "a case that does not exist"
        self.assertRejected(ledger, "has no case 'a case that does not exist'")
        covered["tests"] = [{"file": "test/no-such-file.qtest", "case": "x"}]
        self.assertRejected(ledger, "mapped file test/no-such-file.qtest does not exist")
        covered["tests"] = []
        self.assertRejected(ledger, f"{covered['id']}: recorded as covered but names no executable case")

    def test_quotes_must_be_verbatim(self):
        ledger = copy.deepcopy(LEDGER)
        quoted = row(ledger, lambda entry: entry["source"] == "w3c-soap12" and entry.get("normative_quotes"))
        quoted["normative_quotes"][0] = "a requirement the specification does not state"
        self.assertRejected(ledger, f"{quoted['id']}: quoted requirement is not present verbatim")
        ledger = copy.deepcopy(LEDGER)
        profile = row(ledger, lambda entry: entry["source"] == "wsi12" and entry.get("normative_quotes"))
        profile["normative_quotes"] = []
        self.assertRejected(ledger, f"{profile['id']}: quotes no part of its requirement statement")

    def test_exclusions_need_a_specification_rationale(self):
        ledger = copy.deepcopy(LEDGER)
        excluded = row(ledger, lambda entry: entry["coverage"] == "not-applicable")
        excluded["rationale"] = "The test collection did not test this."
        self.assertRejected(ledger, "excluded on the old collection's coverage rather than on the specification")
        excluded["rationale"] = ""
        self.assertRejected(ledger, f"{excluded['id']}: no rationale recorded")
        excluded["rationale"] = "Not applicable."
        excluded["applicability"] = "applicable"
        self.assertRejected(ledger, "coverage and applicability disagree")

    def test_gaps_and_routes(self):
        ledger = copy.deepcopy(LEDGER)
        entry = row(ledger, lambda entry: entry["coverage"] == "covered" and entry.get("subject") != "ws-addressing")
        entry["coverage"] = "gap"
        self.assertRejected(ledger, f"{entry['id']}: recorded as a gap without saying what is missing")
        entry["gap"] = "the capability is missing"
        entry["coverage"] = "covered"
        self.assertRejected(ledger, f"{entry['id']}: records a gap but is not marked as one")
        del entry["gap"]
        entry["coverage"] = "routed"
        entry["phase"] = "P8"
        self.assertRejected(ledger, "routed to a later phase but still recorded against P8")
        ledger = copy.deepcopy(LEDGER)
        addressing = row(ledger, lambda entry: entry.get("subject") == "ws-addressing"
                         and entry["coverage"] == "covered")
        addressing["coverage"] = "gap"
        addressing["gap"] = "WS-Addressing"
        self.assertRejected(ledger, "WS-Addressing requirement still recorded as a gap")

    def test_pinned_sources(self):
        # a changed specification text fails before any row is checked
        original = verify_ledger.NORMATIVE
        with tempfile.TemporaryDirectory(prefix="ledger-test-") as temp:
            copied = Path(temp) / "normative"
            copied.mkdir()
            for path in original.iterdir():
                if path.is_file():
                    (copied / path.name).write_bytes(path.read_bytes())
            name = next(iter(json.loads((original / "sources.json").read_text())["documents"]))
            target = copied / f"{name}.html"
            target.write_bytes(target.read_bytes() + b"\n")
            with mock.patch.object(verify_ledger, "NORMATIVE", copied), \
                    mock.patch.object(verify_ledger.soap_sections, "NORMATIVE", copied, create=True):
                problems = []
                verify_ledger.check_sources(problems)
        self.assertTrue(any(f"{name}.html: digest" in problem for problem in problems), problems)


if __name__ == "__main__":
    unittest.main()
