#!/usr/bin/env python3
"""Shared union schema graphs across bindings, providers and reconstructed contracts.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import unittest

from test_union_providers import UnionCase
import test_union_providers as providers


def definitions():
    for name, category, bottom, values in (
            ("shared-atomic", "boolean-first", "xs:boolean xs:int",
             (("false", True), ("1", True), ("12", True), ("bad", False), ("12tail", False))),
            ("shared-list", "list", "t:Numbers xs:boolean",
             (("1 2", True), ("", True), ("false", True), ("1 bad", False), ("yes", False)))):
        declarations = '<xs:simpleType name="Numbers"><xs:list itemType="xs:int"/></xs:simpleType>'
        declarations += f'<xs:simpleType name="Level0"><xs:union memberTypes="{bottom}"/></xs:simpleType>'
        for level in range(1, 9):
            declarations += (f'<xs:simpleType name="Level{level}"><xs:union '
                             f'memberTypes="t:Level{level - 1} t:Level{level - 1}"/></xs:simpleType>')
        yield UnionCase(name, category, "t:Level8 t:Level8", values, declarations)


class UnionSchemaGraphsTest(providers.UnionProvidersTest):
    case_definitions = staticmethod(definitions)


if __name__ == "__main__":
    unittest.main()
