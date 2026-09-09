#!/usr/bin/env python3
"""Union member whitespace and preserved lexical values.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from pathlib import Path
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS, XSD
from test_facet_declarations import facet
import survey

import test_union_providers as providers
import test_list_values as lists
import test_union_value_identity as identities


def definitions():
    yield providers.UnionCase("string-first", "string", "xs:string xs:int",
                              ((" A\t B\r\nC ", True), (" \t\r\n ", True),
                               (" A\u00a0B ", True), (" 1 ", True)))
    yield providers.UnionCase("restricted-member", "text", "t:Code xs:int",
                              (("A", True), ("B", True), (" 12 ", True), (" A ", False), ("\tB\n", False), (" C ", False),
                               (" \t ", False), ("A\u00a0", False)),
                              '<xs:simpleType name="Code"><xs:restriction base="xs:string"><xs:pattern value="[AB]"/>'
                              '</xs:restriction></xs:simpleType>')
    yield providers.UnionCase("boolean-member", "boolean-first", "xs:boolean xs:int",
                              ((" false\t", True), ("\n 1 ", True), (" 12 ", True), (" yes ", False), ("1\u00a0", False)))
    yield providers.UnionCase("list-member", "list", "t:Numbers xs:boolean",
                              ((" 1\t 2 ", True), (" \t ", True), (" false\n", True),
                               ("1 bad", False), ("1\u00a02", False)),
                              '<xs:simpleType name="Numbers"><xs:list itemType="xs:int"/></xs:simpleType>')
    yield providers.UnionCase("nested-union", "string", "t:Inner xs:int",
                              ((" A\t B ", True), ("\r\n", True), (" A\u00a0B ", True)),
                              '<xs:simpleType name="Inner"><xs:union memberTypes="xs:string xs:boolean"/></xs:simpleType>')


def value(base, text):
    lexical = " ".join(lists.tokens(text))
    return ("string", text) if base == "string" else providers.value(base, lexical)


class UnionWhitespaceTest(providers.UnionProvidersTest):
    case_definitions = staticmethod(definitions)
    parse_value = staticmethod(value)

    @staticmethod
    def provider_value(case, lexical):
        normalized = " ".join(lists.tokens(lexical))
        return lists.tokens(lexical) if case.base == "list" and normalized not in {"true", "false"} else lexical


class SelectedUnionPatternWhitespaceTest(lists.ListValuesTest):
    case_schema = staticmethod(identities.schema)
    parse_value = staticmethod(lambda base, text: " ".join(lists.tokens(text)))

    @staticmethod
    def provider_value(case, lexical):
        return lexical

    @staticmethod
    def case_definitions():
        for name, members, pattern, values in (
                ("selected-token", "xs:token xs:int", "A B",
                 (("A B", True), (" A\t B ", True), ("A C", False), ("12", False))),
                ("selected-number", "xs:int xs:boolean", "001",
                 (("001", True), (" \t001\n", True), ("1", False), ("true", False))),
                ("selected-list", "t:Items xs:boolean", "01 2",
                 (("01 2", True), (" 01\t2 ", True), ("1 2", False), ("true", False)))):
            declarations = '<xs:simpleType name="Items"><xs:list itemType="xs:int"/></xs:simpleType>'
            declarations += '<xs:simpleType name="Inner"><xs:union memberTypes="' + members + '"/></xs:simpleType>'
            yield identities.IdentityCase(name, name, "t:Inner xs:double", values, declarations,
                                          facets=facet("pattern", pattern))


class UnionWhitespaceDeclarationsTest(unittest.TestCase):
    def test_authored_wildcard_fixture_requires_mixed_content(self):
        fixture = etree.parse(str(Path(__file__).resolve().parent.parent / "test.wsdl"))
        declarations = fixture.xpath("//xs:complexType[@name='i4452']", namespaces={"xs": XSD})
        self.assertEqual(1, len(declarations))
        self.assertEqual("true", declarations[0].get("mixed"))
        jobs = []
        for mixed in (False, True):
            key = str(mixed)
            declaration = etree.fromstring(etree.tostring(declarations[0]))
            declaration.set("mixed", str(mixed).lower())
            schema = etree.Element(f"{{{XSD}}}schema", nsmap={"s": XSD})
            schema.append(declaration)
            etree.SubElement(schema, f"{{{XSD}}}element", name="value", type="i4452")
            documents = {key + "/text": b"<value>1</value>",
                         key + "/cdata": b"<value><![CDATA[some data]]></value>",
                         key + "/child": b"<value><a>1</a></value>"}
            validator = etree.XMLSchema(schema)
            for name, document in documents.items():
                self.assertEqual(mixed or name.endswith("/child"), validator.validate(etree.fromstring(document)),
                                 (name, str(validator.error_log)))
            jobs.append(SchemaJob(key, f"http://example.invalid/{key}.xsd", etree.tostring(schema), documents))
        oracle = run_independent(jobs)
        self.assertEqual({job.name for job in jobs}, set(oracle["schemas"]))
        self.assertEqual({name for job in jobs for name in job.documents}, set(oracle["documents"]))
        for result in oracle["schemas"].values():
            self.assertTrue(result["ok"], result)
            self.assertEqual([], result["warnings"])
        for name, result in oracle["documents"].items():
            self.assertEqual(name.startswith("True/") or name.endswith("/child"), result["ok"], result)
            self.assertEqual([], result["warnings"])

    def test_forbidden_union_facets(self):
        jobs, contracts = [], []
        facets = [(name, "1") for name in ("minInclusive", "minExclusive", "maxInclusive", "maxExclusive",
                                          "length", "minLength", "maxLength", "totalDigits", "fractionDigits")]
        facets += [("whiteSpace", mode) for mode in ("preserve", "replace", "collapse")]
        with tempfile.TemporaryDirectory(prefix="wsdl-union-declarations-") as temporary:
            root = Path(temporary)
            for name, value in facets:
                for inherited in (False, True):
                    key = name + value + str(inherited)
                    restriction = facet(name, value)
                    source = f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
                        <xs:simpleType name="Union"><xs:union memberTypes="xs:string xs:int"/></xs:simpleType>
                        <xs:simpleType name="Base"><xs:restriction base="t:Union">
                        {restriction if inherited else ""}</xs:restriction></xs:simpleType>
                        <xs:simpleType name="Value"><xs:restriction base="t:Base">
                        {"" if inherited else restriction}</xs:restriction></xs:simpleType>
                        <xs:element name="Submit" type="t:Value"/><xs:element name="Reply" type="t:Value"/>
                        </xs:schema>'''.encode()
                    jobs.append(SchemaJob(key, f"http://example.invalid/{key}.xsd", source))
                    with self.assertRaises(etree.XMLSchemaParseError):
                        etree.XMLSchema(etree.fromstring(source))
                    for version in ("11", "12"):
                        path = root / (key + version + ".wsdl")
                        path.write_text(description(version, source.decode()))
                        contracts.append({"name": key + version, "wsdl": str(path), "base": "http://example.invalid/",
                                          "operation": "submit", "binding": "Soap" + version, "messages": []})
            rows = survey.run_worker(contracts, {})
        self.assertEqual(48, len(rows))
        self.assertEqual({case["name"] for case in contracts}, {row["case"] for row in rows})
        for row in rows:
            self.assertEqual("parse", row["stage"])
            self.assertFalse(row["ok"], row)
            self.assertEqual("XSD-SIMPLETYPE-ERROR", row["err"], row)
        oracle = run_independent(jobs)
        self.assertEqual({job.name for job in jobs}, set(oracle["schemas"]))
        for result in oracle["schemas"].values():
            self.assertFalse(result["ok"], result)
            self.assertEqual([], result["warnings"])
        self.assertEqual({}, oracle["documents"])


class UnionPatternWhitespaceTest(unittest.TestCase):
    # This matrix checks schema lexical validation. Union restriction provider
    # metadata has a separate P3 value/facet implementation criterion.
    test_pattern_member_whitespace = lists.ListValuesTest.test_binding_inputs_and_preserved_ordered_values
    check_output = lists.ListValuesTest.check_output
    parse_value = staticmethod(value)

    @staticmethod
    def case_definitions():
        values = (("A B", True), (" A  B ", False), ("A\tB", False), (" A\u00a0B ", False))
        yield providers.UnionCase("own-pattern", "string", "xs:string xs:int", values)
        yield providers.UnionCase("member-pattern", "string", "t:Code xs:int", values,
                                  '<xs:simpleType name="Code"><xs:restriction base="xs:string">'
                                  '<xs:pattern value="A B"/></xs:restriction></xs:simpleType>')

    @staticmethod
    def case_schema(case, model):
        source = providers.schema(case, model)
        if case.name == "own-pattern":
            source = source.replace(b'<xs:simpleType name="Value"><xs:union memberTypes="xs:string xs:int"/></xs:simpleType>',
                                    b'<xs:simpleType name="Union"><xs:union memberTypes="xs:string xs:int"/></xs:simpleType>'
                                    b'<xs:simpleType name="Value"><xs:restriction base="t:Union">'
                                    b'<xs:pattern value="A B"/></xs:restriction></xs:simpleType>')
        return source

    def check_oracles(self, jobs, expected):
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle["schemas"]))
        self.assertEqual(set(expected), set(oracle["documents"]))
        disagreements = set()
        for key, job in jobs.items():
            self.assertTrue(oracle["schemas"][key]["ok"], oracle["schemas"][key])
            self.assertEqual([], oracle["schemas"][key]["warnings"])
            validator = etree.XMLSchema(etree.fromstring(job.schema))
            for name, document in job.documents.items():
                with self.subTest(oracle_document=name):
                    self.assertEqual(expected[name], validator.validate(etree.fromstring(document)), str(validator.error_log))
                    result = oracle["documents"][name]
                    self.assertEqual([], result["warnings"])
                    if result["ok"] != expected[name]:
                        # Xerces 2.12.2 uses WS_COLLAPSE for a union's own pattern,
                        # although XSD 1.0 section 4.3.6 delegates to the member.
                        self.assertEqual("own-pattern", key.split("/")[0])
                        element = etree.fromstring(document)
                        parts = list(element) or [element]
                        self.assertTrue(all(part.text in {" A  B ", "A\tB"} for part in parts))
                        self.assertFalse(expected[name])
                        self.assertTrue(result["ok"])
                        disagreements.add(name)
        self.assertEqual(24, len(disagreements))


if __name__ == "__main__":
    unittest.main()
