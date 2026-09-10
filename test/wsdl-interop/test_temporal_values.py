#!/usr/bin/env python3
"""Exact clocks across SOAP bindings, independent validators and providers.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import unittest
import json
from pathlib import Path
import re
import random
import subprocess
import tempfile
from lxml import etree
from independent import run as run_independent

import temporal_reference as temporal
import test_builtin_list_values as atomic
import test_list_values as lists
from test_facet_declarations import facet


def accepts(case, text):
    try:
        candidate = temporal.value(case.base, text)
    except ValueError:
        return False
    for step in (case.parent, case.facets):
        constraints = etree.fromstring(('<step xmlns:xs="http://www.w3.org/2001/XMLSchema">' + step + '</step>').encode())
        choices, patterns = [], []
        for constraint in constraints:
            name, lexical = etree.QName(constraint).localname, constraint.get('value')
            if name == 'pattern':
                patterns.append(lexical)
                continue
            bound = temporal.value(case.base, lexical)
            if name == 'enumeration':
                choices.append(bound)
                continue
            relation = candidate.compare(bound)
            if relation is None or not {'minInclusive': relation >= 0, 'minExclusive': relation > 0,
                                       'maxInclusive': relation <= 0, 'maxExclusive': relation < 0}[name]:
                return False
        if choices and candidate not in choices:
            return False
        if patterns and not any(re.fullmatch(pattern, temporal.collapse(text)) for pattern in patterns):
            return False
    return True


def definitions():
    for builtin in ('time', 'dateTime'):
        day = '2026-12-31T' if builtin == 'dateTime' else ''
        yield lists.ListCase(builtin + '-grammar', builtin, '', tuple(
            (day + clock + zone, True)
            for clock in ('00:00:00', '12:34:56.123456789012345678901', '23:59:59.0000001')
            for zone in ('', 'Z', '-00:00', '+05:30', '-14:00', '+14:00')) + tuple(
            (day + clock, False) for clock in ('25:00:00Z', '24:00:01Z', '24:00:00.0000001Z',
                                              '12:00:00+14:01', '12:00:00+00:60', '12:00:00.', '12:00:00Ztail')))
        yield lists.ListCase(builtin + '-fraction-enum', builtin,
            facet('enumeration', day + '12:00:00.1234567890123456789Z'),
            ((day + '12:00:00.1234567890123456789000+00:00', True),
             (day + '12:00:00.1234567890123456788Z', False),
             (day + '12:00:00.1234567890123456790Z', False),
             (day + '12:00:00.1234567890123456789', False)))
        yield lists.ListCase(builtin + '-pattern', builtin,
            facet('pattern', '.*12:00:00[.]123456000[-]00:00'),
            ((day + '12:00:00.123456000-00:00', True), (day + '12:00:00.123456Z', False)))
        yield lists.ListCase(builtin + '-floating', builtin,
            facet('enumeration', day + '12:00:00.123456789'),
            ((day + '12:00:00.123456789', True), (day + '12:00:00.123456789Z', False)))


class TemporalValuesTest(lists.ListValuesTest):
    case_schema = staticmethod(atomic.schema)
    parse_value = staticmethod(temporal.value)

    def case_definitions(self):
        return (case for case in definitions() if case.base == self.builtin)

    def test_binding_inputs_and_preserved_ordered_values(self):
        for self.builtin in ('time', 'dateTime'):
            with self.subTest(builtin=self.builtin):
                super().test_binding_inputs_and_preserved_ordered_values()

    def test_detached_element_and_message_providers_and_examples(self):
        for self.builtin in ('time', 'dateTime'):
            with self.subTest(builtin=self.builtin):
                super().test_detached_element_and_message_providers_and_examples()

    def check_oracles(self, jobs, expected):
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle['schemas']))
        self.assertEqual(set(expected), set(oracle['documents']))
        cases = {case.name: case for case in self.case_definitions()}
        fixture = json.loads(Path(__file__).with_name('temporal-validator-defects.json').read_text())
        adjudicated = {}
        for group in fixture['cases']:
            for row in group['values']:
                key = group['builtin'], group['facets'], row['text']
                self.assertNotIn(key, adjudicated)
                adjudicated[key] = row
        disagreements = {'libxml2': 0, 'xerces': 0}
        for key, job in jobs.items():
            case = cases[key.split('/')[0]]
            self.assertTrue(oracle['schemas'][key]['ok'], oracle['schemas'][key])
            self.assertEqual([], oracle['schemas'][key]['warnings'])
            validator = etree.XMLSchema(etree.fromstring(job.schema))
            for name, document in job.documents.items():
                with self.subTest(oracle_document=name):
                    element = etree.fromstring(document)
                    texts = [part.text or '' for part in (list(element) or [element])] + list(element.attrib.values())
                    self.assertTrue(texts)
                    self.assertEqual(expected[name], all(accepts(case, text) for text in texts))
                    self.assertEqual([], oracle['documents'][name]['warnings'])
                    for implementation, observed in (('libxml2', validator.validate(element)),
                                                      ('xerces', oracle['documents'][name]['ok'])):
                        verdicts = []
                        for text in texts:
                            record = adjudicated.get((case.base, case.facets, text)) if not case.parent else None
                            if record is None:
                                verdicts.append(accepts(case, text))
                            else:
                                self.assertEqual(accepts(case, text), record['expected'])
                                verdicts.append(record[implementation])
                        self.assertEqual(all(verdicts), observed, (name, implementation, str(validator.error_log)))
                        disagreements[implementation] += observed != expected[name]
        self.assertEqual(24 if any(not valid for valid in expected.values()) else 0, disagreements['libxml2'])
        self.assertEqual(24 if any(not valid for valid in expected.values()) else 0, disagreements['xerces'])
        print(f"{self.builtin}: {len(jobs)} schemas, {len(expected)} documents; adjudicated {disagreements}", flush=True)

    def test_normative_leap_value_identity(self):
        for builtin, left, right in (
            ('dateTime', '1998-12-31T23:59:60Z', '1998-12-31T22:59:60-01:00'),
            ('dateTime', '1998-12-31T23:59:60.123456789Z', '1999-01-01T05:29:60.123456789000+05:30'),
            ('dateTime', '2026-01-31T23:59:60.5Z', '2026-02-01T00:00:00.5Z'),
            ('dateTime', '2026-01-31T23:59:60.5', '2026-02-01T00:00:00.5'),
            ('time', '23:59:60Z', '22:59:60-01:00'),
        ):
            self.assertEqual(temporal.value(builtin, left), temporal.value(builtin, right))
        self.assertLess(temporal.value('dateTime', '1998-12-31T23:59:60.999999999Z').compare(
                        temporal.value('dateTime', '1999-01-01T00:00:00Z')), 0)
        self.assertLess(temporal.value('dateTime', '1998-12-31T22:59:60.999999999').compare(
                        temporal.value('dateTime', '1998-12-31T23:00:00')), 0)

    def test_native_schema_validator_precision_reductions(self):
        fixture = Path(__file__).with_name('temporal-validator-defects.json')
        result = subprocess.run(['qore', '-b', '--enable-debug',
            str(Path(__file__).with_name('calendar-validator.qr')), str(fixture)],
            capture_output=True, text=True, timeout=30)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('', result.stderr)
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        values = [value for group in json.loads(fixture.read_text())['cases'] for value in group['values']]
        self.assertEqual(4, len(values))
        self.assertEqual(list(range(4)), [row['id'] for row in rows])
        for row, value in zip(rows, values):
            self.assertFalse(value['expected'])
            self.assertEqual(value['libxml2'], row['valid'])

    def test_independent_decimal_value_api(self):
        pairs = []
        for builtin in ('time', 'dateTime'):
            prefix = '2026-12-31T' if builtin == 'dateTime' else ''
            expected = prefix + '12:00:00.1234567890123456789Z'
            for suffix, relation in (('1234567890123456788Z', -1),
                                     ('1234567890123456789000+00:00', 0),
                                     ('1234567890123456790Z', 1)):
                pairs.append((builtin, prefix + '12:00:00.' + suffix, expected, relation))
        pairs += [('time', '23:00:00-02:00', '01:00:00Z', 0),
                  ('time', '01:00:00+02:00', '23:00:00Z', 0),
                  ('time', '24:00:00Z', '00:00:00Z', 0),
                  ('dateTime', '2026-12-31T24:00:00Z', '2027-01-01T00:00:00Z', 0),
                  ('time', '00:00:00Z', '00:00:00', None)]
        # XSD time ordering uses an arbitrary common date. Supplying that date to
        # the Java API keeps timezone endpoint day carries that its direct time
        # comparison discards. UTC canonical clocks make daily aliases identical.
        for hour in (0, 1, 9, 10, 14, 23):
            for floating_hour in (0, 1, 9, 10, 14, 23):
                left, right = f'{hour:02}:00:00Z', f'{floating_hour:02}:00:00'
                relation = temporal.value('time', left).compare(temporal.value('time', right))
                pairs.append(('dateTime', '2000-01-01T' + left, '2000-01-01T' + right, relation))
        source = Path(__file__).with_name('oracle') / 'TemporalValueOracle.java'
        with tempfile.TemporaryDirectory(prefix='wsdl-temporal-java-') as directory:
            built = subprocess.run(['javac', '-Xlint:all', '-Werror', '-d', directory, str(source)],
                                   capture_output=True, text=True, timeout=30)
            self.assertEqual(0, built.returncode, built.stderr)
            self.assertEqual('', built.stderr)
            data = ''.join(f'{i}\t{left}\t{right}\n' for i, (_, left, right, _) in enumerate(pairs))
            result = subprocess.run(['java', '-cp', directory, 'TemporalValueOracle'], input=data,
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual('', result.stderr)
            rows = result.stdout.splitlines()
            self.assertEqual(len(pairs), len(rows))
            fixture = json.loads(Path(__file__).with_name('temporal-validator-defects.json').read_text())
            discrepancies = {(row['left'], row['right']): row for row in fixture['jdk_value_api_discrepancies']}
            observed_discrepancies = set()
            for i, (row, (builtin, left, right, relation)) in enumerate(zip(rows, pairs)):
                fields = row.split('\t')
                self.assertEqual(4, len(fields))
                self.assertEqual(str(i), fields[0])
                normative = 2 if relation is None else relation
                if (left, right) in discrepancies:
                    record = discrepancies[left, right]
                    self.assertEqual(normative, record['normative'])
                    self.assertEqual(record['observed'], int(fields[1]))
                    observed_discrepancies.add((left, right))
                else:
                    self.assertEqual(normative, int(fields[1]), (left, right))
                self.assertEqual(relation, temporal.value(builtin, left).compare(temporal.value(builtin, right)))
                self.assertEqual(temporal.value(builtin, left), temporal.value(builtin, fields[2]))
                self.assertEqual(temporal.value(builtin, right), temporal.value(builtin, fields[3]))
            self.assertEqual(set(discrepancies), observed_discrepancies)

    @staticmethod
    def provider_value(case, lexical):
        return lexical


class TemporalBoundariesTest(unittest.TestCase):
    def test_seeded_clocks_exact_fractions_offsets_and_facets(self):
        rows = []
        randomizer = random.Random(20260910)

        def zone(offset):
            return '' if offset is None else 'Z' if offset == 0 else (
                ('+' if offset > 0 else '-') + f'{abs(offset) // 60:02}:{abs(offset) % 60:02}')

        for builtin in ('time', 'dateTime'):
            prefix = '2026-12-31T' if builtin == 'dateTime' else ''
            for clock in ('00:00:00', '09:00:00', '12:34:56', '14:00:00', '23:59:59', '24:00:00'):
                for offset in (None, -840, -839, -1, 0, 1, 839, 840,
                               *(randomizer.randrange(-840, 841) for _ in range(4))):
                    for bound in ('00:00:00Z', '12:34:56.0000001Z', '23:59:59', '14:00:00'):
                        rows.append({'builtin': builtin, 'value': prefix + clock + zone(offset),
                                     'bound': prefix + bound})
            for fraction in ('', '.0', '.000000000', '.0000001', '.1234567890123456788',
                             '.1234567890123456789', '.1234567890123456790', '.' + '9' * 1000):
                for bound in ('', '.0000001', '.1234567890123456789'):
                    rows.append({'builtin': builtin, 'value': prefix + '12:00:00' + fraction + 'Z',
                                 'bound': prefix + '12:00:00' + bound + 'Z'})
            for clock in ('24:00:00.1Z', '00:60:00Z', '00:00:61Z', '12:00:00+14:01', '12:00:00.'):
                rows.append({'builtin': builtin, 'value': prefix + clock})
        for year in ('-2147483649', '-0004', '-0001', '0001', '0004', '2147483648', '9' * 1000):
            for clock in ('00:00:00', '23:59:59.123456789', '24:00:00'):
                for offset in (None, -840, 0, 840):
                    rows.append({'builtin': 'dateTime', 'value': year + '-12-31T' + clock + zone(offset),
                                 'bound': year + '-12-31T12:00:00Z'})
        for index, row in enumerate(rows):
            row['id'] = index
        with tempfile.TemporaryDirectory(prefix='wsdl-temporal-boundaries-') as directory:
            manifest = Path(directory) / 'manifest.json'
            manifest.write_text(json.dumps(rows))
            result = subprocess.run(['qore', '-b', '--enable-debug',
                str(Path(__file__).with_name('calendar-value-boundaries.qr')), str(manifest)],
                capture_output=True, text=True, timeout=120)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('', result.stderr)
        observed = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(718, len(rows))
        self.assertEqual(list(range(len(rows))), [row['id'] for row in observed])
        for source, actual in zip(rows, observed):
            with self.subTest(id=source['id']):
                try:
                    expected = temporal.value(source['builtin'], source['value'])
                except ValueError:
                    expected = None
                for operation, error in (('serialize', 'SOAP-SERIALIZATION-ERROR'),
                        ('deserialize', 'SOAP-DESERIALIZATION-ERROR'), ('provider', 'RUNTIME-TYPE-ERROR')):
                    if expected is None:
                        self.assertEqual(error, actual.get(operation + '_error'), source)
                        self.assertNotIn(operation, actual)
                    else:
                        self.assertNotIn(operation + '_error', actual)
                        self.assertEqual(expected, temporal.value(source['builtin'], actual[operation]))
                if 'bound' in source:
                    bound = temporal.value(source['builtin'], source['bound'])
                    relation = expected.compare(bound)
                    verdicts = {'enumeration': expected == bound}
                    for name in ('minInclusive', 'minExclusive', 'maxInclusive', 'maxExclusive'):
                        verdicts[name] = relation is not None and {'minInclusive': relation >= 0,
                            'minExclusive': relation > 0, 'maxInclusive': relation <= 0,
                            'maxExclusive': relation < 0}[name]
                    for name, valid in verdicts.items():
                        if valid:
                            self.assertIs(True, actual.get(name), (source, actual))
                        else:
                            self.assertEqual('RUNTIME-TYPE-ERROR', actual.get(name + '_error'), (source, actual))


if __name__ == '__main__':
    unittest.main()
