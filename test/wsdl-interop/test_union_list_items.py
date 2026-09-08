#!/usr/bin/env python3
"""Union-valued list items across SOAP bindings, provider copies and examples.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from decimal import Decimal
import re
import unittest

from lxml import etree

import test_union_list_identity as lists
from test_union_value_identity import IdentityCase


DECLARATIONS = lists.DECLARATIONS + '''
    <xs:simpleType name="Atomic"><xs:union memberTypes="xs:boolean xs:int"/></xs:simpleType>
    <xs:simpleType name="Items"><xs:list itemType="t:Atomic"/></xs:simpleType>'''


def definitions():
    yield IdentityCase(
        "union-items-numeric-enumeration", "mixed", "t:Items t:Decimals",
        (("01 2", True), ("+1 +2", True), ("1.0 2.00", True),
         ("1 2", False), ("true 2", False), ("01 3", False), ("2 01", False), ("", False)),
        DECLARATIONS, facets='<xs:enumeration value="01 2"/>')
    yield IdentityCase(
        "union-items-mixed-enumeration", "mixed", "t:Items t:Decimals",
        (("1 01 2", True), ("true +1 +2", True), ("1 1 2", False), ("01 01 2", False),
         ("1.0 1.0 2.0", False), ("01 1 2", False)),
        DECLARATIONS, facets='<xs:enumeration value="1 01 2"/>')
    yield IdentityCase(
        "union-items-unrestricted", "mixed", "t:Items t:Decimals",
        (("01 1 2", True), ("1.0 2.0", True), ("true 12", True), ("", True),
         ("1 bad", False), ("1.0tail 2", False)), DECLARATIONS)
    yield IdentityCase(
        "union-items-pattern", "mixed", "t:Items t:Decimals",
        (("1 01 2", True), ("true 01 2", False), ("1 1 2", False), ("01 1 2", False)),
        DECLARATIONS, facets='<xs:pattern value="1 01 2"/>')
    yield IdentityCase(
        "union-items-atomic-first", "atomic-first", "xs:boolean t:Items t:Decimals",
        (("01", True), ("+1", True), ("1.0", True), ("1", False), ("true", False), ("1 1", False)),
        DECLARATIONS, facets='<xs:enumeration value="01"/>')
    yield IdentityCase(
        "list-empty-enumeration", "mixed", "t:Items t:Decimals",
        (("", True), (" \t\n ", True), ("0", False), ("1 0", False)),
        DECLARATIONS, facets='<xs:enumeration value=""/>')


def value(base, text):
    parts = lists.unions.matrices.tokens(text)
    boolean = {"true", "false", "1", "0"}
    if base == "atomic-first" and len(parts) == 1 and parts[0] in boolean:
        return "boolean", parts[0] in {"true", "1"}
    if all(item in boolean or (re.fullmatch(r"[+-]?[0-9]+", item)
                              and -2147483648 <= int(item) <= 2147483647) for item in parts):
        items = tuple(("boolean", item in {"true", "1"}) if item in boolean
                      else ("decimal", Decimal(item)) for item in parts)
    else:
        items = tuple(("decimal", Decimal(item)) for item in parts)
    return "list", items


class UnionListItemsTest(lists.UnionListIdentityTest):
    case_definitions = staticmethod(definitions)
    parse_value = staticmethod(value)

    def check_xerces_document(self, key, document, expected, result):
        if expected == result["ok"]:
            return False
        # Xerces 2.12.2 treats LIST_DT and LISTOFUNION_DT as disjoint primitive kinds,
        # before comparing their item values. See list-values-adjudication.md.
        self.assertTrue(expected)
        self.assertFalse(result["ok"])
        self.assertEqual("invalid", result["status"])
        case = key.split("/")[0]
        literals = {
            "union-items-numeric-enumeration": ("1.0 2.00", "01 2"),
            "union-items-atomic-first": ("1.0", "01"),
        }
        self.assertIn(case, literals, result)
        actual, allowed = literals[case]
        self.assertIn(f"cvc-enumeration-valid: Value '{actual}'", result["desc"])
        element = etree.fromstring(document)
        for part in list(element) or [element]:
            self.assertEqual(actual, part.text)
        if key.endswith("/record"):
            self.assertEqual(actual, element.get("choice"))
        self.assertEqual(value("mixed", allowed), value("mixed", actual))
        return True

    def check_xerces_disagreements(self, documents):
        self.assertIn(len(documents), (48, 128))


if __name__ == "__main__":
    unittest.main()
