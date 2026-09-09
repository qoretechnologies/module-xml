#!/usr/bin/env python3
"""XSD anyURI resource identity, escaping and XML Base resolution.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from pathlib import Path
import json
import tempfile
import unittest
from urllib.parse import quote
from xml.sax.saxutils import quoteattr

from test_schema_resources import INTEGER, load, run_fixture, server

XSD = "http://www.w3.org/2001/XMLSchema"


def including(location):
    return f'<xs:schema xmlns:xs="{XSD}"><xs:include schemaLocation={quoteattr(location)}/></xs:schema>'


class SchemaUriTest(unittest.TestCase):
    def test_original_recorded_schema_uri_finding(self):
        finding = json.loads((Path(__file__).parent / "schema-uri-findings.json").read_text())
        with tempfile.TemporaryDirectory(prefix="schema-uri-original-") as directory:
            root = Path(directory)
            (root / finding["resource_name"]).write_text(finding["resource"])
            for case in finding["cases"]:
                with self.subTest(form=case["form"]):
                    main = root / (case["form"] + ".xsd")
                    main.write_text(case["schema"])
                    self.assertEqual({"value": {"value": "17"}}, load(str(main), xml=finding["document"]))

    def test_direct_raw_and_encoded_schema_locations(self):
        target = "/caf%C3%A9%20%E4%B8%AD%E6%96%87%2525.xsd"
        with server({target: (200, {}, INTEGER)}) as (base, requests):
            fixtures = [{"schema": base + location, "xml": "<value>17</value>"}
                        for location in ("/café 中文%2525.xsd", target)]
            results = run_fixture(fixtures)
            self.assertEqual([{"value": {"value": "17"}}] * 2, results)
            self.assertEqual([target] * 2, requests)

    def test_optional_missing_import_keeps_application_output_intact(self):
        with tempfile.TemporaryDirectory(prefix="schema-uri-missing-") as directory:
            missing = (Path(directory) / "missing.xsd").as_uri()
            schemas = []
            for required in (False, True):
                typename = "t:Count" if required else "xs:int"
                schemas.append(f'<xs:schema xmlns:xs="{XSD}" xmlns:t="urn:missing">'
                               f'<xs:import namespace="urn:missing" schemaLocation="{missing}"/>'
                               f'<xs:element name="value" type="{typename}"/></xs:schema>')
            schemas.append(INTEGER.decode())
            results = run_fixture([{"schema": schema, "xml": "<value>17</value>", "text": True}
                                   for schema in schemas])
            self.assertEqual({"value": {"value": "17"}}, results[0])
            self.assertEqual("XSD-SYNTAX-ERROR", results[1]["error"])
            self.assertEqual({"value": {"value": "17"}}, results[2])

    def test_uri_escape_preserves_the_requested_http_resource(self):
        targets = {
            "a%2Fb.xsd": "/base/a%2Fb.xsd", "a%3Fb.xsd": "/base/a%3Fb.xsd",
            "a%23b.xsd": "/base/a%23b.xsd", "a%25b.xsd": "/base/a%25b.xsd",
            "caf%C3%A9%20%E4%B8%AD%E6%96%87.xsd": "/base/caf%C3%A9%20%E4%B8%AD%E6%96%87.xsd",
            "café 中文.xsd": "/base/caf%C3%A9%20%E4%B8%AD%E6%96%87.xsd",
            "a~b.xsd": "/base/a~b.xsd", "./a:b.xsd": "/base/a:b.xsd",
            "a@b.xsd": "/base/a@b.xsd", "a;b.xsd": "/base/a;b.xsd",
            "a!$'()+,b.xsd": "/base/a!$'()+,b.xsd",
            "query.xsd?a=b%2Fc&d=e": "/base/query.xsd?a=b%2Fc&d=e",
            "a//b.xsd": "/base/a//b.xsd", "a//../b.xsd": "/base/a/b.xsd",
        }
        routes = {target: (200, {}, INTEGER) for target in targets.values()}
        with server(routes) as (base, requests):
            fixtures, expected_requests = [], []
            for index, (name, target) in enumerate(targets.items()):
                main = f"/base/main-{index}.xsd"
                routes[main] = (200, {}, including(name).encode())
                for text in ("17", "bad"):
                    fixtures.append({"schema": base + main, "xml": f"<value>{text}</value>"})
                    expected_requests.extend((main, target))
            results = run_fixture(fixtures)
            self.assertEqual(2 * len(targets), len(results))
            for index, name in enumerate(targets):
                with self.subTest(reference=name):
                    self.assertEqual({"value": {"value": "17"}}, results[2 * index])
                    self.assertEqual("PARSE-XML-EXCEPTION", results[2 * index + 1]["error"])
            self.assertEqual(expected_requests, requests)

    def test_text_schema_uri_references_have_no_document_base(self):
        with tempfile.TemporaryDirectory(prefix="schema-uri-text-") as directory:
            path = Path(directory) / "café 中文 %.xsd"
            path.write_bytes(INTEGER)
            # A literal filename percent must be represented as %25 in both URI forms.
            for location in (str(path).replace("%", "%25"), quote(str(path)), path.as_uri()):
                with self.subTest(location=location):
                    self.assertEqual({"value": {"value": "17"}}, load(including(location), text=True))

    def test_include_import_redefine_and_xml_base(self):
        with tempfile.TemporaryDirectory(prefix="schema-uri-components-") as directory:
            root = Path(directory)
            for name in ("plain", "café 中文 dir", "percent%dir"):
                folder = root / name
                folder.mkdir()
                resource_name = "café 中文 %25 file.xsd"
                for spelling in ("raw", "escaped"):
                    location = resource_name.replace("%", "%25") if spelling == "raw" else quote(resource_name)
                    for use_base in (False, True):
                        for kind in ("include", "import", "redefine"):
                            with self.subTest(directory=name, spelling=spelling, xml_base=use_base, kind=kind):
                                namespace = ' targetNamespace="urn:uri-types"' if kind == "import" else ""
                                resource = (f'<xs:schema xmlns:xs="{XSD}"{namespace}>'
                                            '<xs:simpleType name="Count"><xs:restriction base="xs:int"/>'
                                            '</xs:simpleType></xs:schema>')
                                (folder / resource_name).write_text(resource)
                                if kind == "redefine":
                                    relation = (f'<xs:redefine schemaLocation="{location}">'
                                                '<xs:simpleType name="Count"><xs:restriction base="Count">'
                                                '<xs:minInclusive value="10"/></xs:restriction>'
                                                '</xs:simpleType></xs:redefine>')
                                else:
                                    attribute = ' namespace="urn:uri-types"' if kind == "import" else ""
                                    relation = f'<xs:{kind} schemaLocation="{location}"{attribute}/>'
                                base = name.replace("%", "%25") if spelling == "raw" else quote(name)
                                base_attribute = f' xml:base="{base}/"' if use_base else ""
                                typename = "t:Count" if kind == "import" else "Count"
                                schema = (f'<xs:schema xmlns:xs="{XSD}" xmlns:t="urn:uri-types"{base_attribute}>'
                                          f'{relation}<xs:element name="value" type="{typename}"/></xs:schema>')
                                main = (root if use_base else folder) / "main.xsd"
                                main.write_text(schema)
                                self.assertEqual({"value": {"value": "17"}}, load(str(main)))
                                self.assertEqual("PARSE-XML-EXCEPTION", load(str(main), xml="<value>bad</value>")["error"])


if __name__ == "__main__":
    unittest.main()
