#!/usr/bin/env python3
"""Test independent oracle behavior, diagnostics, provenance and cleanup.

Copyright (C) 2026 Qore Technologies, s.r.o.
These are tests of the oracle harness, not claims that Qore passes these cases.
"""

from copy import deepcopy
import hashlib
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
from urllib.parse import urljoin

from lxml import etree

import corpus
import independent
from independent import SchemaJob


XSD = "http://www.w3.org/2001/XMLSchema"
ROOT = Path(__file__).resolve().parent


def scalar(name, kind, values):
    schema = f'<xs:schema xmlns:xs="{XSD}"><xs:element name="v" type="xs:{kind}"/></xs:schema>'
    return SchemaJob(name, "https://schemas.invalid/" + name + ".xsd", schema.encode(),
                     {name + "/" + key: f"<v>{value}</v>".encode() for key, value in values.items()})


class IndependentTest(unittest.TestCase):
    def test_scalars_and_explicit_oracle_limitations(self):
        integer = "1234567891234567838475834753838887348573489123456789123456789"
        decimal = "+10000000999829292922093443563.32423442"
        jobs = [scalar("integer", "integer", {"large": integer, "invalid": "42x"}),
                scalar("decimal", "decimal", {"large": decimal, "invalid": "1e2"}),
                scalar("boolean", "boolean", {"true": "true", "one": "1", "invalid": "True"}),
                scalar("unsigned", "unsignedLong", {"max": "18446744073709551615",
                    "overflow": "18446744073709551616", "negative": "-1", "signed-zero": "-0"}),
                scalar("gMonth", "gMonth", {"april": "--04", "invalid-zone": "--04-15:00",
                    "old-spelling": "--04--"}),
                scalar("entity", "ENTITY", {"undeclared": "lt"}),
                scalar("idref", "IDREF", {"unresolved": "missing"})]
        report = independent.run(jobs)
        self.assertEqual("Xerces-J 2.12.2", report["versions"]["xerces"])
        for job in jobs:
            self.assertTrue(report["schemas"][job.name]["ok"], job.name)
        for name in ("integer/large", "decimal/large", "boolean/true", "boolean/one",
                     "unsigned/max", "gMonth/april"):
            self.assertTrue(report["documents"][name]["ok"], name)
        for name in ("integer/invalid", "decimal/invalid", "boolean/invalid", "unsigned/overflow",
                     "unsigned/negative", "gMonth/invalid-zone", "entity/undeclared", "idref/unresolved"):
            self.assertFalse(report["documents"][name]["ok"], name)
            self.assertIn("SAXParseException", report["documents"][name]["desc"], name)
        # Reproduce known oracle disagreements; never use these acceptances as XSD 1.0 truth.
        self.assertTrue(report["documents"]["unsigned/signed-zero"]["ok"])
        self.assertTrue(report["documents"]["gMonth/old-spelling"]["ok"])

    def test_offline_schema_dependencies_and_document_restrictions(self):
        leaf = f'<xs:schema xmlns:xs="{XSD}"><xs:element name="v" type="xs:int"/></xs:schema>'.encode()
        parent = f'<xs:schema xmlns:xs="{XSD}"><xs:include schemaLocation="nested/leaf.xsd"/></xs:schema>'.encode()
        jobs = [SchemaJob("nested", "https://schemas.invalid/parent.xsd", parent,
                          {"nested-valid": b"<v>42</v>", "nested-invalid": b"<v>x</v>",
                           "forbidden-dtd": b'<!DOCTYPE v [<!ENTITY x SYSTEM "file:///etc/passwd">]><v>&x;</v>'}),
                SchemaJob("missing", "https://missing.invalid/parent.xsd", parent,
                          {"missing-unreachable": b"<v>42</v>"}),
                SchemaJob("empty", "https://schemas.invalid/empty.xsd", b"", {"empty-unreachable": b"<v/>"}),
                SchemaJob("schema-dtd", "https://schemas.invalid/schema-dtd.xsd",
                          b'<!DOCTYPE schema SYSTEM "https://outside.invalid/dtd">' + leaf),
                SchemaJob("unused-import", "urn:unused-import",
                    f'<xs:schema xmlns:xs="{XSD}"><xs:import namespace="urn:unused"/></xs:schema>'.encode()),
                SchemaJob("ambiguous", "urn:ambiguous", f'''<xs:schema xmlns:xs="{XSD}">
                  <xs:element name="v"><xs:complexType><xs:sequence>
                    <xs:element name="a" type="xs:int" minOccurs="0"/>
                    <xs:element name="a" type="xs:int"/>
                  </xs:sequence></xs:complexType></xs:element></xs:schema>'''.encode())]
        report = independent.run(jobs, {"https://schemas.invalid/nested/leaf.xsd": leaf})
        self.assertTrue(report["schemas"]["nested"]["ok"])
        self.assertTrue(report["schemas"]["unused-import"]["ok"])
        self.assertTrue(report["documents"]["nested-valid"]["ok"])
        self.assertFalse(report["documents"]["nested-invalid"]["ok"])
        self.assertIn("DOCTYPE", report["documents"]["forbidden-dtd"]["desc"])
        self.assertIn("resource unavailable offline", report["schemas"]["missing"]["desc"])
        self.assertFalse(report["schemas"]["empty"]["ok"])
        self.assertIn("DOCTYPE", report["schemas"]["schema-dtd"]["desc"])
        self.assertIn("cos-nonambig", report["schemas"]["ambiguous"]["desc"])
        for name in ("missing-unreachable", "empty-unreachable"):
            self.assertIsNone(report["documents"][name]["ok"])
            self.assertEqual("unreachable", report["documents"][name]["status"])

    def test_worker_result_completeness(self):
        jobs = [scalar("a", "int", {"good": "1", "bad": "invalid"}),
                SchemaJob("broken", "urn:broken", b"", {"unreachable": b"<v/>"})]
        enc = independent._encode
        lines = [f'version\t{enc(b"Xerces-J 2.12.2")}\t{enc(b"test-JDK")}',
                 "S\ta\tvalid\t", "V\ta/good\tvalid\t", f'V\ta/bad\tinvalid\t{enc(b"bad int")}',
                 f'S\tbroken\tinvalid\t{enc(b"empty schema")}',
                 f'V\tunreachable\tunreachable\t{enc(b"schema failed")}']
        lines = [lines[0], *(line + "\t" for line in lines[1:])]
        result = independent.check_results(jobs, "\n".join(lines))
        self.assertEqual(2, len(result["schemas"]))
        self.assertEqual(3, len(result["documents"]))
        variants = [lines[1:], lines[:-1], lines + [lines[-1]], lines[:2] + lines[3:]]
        for index, text in ((0, "version\t%%%\t%%%"), (1, "S\ta\tvalid\tbad!"),
                             (1, "S\ta\tunreachable\t"), (2, "V\twrong\tvalid\t"),
                             (3, "V\ta/bad\tinvalid\t"), (5, "V\tunreachable\tvalid\t")):
            variant = lines.copy()
            variant[index] = text + ("\t" if index else "")
            variants.append(variant)
        for variant in variants:
            with self.subTest(variant=variant), self.assertRaises(RuntimeError):
                independent.check_results(jobs, "\n".join(variant))

    def test_warnings_are_retained_without_changing_validation(self):
        schema = f'''<xs:schema xmlns:xs="{XSD}"><xs:simpleType name="Base"><xs:list itemType="xs:int"/>
            </xs:simpleType><xs:element name="v"><xs:simpleType><xs:restriction base="Base">
            <xs:length value="2"/><xs:enumeration value="1 2"/></xs:restriction></xs:simpleType>
            </xs:element></xs:schema>'''.encode()
        report = independent.run([SchemaJob("warn", "urn:warn", schema,
            {"good": b"<v>1 2</v>", "bad": b"<v>1 3</v>"}), scalar("clean", "int", {"clean": "1"})])
        self.assertTrue(report["schemas"]["warn"]["ok"])
        warnings = report["schemas"]["warn"]["warnings"]
        self.assertEqual(1, len(warnings))
        self.assertIn("FacetsContradict", warnings[0])
        self.assertTrue(report["documents"]["good"]["ok"])
        self.assertFalse(report["documents"]["bad"]["ok"])
        self.assertIn("enumeration", report["documents"]["bad"]["desc"])
        self.assertEqual([], report["schemas"]["clean"]["warnings"])
        self.assertTrue(all(not row["warnings"] for row in report["documents"].values()))
        # Diagnostic records retain ordered warning text and reject malformed encodings.
        job = scalar("a", "int", {})
        enc = independent._encode
        prefix = f'version\t{enc(b"Xerces-J 2.12.2")}\t{enc(b"JDK")}\nS\ta\tvalid\t\t'
        result = independent.check_results([job], prefix + enc(b"first") + "," + enc(b"second"))
        self.assertEqual(["first", "second"], result["schemas"]["a"]["warnings"])
        for invalid in ("%%%", enc(b"first") + ",", "," + enc(b"last")):
            with self.subTest(invalid=invalid), self.assertRaises(RuntimeError):
                independent.check_results([job], prefix + invalid)

    def test_invalid_jobs(self):
        a = scalar("a", "int", {"good": "1"})
        b = deepcopy(a)
        b.name = "b"
        for jobs in ([], [a, a], [a, b], [SchemaJob("bad\nname", "urn:schema", b"xml")],
                     [SchemaJob("a", "urn:schema", "text is not bytes")]):
            with self.subTest(jobs=jobs), self.assertRaises(ValueError):
                independent.run(jobs)

    def test_worker_failure_cancellation_and_cleanup(self):
        jobs = [scalar("a", "int", {"good": "1"})]
        for error in (KeyboardInterrupt(), subprocess.TimeoutExpired("java", 60),
                      subprocess.CalledProcessError(1, "java", "", "failure")):
            temporary = []

            def process(command, **kwargs):
                if command[0] == "javac":
                    temporary.append(Path(command[command.index("-d") + 1]))
                    self.assertTrue(temporary[0].is_dir())
                    return subprocess.CompletedProcess(command, 0, "", "")
                raise error

            with patch.object(independent.subprocess, "run", side_effect=process):
                with self.assertRaises(type(error)):
                    independent.run(jobs)
            self.assertEqual(1, len(temporary))
            self.assertFalse(temporary[0].exists())

    def test_cxf_contracts_and_all_imports_are_pinned(self):
        path = ROOT / "cxf/catalog.json"
        metadata = corpus.read_manifest(path)
        catalog = corpus.Catalog(path)
        self.assertEqual("5b660b5f9d26ae1e606c6291e8beb61ef0d7fcc8", metadata["commit"])
        self.assertEqual(8, len(metadata["contracts"]))
        self.assertEqual(9, len(catalog.resources))
        for item in metadata["resources"]:
            doc = etree.fromstring(catalog.resources[item["uri"]])
            actual = []
            for node in doc.iter():
                if node.tag not in (f"{{{XSD}}}import", f"{{{XSD}}}include",
                                    f"{{{XSD}}}redefine", "{http://schemas.xmlsoap.org/wsdl/}import"):
                    continue
                location = node.get("schemaLocation") or node.get("location")
                if location:
                    uri = urljoin(item["uri"], location)
                    self.assertIn(uri, catalog.resources)
                    actual.append(uri)
                else:
                    # swa-mime declares its location-less imported namespace inline.
                    self.assertIn(node.get("namespace"), [s.get("targetNamespace")
                        for s in doc.iter(f"{{{XSD}}}schema")])
            self.assertEqual(item["imports"], actual)
        for item in metadata["notices"].values():
            self.assertEqual(item["sha256"], hashlib.sha256((path.parent / item["path"]).read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
