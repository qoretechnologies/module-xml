#!/usr/bin/env python3
"""IEEE restrictions and primitive identities across actual SOAP bindings.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
import math
from pathlib import Path
import random
import re
import struct
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as run_independent

import test_list_values as lists
import test_builtin_list_values as atomic
import test_ieee_scalars as scalars
import test_union_value_identity as unions
from test_facet_declarations import facet
import test_facet_declarations as declarations


def reference_value(builtin, text):
    text = text.strip(' \t\r\n')
    if text in ('NaN', 'INF', '-INF'):
        return float(text)
    return scalars.ieee.rounded_value(text, builtin == 'double')


def reference_accepts(case, text, libxml_nan_order=False):
    """Evaluate this matrix's facets with rational rounding and XSD partial ordering."""
    value = reference_value(case.base, text)
    for step in (case.parent, case.facets):
        restrictions = etree.fromstring(('<step xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                                        + step + '</step>').encode())
        choices = []
        patterns = []
        for constraint in restrictions:
            name = etree.QName(constraint).localname
            lexical = constraint.get('value')
            if name == 'pattern':
                patterns.append(lexical)
                continue
            bound = reference_value(case.base, lexical)
            if name == 'enumeration':
                choices.append(bound)
                continue
            if math.isnan(value) or math.isnan(bound):
                relation = (0 if math.isnan(value) and math.isnan(bound) else
                            (1 if math.isnan(value) else -1) if libxml_nan_order else None)
            else:
                relation = (value > bound) - (value < bound)
            if relation is None:
                return False
            if not {'minInclusive': relation >= 0, 'minExclusive': relation > 0,
                    'maxInclusive': relation <= 0, 'maxExclusive': relation < 0}[name]:
                return False
        if choices and not any(value == choice or math.isnan(value) and math.isnan(choice) for choice in choices):
            return False
        # The only pattern in this matrix uses the common literal/class grammar.
        if patterns and not any(re.fullmatch(pattern, text.strip(' \t\r\n')) for pattern in patterns):
            return False
    return True


def definitions():
    ordinary = ('-INF', '-1', '-0', '+0', '1', 'INF', 'NaN')
    for builtin in ('float', 'double'):
        for bound, accepted in (
            ('minInclusive', {'-0', '+0', '1', 'INF'}),
            ('minExclusive', {'1', 'INF'}),
            ('maxInclusive', {'-INF', '-1', '-0', '+0'}),
            ('maxExclusive', {'-INF', '-1'}),
        ):
            yield lists.ListCase(builtin + '-' + bound, builtin, facet(bound, '0'),
                tuple((text, text in accepted) for text in ordinary))
        for bound in ('minInclusive', 'maxInclusive', 'minExclusive', 'maxExclusive'):
            inclusive = bound.endswith('Inclusive')
            yield lists.ListCase(builtin + '-nan-' + bound, builtin, facet(bound, 'NaN'),
                tuple((text, inclusive and text == 'NaN') for text in ordinary), example=inclusive)
        yield lists.ListCase(builtin + '-finite', builtin,
            facet('minExclusive', '-INF') + facet('maxExclusive', 'INF'),
            tuple((text, text not in {'INF', '-INF', 'NaN'}) for text in ordinary))
        yield lists.ListCase(builtin + '-special-enum', builtin,
            facet('enumeration', 'NaN') + facet('enumeration', '-0') + facet('enumeration', '1'),
            (('NaN', True), ('-0', True), ('+0', True), ('0e999', True), ('1.0', True), ('1e0', True),
             ('1.01', False), ('INF', False), ('-INF', False)))
        yield lists.ListCase(builtin + '-pattern-enum', builtin,
            facet('enumeration', '1') + facet('pattern', '001[.]00e0'),
            (('001.00e0', True), (' \t001.00e0\n', True), ('1', False), ('1e0', False), ('001.01e0', False)))
        yield lists.ListCase(builtin + '-inherited', builtin, facet('minInclusive', '0'),
            (('NaN', False), ('-0', True), ('1e0', True), ('2', False)),
            parent=facet('enumeration', 'NaN') + facet('enumeration', '0') + facet('enumeration', '1'))
        high = '1.00000011920928955078125' if builtin == 'float' else '1.0000000000000002220446049250313080847263336181640625'
        yield lists.ListCase(builtin + '-adjacent-example', builtin,
            facet('minExclusive', '1') + facet('maxInclusive', high),
            ((high, True), ('1', False), ('2', False)))
    yield lists.ListCase('float-rounded-inclusive', 'float',
        facet('minInclusive', '1.00000001') + facet('maxInclusive', '1.00000005'),
        (('1', True), ('1.00000001', True), ('1.00000005', True), ('1.00000006', False), ('0.9999999', False)))
    yield lists.ListCase('float-rounded-exclusive', 'float', facet('minExclusive', '1'),
        (('1.00000001', False), ('1.00000005', False), ('1.00000006', True)))
    yield lists.ListCase('float-rounded-fixed-bound', 'float', facet('minInclusive', '1.00000001'),
        (('1', True), ('2', True), ('0.9999999', False), ('NaN', False)),
        parent='<xs:minInclusive value="1" fixed="true"/>')
    yield lists.ListCase('float-repeated-exclusive', 'float', facet('minExclusive', '1.00000001'),
        (('1.00000006', True), ('1', False), ('NaN', False)), parent=facet('minExclusive', '1'))
    yield lists.ListCase('float-overflow-enum', 'float', facet('enumeration', 'INF'),
        (('INF', True), ('3.5e38', True), ('1e999', True), ('3.4e38', False), ('NaN', False)))
    yield lists.ListCase('double-rounded-enum', 'double', facet('enumeration', '1.00000000000000001'),
        (('1', True), ('1.00000000000000001', True), ('1.0000000000000002', False)))


class IeeeFacetBindingsTest(lists.ListValuesTest):
    case_definitions = staticmethod(definitions)
    case_schema = staticmethod(atomic.schema)
    parse_value = staticmethod(scalars.value)

    @staticmethod
    def provider_value(case, lexical):
        return lexical

    def check_oracles(self, jobs, expected):
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle['schemas']))
        self.assertEqual(set(expected), set(oracle['documents']))
        cases = {case.name: case for case in self.case_definitions()}
        rejected_schemas = set()
        false_positives = set()
        for key, job in jobs.items():
            case = cases[key.split('/')[0]]
            self.assertTrue(oracle['schemas'][key]['ok'], oracle['schemas'][key])
            self.assertEqual([], oracle['schemas'][key]['warnings'])
            try:
                validator = etree.XMLSchema(etree.fromstring(job.schema))
            except etree.XMLSchemaParseError as error:
                # The same exclusive endpoint is permitted in a derivation (4.3.8).
                # libxml2 wrongly validates it as an instance of the base type.
                self.assertEqual('float-repeated-exclusive', case.name, (key, str(error)))
                self.assertIn("must be greater than '1'", str(error))
                self.assertEqual(reference_value(case.base, '1'), reference_value(case.base, '1.00000001'))
                rejected_schemas.add(key)
                validator = None
            for name, document in job.documents.items():
                with self.subTest(oracle_document=name):
                    self.assertEqual(expected[name], oracle['documents'][name]['ok'], oracle['documents'][name])
                    self.assertEqual([], oracle['documents'][name]['warnings'])
                    element = etree.fromstring(document)
                    parts = list(element) or [element]
                    texts = [part.text or '' for part in parts] + list(element.attrib.values())
                    self.assertTrue(texts)
                    self.assertEqual(expected[name], all(reference_accepts(case, text) for text in texts), name)
                    if validator is None:
                        continue
                    valid = validator.validate(element)
                    if valid and not expected[name]:
                        # xmlSchemaCompareFloats orders NaN above every other value.
                        # Require that precise defect, while Xerces and partial ordering reject the original.
                        self.assertTrue(all(reference_accepts(case, text, True) for text in texts))
                        self.assertEqual(0, len(validator.error_log))
                        false_positives.add(name)
                    else:
                        self.assertEqual(expected[name], valid, str(validator.error_log))
        self.assertEqual({'float-repeated-exclusive/' + model for model in ('atomic', 'record', 'repeated')},
                         rejected_schemas)
        self.assertEqual(372 if any(not valid for valid in expected.values()) else 0, len(false_positives))


def list_definitions():
    for builtin in ('float', 'double'):
        rounded = '1.00000001' if builtin == 'float' else '1.00000000000000001'
        yield lists.ListCase('ieee-list-enum-' + builtin, builtin,
            facet('enumeration', 'NaN -0 ' + rounded),
            (('NaN +0 1', True), (' NaN\t-0\n1.0 ', True), ('NaN 0 ' + rounded, True),
             ('NaN 0 1.0000000000000002' if builtin == 'double' else 'NaN 0 1.00000006', False),
             ('NaN 0', False), ('0 NaN 1', False), ('INF 0 1', False)))


class IeeeListFacetBindingsTest(lists.ListValuesTest):
    case_definitions = staticmethod(list_definitions)

    @staticmethod
    def parse_value(builtin, text):
        return tuple(scalars.value(builtin, item) for item in lists.tokens(text))


def union_definitions():
    for first, second in (('float', 'double'), ('double', 'float')):
        declaration = ('<xs:simpleType name="First"><xs:restriction base="xs:' + first + '">'
                       '<xs:pattern value="1[.]0"/></xs:restriction></xs:simpleType>')
        for restricted in (False, True):
            yield unions.IdentityCase('ieee-union-' + first + str(restricted), first, 't:First xs:' + second,
                tuple((text, not restricted or text == '1.0') for text in
                      ('1.0', '1', '+1', '01.0', 'NaN', '-0', 'INF', '16777217')), declaration,
                facets=facet('enumeration', '1.0') if restricted else '')


class IeeeUnionFacetBindingsTest(lists.ListValuesTest):
    case_definitions = staticmethod(union_definitions)
    case_schema = staticmethod(unions.schema)

    @staticmethod
    def parse_value(first, text):
        builtin = first if text == '1.0' else 'float' if first == 'double' else 'double'
        return builtin, scalars.value(builtin, text)

    @staticmethod
    def provider_value(case, lexical):
        return lexical


class IeeeFacetSamplesTest(unittest.TestCase):
    def test_fixed_digit_counts_are_independent_of_the_builtin_range(self):
        cases, jobs, contracts = {}, {}, []
        with tempfile.TemporaryDirectory(prefix='wsdl-fixed-digit-counts-') as temporary:
            root = Path(temporary)
            for builtin, name, count, value in (('byte', 'totalDigits', '300', '1'),
                    ('unsignedByte', 'totalDigits', '1000', '1'), ('nonPositiveInteger', 'totalDigits', '2', '0'),
                    ('negativeInteger', 'fractionDigits', '0', '-1'), ('positiveInteger', 'fractionDigits', '0', '1')):
                for valid in (False, True):
                    case = declarations.Declaration(builtin + str(valid), facet(name, count if valid else '1'), valid,
                        parent=facet(name, count, ' fixed="true"'), base=builtin)
                    for model in ('atomic', 'simple-content'):
                        key = case.name + '/' + model
                        source = declarations.schema(case, model)
                        cases[key] = case
                        jobs[key] = SchemaJob(key, 'http://example.invalid/' + key + '.xsd', source)
                        if valid:
                            for local in ('Submit', 'Reply'):
                                jobs[key].documents[key + '/' + local] = (
                                    '<' + local + ' xmlns="' + declarations.NS + '">' + value + '</' + local + '>').encode()
                        for version in ('11', '12'):
                            path = root / (key.replace('/', '-') + version + '.wsdl')
                            path.write_text(lists.description(version, source.decode()))
                            contracts.append({'name': key + '/' + version, 'wsdl': str(path),
                                'base': 'http://example.invalid/', 'operation': 'submit', 'binding': 'Soap' + version,
                                'messages': []})
            observed = lists.survey.run_worker(contracts, {})
        self.assertEqual(len(contracts), len(observed))
        self.assertEqual({row['name'] for row in contracts}, {row['case'] for row in observed})
        for row in observed:
            self.assertEqual('parse', row['stage'])
            self.assertEqual(cases[row['case'].rsplit('/', 1)[0]].valid, row['ok'], row)
            if not row['ok']:
                self.assertEqual('XSD-SIMPLETYPE-ERROR', row['err'])
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle['schemas']))
        self.assertEqual({name for job in jobs.values() for name in job.documents}, set(oracle['documents']))
        for key, job in jobs.items():
            with self.subTest(schema=key):
                self.assertEqual(cases[key].valid, oracle['schemas'][key]['ok'], oracle['schemas'][key])
                self.assertEqual([], oracle['schemas'][key]['warnings'])
                if not cases[key].valid:
                    with self.assertRaises(etree.XMLSchemaParseError):
                        etree.XMLSchema(etree.fromstring(job.schema))
                    continue
                validator = etree.XMLSchema(etree.fromstring(job.schema))
                for name, document in job.documents.items():
                    self.assertTrue(oracle['documents'][name]['ok'], oracle['documents'][name])
                    self.assertEqual([], oracle['documents'][name]['warnings'])
                    self.assertTrue(validator.validate(etree.fromstring(document)), str(validator.error_log))

    def test_adjacent_boundaries_and_empty_intervals(self):
        rows = []
        for wide in (False, True):
            fraction, exponent_bits, bias = (52, 11, 1023) if wide else (23, 8, 127)
            fmt, integer_fmt = ('!d', '!Q') if wide else ('!f', '!I')
            sign_bit = 1 << (fraction + exponent_bits)
            infinity = ((1 << exponent_bits) - 1) << fraction
            magnitudes = {0, 1, 2, (1 << fraction) - 1, 1 << fraction, (1 << fraction) + 1,
                          infinity - 1, infinity}
            for exponent in (1, 2, bias - 1, bias, bias + 1, (1 << exponent_bits) - 2):
                center = exponent << fraction
                magnitudes.update((center - 1, center, center + 1))
            rng = random.Random(0xFACEE2026 + wide)
            magnitudes.update(rng.randrange(1, infinity) for _ in range(48))

            def unpack(bits):
                return struct.unpack(fmt, struct.pack(integer_fmt, bits))[0]

            def text(value):
                if math.isinf(value):
                    return '-INF' if value < 0 else 'INF'
                return repr(value)

            for magnitude in sorted(magnitudes):
                for negative in (False, True):
                    bits = magnitude | (sign_bit if negative else 0)
                    value = unpack(bits)
                    for upward in (False, True):
                        if magnitude == infinity and upward != negative:
                            continue  # no value lies beyond the infinity endpoint
                        if not magnitude:
                            next_bits = 1 | (0 if upward else sign_bit)
                        else:
                            next_bits = bits + (1 if upward != negative else -1)
                        adjacent = unpack(next_bits)
                        base = dict(builtin='double' if wide else 'float', endpoint=text(value),
                                    facet='minExclusive' if upward else 'maxExclusive', next=text(adjacent))
                        # A singleton interval forces the exact next representable target value.
                        rows.append(dict(base, opposite='maxInclusive' if upward else 'minInclusive', empty=False))
                        # Removing that last value leaves a valid schema with no possible instance.
                        rows.append(dict(base, opposite='maxExclusive' if upward else 'minExclusive', empty=True))
        for index, row in enumerate(rows):
            row['id'] = index
        with tempfile.TemporaryDirectory(prefix='wsdl-ieee-facet-samples-') as temporary:
            path = Path(temporary) / 'cases.json'
            path.write_text(json.dumps(rows))
            result = subprocess.run(['qore', '--enable-debug', str(Path(__file__).with_name('ieee-facet-samples.qr')),
                                     str(path)], text=True, capture_output=True, timeout=90)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('', result.stderr)
        observed = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(list(range(len(rows))), [row['id'] for row in observed])
        self.assertGreater(len(rows), 1000)
        for source, actual in zip(rows, observed):
            with self.subTest(source=source):
                self.assertEqual(2, len(actual['results']))
                for variant in actual['results']:
                    if source['empty']:
                        self.assertEqual('XSD-SAMPLE-ERROR', variant.get('err'), variant)
                    else:
                        self.assertNotIn('err', variant)
                        # XSD 1.0 has one zero value; either native sign denotes it.
                        self.assertEqual(float(source['next']), float(variant['value']))
                        self.assertEqual(float(source['next']), float(variant['provider']))


if __name__ == '__main__':
    unittest.main()
