#!/usr/bin/env python3
"""Native QName union candidates, order and cleanup against XSD and Xerces.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as run_independent

ROOT = Path(__file__).resolve().parent
DEFINITIONS = '''<xs:simpleType name="QNameString"><xs:union memberTypes="xs:QName xs:string"/></xs:simpleType>
<xs:simpleType name="StringQName"><xs:union memberTypes="xs:string xs:QName"/></xs:simpleType>
<xs:simpleType name="QNameInt"><xs:union memberTypes="xs:QName xs:int"/></xs:simpleType>
<xs:simpleType name="StringChoice"><xs:restriction base="QNameString"><xs:enumeration value="p:Name"/></xs:restriction></xs:simpleType>
<xs:simpleType name="QNameChoice"><xs:restriction base="QNameString"><xs:enumeration xmlns:c="urn:catalog" value="c:Name"/></xs:restriction></xs:simpleType>
<xs:simpleType name="Nested"><xs:union memberTypes="QNameInt xs:string"/></xs:simpleType>
<xs:simpleType name="QNameList"><xs:list itemType="xs:QName"/></xs:simpleType>
<xs:simpleType name="ListOrString"><xs:union memberTypes="QNameList xs:string"/></xs:simpleType>
<xs:simpleType name="IntItems"><xs:list itemType="QNameInt"/></xs:simpleType>
<xs:simpleType name="StringItems"><xs:list itemType="QNameString"/></xs:simpleType>'''
CASES = (("p:Name", ""), ("p:Name", "urn:catalog"), ("p:Name", "urn:other"),
         ("xml:lang", ""), ("Name", ""), ("", ""), ("p:Name:Bad", ""), ("17", ""),
         ("p:Name 17", ""), ("p:Name 17", "urn:catalog"))
# XSD 1.0: the first matching member selects the primitive value. Unbound
# QName text can be a string, but binding its prefix changes that selection.
VALID = {"xs:QName": {1, 2, 3, 4}, "QNameString": set(range(10)),
         "StringQName": set(range(10)), "QNameInt": {1, 2, 3, 4, 7},
         "StringChoice": {0}, "QNameChoice": {1}, "Nested": set(range(10)),
         "ListOrString": set(range(10)), "IntItems": {1, 2, 3, 4, 5, 7, 9},
         "StringItems": set(range(10))}
# The unpatched library reports QName trial errors even when a later member
# accepts. Keep these exact old-oracle disagreements visible, never waived for Qore.
TRIAL_ERRORS = {("QNameString", 0), ("StringChoice", 0), ("Nested", 0),
                ("ListOrString", 0), ("ListOrString", 8), ("StringItems", 0), ("StringItems", 8)}


def fixtures():
    for kind, valid in VALID.items():
        for shape in ("content", "attribute", "both"):
            attribute = f'<xs:attribute name="category" type="{kind}" use="required"/>' if shape != "content" else ""
            element_type = kind if shape != "attribute" else "xs:string"
            schema = ('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">' + DEFINITIONS
                      + '<xs:element name="value"><xs:complexType><xs:simpleContent>'
                      f'<xs:extension base="{element_type}">{attribute}</xs:extension>'
                      '</xs:simpleContent></xs:complexType></xs:element></xs:schema>')
            for index, (lexical, uri) in enumerate(CASES):
                element = etree.Element("value", nsmap={"p": uri} if uri else None)
                if shape != "content":
                    element.set("category", lexical)
                if shape != "attribute":
                    element.text = lexical
                yield {"name": f"{kind}-{shape}-{index}", "group": f"{kind}-{shape}",
                       "schema": schema, "xml": etree.tostring(element, encoding="unicode"),
                       "valid": index in valid, "text": lexical if shape != "attribute" else "",
                       "attribute": lexical if shape != "content" else None,
                       "trial_error": (kind, index) in TRIAL_ERRORS,
                       "diagnostics": 2 if shape == "both" else 1}


class QNameUnionValidatorTest(unittest.TestCase):
    def test_ordered_members_and_native_validation(self):
        rows = list(fixtures())
        self.assertEqual(300, len(rows))
        self.assertEqual(300, len({row["name"] for row in rows}))
        jobs = {}
        for row in rows:
            group = row["group"]
            if group not in jobs:
                jobs[group] = SchemaJob(group, f"urn:qname-union:{group}", row["schema"].encode())
            jobs[group].documents[row["name"]] = row["xml"].encode()
        independent = run_independent(list(jobs.values()))
        self.assertEqual(30, len(independent["schemas"]))
        self.assertEqual(300, len(independent["documents"]))
        for verdict in independent["schemas"].values():
            self.assertTrue(verdict["ok"], verdict)
            self.assertEqual([], verdict["warnings"])
        artifacts = Path(tempfile.mkdtemp(prefix="xml-qname-union-validator-"))
        manifest = artifacts / "fixtures.json"
        manifest.write_text(json.dumps({"rows": rows}, indent=2) + "\n")
        process = subprocess.run(["qore", "-b", "--enable-debug", ROOT / "qname-union-validator.qr", manifest],
                                 text=True, capture_output=True, timeout=120)
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual("", process.stderr)
        results = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual([row["name"] for row in rows], [row["name"] for row in results])
        validators = {name: etree.XMLSchema(etree.fromstring(job.schema)) for name, job in jobs.items()}
        mismatches = []
        library = []
        for row, result in zip(rows, results):
            with self.subTest(name=row["name"]):
                verdict = independent["documents"][row["name"]]
                self.assertEqual(row["valid"], verdict["ok"], verdict)
                self.assertEqual([], verdict["warnings"])
                for method in ("parse", "reader", "cursor", "grouped"):
                    self.assertEqual(row["valid"], result[method], result)
                    if not row["valid"]:
                        self.assertEqual("PARSE-XML-EXCEPTION", result[method + "_error"])
                if row["valid"]:
                    self.assertTrue(result["preserved"])
                    self.assertEqual("value", result["element"])
                    self.assertEqual(row["text"], result["text"])
                    self.assertEqual(row["attribute"], result["attribute"])
                    self.assertEqual(row["text"] or None, result["cursor_value"])
                    self.assertEqual(row["text"] or None, result["grouped_value"])
                validator = validators[row["group"]]
                ok = validator.validate(etree.fromstring(row["xml"].encode()))
                errors = [error.type_name for error in validator.error_log]
                library.append({"name": row["name"], "ok": ok, "errors": errors})
                if ok != row["valid"]:
                    self.assertTrue(row["trial_error"] and row["valid"])
                    self.assertEqual(["SCHEMAV_CVC_DATATYPE_VALID_1_2_1"] * row["diagnostics"], errors)
                    mismatches.append(row["name"])
        expected = sorted(row["name"] for row in rows if row["trial_error"])
        self.assertEqual(21, len(expected))
        # A fixed independent libxml2 may agree on all rows. An affected one
        # must produce the entire precisely identified set, not arbitrary gaps.
        self.assertIn(sorted(mismatches), (expected, []))
        (artifacts / "results.json").write_text(json.dumps({
            "fixtures_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
            "xerces": independent, "libxml2_version": etree.LIBXML_VERSION,
            "libxml2": library, "native": results, "disagreements": mismatches}, indent=2) + "\n")
        print(f"QName union validation artifacts: {artifacts}", flush=True)


if __name__ == "__main__":
    unittest.main()
