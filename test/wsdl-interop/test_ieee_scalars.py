#!/usr/bin/env python3
"""Exact IEEE values through WSDL scalars, providers and actual SOAP bindings.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
import math
import re
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import run as run_independent

import test_ieee_conversion as ieee
import test_list_values as lists
import test_builtin_list_values as atomic


def value(builtin, text):
    text = text.strip(' \t\r\n')
    if text == 'NaN':
        return 'NaN'
    if text in {'INF', '-INF'}:
        return text
    result = ieee.rounded_value(text, builtin == 'double')
    if math.isinf(result):
        return '-INF' if result < 0 else 'INF'
    return struct.pack('!d', result)


def definitions():
    for builtin in ('float', 'double'):
        valid = ('1', '+001.25e+2', ' \t-1.25\r\n', '1.', '.5', '1.e2', '-0', '0', 'INF', '-INF', 'NaN',
                 '16777217', '16777219', '0.1', '1.00000005960464477539062500000000001',
                 '1.00000005960464477539062499999999999', '1.401298464324817e-45', '4.9406564584124654e-324',
                 '1.00000000000000011102230246251565404236316680908203125001',
                 '3.40282356779733661637539395458142568448e38', '3.5e38', '1e309', '-1e-400')
        invalid = ('', ' ', '1tail', '1e', '1e+', '1e-', '.', '+.', '1e2e3', '1.2.3', '1e2.0',
                   '0x1p0', '1,2', '1 2', '+INF', 'nan', 'inf', '-NaN', '+NaN', '١', '１', '1\u00a0')
        yield lists.ListCase('ieee-' + builtin, builtin, '',
                             tuple((text, True) for text in valid) + tuple((text, False) for text in invalid))


class IeeeBindingsTest(lists.ListValuesTest):
    case_definitions = staticmethod(definitions)
    case_schema = staticmethod(atomic.schema)
    parse_value = staticmethod(value)

    @staticmethod
    def provider_value(case, lexical):
        return lexical

    def check_oracles(self, jobs, expected):
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle['schemas']))
        self.assertEqual(set(expected), set(oracle['documents']))
        false_positives = set()
        for key, job in jobs.items():
            self.assertTrue(oracle['schemas'][key]['ok'], oracle['schemas'][key])
            self.assertEqual([], oracle['schemas'][key]['warnings'])
            validator = etree.XMLSchema(etree.fromstring(job.schema))
            for name, document in job.documents.items():
                with self.subTest(oracle_document=name):
                    self.assertEqual(expected[name], oracle['documents'][name]['ok'], oracle['documents'][name])
                    self.assertEqual([], oracle['documents'][name]['warnings'])
                    element = etree.fromstring(document)
                    valid = validator.validate(element)
                    if valid and not expected[name]:
                        # libxml2's exponent scan does not require a digit after e/E and its optional sign.
                        # Keep the original invalid documents; Xerces and the XSD grammar must reject them.
                        parts = list(element) or [element]
                        texts = [part.text or '' for part in parts] + list(element.attrib.values())
                        self.assertTrue(texts)
                        for text in texts:
                            self.assertIn(text, {'1e', '1e+', '1e-'})
                            self.assertIsNone(re.fullmatch(
                                r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?', text))
                        self.assertEqual(0, len(validator.error_log))
                        false_positives.add(name)
                    else:
                        self.assertEqual(expected[name], valid, str(validator.error_log))
        self.assertEqual(72 if any(not valid for valid in expected.values()) else 0, len(false_positives))


def list_definitions():
    for builtin in ('float', 'double'):
        yield lists.ListCase('ieee-list-' + builtin, builtin, '',
            (('16777217 -0 NaN INF', True), (' \t0.1\r\n-1e-400 ', True), ('', True),
             ('1.00000005960464477539062500000000001 1e309', True),
             ('1 2tail', False), ('1 +INF', False), ('nan', False)))


class IeeeListBindingsTest(lists.ListValuesTest):
    case_definitions = staticmethod(list_definitions)

    @staticmethod
    def parse_value(builtin, text):
        return tuple(value(builtin, item) for item in lists.tokens(text))


class IeeeScalarRoundingTest(ieee.IeeeConversionTest):
    def check_cases(self, rows):
        for index, row in enumerate(rows):
            row['id'] = index
        with tempfile.TemporaryDirectory(prefix='wsdl-ieee-scalars-') as temporary:
            path = Path(temporary) / 'cases.json'
            path.write_text(json.dumps(rows))
            result = subprocess.run(['qore', '--enable-debug', str(Path(__file__).with_name('ieee-scalars.qr')),
                                     str(path)], text=True, capture_output=True, timeout=90)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('', result.stderr)
        observed = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(rows), len(observed))
        self.assertEqual(list(range(len(rows))), [row['id'] for row in observed])
        for source, actual in zip(rows, observed):
            reference = struct.pack('!d', ieee.rounded_value(source['text'], source['wide']))
            self.assertEqual(4, len(actual['values']))
            for stage, converted in enumerate(actual['values']):
                self.assertEqual(reference, struct.pack('!d', float(converted)), (source, actual, stage))
            if source['kind'] == 'string':
                self.assertEqual(source['text'], actual['encoded'])


if __name__ == '__main__':
    unittest.main()
