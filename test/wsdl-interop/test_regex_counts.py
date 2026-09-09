#!/usr/bin/env python3
"""Structural XSD repetition matching and actual SOAP contracts.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import itertools
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from lxml import etree

import test_regex_classes as classes


def small_patterns():
    # Variable-width alternatives make attainable repetition counts discontinuous.
    bases = ('a', 'ab', 'a|b', 'a|aaa', '|a', '')
    for base in bases:
        for low, high in ((0, 0), (0, 1), (1, 1), (1, 3), (2, 2), (3, 3), (3, 5), (0, None), (2, None)):
            yield '(' + base + '){' + str(low) + ',' + (str(high) if high is not None else '') + '}'
    for base in bases:
        yield 'a(' + base + '){1,4}b'
        yield '((' + base + '){1,3}){2,4}'


class StructuralRegexTest(unittest.TestCase):
    def run_patterns(self, definitions):
        rows = [dict(name=str(i), pattern=pattern, values=values)
                for i, (pattern, values, _) in enumerate(definitions)]
        with tempfile.TemporaryDirectory(prefix='wsdl-structural-regex-') as temporary:
            manifest = Path(temporary) / 'manifest.json'
            manifest.write_text(json.dumps(rows))
            process = subprocess.run(['qore', '-b', '--enable-debug',
                str(Path(__file__).with_name('regex-structural.qr')), str(manifest)],
                text=True, capture_output=True, timeout=90)
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual('', process.stderr)
        observed = [json.loads(line) for line in process.stdout.splitlines()]
        expected = {(str(i), copy, value): (pattern, accepted)
                    for i, (pattern, values, verdicts) in enumerate(definitions)
                    for value, accepted in zip(values, verdicts) for copy in (0, 1)}
        self.assertEqual(len(expected), len(observed))
        self.assertEqual(set(expected), {(row['name'], row['copy'], row['text']) for row in observed})
        for row in observed:
            pattern, accepted = expected[row['name'], row['copy'], row['text']]
            with self.subTest(pattern=pattern, text=row['text'], copy=row['copy']):
                self.assertEqual(pattern, row['source'])
                self.assertEqual(accepted, row['ok'])

    def test_exhaustive_small_count_languages(self):
        values = [''.join(chars) for size in range(7) for chars in itertools.product('ab', repeat=size)]
        self.run_patterns([(pattern, values, [bool(re.fullmatch(pattern, value)) for value in values])
                           for pattern in small_patterns()])

    def test_structural_unicode_and_character_classes(self):
        definitions = []
        for case in classes.definitions():
            # This test drives the structural object directly, including patterns normally handled by PCRE.
            if case.name in {'regex-inherited', 'regex-alternatives'}:
                continue
            wrapper = '<root xmlns:xs="http://www.w3.org/2001/XMLSchema">' + case.facets + '</root>'
            pattern = etree.fromstring(wrapper.encode())[0].get('value')
            definitions.append((pattern, [value for value, _ in case.values], [ok for _, ok in case.values]))
        self.run_patterns(definitions)


HUGE = '999999999999999999999999'
BOUND = 16
# These separately identified patterns agree only for lexical strings of at most BOUND characters.
# They do not claim equivalence of the complete infinite languages.
BOUNDED = {
    'count-upper': ('a{0,' + HUGE + '}', 'a{0,16}'),
    'count-nullable': ('(a?){' + HUGE + '}', 'a{0,16}'),
    'count-empty': ('(){' + HUGE + '}', '()'),
    'count-minimum': ('a{' + HUGE + '}', 'a{17}'),
    'count-groups': ('((a|b){2}){0,' + HUGE + '}', '((a|b){2}){0,8}'),
    'count-unicode': ('(Α|中|𐀀){1,' + HUGE + '}', '(Α|中|𐀀){1,16}'),
}


def binding_definitions():
    from test_facet_declarations import facet
    for name, pattern, valid, invalid, example in (
        ('literal', 'a{65536}', ('a' * 65536,), ('a' * 65535, 'a' * 65537), False),
        ('group', '(ab){32768}', ('ab' * 32768,), ('ab' * 32767, 'ab' * 32768 + 'a'), False),
        ('upper', BOUNDED['count-upper'][0], ('', 'a', 'aaa'), ('b', 'aab'), True),
        ('nullable', BOUNDED['count-nullable'][0], ('', 'a', 'aaa'), ('b', 'aab'), True),
        ('empty', BOUNDED['count-empty'][0], ('',), ('a',), True),
        ('minimum', BOUNDED['count-minimum'][0], (), ('', 'a', 'aaa'), False),
        ('groups', BOUNDED['count-groups'][0], ('', 'ab', 'baab'), ('a', 'aba', 'ac'), True),
        ('unicode', BOUNDED['count-unicode'][0], ('Α', '中𐀀Α'), ('', 'a', '中a'), True),
    ):
        yield classes.lists.ListCase('count-' + name, 'string', facet('pattern', pattern),
            tuple([(value, True) for value in valid] + [(value, False) for value in invalid]), example=example)


class RegexCountBindingsTest(classes.lists.ListValuesTest):
    case_definitions = staticmethod(binding_definitions)
    case_schema = staticmethod(classes.builtin.schema)
    parse_value = staticmethod(lambda base, text: text)
    provider_value = staticmethod(lambda case, lexical: lexical)

    def check_oracles(self, jobs, expected):
        from independent import SchemaJob, run as run_independent
        from test_facet_declarations import facet
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle['schemas']))
        self.assertEqual(set(expected), set(oracle['documents']))
        derivatives = []
        for key, job in jobs.items():
            family = key.split('/')[0]
            limited = family in BOUNDED
            result = oracle['schemas'][key]
            self.assertEqual([], result['warnings'])
            self.assertEqual(not limited, result['ok'], result)
            if limited:
                self.assertIn('quantity value overflow', result['desc'])
                with self.assertRaises(etree.XMLSchemaParseError):
                    etree.XMLSchema(etree.fromstring(job.schema))
                source, replacement = (facet('pattern', value).encode() for value in BOUNDED[family])
                self.assertEqual(1, job.schema.count(source))
                derivatives.append(SchemaJob(key + '/bounded', job.uri + '.bounded',
                    job.schema.replace(source, replacement),
                    documents={name + '/bounded': data for name, data in job.documents.items()}))
                for name, data in job.documents.items():
                    element = etree.fromstring(data)
                    for part in element.iter():
                        self.assertLessEqual(len(part.text or ''), BOUND)
                        for value in part.attrib.values():
                            self.assertLessEqual(len(value), BOUND)
                    assessment = oracle['documents'][name]
                    self.assertIsNone(assessment['ok'])
                    self.assertEqual('unreachable', assessment['status'])
                    self.assertEqual('schema compilation failed: ' + key, assessment['desc'])
                    self.assertEqual([], assessment['warnings'])
            else:
                validator = etree.XMLSchema(etree.fromstring(job.schema))
                for name, data in job.documents.items():
                    assessment = oracle['documents'][name]
                    self.assertEqual([], assessment['warnings'])
                    self.assertEqual(expected[name], assessment['ok'], assessment)
                    self.assertEqual(expected[name], validator.validate(etree.fromstring(data)), str(validator.error_log))
        bounded = run_independent(derivatives)
        self.assertEqual({job.name for job in derivatives}, set(bounded['schemas']))
        self.assertEqual({name for job in derivatives for name in job.documents}, set(bounded['documents']))
        for job in derivatives:
            self.assertTrue(bounded['schemas'][job.name]['ok'], bounded['schemas'][job.name])
            self.assertEqual([], bounded['schemas'][job.name]['warnings'])
            validator = etree.XMLSchema(etree.fromstring(job.schema))
            for name, data in job.documents.items():
                accepted = expected[name.removesuffix('/bounded')]
                result = bounded['documents'][name]
                self.assertEqual([], result['warnings'])
                self.assertEqual(accepted, result['ok'], result)
                self.assertEqual(accepted, validator.validate(etree.fromstring(data)), str(validator.error_log))


if __name__ == '__main__':
    unittest.main()
