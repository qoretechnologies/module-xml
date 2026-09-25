"""Observe imported component edges with pinned WSDL4J, independently of Qore.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
import jvm

ROOT = Path(__file__).resolve().parent
ORACLE = ROOT / "oracle"
FIXTURES = ROOT / "regressions" / "wsdl-imports"


class WsdlImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = json.loads((ORACLE / "wsdl4j-manifest.json").read_text())
        if manifest["implementation"] != "WSDL4J" or manifest["version"] != "1.6.3":
            raise ValueError("unexpected WSDL oracle manifest")
        for artifact in manifest["artifacts"]:
            source = (ORACLE / artifact["path"]).read_bytes()
            if len(source) != artifact["size"] or hashlib.sha256(source).hexdigest() != artifact["sha256"]:
                raise ValueError("modified pinned WSDL4J artifact: " + artifact["path"])
        cls.directory = tempfile.TemporaryDirectory(prefix="wsdl-import-oracle-")
        cls.addClassCleanup(cls.directory.cleanup)
        cls.classes = Path(cls.directory.name) / "classes"
        cls.classes.mkdir()
        cls.jar = ORACLE / "wsdl4j-1.6.3.jar"
        command = ["javac", "-Xlint:all", "-Werror", "-cp", str(cls.jar), "-d", str(cls.classes),
                   str(ORACLE / "WsdlImportOracle.java")]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60, check=True, env=jvm.environment())
        if result.stdout or result.stderr:
            raise RuntimeError("unexpected oracle compiler diagnostics")

    def run_oracle(self, source, valid=True):
        command = ["java", "-cp", str(self.classes) + os.pathsep + str(self.jar), "WsdlImportOracle", str(source)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=30, env=jvm.environment())
        if not valid:
            self.assertNotEqual(0, result.returncode)
            self.assertTrue(result.stderr.strip())
            self.assertEqual("", result.stdout)
            return result.stderr
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        lines = result.stdout.splitlines()
        self.assertGreater(len(lines), 1)
        heading = lines.pop(0).split("\t")
        self.assertEqual("documents", heading[0])
        self.assertEqual(2, len(heading))
        self.assertEqual(lines, sorted(set(lines)))
        return int(heading[1]), set(lines)

    def test_cross_file_cycle_and_diamond(self):
        count, observations = self.run_oracle(FIXTURES / "root.wsdl")
        self.assertEqual(5, count)
        self.assertEqual({
            "binding\t{urn:bindings}B\t{urn:ports}P",
            "body\t{urn:bindings}B/send/input\turn:wire",
            "body\t{urn:bindings}B/send/output\turn:wire",
            "message\t{urn:headers}H", "message\t{urn:messages}M",
            "part\t{urn:headers}H/token\telement:{urn:headers}token",
            "part\t{urn:messages}M/value\ttype:{http://www.w3.org/2001/XMLSchema}string",
            "operation\t{urn:ports}P/send\t{urn:messages}M\t{urn:messages}M",
            "port\t{urn:root}S/Endpoint\t{urn:bindings}B",
            "protocol\t{urn:bindings}B\thttp://schemas.xmlsoap.org/wsdl/soap/",
        }, observations)

    def test_colliding_names_keep_namespace_identity(self):
        count, observations = self.run_oracle(FIXTURES / "collisions" / "root.wsdl")
        self.assertEqual(3, count)
        expected = set()
        for suffix, scalar, protocol in (("a", "string", "soap"), ("b", "int", "soap12")):
            namespace = "{urn:" + suffix + "}"
            expected.update({
                f"binding\t{namespace}B\t{namespace}P",
                f"message\t{namespace}M",
                f"operation\t{namespace}P/send\t{namespace}M\t{namespace}M",
                f"port\t{namespace}S/Endpoint\t{namespace}B",
                f"part\t{namespace}M/value\ttype:{{http://www.w3.org/2001/XMLSchema}}{scalar}",
                f"protocol\t{namespace}B\thttp://schemas.xmlsoap.org/wsdl/{protocol}/",
                f"body\t{namespace}B/send/input\turn:{suffix}",
                f"body\t{namespace}B/send/output\turn:{suffix}",
            })
        self.assertEqual(expected, observations)

    def copied_graph(self):
        directory = tempfile.TemporaryDirectory(prefix="wsdl-import-negative-")
        self.addCleanup(directory.cleanup)
        target = Path(directory.name)
        for source in FIXTURES.glob("*.wsdl"):
            shutil.copyfile(source, target / source.name)
        return target

    def test_mismatched_import_leaves_binding_unresolved(self):
        directory = self.copied_graph()
        source = directory / "root.wsdl"
        source.write_text(source.read_text().replace('namespace="urn:bindings"', 'namespace="urn:other"'))
        error = self.run_oracle(source, valid=False)
        self.assertIn("undefined binding {urn:bindings}B", error)

    def test_wrong_reference_namespace_cannot_borrow_local_name(self):
        directory = self.copied_graph()
        source = directory / "binding.wsdl"
        source.write_text(source.read_text().replace('xmlns:p="urn:ports"', 'xmlns:p="urn:missing"'))
        error = self.run_oracle(directory / "root.wsdl", valid=False)
        self.assertIn("undefined", error)

    def test_missing_resource_rejects(self):
        directory = self.copied_graph()
        source = directory / "root.wsdl"
        source.write_text(source.read_text().replace('location="binding.wsdl"', 'location="missing.wsdl"'))
        error = self.run_oracle(source, valid=False)
        self.assertIn("missing fixture resource", error)


if __name__ == "__main__":
    unittest.main()
