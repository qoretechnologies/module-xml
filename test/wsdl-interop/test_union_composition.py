#!/usr/bin/env python3
"""XSD 1.0 union composition across bindings and detached providers.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import unittest

import test_union_providers as unions
from test_union_value_identity import IdentityCase, schema as restricted_schema


def declarations(members):
    return (f'<xs:simpleType name="Inner"><xs:union memberTypes="{members}"/></xs:simpleType>'
            '<xs:simpleType name="Restricted"><xs:restriction base="t:Inner">'
            '<xs:pattern value="0[0-9]+"/><xs:enumeration value="01"/>'
            '</xs:restriction></xs:simpleType>')


def definitions():
    for name, category, members in (("integer-first", "integer-first", "xs:int xs:boolean"),
                                    ("boolean-first", "boolean-first", "xs:boolean xs:int"),
                                    ("inline-member", "integer-first", "xs:int xs:boolean")):
        yield IdentityCase(name, category, "t:Restricted",
                           (("01", True), ("1", True), ("2", True), ("true", True), ("false", True),
                            ("bad", False), ("1.5", False), ("12tail", False)), declarations(members))
    yield IdentityCase("outer-restriction", "integer-first", "t:Restricted",
                       (("2", True), ("true", True), ("1", False), ("01", False), ("false", False)),
                       declarations("xs:int xs:boolean"),
                       facets='<xs:pattern value="2|true"/><xs:enumeration value="2"/><xs:enumeration value="true"/>')
    yield IdentityCase("list-restriction", "list", "t:Restricted",
                       (("10 11", True), ("20 21", True), ("true", True), ("false", True),
                        ("10", False), ("9 10", False), ("10 11 12", False), ("bad", False)),
                       '<xs:simpleType name="Number"><xs:restriction base="xs:int"><xs:minInclusive value="10"/>'
                       '</xs:restriction></xs:simpleType><xs:simpleType name="Items"><xs:list itemType="t:Number"/>'
                       '</xs:simpleType><xs:simpleType name="Pair"><xs:restriction base="t:Items"><xs:length value="2"/>'
                       '</xs:restriction></xs:simpleType><xs:simpleType name="Inner"><xs:union memberTypes="t:Pair xs:boolean"/>'
                       '</xs:simpleType><xs:simpleType name="Restricted"><xs:restriction base="t:Inner">'
                       '<xs:enumeration value="10 11"/></xs:restriction></xs:simpleType>')


def schema(case, model):
    source = restricted_schema(case, model)
    if case.name == "inline-member":
        original = b'<xs:simpleType name="Value"><xs:union memberTypes="t:Restricted"/></xs:simpleType>'
        replacement = (b'<xs:simpleType name="Value"><xs:union><xs:simpleType>'
                       b'<xs:restriction base="t:Restricted"><xs:pattern value="01"/></xs:restriction>'
                       b'</xs:simpleType></xs:union></xs:simpleType>')
        assert source.count(original) == 1
        source = source.replace(original, replacement)
    return source


class UnionCompositionTest(unions.UnionProvidersTest):
    case_definitions = staticmethod(definitions)
    case_schema = staticmethod(schema)


if __name__ == "__main__":
    unittest.main()
