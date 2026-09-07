#!/usr/bin/env python3
"""Offline independent checks for XSD include/import construction.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

import json
from pathlib import Path
import tempfile
import unittest

from lxml import etree

import corpus
import survey
from independent import SchemaJob, run as run_independent


ROOT = Path(__file__).resolve().parent
BASE = "https://example.invalid/schema/"
XSD = "http://www.w3.org/2001/XMLSchema"


def schema(body, namespace=None):
    attributes = f' targetNamespace="{namespace}" xmlns:t="{namespace}"' if namespace else ""
    return f'<xs:schema xmlns:xs="{XSD}"{attributes}>{body}</xs:schema>'.encode()


class MemoryResolver(etree.Resolver):
    def __init__(self, resources, requests):
        self.resources = resources
        self.requests = requests

    def resolve(self, url, public_id, context):
        if url not in self.resources:
            raise OSError(f"unlisted schema dependency: {url}")
        self.requests.append(url)
        return self.resolve_string(self.resources[url], context, base_url=url)


def compile_schema(source, uri, resources, requests=None):
    parser = etree.XMLParser(no_network=True, resolve_entities=False)
    parser.resolvers.add(MemoryResolver(resources, requests if requests is not None else []))
    return etree.XMLSchema(etree.fromstring(source, parser, base_url=uri))


class CompositionTest(unittest.TestCase):
    def test_group_reference_context_and_cycles(self):
        declarations = {
            "element-group": ('<xs:group name="Fields" xmlns:k="http://www.w3.org/2001/XMLSchema">'
                              '<xs:sequence><xs:element name="value" type="k:int"/></xs:sequence></xs:group>'
                              '<xs:complexType name="Record"><xs:group xmlns:k="urn:types" ref="k:Fields"/>'
                              '</xs:complexType>', True),
            "attribute-group": ('<xs:attributeGroup name="Fields" xmlns:k="http://www.w3.org/2001/XMLSchema">'
                                '<xs:attribute name="flag" type="k:boolean"/></xs:attributeGroup>'
                                '<xs:complexType name="Record"><xs:attributeGroup xmlns:k="urn:types" ref="k:Fields"/>'
                                '</xs:complexType>', True),
            "cyclic-element-group": ('<xs:group name="A"><xs:sequence><xs:group ref="t:A"/>'
                                     '</xs:sequence></xs:group>', False),
            "cyclic-attribute-group": ('<xs:attributeGroup name="A"><xs:attributeGroup ref="t:A"/>'
                                       '</xs:attributeGroup>', False),
            "absent-element-group": ('<xs:complexType name="Record"><xs:group ref="t:Missing"/>'
                                     '</xs:complexType>', False),
            "absent-attribute-group": ('<xs:complexType name="Record"><xs:attributeGroup ref="t:Missing"/>'
                                       '</xs:complexType>', False),
            "duplicate-attribute-group": ('<xs:attributeGroup name="Fields"><xs:attribute name="flag"/>'
                                          '<xs:attribute name="flag"/></xs:attributeGroup>', False),
            "prohibited-duplicates": ('<xs:attributeGroup name="Fields"><xs:attribute name="flag" use="prohibited"/>'
                                      '<xs:attribute name="flag" use="prohibited"/></xs:attributeGroup>', True),
            "prohibited-and-active": ('<xs:complexType name="Record"><xs:attribute name="flag" use="prohibited"/>'
                                      '<xs:attribute name="flag" type="xs:boolean"/></xs:complexType>', True),
            "prohibit-required-base": ('<xs:complexType name="Base"><xs:attribute name="flag" use="required"/>'
                                       '</xs:complexType><xs:complexType name="Record"><xs:complexContent>'
                                       '<xs:restriction base="t:Base"><xs:attribute name="flag" use="prohibited"/>'
                                       '</xs:restriction></xs:complexContent></xs:complexType>', False),
        }
        jobs, cases = [], []
        with tempfile.TemporaryDirectory(prefix="wsdl-group-dependencies-") as temporary:
            for name, (declaration, valid) in declarations.items():
                source = schema(declaration, "urn:types")
                path = Path(temporary) / (name + ".xsd")
                path.write_bytes(source)
                uri = BASE + path.name
                jobs.append(SchemaJob(name, uri, source))
                cases.append({"name": name, "wsdl": str(path), "base": BASE, "schema_only": True, "messages": []})
                if valid:
                    compile_schema(source, uri, {})
                else:
                    with self.subTest(name=name), self.assertRaises(etree.XMLSchemaParseError):
                        compile_schema(source, uri, {})
            rows = survey.run_worker(cases, {})
        self.assertEqual(len(declarations), len(rows))
        for row in rows:
            self.assertEqual(declarations[row["case"]][1], row["ok"], row)
            if not row["ok"]:
                self.assertEqual("WSDL-ERROR", row["err"])
        oracle = run_independent(jobs, {})
        for name, (_, valid) in declarations.items():
            self.assertEqual(valid, oracle["schemas"][name]["ok"], (name, oracle["schemas"][name]))

    def test_simple_dependency_graphs(self):
        declarations = {
            "forward-union": ('<xs:simpleType name="A"><xs:union memberTypes="t:B&#x9;xs:int"/></xs:simpleType>'
                              '<xs:simpleType name="B"><xs:restriction base="xs:string"/></xs:simpleType>', True),
            "inline-restriction": ('<xs:simpleType name="A"><xs:restriction><xs:simpleType>'
                                   '<xs:restriction base="xs:int"/></xs:simpleType></xs:restriction></xs:simpleType>',
                                   True),
            "restriction-cycle": ('<xs:simpleType name="A"><xs:restriction base="t:A"/></xs:simpleType>', False),
            "union-cycle": ('<xs:simpleType name="A"><xs:union memberTypes="xs:string t:A"/></xs:simpleType>', False),
            "list-cycle": ('<xs:simpleType name="A"><xs:list itemType="t:A"/></xs:simpleType>', False),
            "complex-base": ('<xs:complexType name="B"/><xs:simpleType name="A">'
                             '<xs:restriction base="t:B"/></xs:simpleType>', False),
            "list-list": ('<xs:simpleType name="A"><xs:list itemType="xs:IDREFS"/></xs:simpleType>', False),
            "list-unspecified-variety": ('<xs:simpleType name="A"><xs:list itemType="xs:anySimpleType"/>'
                                         '</xs:simpleType>', False),
        }
        jobs, cases = [], []
        with tempfile.TemporaryDirectory(prefix="wsdl-simple-dependencies-") as temporary:
            for name, (declaration, valid) in declarations.items():
                source = schema(declaration, "urn:types")
                path = Path(temporary) / (name + ".xsd")
                path.write_bytes(source)
                uri = BASE + path.name
                jobs.append(SchemaJob(name, uri, source))
                cases.append({"name": name, "wsdl": str(path), "base": BASE, "schema_only": True, "messages": []})
                if valid:
                    compile_schema(source, uri, {})
                else:
                    with self.subTest(name=name), self.assertRaises(etree.XMLSchemaParseError):
                        compile_schema(source, uri, {})
            rows = survey.run_worker(cases, {})
        self.assertEqual(len(declarations), len(rows))
        for row in rows:
            self.assertEqual(declarations[row["case"]][1], row["ok"], row)
            if not row["ok"]:
                self.assertEqual("WSDL-ERROR", row["err"])
        oracle = run_independent(jobs, {})
        for name, (_, valid) in declarations.items():
            if name == "list-unspecified-variety" and oracle["schemas"][name]["ok"]:
                # Pinned Xerces accepts xs:anySimpleType as a list item despite its absent variety.
                # libxml2 and Qore reject above; see the composition oracle adjudication.
                self.assertFalse(valid)
                continue
            self.assertEqual(valid, oracle["schemas"][name]["ok"], (name, oracle["schemas"][name]))

    def test_chameleon_cycles_and_namespace_rejections(self):
        common = schema('<xs:simpleType name="Local"><xs:restriction base="xs:int"/></xs:simpleType>'
                        '<xs:element name="value" type="Local"/>')
        a = schema('<xs:import namespace="urn:b" schemaLocation="b.xsd"/>'
                   '<xs:simpleType name="Shared"><xs:restriction base="xs:int"/></xs:simpleType>'
                   '<xs:element xmlns:b="urn:b" name="value" type="b:Other"/>', "urn:a")
        b = schema('<xs:import namespace="urn:a" schemaLocation="a.xsd"/>'
                   '<xs:simpleType name="Other"><xs:restriction xmlns:a="urn:a" base="a:Shared"/>'
                   '</xs:simpleType>', "urn:b")
        resources = {BASE + "common.xsd": common, BASE + "a.xsd": a, BASE + "b.xsd": b}
        examples = {
            "chameleon-a": (schema('<xs:include schemaLocation="common.xsd"/>', "urn:a"), True,
                            b'<value xmlns="urn:a">42</value>'),
            "chameleon-b": (schema('<xs:include schemaLocation="common.xsd"/>', "urn:b"), True,
                            b'<value xmlns="urn:b">42</value>'),
            "cycle": (a, True, b'<value xmlns="urn:a">42</value>'),
            "no-namespace-import": (schema('<xs:import schemaLocation="common.xsd"/>', "urn:a"), True,
                                    b'<value>42</value>'),
            "include-mismatch": (schema('<xs:include schemaLocation="a.xsd"/>', "urn:wrong"), False, None),
            "import-mismatch": (schema('<xs:import namespace="urn:wrong" schemaLocation="a.xsd"/>', "urn:c"),
                                False, None),
            "import-chameleon": (schema('<xs:import namespace="urn:wrong" schemaLocation="common.xsd"/>',
                                        "urn:c"), False, None),
            "self-import": (schema('<xs:import namespace="urn:a"/>', "urn:a"), False, None),
        }
        jobs, cases = [], []
        with tempfile.TemporaryDirectory(prefix="wsdl-composition-test-") as temporary:
            for name, (source, valid, payload) in examples.items():
                path = Path(temporary) / (name + ".xsd")
                path.write_bytes(source)
                uri = BASE + ("a.xsd" if name == "cycle" else path.name)
                documents = {name + "/valid": payload, name + "/invalid": payload.replace(b"42", b"invalid")} \
                    if payload else {}
                jobs.append(SchemaJob(name, uri, source, documents))
                cases.append({"name": name, "wsdl": str(path), "base": BASE, "schema_only": True,
                              "messages": []})
                with self.subTest(name=name):
                    if valid:
                        compiled = compile_schema(source, uri, resources)
                        self.assertTrue(compiled.validate(etree.fromstring(payload)), str(compiled.error_log))
                        self.assertFalse(compiled.validate(etree.fromstring(documents[name + "/invalid"])))
                    else:
                        requests = []
                        try:
                            compile_schema(source, uri, resources, requests)
                        except etree.XMLSchemaParseError:
                            pass
                        else:
                            # libxml2 2.12.10 accepts these unused mismatched imports after fetching them.
                            # src-import.3.1 and Xerces adjudicate both as invalid; Qore must reject below.
                            # See regressions/schema-composition/validator-notes.md.
                            self.assertIn(name, ("import-mismatch", "import-chameleon"))
                            self.assertIn(BASE + ("a.xsd" if name == "import-mismatch" else "common.xsd"), requests)
            rows = survey.run_worker(cases, {key: value.decode() for key, value in resources.items()})
        self.assertEqual(len(examples), len(rows))
        for row in rows:
            self.assertEqual(examples[row["case"]][1], row["ok"], row)
            if not row["ok"]:
                self.assertEqual("WSDL-ERROR", row["err"])
        oracle = run_independent(jobs, resources)
        for name, (_, valid, payload) in examples.items():
            self.assertEqual(valid, oracle["schemas"][name]["ok"], oracle["schemas"][name])
            if payload:
                self.assertTrue(oracle["documents"][name + "/valid"]["ok"])
                self.assertFalse(oracle["documents"][name + "/invalid"]["ok"])

    def test_issue4449_derivative_provenance_and_schema_validity(self):
        directory = ROOT / "derivatives/Issue4449"
        manifest = json.loads((directory / "manifest.json").read_text())
        resources = {}
        for entry in manifest["files"]:
            source = (directory / entry["source"]).read_bytes()
            derived = (directory / entry["file"]).read_bytes()
            corpus.check_digest(source, entry["source_sha256"], entry["source"])
            corpus.check_digest(derived, entry["sha256"], entry["file"])
            for change in entry["changes"]:
                self.assertEqual(1, source.count(change["old"].encode()))
                source = source.replace(change["old"].encode(), change["new"].encode())
            self.assertEqual(source, derived)
            resources[BASE + entry["file"]] = derived
        jobs = []
        payload = b'<test1 xmlns="http://qore.org/issue-4449"><arg1>x</arg1><arg2>y</arg2></test1>'
        for index in (1, 2):
            name = f"issue-4449-schema-{index}.xsd"
            uri = BASE + name
            compiled = compile_schema(resources[uri], uri, resources)
            self.assertTrue(compiled.validate(etree.fromstring(payload)), str(compiled.error_log))
            original = (ROOT.parent / name).read_bytes()
            with self.assertRaises(etree.XMLSchemaParseError):
                compile_schema(original, uri, resources)
            jobs.append(SchemaJob(name, uri, resources[uri], {name + "/value": payload}))
        oracle = run_independent(jobs, resources)
        self.assertTrue(all(row["ok"] for row in oracle["schemas"].values()), oracle)
        self.assertTrue(all(row["ok"] for row in oracle["documents"].values()), oracle)


if __name__ == "__main__":
    unittest.main()
