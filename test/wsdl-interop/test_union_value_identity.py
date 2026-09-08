#!/usr/bin/env python3
"""Union primitive values, enumerations and lexical restrictions at SOAP boundaries.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from dataclasses import dataclass
import unittest

import test_union_providers as unions


@dataclass(frozen=True)
class IdentityCase(unions.UnionCase):
    facets: str = ""


def definitions():
    yield IdentityCase(
        "ambiguous-integers", "boolean-first", "xs:boolean xs:int",
        (("01", True), ("000", True), ("+1", True), ("-0", True),
         ("1", True), ("0", True), ("12", True), ("true", True),
         ("false", True), ("1.0", False), ("yes", False)))
    yield IdentityCase(
        "ambiguous-booleans", "string-boolean", "t:Word xs:boolean",
        (("1", True), ("0", True), ("true", True), ("false", True),
         ("01", False), ("12", False), ("yes", False)),
        '<xs:simpleType name="Word"><xs:restriction base="xs:string">'
        '<xs:pattern value="true|false"/></xs:restriction></xs:simpleType>')
    yield IdentityCase(
        "decimal-enumeration", "decimal", "xs:int xs:decimal",
        (("1", True), ("01", True), ("1.0", True), ("+1.00", True),
         ("0", False), ("2", False), ("1.001", False)),
        facets='<xs:enumeration value="01"/>')
    yield IdentityCase(
        "boolean-enumeration", "boolean-first", "xs:boolean xs:int",
        (("true", True), ("1", True), ("01", False), ("+1", False),
         ("0", False), ("false", False), ("2", False)),
        facets='<xs:enumeration value="1"/>')
    yield IdentityCase(
        "boolean-pattern", "boolean-first", "xs:boolean xs:int",
        (("0", True), ("false", False), ("true", False), ("1", False), ("00", False)),
        facets='<xs:pattern value="0"/>')


def schema(case, model):
    source = unions.schema(case, model).decode()
    if case.facets:
        original = f'<xs:simpleType name="Value"><xs:union memberTypes="{case.members}"/></xs:simpleType>'
        assert source.count(original) == 1
        replacement = original.replace('name="Value"', 'name="Base"')
        replacement += ('<xs:simpleType name="Value"><xs:restriction base="t:Base">'
                        + case.facets + '</xs:restriction></xs:simpleType>')
        source = source.replace(original, replacement)
    return source.encode()


def value(base, text):
    if base == "string-boolean":
        if text in {"true", "false"}:
            return "string", text
        if text in {"1", "0"}:
            return "boolean", text == "1"
        raise ValueError(f"invalid string/boolean union text: {text!r}")
    return unions.value(base, text)


class UnionValueIdentityTest(unions.UnionProvidersTest):
    case_definitions = staticmethod(definitions)
    case_schema = staticmethod(schema)
    parse_value = staticmethod(value)


if __name__ == "__main__":
    unittest.main()
