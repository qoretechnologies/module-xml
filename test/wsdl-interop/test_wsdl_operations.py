#!/usr/bin/env python3
"""Check operation defaults and overload selection with pinned WSDL4J.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from independent import SchemaJob, run
import jvm

ROOT = Path(__file__).resolve().parent
ORACLE = ROOT / "oracle"
FIXTURES = ROOT / "regressions" / "wsdl-operations"


class WsdlOperationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = json.loads((ORACLE / "wsdl4j-manifest.json").read_text())
        if manifest["implementation"] != "WSDL4J" or manifest["version"] != "1.6.3":
            raise ValueError("unexpected WSDL oracle manifest")
        for artifact in manifest["artifacts"]:
            data = (ORACLE / artifact["path"]).read_bytes()
            if len(data) != artifact["size"] or hashlib.sha256(data).hexdigest() != artifact["sha256"]:
                raise ValueError("modified WSDL4J artifact: " + artifact["path"])
        cls.directory = tempfile.TemporaryDirectory(prefix="wsdl-operation-oracle-")
        cls.addClassCleanup(cls.directory.cleanup)
        cls.classes = Path(cls.directory.name) / "classes"
        cls.classes.mkdir()
        cls.jar = ORACLE / "wsdl4j-1.6.3.jar"
        result = subprocess.run(
            ["javac", "-Xlint:all", "-Werror", "-cp", str(cls.jar), "-d", str(cls.classes),
             str(ORACLE / "WsdlOperationOracle.java")],
            capture_output=True, text=True, timeout=60, check=True, env=jvm.environment())
        if result.stdout or result.stderr:
            raise RuntimeError("unexpected oracle compiler diagnostics")

    def oracle(self, path, valid=True):
        result = subprocess.run(
            ["java", "-cp", str(self.classes) + os.pathsep + str(self.jar), "WsdlOperationOracle", str(path)],
            capture_output=True, text=True, timeout=30, env=jvm.environment())
        if not valid:
            self.assertNotEqual(0, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertTrue(result.stderr.strip())
            return result.stderr
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(sorted(set(lines)), lines)
        return set(lines)

    def test_default_names_and_message_order(self):
        self.assertEqual({
            "operation\t{urn:ops}P\toneway\tONE_WAY,0\toneway\t-",
            "operation\t{urn:ops}P\tnotification\tNOTIFICATION,3\t-\tnotification",
            "operation\t{urn:ops}P\trequest-response\tREQUEST_RESPONSE,1\trequest-responseRequest\trequest-responseResponse",
            "operation\t{urn:ops}P\tsolicit-response\tSOLICIT_RESPONSE,2\tsolicit-responseSolicit\tsolicit-responseResponse",
        }, self.oracle(FIXTURES / "defaults.wsdl"))

    def test_input_output_and_combined_selectors(self):
        declarations = {
            "operation\t{urn:ops}P\tlookup\tREQUEST_RESPONSE,1\tById\tResultId",
            "operation\t{urn:ops}P\tlookup\tREQUEST_RESPONSE,1\tByName\tResultName",
        }
        for fixture, suffix in (("input-only", "Id"), ("output-only", "Name"), ("both", "Name")):
            with self.subTest(fixture=fixture):
                self.assertEqual(declarations | {f"binding\t{{urn:ops}}B\tlookup\tBy{suffix}\tResult{suffix}"},
                                 self.oracle(FIXTURES / f"rr-{fixture}.wsdl"))

    def test_unknown_and_mismatched_selectors_are_not_definitions(self):
        for fixture in ("unknown", "mismatched"):
            with self.subTest(fixture=fixture):
                self.assertIn("undefined", self.oracle(FIXTURES / f"rr-{fixture}.wsdl", valid=False))

    def test_ambiguous_binding_rejects(self):
        self.assertIn("Duplicate operation", self.oracle(FIXTURES / "overload-unnamed.wsdl", valid=False))

    def test_duplicate_signatures_reject(self):
        path = Path(self.directory.name) / "duplicate.wsdl"
        source = (FIXTURES / "rr-input-only.wsdl").read_text()
        path.write_text(source.replace("ByName", "ById").replace("ResultName", "ResultId"))
        self.assertIn("Duplicate operation", self.oracle(path, valid=False))

    def test_imported_overloads_select_within_their_port_namespace(self):
        self.assertEqual({
            "operation\t{urn:ops}P\tlookup\tREQUEST_RESPONSE,1\tById\tResultId",
            "operation\t{urn:ops}P\tlookup\tREQUEST_RESPONSE,1\tByName\tResultName",
            "binding\t{urn:ops}B\tlookup\tById\tResultId",
            "binding\t{urn:root}Imported\tlookup\tByName\tResultName",
        }, self.oracle(FIXTURES / "import.wsdl"))

    def test_abstract_message_presence_against_pinned_wsdl_schema(self):
        root = ROOT / "regressions" / "wsdl-declarations"
        manifest = json.loads((root / "oracle-cases.json").read_text())
        schema = (root / manifest["schema_file"]).read_bytes()
        self.assertEqual(manifest["schema_sha256"], hashlib.sha256(schema).hexdigest())
        documents = {"four-patterns": (FIXTURES / "defaults.wsdl").read_bytes(),
                     "empty-message": (FIXTURES / "rr-input-only.wsdl").read_bytes(),
                     "no-message": b'<w:definitions xmlns:w="http://schemas.xmlsoap.org/wsdl/">'
                         b'<w:portType name="P"><w:operation name="empty"/></w:portType></w:definitions>'}
        report = run([SchemaJob("wsdl-1.1", manifest["schema_url"], schema, documents)])
        self.assertTrue(report["schemas"]["wsdl-1.1"]["ok"], report)
        self.assertEqual([], report["schemas"]["wsdl-1.1"]["warnings"])
        for name in documents:
            with self.subTest(name=name):
                result = report["documents"][name]
                self.assertEqual(name != "no-message", result["ok"], result)
                self.assertEqual([], result["warnings"])


if __name__ == "__main__":
    unittest.main()
