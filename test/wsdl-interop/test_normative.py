#!/usr/bin/env python3
"""Normative XSD 1.0 lexical and exact-value regression assertions.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

from copy import deepcopy
import unittest

from lxml import etree

import normative


class NormativeTest(unittest.TestCase):
    def test_unsigned_signs_and_bounds(self):
        for datatype, maximum in normative.UNSIGNED_MAX.items():
            for value in ("0", "00042", " \t42\n", str(maximum)):
                self.assertTrue(normative.lexical_valid(datatype, value), (datatype, value))
            for value in ("-0", "+42", "-1", "", " ", "0x2a", "42x", "1.0", "1e2", "４２", str(maximum + 1)):
                self.assertFalse(normative.lexical_valid(datatype, value), (datatype, value))
        self.assertTrue(normative.lexical_valid("nonNegativeInteger", "-0"))
        self.assertTrue(normative.lexical_valid("nonNegativeInteger", "+42"))

    def test_gmonth_second_edition_and_timezone_boundaries(self):
        for value in ("--01", "--12", "--04Z", "--04+14:00", "--04-14:00", "--04+00:00", "--04-13:59"):
            self.assertTrue(normative.lexical_valid("gMonth", value), value)
        for value in ("--04--", "--04-15:00", "--04+14:01", "--04-14:01", "--04+00:60",
                      "--00", "--13", "--4", "--04ZZ", "--04+1:00", "", "04"):
            self.assertFalse(normative.lexical_valid("gMonth", value), value)

    def test_large_numbers_and_loss_detection(self):
        expected = "+10000000999829292922093443563.32423442"
        self.assertTrue(normative.same_number("decimal", expected, "10000000999829292922093443563.324234420"))
        self.assertFalse(normative.same_number("decimal", expected, "10000001000000000000000000000"))
        self.assertFalse(normative.same_number("decimal", expected, "1.0000001e+28"))
        self.assertTrue(normative.same_number("integer", "+00042", "42"))
        self.assertFalse(normative.same_number("integer", "42", "42.0"))
        for value in (".5", "210.", "+100000000000000000000000000000000000000000000.00"):
            self.assertTrue(normative.lexical_valid("decimal", value))
        for value in ("NaN", "INF", ".", "+", "1e0", "1.2x", "", "\u00a042"):
            self.assertFalse(normative.lexical_valid("decimal", value))
        for datatype, accepted, rejected in (("positiveInteger", "1", "0"), ("negativeInteger", "-1", "-0"),
                                              ("nonNegativeInteger", "0", "-1"), ("nonPositiveInteger", "-0", "1")):
            self.assertTrue(normative.lexical_valid(datatype, accepted))
            self.assertFalse(normative.lexical_valid(datatype, rejected))
        with self.assertRaises(ValueError):
            normative.lexical_valid("unknown", "42")

    def test_expanded_name_selection_and_contradictions(self):
        first = etree.fromstring(b'<a:r xmlns:a="urn:a"><a:v n="-0"/></a:r>')
        second = etree.fromstring(b'<r xmlns="urn:a"><v n="-0"/></r>')
        assertion = {"elements": ["{urn:a}r", "{urn:a}v"], "attribute": "n", "lexical": "-0",
                     "datatype": "unsignedInt", "valid": False}
        for payload in (first, second):
            result = normative.check_assertions(payload, [assertion])
            self.assertEqual(False, result[0]["valid"])
        for key, value in (("lexical", "+0"), ("valid", True), ("attribute", "missing"),
                           ("elements", ["{urn:wrong}r", "{urn:a}v"])):
            invalid = deepcopy(assertion)
            invalid[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                normative.check_assertions(first, [invalid])
        duplicate = etree.fromstring(b'<a:r xmlns:a="urn:a"><a:v n="-0"/><a:v n="-0"/></a:r>')
        with self.assertRaisesRegex(ValueError, "exactly one"):
            normative.check_assertions(duplicate, [assertion])

    def test_idref_source_copy_preserves_names_and_tokens(self):
        source = etree.fromstring(b'<a:r xmlns:a="urn:a"><a:v refs="foo  bar"/></a:r>')
        same = etree.fromstring(b'<r xmlns="urn:a">\n<v refs="foo bar"/>\n</r>')
        self.assertTrue(normative.same_token_content(source, same))
        for data in (b'<r xmlns="urn:b"><v refs="foo bar"/></r>',
                     b'<r xmlns="urn:a"><v refs="bar foo"/></r>',
                     b'<r xmlns="urn:a"><v refs="foo bar" id="foo"/></r>'):
            self.assertFalse(normative.same_token_content(source, etree.fromstring(data)))


if __name__ == "__main__":
    unittest.main()
