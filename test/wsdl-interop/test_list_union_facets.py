#!/usr/bin/env python3
"""List-owned facets with ordered union item values in real SOAP bindings.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import unittest

import test_list_values as lists
from test_facet_declarations import facet
from test_union_list_items import value


def definitions():
    yield lists.ListCase("mixed-enum", "mixed", facet("enumeration", "1 01 2"),
        (("true +1 +2", True), (" 1\t01\n02 ", True), ("1 1 2", False), ("01 01 2", False),
         ("1 01 3", False), ("1 2 01", False), ("", False)))
    yield lists.ListCase("decimal-enum", "mixed", facet("enumeration", "01 2"),
        (("+1 +2", True), ("001 02", True), ("1 2", False), ("01 3", False), ("1.0 2", False)))
    yield lists.ListCase("own-pattern", "mixed", facet("enumeration", "true +1 +2")
        + facet("pattern", "1 001 002"),
        (("1 001 002", True), (" 1\t001\n002 ", True), ("true +1 +2", False), ("1 01 2", False)))
    yield lists.ListCase("inherited-pattern", "mixed", facet("enumeration", "01 12"),
        (("01 12", True), ("+1 12", False), ("1 12", False), ("01 13", False)),
        parent=facet("pattern", "0[0-9] 12"))
    yield lists.ListCase("inherited-enum", "mixed", facet("length", 2),
        (("01 12", True), ("+1 +12", True), ("1 12", False), ("01 13", False), ("01", False)),
        parent=facet("enumeration", "01 12"))
    yield lists.ListCase("restricted-items", "mixed", facet("length", 2),
        (("01 12", True), ("+1 +12", True), ("1 12", False), ("01 13", False), ("01", False)),
        item_facets=facet("enumeration", "01") + facet("enumeration", "12"))
    yield lists.ListCase("empty-enum", "mixed", facet("enumeration", ""),
        (("", True), (" \t\n", True), ("0", False), ("1 0", False)))
    yield lists.ListCase("pattern-alternatives", "mixed", facet("pattern", "1 001") + facet("pattern", "0 002"),
        (("1 001", True), ("0 002", True), ("true 001", False), ("1 1", False)))
    yield lists.ListCase("length-boundaries", "mixed", facet("minLength", 1) + facet("maxLength", 2),
        (("1", True), ("01 12", True), ("", False), ("1 2 3", False), ("1 bad", False)))


def schema(case, model):
    original = lists.schema(case, model).decode().replace("xs:mixed", "t:Atomic")
    declaration = '<xs:simpleType name="Atomic"><xs:union memberTypes="xs:boolean xs:int"/></xs:simpleType>'
    return original.replace('<xs:simpleType', declaration + '<xs:simpleType', 1).encode()


class ListUnionFacetsTest(lists.ListValuesTest):
    case_definitions = staticmethod(definitions)
    case_schema = staticmethod(schema)
    parse_value = staticmethod(value)


if __name__ == "__main__":
    unittest.main()
