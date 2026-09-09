#!/usr/bin/env python3
"""Exact XSD duration bounds, four-reference-date equality and arithmetic limits.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from fractions import Fraction
import itertools
import json
from pathlib import Path
import random
import subprocess
import tempfile
import unittest

import duration_reference as duration
from lxml import etree
from independent import run as run_independent
import test_builtin_list_values as atomic
import test_list_values as lists
from test_facet_declarations import facet


def verdicts(value, bound):
    relation = duration.compare(value, bound)
    return {name: relation is not None and predicate(relation) for name, predicate in (
        ('enumeration', lambda r: r == 0), ('minInclusive', lambda r: r >= 0),
        ('minExclusive', lambda r: r > 0), ('maxInclusive', lambda r: r <= 0),
        ('maxExclusive', lambda r: r < 0))}


class DurationArithmeticTest(unittest.TestCase):
    def test_normative_partial_order_and_gregorian_cycles(self):
        for sign in ('', '-'):
            for years in (400, 800, 2000, 400 * 10 ** 1000):
                self.assertEqual(0, duration.compare(f'{sign}P{years}Y', f'{sign}P{years // 400 * 146097}D'))
        for days in (28, 29, 30, 31):
            self.assertIsNone(duration.compare('P1M', f'P{days}D'))
        self.assertEqual(1, duration.compare('P1M', 'P27D'))
        self.assertEqual(-1, duration.compare('P1M', 'P32D'))
        self.assertEqual(0, duration.compare('-P0Y', 'PT0S'))
        self.assertEqual(-1, duration.compare('PT1.00000000000000001S', 'PT1.00000000000000002S'))
        self.assertEqual((0, Fraction(1, 10 ** 1001)), duration.components('PT0.' + '0' * 1000 + '1S'))
        # Appendix E works with numeric years internally, including zero.
        self.assertEqual(366, duration.ordinal(1, 1) - duration.ordinal(0, 1))
        for year in range(-400, 401):
            self.assertEqual(146097, duration.ordinal(year + 400, 3) - duration.ordinal(year, 3))

    def test_seeded_components_fractions_and_four_anchor_facet_matrix(self):
        ordinary = ('PT0S', '-PT0S', 'PT0.1S', '-PT0.1S', 'P1M', 'P27D', 'P28D', 'P29D', 'P30D',
                    'P31D', 'P32D', 'P1Y', 'P365D', 'P366D', 'P400Y', 'P146097D', '-P1M', '-P28D',
                    '-P27D', '-P400Y', '-P146097D', 'P2000Y', 'P730485D', '-P2000Y', '-P730485D',
                    'PT1.00000000000000001S', 'PT1.00000000000000002S', '-PT1.00000000000000001S',
                    '-PT1.00000000000000002S', 'P1Y2M3DT4H5M6.789S')
        pairs = list(itertools.product(ordinary, repeat=2))
        generator = random.Random(20260909)
        for _ in range(120):
            sign = generator.choice(('', '-'))
            year, month, day, hour, minute, second = (generator.randrange(100000) for _ in range(6))
            fraction = f'{generator.randrange(10 ** 30):030}'
            text = f'{sign}P{year}Y{month}M{day}DT{hour}H{minute}M{second}.{fraction}S'
            months, seconds = duration.components(text)
            integer, fraction_value = divmod(abs(seconds), 1)
            # Independent normalization using Python integers and rational arithmetic.
            fractional_digits = f'{int(fraction_value * 10 ** 30):030}'
            alias = f'{sign}P{abs(months)}MT{integer}.{fractional_digits}S'
            pairs.extend(((text, alias), (alias, text), (text, generator.choice(ordinary))))
        for digits in (9, 18, 19, 100, 1000):
            cycles = 10 ** digits
            for sign in ('', '-'):
                years = f'{sign}P{400 * cycles}Y'
                days = f'{sign}P{146097 * cycles}D'
                tiny = f'{sign}PT0.' + '0' * digits + '1S'
                pairs.extend(((years, days), (days, years), (days[:-1] + 'DT0.1S', years),
                              (tiny, 'PT0S'), ('PT0S', tiny), (tiny, tiny[:-1] + '0S')))
        # Shift each reference date across zero and Gregorian century boundaries.
        for year, month in duration.ANCHORS:
            for target in (-400, -100, -1, 0, 1, 100, 400):
                months = (year - target) * 12 + month - 1
                text = f'-P{months}M'
                pairs.extend(((text, text), (text, text + 'T0.000000000000000001S')))
        rows = [{'id': index, 'builtin': 'duration', 'value': value, 'bound': bound}
                for index, (value, bound) in enumerate(pairs)]
        with tempfile.TemporaryDirectory(prefix='wsdl-duration-boundaries-') as temporary:
            manifest = Path(temporary) / 'manifest.json'
            manifest.write_text(json.dumps(rows))
            process = subprocess.run(['qore', '-b', '--enable-debug',
                str(Path(__file__).with_name('duration-value-boundaries.qr')), str(manifest)],
                text=True, capture_output=True, timeout=120)
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual('', process.stderr)
        actual = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(1376, len(rows))
        self.assertEqual(list(range(len(rows))), [row['id'] for row in actual])
        for row, observed in zip(rows, actual):
            with self.subTest(id=row['id'], value=row['value'], bound=row['bound']):
                for operation in ('serialize', 'deserialize', 'provider'):
                    self.assertNotIn(operation + '_error', observed)
                    self.assertEqual(duration.components(row['value']), duration.components(observed[operation]))
                for facet, valid in verdicts(row['value'], row['bound']).items():
                    if valid:
                        self.assertIs(True, observed.get(facet), observed)
                    else:
                        self.assertEqual('RUNTIME-TYPE-ERROR', observed.get(facet + '_error'), observed)

# The common binding driver exercises actual SOAP 1.1/1.2 WSDL bindings, both
# directions, scalar/record/repeated values, detached fields and generated examples.


def accepts(case, text):
    try:
        duration.components(text)
    except ValueError:
        return False
    for step in (case.parent, case.facets):
        root = etree.fromstring(('<step xmlns:xs="http://www.w3.org/2001/XMLSchema">' + step + '</step>').encode())
        enumeration = []
        for constraint in root:
            kind = etree.QName(constraint).localname
            lexical = constraint.get('value')
            if kind == 'enumeration':
                enumeration.append(lexical)
            elif not verdicts(text, lexical)[kind]:
                return False
        if enumeration and not any(duration.compare(text, value) == 0 for value in enumeration):
            return False
    return True


def definitions():
    for kind in ('minInclusive', 'minExclusive', 'maxInclusive', 'maxExclusive'):
        for label, bound, values in (
                ('month', 'P1M', ('P27D', 'P28D', 'P29D', 'P30D', 'P31D', 'P32D', 'P1M')),
                ('fraction', 'PT1.00000000000000001S', ('PT1S', 'PT1.000000000000000009S', 'PT1.00000000000000001S', 'PT1.00000000000000002S')),
                ('cycle', 'P400Y', ('P400Y', 'P4800M', 'P146097D', 'P146098D', 'P146096D'))):
            case = lists.ListCase(f'{label}-{kind}', 'duration', facet(kind, bound), ())
            yield lists.ListCase(case.name, 'duration', case.facets, tuple((text, accepts(case, text)) for text in values))
    for label, bound, values in (
            ('fraction', 'PT1.00000000000000001S', ('PT1.00000000000000001S', 'PT1.000000000000000010S',
                                                  'PT1.00000000000000002S', 'PT1S')),
            ('cycle', 'P400Y', ('P400Y', 'P4800M', 'P146097D', 'P146098D', 'P146096D')),
            ('negative-cycle', '-P2000Y', ('-P2000Y', '-P730485D', '-P730484D'))):
        case = lists.ListCase(label + '-enumeration', 'duration', facet('enumeration', bound), ())
        yield lists.ListCase(case.name, 'duration', case.facets, tuple((text, accepts(case, text)) for text in values))


class DurationFacetBindingsTest(lists.ListValuesTest):
    case_definitions = staticmethod(definitions)
    case_schema = staticmethod(atomic.schema)
    parse_value = staticmethod(lambda builtin, text: duration.value(text))

    @staticmethod
    def provider_value(case, lexical):
        return lexical

    def check_oracles(self, jobs, expected):
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle['schemas']))
        self.assertEqual(set(expected), set(oracle['documents']))
        cases = {case.name: case for case in definitions()}
        fixture = json.loads(Path(__file__).with_name('duration-facet-validator-defects.json').read_text())
        adjudicated = {(group['facets'], row['text']): row for group in fixture['cases'] for row in group['values']}
        for key, job in jobs.items():
            case = cases[key.split('/')[0]]
            self.assertTrue(oracle['schemas'][key]['ok'], oracle['schemas'][key])
            self.assertEqual([], oracle['schemas'][key]['warnings'])
            validator = etree.XMLSchema(etree.fromstring(job.schema))
            for name, document in job.documents.items():
                with self.subTest(oracle_document=name):
                    self.assertEqual([], oracle['documents'][name]['warnings'])
                    element = etree.fromstring(document)
                    parts = list(element) or [element]
                    texts = [part.text or '' for part in parts] + list(element.attrib.values())
                    self.assertTrue(texts)
                    self.assertEqual(expected[name], all(accepts(case, text) for text in texts))
                    for implementation, observed in (('libxml2_2_12_10', validator.validate(element)),
                            ('xerces_2_12_2', oracle['documents'][name]['ok'])):
                        verdict = []
                        for text in texts:
                            record = adjudicated.get((case.facets, text))
                            normative = accepts(case, text)
                            if record is not None:
                                self.assertEqual(normative, record['expected'])
                            verdict.append(record[implementation] if record else normative)
                        self.assertEqual(all(verdict), observed, (name, implementation, str(validator.error_log)))


if __name__ == '__main__':
    unittest.main()
