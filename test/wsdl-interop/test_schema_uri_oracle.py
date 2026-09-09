#!/usr/bin/env python3
"""Offline oracle URI resource selection with unchanged schema/document bytes.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from urllib.parse import quote
from xml.sax.saxutils import quoteattr

from independent import SchemaJob, run
from test_schema_resources import load, server

XSD = "http://www.w3.org/2001/XMLSchema"
INTEGER = f'<xs:schema xmlns:xs="{XSD}"><xs:element name="value" type="xs:int"/></xs:schema>'.encode()


class SchemaUriOracleTest(unittest.TestCase):
    def assert_results(self, report, names):
        self.assertEqual(set(names), set(report["schemas"]))
        self.assertEqual({name + suffix for name in names for suffix in ("/valid", "/invalid")},
                         set(report["documents"]))
        for name in names:
            with self.subTest(name=name):
                self.assertTrue(report["schemas"][name]["ok"], report["schemas"][name])
                self.assertEqual([], report["schemas"][name]["warnings"])
                self.assertTrue(report["documents"][name + "/valid"]["ok"])
                self.assertEqual([], report["documents"][name + "/valid"]["warnings"])
                self.assertFalse(report["documents"][name + "/invalid"]["ok"])
                self.assertIn("SAXParseException", report["documents"][name + "/invalid"]["desc"])

    @staticmethod
    def job(name, uri, schema):
        return SchemaJob(name, uri, schema, {name + "/valid": b"<value>17</value>",
                                           name + "/invalid": b"<value>bad</value>"})

    def test_exact_resource_identity(self):
        # Explicit expectations come from RFC 3986; urljoin/URI.resolve are not
        # used as an oracle for dot segments, empty segments or query references.
        cases = (("café 中文.xsd", "caf%C3%A9%20%E4%B8%AD%E6%96%87.xsd"),
                 ("caf%C3%A9%20%E4%B8%AD%E6%96%87.xsd", "caf%C3%A9%20%E4%B8%AD%E6%96%87.xsd"),
                 ("  café   中文.xsd  ", "caf%C3%A9%20%E4%B8%AD%E6%96%87.xsd"),
                 ("a%2Fb.xsd", "a%2Fb.xsd"), ("a%3Fb.xsd", "a%3Fb.xsd"),
                 ("a%23b.xsd", "a%23b.xsd"), ("a%25b.xsd", "a%25b.xsd"),
                 ("./a:b~.xsd", "a:b~.xsd"), ("g//h.xsd", "g//h.xsd"),
                 ("g//../h.xsd", "g/h.xsd"), ("?leaf", "main.xsd?leaf"))
        jobs, resources = [], {}
        for base in ("http://schema-uri.invalid/base/", "file:///contracts/café dir/"):
            for index, (location, target) in enumerate(cases):
                name = str(len(jobs))
                schema = f'<xs:schema xmlns:xs="{XSD}"><xs:include schemaLocation={quoteattr(location)}/></xs:schema>'
                jobs.append(self.job(name, base + "main.xsd", schema.encode()))
                resources[quote(base, safe=":/%") + target] = INTEGER
        self.assert_results(run(jobs, resources), [job.name for job in jobs])

    def test_components_and_explicit_xerces_xml_base_defect(self):
        # Xerces XSDHandler.doc2SystemId uses the document URI, ignoring xml:base.
        # Keep its six false negatives visible; the same bytes must pass natively.
        jobs, resources, routes, native = [], {}, {}, {}
        with server(routes) as (base, requests):
            for kind in ("include", "import", "redefine"):
                for xml_base in (False, True):
                    for escaped in (False, True):
                        name = f"{kind}-{xml_base}-{escaped}"
                        location = "café 中文.xsd"
                        if escaped:
                            location = quote(location)
                        namespace = ' targetNamespace="urn:types"' if kind == "import" else ""
                        resource = (f'<xs:schema xmlns:xs="{XSD}"{namespace}><xs:simpleType name="Count">'
                                    '<xs:restriction base="xs:int"/></xs:simpleType></xs:schema>').encode()
                        root = base + "/" + name + "/"
                        schema_base = ' xml:base="café dir/"' if xml_base else ""
                        relation_namespace = ' namespace="urn:types"' if kind == "import" else ""
                        redefine = ('<xs:simpleType name="Count"><xs:restriction base="Count">'
                                    '<xs:minInclusive value="10"/></xs:restriction></xs:simpleType>') if kind == "redefine" else ""
                        typename = "t:Count" if kind == "import" else "Count"
                        schema = (f'<xs:schema xmlns:xs="{XSD}" xmlns:t="urn:types"{schema_base}>'
                                  f'<xs:{kind} schemaLocation="{location}"{relation_namespace}>{redefine}</xs:{kind}>'
                                  f'<xs:element name="value" type="{typename}"/></xs:schema>').encode()
                        resource_uri = root + ("caf%C3%A9%20dir/" if xml_base else "") + "caf%C3%A9%20%E4%B8%AD%E6%96%87.xsd"
                        resources[resource_uri] = resource
                        routes[resource_uri[len(base):]] = (200, {}, resource)
                        routes["/" + name + "/main.xsd"] = (200, {}, schema)
                        jobs.append(self.job(name, root + "main.xsd", schema))
            for job in jobs:
                native[job.name] = load(job.uri)
                self.assertEqual({"value": {"value": "17"}}, native[job.name])
                self.assertEqual("PARSE-XML-EXCEPTION", load(job.uri, xml="<value>bad</value>")["error"])
            report = run(jobs, resources)
            self.assertEqual(12, len(report["schemas"]))
            self.assertEqual(24, len(report["documents"]))
            defects = []
            for job in jobs:
                if "-True-" in job.name:
                    verdict = report["schemas"][job.name]
                    self.assertFalse(verdict["ok"])
                    self.assertEqual([], verdict["warnings"])
                    wrong_uri = base + "/" + job.name + "/caf%C3%A9%20%E4%B8%AD%E6%96%87.xsd"
                    self.assertEqual("java.lang.IllegalArgumentException: resource unavailable offline: " + wrong_uri,
                                     verdict["desc"])
                    for suffix in ("/valid", "/invalid"):
                        self.assertIsNone(report["documents"][job.name + suffix]["ok"])
                    defects.append(job.name)
                else:
                    selected = {"schemas": {job.name: report["schemas"][job.name]},
                                "documents": {name: report["documents"][name] for name in job.documents}}
                    self.assert_results(selected, [job.name])
            self.assertEqual([f"{kind}-True-{escaped}" for kind in ("include", "import", "redefine")
                              for escaped in (False, True)], defects)
            artifacts = Path(tempfile.mkdtemp(prefix="xml-schema-uri-oracle-"))
            evidence = {"xerces": report, "native": native, "validator_defects": defects,
                        "schemas": [{"name": job.name, "uri": job.uri, "schema": job.schema.decode(),
                                     "sha256": hashlib.sha256(job.schema).hexdigest(), "expected_valid": True}
                                    for job in jobs]}
            (artifacts / "results.json").write_text(json.dumps(evidence, indent=2) + "\n")
            print(f"Schema URI oracle artifacts: {artifacts}", flush=True)

    def test_file_uri_aliases_and_percent_hex_case(self):
        jobs, resources = [], {}
        for index, (source, registered) in enumerate((("file:///contracts/a%2Fb.xsd", "file:/contracts/a%2fb.xsd"),
                                                    ("file:/contracts/a%2fb.xsd", "file:///contracts/a%2Fb.xsd"))):
            name = str(index)
            schema = f'<xs:schema xmlns:xs="{XSD}"><xs:include schemaLocation="{source}"/></xs:schema>'.encode()
            jobs.append(self.job(name, "urn:alias:" + name, schema))
            resources[registered] = INTEGER
        # Each alias is a separate manifest: registering both is intentionally
        # rejected as a duplicate, even if the resource bytes are identical.
        for job, item in zip(jobs, resources.items(), strict=True):
            self.assert_results(run([job], dict([item])), [job.name])

    def test_alias_duplicates_are_rejected(self):
        job = self.job("duplicate", "urn:duplicate", INTEGER)
        for content in (INTEGER, b"different"):
            with self.subTest(content=content):
                with self.assertRaises(subprocess.CalledProcessError) as caught:
                    run([job], {"file:///contracts/leaf.xsd": INTEGER, "file:/contracts/leaf.xsd": content})
                self.assertIn("duplicate resource", caught.exception.stderr)

    def test_unknown_and_malformed_locations_cannot_load_resources(self):
        jobs = []
        for index, location in enumerate(("missing.xsd", "bad%", "bad%2", "bad%GG")):
            schema = f'<xs:schema xmlns:xs="{XSD}"><xs:include schemaLocation="{location}"/></xs:schema>'.encode()
            jobs.append(self.job(str(index), "http://schema-uri.invalid/main.xsd", schema))
        report = run(jobs)
        for job in jobs:
            with self.subTest(name=job.name):
                self.assertFalse(report["schemas"][job.name]["ok"])
                self.assertIsNone(report["documents"][job.name + "/valid"]["ok"])
        self.assertIn("resource unavailable offline", report["schemas"]["0"]["desc"])


if __name__ == "__main__":
    unittest.main()
