#!/usr/bin/env python3
"""Offline corpus integrity, import resolution, and extraction failure regressions.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from lxml import etree

import corpus
import survey


class CorpusTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="wsdl-corpus-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def manifest(self, members=None):
        members = members if members is not None else {"databinding/example.xml": b"<original/>"}
        archive = self.root / "archive.zip"
        with zipfile.ZipFile(archive, "w") as stream:
            for name, data in members.items():
                stream.writestr(name, data)
        value = {"format": 1, "archive": {
            "path": archive.name, "size": archive.stat().st_size,
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest()},
            "files": {name: {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                      for name, data in members.items()}}
        path = self.root / "inventory.json"
        path.write_text(json.dumps(value))
        return path, value

    def catalog(self):
        schema = b'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"/>'
        (self.root / "external.xsd").write_bytes(schema)
        value = {"format": 1, "resources": [{"uri": "https://example.invalid/external.xsd",
                 "path": "external.xsd", "sha256": hashlib.sha256(schema).hexdigest()}]}
        path = self.root / "catalog.json"
        path.write_text(json.dumps(value))
        return path, value

    def test_pinned_archive(self):
        manifest = corpus.verify_archive()
        self.assertEqual(4191, len(manifest["files"]))
        self.assertEqual(36553600, sum(f["size"] for f in manifest["files"].values()))
        self.assertEqual("510b1528e5bdaee527c416524e6462c73f5e82b5237af4a4f7fef65904b90aca",
                         manifest["archive"]["sha256"])

    def test_extraction_integrity_and_no_overwrite(self):
        path, original = self.manifest()
        directory = self.root / "extracted"
        corpus.extract(directory, path)
        self.assertEqual(original, corpus.verify_extraction(directory, path))
        self.assertEqual(b"<original/>", (directory / "databinding/example.xml").read_bytes())
        with self.assertRaises(FileExistsError):
            corpus.extract(directory, path)
        (directory / "databinding/example.xml").write_bytes(b"<modified/>")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            corpus.verify_extraction(directory, path)
        (directory / "databinding/example.xml").unlink()
        with self.assertRaisesRegex(ValueError, "missing corpus file"):
            corpus.verify_extraction(directory, path)

    def test_extraction_failure_and_cancellation_cleanup(self):
        path, _ = self.manifest()
        before = set(self.root.iterdir())
        for error in (OSError("disk full"), KeyboardInterrupt()):
            with patch.object(Path, "write_bytes", side_effect=error):
                with self.assertRaises(type(error)):
                    corpus.extract(self.root / "extracted", path)
            self.assertEqual(before, set(self.root.iterdir()))

    def test_invalid_manifests(self):
        path, original = self.manifest()
        variants = [[], {}, {"format": True}, {"format": 2}, {"format": 1, "files": []}]
        for section, key, value in (("archive", "path", "../archive.zip"),
                                     ("archive", "size", True), ("archive", "size", -1),
                                     ("archive", "sha256", "broken"),
                                     ("archive", "size", corpus.MAX_ARCHIVE_BYTES + 1)):
            variant = deepcopy(original)
            variant[section][key] = value
            variants.append(variant)
        for variant in variants:
            path.write_text(json.dumps(variant))
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                corpus.load_inventory(path)
        path.write_text('{"format":1,"format":1}')
        with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
            corpus.read_manifest(path)
        path.write_text('{"format":')
        with self.assertRaises(json.JSONDecodeError):
            corpus.read_manifest(path)

    def test_invalid_archive(self):
        path, original = self.manifest()
        (self.root / "archive.zip").write_bytes(b"invalid zip")
        with self.assertRaisesRegex(ValueError, "archive size mismatch"):
            corpus.verify_archive(path)
        path, original = self.manifest()
        original["archive"]["sha256"] = "0" * 64
        path.write_text(json.dumps(original))
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            corpus.verify_archive(path)
        path, original = self.manifest()
        original["files"]["absent"] = {"size": 0, "sha256": hashlib.sha256(b"").hexdigest()}
        path.write_text(json.dumps(original))
        with self.assertRaisesRegex(ValueError, "missing archive members"):
            corpus.verify_archive(path)

    def test_archive_member_rejection(self):
        for mode in ("duplicate", "symlink", "unexpected", "wrong-size", "wrong-digest"):
            path, manifest = self.manifest()
            archive = self.root / "archive.zip"
            name = "databinding/example.xml"
            if mode in ("duplicate", "symlink", "unexpected"):
                with zipfile.ZipFile(archive, "a") as stream:
                    if mode == "duplicate":
                        with self.assertWarnsRegex(UserWarning, "Duplicate name"):
                            stream.writestr(name, b"<original/>")
                    elif mode == "symlink":
                        entry = zipfile.ZipInfo("link")
                        entry.external_attr = (stat.S_IFLNK | 0o777) << 16
                        stream.writestr(entry, b"/outside")
                    else:
                        stream.writestr("extra", b"unexpected")
                manifest["archive"]["sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
                manifest["archive"]["size"] = archive.stat().st_size
            elif mode == "wrong-size":
                manifest["files"][name]["size"] += 1
            else:
                manifest["files"][name]["sha256"] = "0" * 64
            path.write_text(json.dumps(manifest))
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                corpus.verify_archive(path)

    def test_resource_limits(self):
        path, _ = self.manifest()
        for constant, maximum in (("MAX_FILES", 0), ("MAX_ARCHIVE_BYTES", 1),
                                   ("MAX_EXPANDED_BYTES", 1)):
            with patch.object(corpus, constant, maximum), self.assertRaises(ValueError):
                corpus.verify_archive(path)
        path, _ = self.catalog()
        for constant, maximum in (("MAX_FILES", 0), ("MAX_ARCHIVE_BYTES", 1),
                                   ("MAX_EXPANDED_BYTES", 1)):
            with patch.object(corpus, constant, maximum), self.assertRaises(ValueError):
                corpus.Catalog(path)

    def test_path_and_symlink_escape(self):
        for name in ("", "/absolute", "../escape", "a/../../b", "a//b", "./a", "a/./b",
                     "a\\b", "C:/b", "a\x00b", None):
            with self.subTest(name=name), self.assertRaises(ValueError):
                corpus.relative_path(name)
        (self.root / "escape").symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "escapes root"):
            corpus.local_path(self.root, "escape/anything")

    def test_catalog_integrity_and_immutability(self):
        path, original = self.catalog()
        catalog = corpus.Catalog(path)
        uri = original["resources"][0]["uri"]
        self.assertEqual((self.root / "external.xsd").read_text(), catalog.qore_cache()[uri])
        with self.assertRaises(TypeError):
            catalog.resources[uri] = b"<replacement/>"
        (self.root / "external.xsd").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            corpus.Catalog(path)

    def test_malformed_catalog(self):
        path, original = self.catalog()
        variants = [{"format": 1}, {"format": 1, "resources": {}},
                    {"format": 1, "resources": [None]},
                    {"format": 1, "resources": original["resources"] * 2}]
        for key, value in (("uri", "file:///etc/passwd"), ("uri", "https:///no-host"),
                           ("uri", "https://example.invalid/a#fragment"), ("path", "../outside"),
                           ("sha256", "0" * 64), ("path", None)):
            variant = deepcopy(original)
            variant["resources"][0][key] = value
            variants.append(variant)
        for variant in variants:
            path.write_text(json.dumps(variant))
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                corpus.Catalog(path)
        path.write_text(json.dumps(original))
        (self.root / "external.xsd").unlink()
        with self.assertRaises(FileNotFoundError):
            corpus.Catalog(path)

    def test_catalog_nested_import_base_uri(self):
        path, value = self.catalog()
        uri = value["resources"][0]["uri"]
        nested = b'''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
          <xs:include schemaLocation="nested.xsd"/></xs:schema>'''
        (self.root / "external.xsd").write_bytes(nested)
        value["resources"][0]["sha256"] = hashlib.sha256(nested).hexdigest()
        leaf = b'''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
          <xs:element name="answer" type="xs:int"/></xs:schema>'''
        (self.root / "nested.xsd").write_bytes(leaf)
        value["resources"].append({"uri": uri.replace("external", "nested"), "path": "nested.xsd",
                                   "sha256": hashlib.sha256(leaf).hexdigest()})
        path.write_text(json.dumps(value))
        xml_parser = survey.parser(self.root, corpus.Catalog(path))
        schema = etree.XMLSchema(etree.parse(uri, xml_parser))
        self.assertTrue(schema.validate(etree.fromstring(b"<answer>42</answer>")))
        self.assertFalse(schema.validate(etree.fromstring(b"<answer>invalid</answer>")))
        with self.assertRaisesRegex(OSError, "external resource unavailable offline"):
            etree.parse("https://example.invalid/unknown.xsd", xml_parser)

    def test_authoritative_catalog_and_empty_source(self):
        catalog = corpus.Catalog()
        self.assertEqual(5, len(catalog.resources))
        empty = survey.SOURCE + "static/Imported.xsd"
        self.assertEqual(b"", catalog.resources[empty])
        for uri in catalog.resources:
            xml_parser = survey.parser(self.root, catalog)
            if uri == empty:
                with self.assertRaisesRegex(etree.XMLSyntaxError, "Document is empty"):
                    etree.parse(uri, xml_parser)
            else:
                self.assertEqual("{http://www.w3.org/2001/XMLSchema}schema",
                                 etree.parse(uri, xml_parser).getroot().tag)

    def test_schema_failure_isolation(self):
        cases = []
        for name, content in (("Missing", '<xs:include schemaLocation="https://absent.invalid/a.xsd"/>'),
                              ("Unrelated", '<xs:element name="a" type="xs:undefinedType"/>')):
            directory = self.root / name
            directory.mkdir()
            (directory / f"echo{name}.xsd").write_text(
                '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">' + content + '</xs:schema>')
            message = directory / "message.xml"
            message.write_text("<unused/>")
            cases.append({"name": name, "messages": [{"file": name + "/message.xml", "path": str(message)}]})
        report = survey.examine(self.root, cases, [])
        self.assertIn("absent.invalid", report["inputs"]["Missing/message.xml"]["desc"])
        self.assertIn("undefinedType", report["inputs"]["Unrelated/message.xml"]["desc"])
        self.assertNotIn("absent.invalid", report["inputs"]["Unrelated/message.xml"]["desc"])

    def test_cli_and_real_qore_catalog(self):
        extracted = self.root / "extracted"
        run = subprocess.run([sys.executable, str(Path(corpus.__file__)), "--extract", str(extracted)],
                             capture_output=True, text=True, check=True, timeout=30)
        self.assertEqual("", run.stderr)
        root = extracted / corpus.EXAMPLES
        report = self.root / "report.json"
        run = subprocess.run([sys.executable, str(Path(survey.__file__)), str(root),
                              "--soap-version", "both", "--catalog", str(corpus.CATALOG),
                              "--output", str(report)], capture_output=True, text=True, check=True, timeout=60)
        self.assertEqual("", run.stderr)
        result = json.loads(report.read_text())
        self.assertEqual(293, result["scope"]["wsdls"])
        self.assertEqual(1136, result["scope"]["messages"])
        self.assertEqual(5, len(result["catalog_sha256"]))
        for row in result["rows"]:
            self.assertNotEqual("WSDL-ASYNC-IMPORT", row.get("err"), row)
        chameleon = [r for r in result["rows"] if r["case"] == "ChameleonInclude"]
        self.assertEqual(2, sum(r["stage"] == "serialize" and r["ok"] for r in chameleon))


if __name__ == "__main__":
    unittest.main()
