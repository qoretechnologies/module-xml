#!/usr/bin/env python3
"""Calendar values and facets across actual SOAP bindings and detached providers.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
from pathlib import Path
import random
import re
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import run as run_independent
import calendar_reference as calendar
import test_builtin_list_values as atomic
import test_list_values as lists
import test_union_value_identity as unions
from test_facet_declarations import facet


SAMPLES = {'date': '2000-06-15', 'gYear': '2000', 'gYearMonth': '2000-06',
           'gMonthDay': '--06-15', 'gMonth': '--06', 'gDay': '---15'}


def accepts(case, text):
    try:
        candidate = calendar.value(case.base, text)
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
            bound = calendar.value(case.base, lexical)
            if name == 'enumeration':
                choices.append(bound)
                continue
            relation = candidate.compare(bound)
            if relation is None or not {'minInclusive': relation >= 0, 'minExclusive': relation > 0,
                                       'maxInclusive': relation <= 0, 'maxExclusive': relation < 0}[name]:
                return False
        if choices and candidate not in choices:
            return False
        # Only literal/class patterns are authored in this independent matrix.
        if patterns and not any(re.fullmatch(pattern, calendar.collapse(text)) for pattern in patterns):
            return False
    return True


def definitions():
    for builtin, sample in SAMPLES.items():
        yield lists.ListCase(builtin + '-grammar', builtin, '',
            tuple((sample + zone, True) for zone in ('', 'Z', '-00:00', '+05:30', '-14:00', '+14:00'))
            + tuple((sample + zone, False) for zone in ('+14:01', '-14:01', '+00:60', '+15:00', 'z', 'Ztail', '\u00a0'))
            + ((' \t' + sample + 'Z\r\n', True), ('', False)))
        yield lists.ListCase(builtin + '-enum', builtin, facet('enumeration', sample + 'Z'),
            ((sample + 'Z', True), (sample + '+00:00', True), (sample + '-00:00', True),
             (sample, False), (sample + '-00:01', False), (sample + '+00:01', False)))
        yield lists.ListCase(builtin + '-pattern', builtin,
            facet('enumeration', sample + 'Z') + facet('pattern', sample + '[-]00:00'),
            ((sample + '-00:00', True), (' \t' + sample + '-00:00\n', True), (sample + 'Z', False),
             (sample + '+00:00', False), (sample, False)))
        yield lists.ListCase(builtin + '-inherited', builtin, facet('minInclusive', sample + 'Z'),
            ((sample + '-00:00', True), (sample, False), (sample + '-01:00', False)),
            parent=facet('enumeration', sample + 'Z') + facet('enumeration', sample))
        for bound in ('minInclusive', 'minExclusive', 'maxInclusive', 'maxExclusive'):
            for zoned in (False, True):
                endpoint = sample + ('Z' if zoned else '')
                case = lists.ListCase(builtin + '-' + bound + str(zoned), builtin, facet(bound, endpoint), ())
                texts = tuple(sample + zone for zone in ('', 'Z', '-00:00', '+00:01', '-00:01', '+14:00', '-14:00'))
                yield lists.ListCase(case.name, builtin, case.facets, tuple((text, accepts(case, text)) for text in texts))
    for builtin, first, alias, different in (
        ('date', '2002-10-10+13:00', '2002-10-09-11:00', '2002-10-10-11:00'),
        ('date', '0001-01-01+14:00', '-0001-12-31-10:00', '-0001-12-31-09:59'),
        ('gMonthDay', '--01-02+14:00', '--01-01-10:00', '--01-01-09:59'),
        ('gDay', '---02+14:00', '---01-10:00', '---01-10:01'),
    ):
        yield lists.ListCase(builtin + '-crossday-' + first, builtin, facet('enumeration', first),
                             ((first, True), (alias, True), (different, False)))
    for builtin, valid, invalid in (
        ('date', ('-0004-02-29Z', '-0400-02-29', '12000-02-29Z', '1900-02-28'),
         ('0000-01-01', '-0000-01-01', '00001-01-01', '-0001-02-29', '-0100-02-29', '1900-02-29', '2000-04-31')),
        ('gYear', ('-0001', '-0004Z', '12000Z'), ('0000', '-0000', '02000', '+2000')),
        ('gYearMonth', ('-0001-01Z', '12000-12'), ('0000-01', '-0000-01', '02000-01', '2000-00', '2000-13')),
        ('gMonthDay', ('--02-29Z', '--12-31'), ('--02-30', '--04-31', '--00-01', '--01-00')),
        ('gMonth', ('--01', '--12Z'), ('--00', '--13', '--01--')),
        ('gDay', ('---01', '---31Z'), ('---00', '---32')),
    ):
        yield lists.ListCase(builtin + '-boundaries', builtin, '',
                             tuple((text, True) for text in valid) + tuple((text, False) for text in invalid))


class CalendarBindingsTest(lists.ListValuesTest):
    case_schema = staticmethod(atomic.schema)
    parse_value = staticmethod(calendar.value)

    def case_definitions(self):
        return (case for case in definitions() if case.base == self.builtin)

    def test_binding_inputs_and_preserved_ordered_values(self):
        for self.builtin in SAMPLES:
            with self.subTest(builtin=self.builtin):
                super().test_binding_inputs_and_preserved_ordered_values()

    def test_detached_element_and_message_providers_and_examples(self):
        # Keep each complete builtin matrix inside the common worker's bounded
        # deadline and independent oracle's document limit.
        for self.builtin in SAMPLES:
            with self.subTest(builtin=self.builtin):
                super().test_detached_element_and_message_providers_and_examples()

    @staticmethod
    def provider_value(case, lexical):
        return lexical

    def check_oracles(self, jobs, expected):
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle['schemas']))
        self.assertEqual(set(expected), set(oracle['documents']))
        cases = {case.name: case for case in self.case_definitions()}
        adjudicated = {}
        fixture = json.loads(Path(__file__).with_name('calendar-validator-defects.json').read_text())
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
                    self.assertEqual([], oracle['documents'][name]['warnings'])
                    element = etree.fromstring(document)
                    parts = list(element) or [element]
                    texts = [part.text or '' for part in parts] + list(element.attrib.values())
                    self.assertTrue(texts)
                    self.assertEqual(expected[name], all(accepts(case, text) for text in texts), name)
                    valid = validator.validate(element)
                    for implementation, observed in (('libxml2', valid), ('xerces', oracle['documents'][name]['ok'])):
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
        inputs = any(not valid for valid in expected.values())
        libxml_counts = ({'date': 108, 'gYear': 396, 'gYearMonth': 396, 'gMonthDay': 420, 'gMonth': 324, 'gDay': 420}
                        if inputs else {'date': 0, 'gYear': 560, 'gYearMonth': 560, 'gMonthDay': 624, 'gMonth': 432, 'gDay': 624})
        self.assertEqual(libxml_counts[self.builtin], disagreements['libxml2'])
        self.assertEqual(12 if inputs and self.builtin == 'gMonth' else 0, disagreements['xerces'])


def list_definitions():
    for builtin, sample in SAMPLES.items():
        yield lists.ListCase('calendar-list-' + builtin, builtin,
            facet('enumeration', sample + 'Z ' + sample),
            ((sample + '-00:00 ' + sample, True), (' \t' + sample + '+00:00\n' + sample + ' ', True),
             (sample + ' ' + sample + 'Z', False), (sample + 'Z', False),
             (sample + 'Z ' + sample + 'Z', False), (sample + 'Z bad', False), ('', False)))


class CalendarListBindingsTest(lists.ListValuesTest):
    case_definitions = staticmethod(list_definitions)

    @staticmethod
    def parse_value(builtin, text):
        return tuple(calendar.value(builtin, item) for item in lists.tokens(text))


def union_definitions():
    for builtin, sample in SAMPLES.items():
        yield unions.IdentityCase('calendar-union-' + builtin, builtin, 'xs:' + builtin + ' xs:string',
            ((sample + 'Z', True), (sample + '+00:00', True), (sample + '-00:00', True),
             (sample, False), (sample + '+01:00', False), ('label', False)),
            facets=facet('enumeration', sample + 'Z'))
        text_type = '<xs:simpleType name="Text"><xs:restriction base="xs:string">' + facet('pattern', sample + 'Z') + '</xs:restriction></xs:simpleType>'
        yield unions.IdentityCase('calendar-text-first-' + builtin, builtin + '#text', 't:Text xs:' + builtin,
            ((sample + 'Z', True), (sample + '-00:00', False), (sample + '+00:00', False),
             (sample, False), ('label', False)), text_type, facets=facet('enumeration', sample + 'Z'))


class CalendarUnionBindingsTest(lists.ListValuesTest):
    case_definitions = staticmethod(union_definitions)
    case_schema = staticmethod(unions.schema)

    @staticmethod
    def provider_value(case, lexical):
        return lexical

    @staticmethod
    def parse_value(builtin, text):
        builtin, *text_first = builtin.split('#')
        text = calendar.collapse(text)
        if text_first and text == SAMPLES[builtin] + 'Z':
            return 'string', text
        try:
            return builtin, calendar.value(builtin, text)
        except ValueError:
            if text_first:
                raise
            return 'string', text


class CalendarReferenceTest(unittest.TestCase):
    def test_ordinals_cover_full_gregorian_cycles_and_no_year_zero(self):
        self.assertEqual(0, calendar.ordinal(1, 1, 1))
        self.assertEqual(-1, calendar.ordinal(-1, 12, 31))
        self.assertEqual(-146097, calendar.ordinal(-400, 1, 1))
        self.assertEqual(146097, calendar.ordinal(401, 1, 1))
        self.assertEqual(97, sum(calendar.leap(year) for year in range(1, 401)))
        for year in tuple(range(-400, 0)) + tuple(range(1, 401)):
            following = 1 if year == -1 else year + 1
            self.assertEqual(365 + calendar.leap(year), calendar.ordinal(following, 1, 1) - calendar.ordinal(year, 1, 1))
            self.assertEqual(1 + calendar.leap(year), calendar.ordinal(year, 3, 1) - calendar.ordinal(year, 2, 28))

    def test_arbitrary_years_and_timezone_uncertainty(self):
        huge = '1' + '0' * 1000
        previous = '9' * 1000
        self.assertEqual(calendar.value('date', huge + '-01-01+14:00'),
                         calendar.value('date', previous + '-12-31-10:00'))
        self.assertEqual(calendar.value('date', '-' + previous + '-01-01+14:00'),
                         calendar.value('date', '-' + huge + '-12-31-10:00'))
        absent = calendar.value('date', '2000-01-02')
        for text in ('2000-01-02Z', '2000-01-02+14:00', '2000-01-02-14:00'):
            zoned = calendar.value('date', text)
            self.assertNotEqual(absent, zoned)
            self.assertIsNone(absent.compare(zoned))
            self.assertIsNone(zoned.compare(absent))
        self.assertEqual(1, absent.compare(calendar.value('date', '2000-01-01-09:59')))
        self.assertEqual(-1, absent.compare(calendar.value('date', '2000-01-03+09:59')))


class CalendarBoundariesTest(unittest.TestCase):
    def test_seeded_offsets_extended_years_leap_boundaries_and_exact_facets(self):
        rows = []
        randomizer = random.Random(20260909)

        def zone(offset):
            if offset is None:
                return ''
            if offset == 0:
                return 'Z'
            return ('+' if offset > 0 else '-') + f'{abs(offset) // 60:02}:{abs(offset) % 60:02}'

        for builtin, sample in SAMPLES.items():
            for offset in (None, -840, -839, -1, 0, 1, 839, 840, *(randomizer.randrange(-840, 841) for _ in range(24))):
                for bound in (None, -840, 0, 840):
                    rows.append({'builtin': builtin, 'value': sample + zone(offset), 'bound': sample + zone(bound)})
        years = ('-2147483649', '-2147483648', '-32769', '-0400', '-0100', '-0004', '-0001',
                 '0001', '0004', '0100', '0400', '32768', '2147483647', '2147483648',
                 '9' * 1000, '1' + '0' * 1000, '-' + '9' * 1000, '-1' + '0' * 1000)
        for year in years:
            for month, day in ((1, 1), (2, 28), (2, 29), (3, 1), (12, 31)):
                text = year + f'-{month:02}-{day:02}'
                for offset in (None, 840, -840):
                    row = {'builtin': 'date', 'value': text + zone(offset)}
                    try:
                        calendar.value('date', row['value'])
                    except ValueError:
                        pass
                    else:
                        row['bound'] = year + '-03-01Z'
                    rows.append(row)
        for sign in ('', '-'):
            for year in range(1, 401):
                rows.append({'builtin': 'date', 'value': sign + f'{year:04}-02-29Z'})
        for index, row in enumerate(rows):
            row['id'] = index
        with tempfile.TemporaryDirectory(prefix='wsdl-calendar-boundaries-') as temporary:
            path = Path(temporary) / 'manifest.json'
            path.write_text(json.dumps(rows))
            result = subprocess.run(['qore', '-b', '--enable-debug',
                str(Path(__file__).with_name('calendar-value-boundaries.qr')), str(path)],
                capture_output=True, text=True, timeout=90)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('', result.stderr)
        observed = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(1838, len(rows))
        self.assertEqual(list(range(len(rows))), [row['id'] for row in observed])
        for source, actual in zip(rows, observed):
            with self.subTest(id=source['id']):
                try:
                    expected = calendar.value(source['builtin'], source['value'])
                except ValueError:
                    expected = None
                for operation, error in (('serialize', 'SOAP-SERIALIZATION-ERROR'),
                        ('deserialize', 'SOAP-DESERIALIZATION-ERROR'), ('provider', 'RUNTIME-TYPE-ERROR')):
                    if expected is None:
                        self.assertEqual(error, actual.get(operation + '_error'), source)
                        self.assertNotIn(operation, actual)
                    else:
                        self.assertNotIn(operation + '_error', actual)
                        self.assertEqual(expected, calendar.value(source['builtin'], actual[operation]))
                if 'bound' in source:
                    bound = calendar.value(source['builtin'], source['bound'])
                    relation = expected.compare(bound)
                    verdicts = {'enumeration': expected == bound}
                    for name in ('minInclusive', 'minExclusive', 'maxInclusive', 'maxExclusive'):
                        verdicts[name] = relation is not None and {'minInclusive': relation >= 0,
                            'minExclusive': relation > 0, 'maxInclusive': relation <= 0, 'maxExclusive': relation < 0}[name]
                    for constraint, valid in verdicts.items():
                        if valid:
                            self.assertIs(True, actual.get(constraint), (source, actual))
                        else:
                            self.assertEqual('RUNTIME-TYPE-ERROR', actual.get(constraint + '_error'), (source, actual))


if __name__ == '__main__':
    unittest.main()
