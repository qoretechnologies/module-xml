#!/usr/bin/env python3
"""Boolean lexical restrictions checked by real SOAP bindings and independent XSD processors.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from dataclasses import dataclass
from pathlib import Path
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS, XSD
from test_facet_declarations import facet
import test_list_values as matrices
import survey


@dataclass(frozen=True)
class BooleanCase:
    name: str
    facets: str
    values: tuple[tuple[str, bool], ...]
    parent: str = ""
    example: bool = True
    base: str = "boolean"
    fixed: str | None = None


def definitions():
    yield BooleanCase("digits", facet("pattern", "0|1"),
                      (("0", True), ("1", True), (" \t1\n", True), ("false", False),
                       ("true", False), ("01", False), ("", False), ("1\u00a0", False), ("1 0", False)))
    yield BooleanCase("words", facet("pattern", "true|false"),
                      (("true", True), ("false", True), ("false\n", True), ("1", False), ("FALSE", False)))
    yield BooleanCase("alternatives", facet("pattern", "0") + facet("pattern", "false"),
                      (("0", True), ("false", True), ("1", False)))
    yield BooleanCase("intersection", facet("pattern", "false|0"),
                      (("0", True), ("false", False), ("1", False)), parent=facet("pattern", "0|1"))
    yield BooleanCase("inherited", "", (("0", True), ("false", False)), parent=facet("pattern", "0|1"))
    yield BooleanCase("empty-intersection", facet("pattern", "true|false"),
                      (("true", False), ("false", False), ("1", False), ("0", False)),
                      parent=facet("pattern", "0|1"), example=False)
    yield BooleanCase("empty-value-space", facet("pattern", "yes"),
                      (("yes", False), ("true", False)), example=False)
    yield BooleanCase("whitespace", facet("whiteSpace", "collapse"),
                      ((" true\t", True), ("false", True), ("1", True), ("0", True), ("\u00a0true", False)))
    yield BooleanCase("fixed-false", facet("pattern", "false|0"),
                      (("0", True), ("false", True), ("1", False)), fixed="false")
    yield BooleanCase("list-items", facet("pattern", "0|1"),
                      (("0 1", True), ("1\t0", True), ("", True), ("false true", False), ("0 yes", False)),
                      base="boolean-list")


def schema(case, model):
    declarations = f'''<xs:simpleType name="Base"><xs:restriction base="xs:boolean">{case.parent}</xs:restriction></xs:simpleType>
        <xs:simpleType name="Flag"><xs:restriction base="t:Base">{case.facets}</xs:restriction></xs:simpleType>'''
    if case.base == "boolean-list":
        declarations += '<xs:simpleType name="Value"><xs:list itemType="t:Flag"/></xs:simpleType>'
    else:
        declarations += '<xs:simpleType name="Value"><xs:restriction base="t:Flag"/></xs:simpleType>'
    root_type = "t:Value"
    if model == "record":
        root_type = "t:Record"
        fixed = f' fixed="{case.fixed}"' if case.fixed is not None else ""
        declarations += f'''<xs:complexType name="Record"><xs:simpleContent><xs:extension base="t:Value">
            <xs:attribute name="choice" type="t:Value" use="required"{fixed}/>
            </xs:extension></xs:simpleContent></xs:complexType>'''
    elif model == "repeated":
        root_type = "t:Record"
        declarations += '''<xs:complexType name="Record"><xs:sequence><xs:element name="item" type="t:Value"
            maxOccurs="3"/></xs:sequence></xs:complexType>'''
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">{declarations}
        <xs:element name="Submit" type="{root_type}"/><xs:element name="Reply" type="{root_type}"/></xs:schema>'''.encode()


def value(base, text):
    parts = matrices.tokens(text)
    if base == "boolean" and len(parts) != 1:
        raise ValueError("an atomic boolean requires exactly one token")
    if any(part not in {"true", "false", "1", "0"} for part in parts):
        raise ValueError("invalid boolean lexical form")
    values = tuple(part in {"true", "1"} for part in parts)
    return values[0] if base == "boolean" else values


class BooleanFacetsTest(matrices.ListValuesTest):
    case_definitions = staticmethod(definitions)
    case_schema = staticmethod(schema)
    parse_value = staticmethod(value)

    @staticmethod
    def provider_value(case, lexical):
        return matrices.tokens(lexical) if case.base == "boolean-list" else lexical

    def check_oracles(self, jobs, expected):
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle["schemas"]))
        self.assertEqual(set(expected), set(oracle["documents"]))
        for key, job in jobs.items():
            self.assertTrue(oracle["schemas"][key]["ok"], oracle["schemas"][key])
            self.assertEqual([], oracle["schemas"][key]["warnings"])
            validator = etree.XMLSchema(etree.fromstring(job.schema))
            for name, document in job.documents.items():
                with self.subTest(oracle_document=name):
                    self.assertEqual(expected[name], validator.validate(etree.fromstring(document)), str(validator.error_log))
                    self.assertEqual(expected[name], oracle["documents"][name]["ok"], oracle["documents"][name])
                    self.assertEqual([], oracle["documents"][name]["warnings"])

    def test_invalid_boolean_facet_declarations(self):
        jobs, contracts = [], []
        with tempfile.TemporaryDirectory(prefix="wsdl-boolean-declarations-") as temporary:
            root = Path(temporary)
            for name in ("enumeration", "minInclusive", "maxInclusive", "minExclusive", "maxExclusive",
                         "length", "minLength", "maxLength", "totalDigits", "fractionDigits"):
                for inherited in (False, True):
                    key = name + str(inherited)
                    case = BooleanCase(key, "" if inherited else facet(name, 1), (),
                                       parent=facet(name, 1) if inherited else "")
                    source = schema(case, "atomic")
                    jobs.append(SchemaJob(key, f"http://example.invalid/{key}.xsd", source))
                    with self.assertRaises(etree.XMLSchemaParseError):
                        etree.XMLSchema(etree.fromstring(source))
                    for version in ("11", "12"):
                        path = root / (key + version + ".wsdl")
                        path.write_text(description(version, source.decode()))
                        contracts.append({"name": key + version, "wsdl": str(path), "base": "http://example.invalid/",
                                          "operation": "submit", "binding": "Soap" + version, "messages": []})
            rows = survey.run_worker(contracts, {})
        self.assertEqual(len(contracts), len(rows))
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


if __name__ == "__main__":
    unittest.main()
