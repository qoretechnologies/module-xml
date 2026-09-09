#!/usr/bin/env python3
"""Binary octet facets, retained spellings and reconstructed SOAP consumers.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import re
import unittest

import binary_reference
import test_builtin_list_values as atomic
import test_list_values as lists
import test_union_value_identity as unions
from test_facet_declarations import facet


def definitions():
    yield lists.ListCase("hex-enum", "hexBinary", facet("enumeration", "FF"),
        (("FF", True), ("ff", True), (" \tFf\r\n", True), ("fe", False), ("ffff", False), ("", False)))
    yield lists.ListCase("base64-enum", "base64Binary", facet("enumeration", "A A = ="),
        (("AA==", True), ("A A = =", True), ("A\tA=\n=", True), ("AQ==", False), ("AAA=", False), ("", False)))
    for builtin in ("hexBinary", "base64Binary"):
        zero = "00" if builtin == "hexBinary" else "AA=="
        two = "0000" if builtin == "hexBinary" else "AAA="
        three = "000000" if builtin == "hexBinary" else "AAAA"
        yield lists.ListCase(builtin + "-empty", builtin, facet("enumeration", ""),
            (("", True), (" \t\r\n", True), (zero, False)))
        yield lists.ListCase(builtin + "-count", builtin, facet("maxLength", 2),
            ((zero, True), (two, True), ("", False), (three, False)), parent=facet("minLength", 1))
    yield lists.ListCase("hex-pattern", "hexBinary", facet("pattern", "FF"),
        (("FF", True), (" \tFF\r\n", True), ("ff", False), ("Fe", False), ("", False)))
    yield lists.ListCase("base64-pattern", "base64Binary", facet("pattern", "A A = ="),
        (("A A = =", True), (" A\tA =\n= ", True), ("AA==", False), ("A Q = =", False)))
    yield lists.ListCase("hex-pattern-inherited", "hexBinary", facet("length", 1),
        (("FF", True), ("AB", True), ("ff", False), ("ABCDEF", False)), parent=facet("pattern", "[A-F]+"))
    yield lists.ListCase("base64-pattern-inherited", "base64Binary", facet("length", 1),
        (("A A = =", True), ("AA==", False), ("A Q = =", False)), parent=facet("pattern", "A A = ="))
    yield lists.ListCase("hex-own-enum-pattern", "hexBinary", facet("enumeration", "ff") + facet("pattern", "FF"),
        (("FF", True), ("ff", False), ("FE", False)))
    yield lists.ListCase("base64-own-enum-pattern", "base64Binary",
        facet("enumeration", "AA==") + facet("pattern", "A A = ="),
        (("A A = =", True), ("AA==", False), ("A Q = =", False)))


class BinaryFacetBindingsTest(lists.ListValuesTest):
    case_definitions = staticmethod(definitions)
    case_schema = staticmethod(atomic.schema)
    parse_value = staticmethod(binary_reference.value)

    @staticmethod
    def provider_value(case, lexical):
        return lexical


def list_definitions():
    yield lists.ListCase("hex-list-enum", "hexBinary", facet("enumeration", "FF 00"),
        (("ff 00", True), ("FF\t00", True), ("00 ff", False), ("fe 00", False), ("", False)))
    yield lists.ListCase("base64-list-enum", "base64Binary", facet("enumeration", "AA== AAA="),
        (("AA== AAA=", True), (" AA==\tAAA= ", True), ("AAA= AA==", False), ("AB== AAA=", False)))
    yield lists.ListCase("hex-list-pattern", "hexBinary", facet("enumeration", "ff 00") + facet("pattern", "FF 00"),
        (("FF 00", True), ("FF\t00", True), ("ff 00", False), ("FE 00", False)))
    yield lists.ListCase("hex-patterned-items", "hexBinary", facet("length", 2),
        (("FF FF", True), ("FF\tFF", True), ("ff FF", False), ("FF", False)), item_facets=facet("pattern", "FF"))


class BinaryListBindingsTest(lists.ListValuesTest):
    case_definitions = staticmethod(list_definitions)
    parse_value = staticmethod(lambda builtin, text: tuple(binary_reference.value(builtin, token)
                                                         for token in lists.tokens(text)))


def union_definitions():
    yield unions.IdentityCase("hex-pattern-union", "hex-upper", "t:Encoded xs:string",
        (("FF", True), (" FF ", True), ("ff", False), ("FE", False), ("label", False)),
        '<xs:simpleType name="Encoded"><xs:restriction base="xs:hexBinary"><xs:pattern value="[A-F]{2}"/>'
        '</xs:restriction></xs:simpleType>', facets=facet("enumeration", "FF"))
    yield unions.IdentityCase("base64-pattern-union", "base64-spaced", "t:Encoded xs:string",
        (("A A = =", True), (" A\tA =\n= ", True), ("AA==", False), ("AQ==", False), ("label", False)),
        '<xs:simpleType name="Encoded"><xs:restriction base="xs:base64Binary"><xs:pattern value="A A = ="/>'
        '</xs:restriction></xs:simpleType>', facets=facet("enumeration", "A A = ="))
    yield unions.IdentityCase("binary-primitive-families", "binary-families", "xs:hexBinary xs:base64Binary",
        (("FF", True), ("ff", True), ("/w==", False), ("FE", False), ("", False)), facets=facet("enumeration", "FF"))
    yield unions.IdentityCase("binary-union-own-pattern", "binary-families", "xs:hexBinary xs:base64Binary",
        (("FF", True), (" FF ", True), ("\tFF\n", True), ("ff", False), ("/w==", False), ("FE", False), ("", False)),
        facets=facet("enumeration", "FF") + facet("pattern", "FF"))
    yield unions.IdentityCase("binary-union-outer-whitespace", "binary-families", "xs:hexBinary xs:base64Binary",
        ((" FF ", False), ("FF", False), (" ff ", False), (" /w== ", False), (" FE ", False), ("", False)),
        facets=facet("enumeration", "FF") + facet("pattern", " FF "), example=False)
    yield unions.IdentityCase("binary-union-list-items", "binary-list", "t:Items xs:boolean",
        (("FF FF", True), (" FF\tFF ", True), ("ff FF", False), ("FF", False), ("true", False)),
        '<xs:simpleType name="Encoded"><xs:restriction base="xs:hexBinary"><xs:pattern value="FF"/>'
        '</xs:restriction></xs:simpleType><xs:simpleType name="Either"><xs:union memberTypes="t:Encoded xs:string"/>'
        '</xs:simpleType><xs:simpleType name="Selected"><xs:restriction base="t:Either"><xs:enumeration value="FF"/>'
        '</xs:restriction></xs:simpleType><xs:simpleType name="Items"><xs:list itemType="t:Selected"/>'
        '</xs:simpleType>', facets=facet("enumeration", "FF FF") + facet("pattern", "FF FF"))


def union_value(base, text):
    collapsed = re.sub(r"[ \t\r\n]+", " ", text).strip(" ")
    if base == "binary-list":
        return "list", tuple(("hexBinary", binary_reference.value("hexBinary", part))
                             for part in lists.tokens(text))
    if base == "hex-upper":
        return ("hexBinary", binary_reference.value("hexBinary", text)) if re.fullmatch(r"[A-F]{2}", collapsed) else ("string", text)
    if base == "base64-spaced":
        return ("base64Binary", binary_reference.value("base64Binary", text)) if collapsed == "A A = =" else ("string", text)
    for builtin in ("hexBinary", "base64Binary"):
        try:
            return builtin, binary_reference.value(builtin, text)
        except ValueError:
            pass
    raise ValueError("no binary union member accepts the text")


class BinaryUnionBindingsTest(lists.ListValuesTest):
    case_definitions = staticmethod(union_definitions)
    case_schema = staticmethod(unions.schema)
    parse_value = staticmethod(union_value)

    @staticmethod
    def provider_value(case, lexical):
        return lexical


if __name__ == "__main__":
    unittest.main()
