#!/usr/bin/env python3
"""Exact binary lexical rules and octets across actual SOAP bindings.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import base64
import json
from pathlib import Path
import unittest

from lxml import etree
from independent import run as run_independent

import binary_reference
import test_builtin_list_values as atomic
import test_list_values as lists


def definitions():
    yield lists.ListCase("hex-grammar", "hexBinary", "", (
        ("", True), (" \t\r\n", True), ("00", True), ("00ff", True), ("00FF", True),
        (" \t2061096220\r\n", True), ("0123456789AbCdEf", True),
        (bytes(range(256)).hex(), True), ("1", False), ("000", False),
        ("0x00", False), ("gg", False), ("00 ff", False), ("0\t0", False),
        ("00\u00a0", False), ("０0", False), ("00trailing", False)))
    yield lists.ListCase("base64-grammar", "base64Binary", "", (
        ("", True), (" \t\r\n", True), ("AA==", True), ("AAA=", True), ("AAAA", True),
        ("A A = =", True), ("A\tA\r=\n=", True), ("A A A =", True),
        (" \tIGEJYiA=\r\n", True), ("/w==", True), ("//8=", True), ("////", True),
        (base64.b64encode(bytes(range(256))).decode(), True),
        ("A", False), ("AA", False), ("AAA", False), ("AAAAA", False),
        ("=", False), ("====", False), ("A===", False), ("AA===", False),
        ("AA==AA==", False), ("AA=A", False), ("=AAA", False), ("AAA==", False),
        ("AB==", False), ("AAB=", False), ("AA==trailing", False),
        ("AA==!", False), ("!? ???", False), ("AA==\u00a0", False),
        ("ＡA==", False), ("_w==", False), ("-w==", False)))
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    for padding, step in (("==", 16), ("=", 4)):
        yield lists.ListCase("base64-pad-" + str(len(padding)), "base64Binary", "",
            tuple((("A" if padding == "==" else "AA") + char + padding, index % step == 0)
                  for index, char in enumerate(alphabet)))


class BinaryBindingsTest(lists.ListValuesTest):
    case_definitions = staticmethod(definitions)
    case_schema = staticmethod(atomic.schema)
    parse_value = staticmethod(binary_reference.value)

    @staticmethod
    def provider_value(case, lexical):
        return lexical

    def check_oracles(self, jobs, expected):
        fixture = json.loads(Path(__file__).with_name("binary-validator-defects.json").read_text())
        defects = {(group["builtin"], row["text"]): row
                   for group in fixture["cases"] for row in group["values"]}
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle["schemas"]))
        self.assertEqual(set(expected), set(oracle["documents"]))
        disagreements = {"libxml2": 0, "xerces": 0}
        builtins = {case.name: case.base for case in definitions()}
        for key, job in jobs.items():
            self.assertTrue(oracle["schemas"][key]["ok"], oracle["schemas"][key])
            self.assertEqual([], oracle["schemas"][key]["warnings"])
            validator = etree.XMLSchema(etree.fromstring(job.schema))
            builtin = builtins[key.split("/")[0]]
            for name, document in job.documents.items():
                with self.subTest(oracle_document=name):
                    element = etree.fromstring(document)
                    parts = list(element) or [element]
                    lexical = parts[0].text or ""
                    self.assertTrue(all((part.text or "") == lexical for part in parts))
                    if "choice" in element.attrib:
                        self.assertEqual(lexical, element.get("choice"))
                    try:
                        binary_reference.value(builtin, lexical)
                        valid = True
                    except ValueError:
                        valid = False
                    self.assertEqual(expected[name], valid)
                    defect = defects.get((builtin, lexical))
                    if defect:
                        self.assertEqual(valid, defect["expected"])
                    libxml = defect["libxml2_2_12_10"] if defect else valid
                    xerces = defect["xerces_2_12_2"] if defect else valid
                    self.assertEqual(libxml, validator.validate(element), str(validator.error_log))
                    self.assertEqual(xerces, oracle["documents"][name]["ok"], oracle["documents"][name])
                    self.assertEqual([], oracle["documents"][name]["warnings"])
                    disagreements["libxml2"] += libxml != valid
                    disagreements["xerces"] += xerces != valid
        # The three exact MIME-tolerance defects occur only in authored input;
        # Qore and Xerces reject each, and every generated output validates.
        self.assertEqual({"libxml2": 36, "xerces": 0} if any(not v for v in expected.values())
                         else {"libxml2": 0, "xerces": 0}, disagreements)


class BinaryReferenceTest(unittest.TestCase):
    def test_grammar_and_exact_octets(self):
        for case in definitions():
            for lexical, expected in case.values:
                with self.subTest(builtin=case.base, lexical=lexical):
                    if expected:
                        binary_reference.value(case.base, lexical)
                    else:
                        with self.assertRaises(ValueError):
                            binary_reference.value(case.base, lexical)
        self.assertEqual(b" a\tb ", binary_reference.value("base64Binary", "IGEJYiA="))
        self.assertEqual(b" a\tb ", binary_reference.value("hexBinary", "2061096220"))
        self.assertEqual(b"\0", binary_reference.value("base64Binary", " A A = = "))
        octets = bytes(range(256)) * 256
        self.assertEqual(octets, binary_reference.value("base64Binary", base64.b64encode(octets).decode()))
        self.assertEqual(octets, binary_reference.value("hexBinary", octets.hex().upper()))
        for builtin in ("hexBinary", "base64Binary"):
            for lexical in ("00\0", "AA==\0", "00\v", "AA==\f"):
                with self.subTest(builtin=builtin, lexical=lexical), self.assertRaises(ValueError):
                    binary_reference.value(builtin, lexical)
        with self.assertRaises(ValueError):
            binary_reference.value("unknown", "")


if __name__ == "__main__":
    unittest.main()
