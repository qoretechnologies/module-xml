#!/usr/bin/env python3
"""Ordered atomic list values in unions across SOAP bindings and providers.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import base64
from decimal import Decimal
import re
import unittest

from lxml import etree
from independent import run as run_independent
import test_union_providers as unions
from test_union_value_identity import IdentityCase, schema


DECLARATIONS = '''<xs:simpleType name="Word"><xs:restriction base="xs:string">
    <xs:pattern value="true|false"/></xs:restriction></xs:simpleType>
    <xs:simpleType name="Words"><xs:list itemType="t:Word"/></xs:simpleType>
    <xs:simpleType name="Booleans"><xs:list itemType="xs:boolean"/></xs:simpleType>
    <xs:simpleType name="Integers"><xs:list itemType="xs:integer"/></xs:simpleType>
    <xs:simpleType name="Decimals"><xs:list itemType="xs:decimal"/></xs:simpleType>
    <xs:simpleType name="Hex"><xs:list itemType="xs:hexBinary"/></xs:simpleType>
    <xs:simpleType name="Base64"><xs:list itemType="xs:base64Binary"/></xs:simpleType>'''


def definitions():
    yield IdentityCase(
        "list-boolean-spelling", "words-boolean", "t:Words t:Booleans",
        (("1 0", True), ("0 1", True), ("true false", True), ("1 false", True),
         ("", True), ("yes no", False), ("01 0", False)), DECLARATIONS)
    yield IdentityCase(
        "list-integer-spelling", "boolean-integer", "t:Booleans t:Integers",
        (("01 00", True), ("+1 -0", True), ("true false", True), ("1 0", True),
         ("12 -2", True), ("", True), ("1 bad", False), ("1.0 2", False)), DECLARATIONS)
    yield IdentityCase(
        "list-numeric-enumeration", "numeric", "t:Integers t:Decimals",
        (("1 2", True), ("01 +2", True), ("1.0 +2.00", True), (" +001\t02 ", True),
         ("2 1", False), ("1 3", False), ("1", False), ("1 2 3", False), ("", False)),
        DECLARATIONS, facets='<xs:enumeration value="01 +2"/>')
    yield IdentityCase(
        "list-boolean-enumeration", "boolean-integer", "t:Booleans t:Integers",
        (("true false", True), ("1 0", True), ("01 0", False), ("1 00", False),
         ("0 1", False), ("1", False), ("", False)),
        DECLARATIONS, facets='<xs:enumeration value="1 0"/>')
    yield IdentityCase(
        "list-empty-enumeration", "boolean-integer", "t:Booleans t:Integers",
        (("", True), (" \t\n ", True), ("0", False), ("1 0", False)),
        DECLARATIONS, facets='<xs:enumeration value=""/>')
    yield IdentityCase(
        "list-union-pattern", "boolean-integer", "t:Booleans t:Integers",
        (("1 0", True), ("true false", False), ("0 1", False), ("01 0", False)),
        DECLARATIONS, facets='<xs:pattern value="1 0"/>')
    yield IdentityCase(
        "list-binary-families", "binary", "t:Hex t:Base64",
        (("4142 43", True), ("QQ== Qg==", True), ("4142 QQ==", True), ("", True),
         ("!? ???", False)), DECLARATIONS)
    yield IdentityCase(
        "list-distinct-from-atomic", "atomic-boolean", "xs:boolean t:Integers",
        (("01", True), ("+1", True), ("1", False), ("true", False), ("1 1", False)),
        DECLARATIONS, facets='<xs:enumeration value="01"/>')


def value(base, text):
    parts = unions.matrices.tokens(text)
    if base == "binary":
        if all(re.fullmatch(r"(?:[0-9a-fA-F]{2})+", item) for item in parts):
            return "list", tuple(("hexBinary", bytes.fromhex(item)) for item in parts)
        return "list", tuple(("base64Binary", base64.b64decode(item, validate=True)) for item in parts)
    if base == "atomic-boolean":
        if len(parts) == 1 and parts[0] in {"true", "false", "1", "0"}:
            return "boolean", parts[0] in {"true", "1"}
        return "list", tuple(("decimal", Decimal(item)) for item in parts)
    if base == "words-boolean" and all(item in {"true", "false"} for item in parts):
        items = tuple(("string", item) for item in parts)
    elif base != "numeric" and all(item in {"true", "false", "1", "0"} for item in parts):
        items = tuple(("boolean", item in {"true", "1"}) for item in parts)
    else:
        items = tuple(("decimal", Decimal(item)) for item in parts)
    return "list", items


class UnionListIdentityTest(unions.UnionProvidersTest):
    case_definitions = staticmethod(definitions)
    case_schema = staticmethod(schema)
    parse_value = staticmethod(value)

    @staticmethod
    def provider_value(case, lexical):
        return lexical if case.facets else unions.matrices.tokens(lexical)

    def check_oracles(self, jobs, expected):
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle["schemas"]))
        self.assertEqual(set(expected), set(oracle["documents"]))
        unassessed_schemas, unassessed_documents = set(), 0
        binary_false_positives = set()
        for key, job in jobs.items():
            self.assertTrue(oracle["schemas"][key]["ok"], oracle["schemas"][key])
            self.assertEqual([], oracle["schemas"][key]["warnings"])
            try:
                validator = etree.XMLSchema(etree.fromstring(job.schema))
            except etree.XMLSchemaParseError as error:
                # The P3-10 null empty-list value defect also affects a union's enumeration.
                # See list-values-adjudication.md; Xerces and exact item assertions still apply.
                self.assertEqual("list-empty-enumeration", key.split("/")[0], (key, str(error)))
                self.assertEqual(["SCHEMAP_INTERNAL", "SCHEMAP_INTERNAL"],
                                 [entry.type_name for entry in error.error_log])
                self.assertIn("value was not computed", error.error_log[0].message)
                unassessed_schemas.add(key)
                unassessed_documents += len(job.documents)
                validator = None
            for name, document in job.documents.items():
                with self.subTest(oracle_document=name):
                    self.assertEqual(expected[name], oracle["documents"][name]["ok"], oracle["documents"][name])
                    self.assertEqual([], oracle["documents"][name]["warnings"])
                    if validator is not None:
                        element = etree.fromstring(document)
                        valid = validator.validate(element)
                        if valid and not expected[name]:
                            # libxml2's base64 validator ignores nonalphabet characters as MIME does.
                            # XSD 1.0's base64Binary lexical grammar forbids these punctuation tokens.
                            self.assertEqual("list-binary-families", key.split("/")[0])
                            self.assertEqual([], list(validator.error_log))
                            for part in list(element) or [element]:
                                self.assertEqual("!? ???", part.text)
                                for token in unions.matrices.tokens(part.text):
                                    with self.assertRaises(ValueError):
                                        base64.b64decode(token, validate=True)
                            if key.endswith("/record"):
                                self.assertEqual("!? ???", element.get("choice"))
                            binary_false_positives.add(name)
                        else:
                            self.assertEqual(expected[name], valid, str(validator.error_log))
        self.assertIn(len(unassessed_schemas), (0, 3))
        self.assertIn(len(binary_false_positives), (0, 12))
        print(f"libxml2 {etree.LIBXML_VERSION}: {len(unassessed_schemas)} known empty-list enumeration schemas, "
              f"{unassessed_documents} documents unassessed, {len(binary_false_positives)} binary false positives; "
              f"Xerces assessed all {len(expected)} documents")


if __name__ == "__main__":
    unittest.main()
