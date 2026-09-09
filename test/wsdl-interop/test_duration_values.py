#!/usr/bin/env python3
"""Exact duration lexical/native boundaries in SOAP bindings and consumers.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from fractions import Fraction
import json
from pathlib import Path
import unittest

from lxml import etree
from independent import run as run_independent
import duration_reference
import test_builtin_list_values as atomic
import test_list_values as lists


def definitions():
    yield lists.ListCase('duration-grammar', 'duration', '', (
        ('P0Y', True), ('-PT0S', True), ('P1Y2M3DT4H5M6.789S', True),
        ('-P1Y2M3DT4H5M6.789S', True), ('P1DT0S', True), ('P13M', True),
        ('PT61M', True), ('PT61S', True), ('P0001Y00M0DT00H00M00.000S', True),
        (' \tP1D\r\n', True), ('PT0.0000001S', True),
        ('PT1.00000000000000001S', True), ('PT1.00000000000000002S', True),
        ('P1DT', False), ('P1YT', False), ('P', False), ('PT', False), ('', False),
        ('PT.5S', False), ('PT1.S', False), ('P1.5D', False), ('PT1e2S', False),
        ('P1W', False), ('P-1D', False), ('+P1D', False), ('P1D1Y', False),
        ('PT1M1H', False), ('P١D', False), ('PT１S', False), ('P1D\ntrailing', False),
        ('P1D\u00a0', False), ('P1 D', False), ('P1D T1H', False)))


class DurationBindingsTest(lists.ListValuesTest):
    case_definitions = staticmethod(definitions)
    case_schema = staticmethod(atomic.schema)
    parse_value = staticmethod(lambda builtin, text: duration_reference.components(text))

    @staticmethod
    def provider_value(case, lexical):
        return lexical

    def check_oracles(self, jobs, expected):
        fixture = json.loads(Path(__file__).with_name('duration-validator-defects.json').read_text())
        defects = {row['text']: row for group in fixture['cases'] for row in group['values']}
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle['schemas']))
        self.assertEqual(set(expected), set(oracle['documents']))
        disagreements = {'libxml2': 0, 'xerces': 0}
        for key, job in jobs.items():
            self.assertTrue(oracle['schemas'][key]['ok'], oracle['schemas'][key])
            self.assertEqual([], oracle['schemas'][key]['warnings'])
            validator = etree.XMLSchema(etree.fromstring(job.schema))
            for name, document in job.documents.items():
                with self.subTest(oracle_document=name):
                    element = etree.fromstring(document)
                    parts = list(element) or [element]
                    lexical = parts[0].text or ''
                    self.assertTrue(all((part.text or '') == lexical for part in parts))
                    if 'choice' in element.attrib:
                        self.assertEqual(lexical, element.get('choice'))
                    try:
                        duration_reference.components(lexical)
                        valid = True
                    except ValueError:
                        valid = False
                    self.assertEqual(expected[name], valid)
                    defect = defects.get(lexical)
                    if defect:
                        self.assertEqual(valid, defect['expected'])
                    libxml = defect['libxml2_2_12_10'] if defect else valid
                    xerces = defect['xerces_2_12_2'] if defect else valid
                    self.assertEqual(libxml, validator.validate(element), str(validator.error_log))
                    self.assertEqual(xerces, oracle['documents'][name]['ok'], oracle['documents'][name])
                    self.assertEqual([], oracle['documents'][name]['warnings'])
                    disagreements['libxml2'] += libxml != valid
                    disagreements['xerces'] += xerces != valid
        # Request/response input matrices have the three recorded lexical defects;
        # every generated/reconstructed output uses valid collapsed duration text.
        self.assertEqual({'libxml2': 36, 'xerces': 12} if any(not v for v in expected.values())
                         else {'libxml2': 0, 'xerces': 0}, disagreements)


class DurationReferenceTest(unittest.TestCase):
    def test_exact_components_and_invalid_grammar(self):
        self.assertEqual((14, Fraction(273906789, 1000)), duration_reference.components('P1Y2M3DT4H5M6.789S'))
        self.assertEqual((-14, Fraction(-273906789, 1000)), duration_reference.components('-P1Y2M3DT4H5M6.789S'))
        self.assertEqual((0, 0), duration_reference.components('-PT0S'))
        self.assertEqual((12 * (10 ** 1000 - 1), 0), duration_reference.components('P' + '9' * 1000 + 'Y'))
        self.assertEqual((0, Fraction(1, 10 ** 1001)), duration_reference.components('PT0.' + '0' * 1000 + '1S'))
        self.assertNotEqual(duration_reference.components('PT1.00000000000000001S'),
                            duration_reference.components('PT1.00000000000000002S'))
        for lexical in ('P1DT', 'PT.5S', 'PT1.S', 'P1W', 'P١D', 'P1D\u00a0', 'P', ''):
            with self.subTest(lexical=lexical), self.assertRaises(ValueError):
                duration_reference.components(lexical)


if __name__ == '__main__':
    unittest.main()
