#!/usr/bin/env python3
"""Ordered union provider conversion across SOAP bindings and detached consumers.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from dataclasses import dataclass
from decimal import Decimal
import unittest

from lxml import etree

from independent import run as run_independent
from test_attribute_values import NS, XSD
import test_list_values as matrices


@dataclass(frozen=True)
class UnionCase:
    name: str
    base: str
    members: str
    values: tuple[tuple[str, bool], ...]
    declarations: str = ""
    example: bool = True


def definitions():
    values = (("false", True), ("true", True), ("1", True), ("0", True), ("12", True),
              ("yes", False), ("12tail", False), ("1.0", False))
    yield UnionCase("boolean-first", "boolean-first", "xs:boolean xs:int", values)
    yield UnionCase("integer-first", "integer-first", "xs:int xs:boolean", values)
    yield UnionCase("restricted-members", "integer-first", "t:Small t:Flag",
                    (("10", True), ("20", True), ("false", True), ("9", False), ("21", False), ("true", False)),
                    '''<xs:simpleType name="Small"><xs:restriction base="xs:int"><xs:minInclusive value="10"/>
                    <xs:maxInclusive value="20"/></xs:restriction></xs:simpleType>
                    <xs:simpleType name="Flag"><xs:restriction base="xs:boolean"><xs:pattern value="false"/>
                    </xs:restriction></xs:simpleType>''')
    yield UnionCase("exact-decimal", "decimal", "xs:decimal xs:boolean",
                    (("12345678901234567890.123456789", True), (".000000000000000000001", True),
                     ("false", True), ("0", True), ("1e2", False), ("1tail", False)))
    yield UnionCase("list-or-boolean", "list", "t:Numbers xs:boolean",
                    (("1 2", True), ("1", True), ("", True), ("false", True), ("1 bad", False), ("yes", False)),
                    '<xs:simpleType name="Numbers"><xs:list itemType="xs:int"/></xs:simpleType>')
    yield UnionCase("text-or-integer", "text", "t:Code xs:int",
                    (("A", True), ("B", True), ("12", True), ("C", False), ("12tail", False)),
                    '<xs:simpleType name="Code"><xs:restriction base="xs:string"><xs:pattern value="[AB]"/>'
                    '</xs:restriction></xs:simpleType>')


def schema(case, model):
    declarations = case.declarations + f'<xs:simpleType name="Value"><xs:union memberTypes="{case.members}"/></xs:simpleType>'
    root_type = "t:Value"
    if model == "record":
        root_type = "t:Record"
        declarations += '''<xs:complexType name="Record"><xs:simpleContent><xs:extension base="t:Value">
            <xs:attribute name="choice" type="t:Value" use="required"/>
            </xs:extension></xs:simpleContent></xs:complexType>'''
    elif model == "repeated":
        root_type = "t:Record"
        declarations += '''<xs:complexType name="Record"><xs:sequence><xs:element name="item" type="t:Value"
            maxOccurs="3"/></xs:sequence></xs:complexType>'''
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">{declarations}
        <xs:element name="Submit" type="{root_type}"/><xs:element name="Reply" type="{root_type}"/></xs:schema>'''.encode()


def value(base, text):
    if base == "list" and text not in {"true", "false"}:
        return "list", tuple(int(token) for token in matrices.tokens(text))
    if text in {"true", "false"} or (base == "boolean-first" and text in {"1", "0"}):
        return "boolean", text in {"true", "1"}
    if base == "text" and text in {"A", "B"}:
        return "string", text
    return "decimal", Decimal(text)


class UnionProvidersTest(matrices.ListValuesTest):
    case_definitions = staticmethod(definitions)
    case_schema = staticmethod(schema)
    parse_value = staticmethod(value)

    @staticmethod
    def provider_value(case, lexical):
        return matrices.tokens(lexical) if case.base == "list" and lexical not in {"true", "false"} else lexical

    def check_oracles(self, jobs, expected):
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle["schemas"]))
        self.assertEqual(set(expected), set(oracle["documents"]))
        precision_disagreements = set()
        for key, job in jobs.items():
            self.assertTrue(oracle["schemas"][key]["ok"], oracle["schemas"][key])
            self.assertEqual([], oracle["schemas"][key]["warnings"])
            validator = etree.XMLSchema(etree.fromstring(job.schema))
            for name, document in job.documents.items():
                with self.subTest(oracle_document=name):
                    self.assertEqual(expected[name], oracle["documents"][name]["ok"], oracle["documents"][name])
                    self.assertEqual([], oracle["documents"][name]["warnings"])
                    element = etree.fromstring(document)
                    valid = validator.validate(element)
                    if expected[name] and not valid:
                        # P1/P3-04: libxml2 2.12's decimal parser has a 24-digit buffer.
                        # The same primitive limitation applies when decimal is a union member.
                        self.assertEqual("exact-decimal", key.split("/")[0], str(validator.error_log))
                        parts = list(element) or [element]
                        self.assertTrue(all(part.text == "12345678901234567890.123456789" for part in parts))
                        self.assertTrue(all(error.type_name == "SCHEMAV_CVC_DATATYPE_VALID_1_2_3"
                                            for error in validator.error_log), str(validator.error_log))
                        precision_disagreements.add(name)
                    else:
                        self.assertEqual(expected[name], valid, str(validator.error_log))
        # Binding documents and consumer documents have separate exact matrices; newer libxml2 may accept all.
        self.assertIn(len(precision_disagreements), (0, 24, 64))


if __name__ == "__main__":
    unittest.main()
