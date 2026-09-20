#!/usr/bin/env python3
"""Whole-archive coverage and aggregate source-defect regressions.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

from collections import Counter
from pathlib import Path
import tempfile
import unittest

from lxml import etree

import archive_roles
import corpus


class ArchiveRolesTest(unittest.TestCase):
    def test_complete_archive_roles_and_dependency_adjudication(self):
        with tempfile.TemporaryDirectory(prefix="wsdl-archive-roles-test-") as temporary:
            root = Path(temporary) / "corpus"
            corpus.extract(root)
            # This single worker constructs all 18 historical aggregate contracts.
            report = archive_roles.assess(root, worker_timeout=600)
            self.assertEqual(4191, len(report["files"]))
            self.assertEqual(4191, sum(report["role_counts"].values()))
            self.assertEqual([], report["unclassified"])
            for role in ("echo-wsdl1", "echo-schema", "duplicate-echo-schema", "wsdl2-description"):
                self.assertEqual(293, report["role_counts"][role])
            self.assertEqual(568, report["role_counts"]["bare-echo-payload"])
            self.assertEqual(568, report["role_counts"]["raw-payload-fragment"])
            self.assertEqual(1136, report["role_counts"]["soap-message"])
            self.assertEqual(18, len(report["additional_contracts"]))
            self.assertEqual(4, sum(c["source_valid"] is False for c in report["additional_contracts"]))
            for record in report["additional_contracts"]:
                self.assertIn("qore", record)
                if record["source_valid"]:
                    self.assertTrue(record["qore"]["ok"], record["qore"])
                if not record["source_valid"]:
                    self.assertTrue(record["parse_requirement_passed"])
                    self.assertEqual("passed", record["grammar_rejection"]["status"])
                    self.assertEqual("XSD10-schema-import-order", record["grammar_rejection"]["requirement"])
                for schema in record["schemas"]:
                    self.assertIs(schema["source_valid"], schema["xerces"]["ok"])
                    self.assertIs(schema["source_valid"], schema["lxml"]["ok"])
                    if not schema["source_valid"]:
                        self.assertTrue(schema["normative_errors"])
                        self.assertIn("XSD10-schema-import-order", [e["requirement"] for e in schema["normative_errors"]])
            missing = [edge for edge in report["imports"] if edge["status"] == "invalid-source-location"]
            self.assertEqual(2, len(missing))
            for edge in missing:
                self.assertEqual(404, edge["evidence"]["http_status"])
                self.assertIn("/examples/6/static/RelativeIncluded.xsd", edge["uri"])
            self.assertEqual(1136, len(report["aggregate_messages"]))
            self.assertEqual(568, len({m["id"] for m in report["aggregate_messages"]}))
            self.assertTrue(all(not m["source_valid"] and not m["actual_root"].startswith("{")
                                and m["expected_root"].startswith("{") for m in report["aggregate_messages"]))
            self.assertEqual({568}, set(Counter(m["source"] for m in report["aggregate_messages"]).values()))
            # An extra archive source cannot disappear into a metadata category.
            (root / "databinding/extra.xml").write_text("<extra/>")
            with self.assertRaisesRegex(ValueError, "missing or extra files"):
                archive_roles.assess(root)

    def test_worker_timeout_validation_precedes_archive_access(self):
        for value in (0, -1, 3601, True, 1.5, "180"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                archive_roles.assess(Path("/nonexistent-wsdl-archive"), worker_timeout=value)

    def test_normative_schema_grammar(self):
        xs = archive_roles.contract.XSD
        valid = etree.fromstring(f'<s:schema xmlns:s="{xs}"><s:annotation/><s:import namespace="urn:a"/>'
                                 '<s:element name="a" type="s:string"/><s:annotation/></s:schema>'.encode())
        self.assertEqual([], archive_roles.schema_grammar_errors(valid))
        bad = etree.fromstring(f'<s:schema xmlns:s="{xs}"><s:element name="a" type="s:string"/>'
                               '<s:import namespace="urn:a"/><wsdl/></s:schema>'.encode())
        self.assertEqual(["XSD10-schema-import-order", "XSD10-schema-content"],
                         [e["requirement"] for e in archive_roles.schema_grammar_errors(bad)])

    def test_source_copy_signature_preserves_names_values_and_qname_context(self):
        first = etree.fromstring(b'<a:r xmlns:a="urn:a" xmlns:q="urn:q">\n<a:v x="q:t">42</a:v>\n</a:r>')
        same = etree.fromstring(b'<r xmlns="urn:a" xmlns:q="urn:q"><v x="q:t">42</v></r>')
        self.assertEqual(archive_roles.signature(first), archive_roles.signature(same))
        for wire in (b'<r xmlns="urn:wrong" xmlns:q="urn:q"><v x="q:t">42</v></r>',
                     b'<r xmlns="urn:a" xmlns:q="urn:wrong"><v x="q:t">42</v></r>',
                     b'<r xmlns="urn:a" xmlns:q="urn:q"><v x="q:t">43</v></r>',
                     b'<r xmlns="urn:a" xmlns:q="urn:q"><v x="q:t"> 42 </v></r>'):
            self.assertNotEqual(archive_roles.signature(first), archive_roles.signature(etree.fromstring(wire)))


if __name__ == "__main__":
    unittest.main()
