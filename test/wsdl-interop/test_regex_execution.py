#!/usr/bin/env python3
"""XSD alternatives and closures through structural execution and SOAP bindings.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import itertools
import re
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent

import test_builtin_list_values as builtin
import test_list_values as lists
import test_regex_counts as counts
from test_facet_declarations import facet


# Globally equal languages, kept as separate oracle schemas; original payload bytes are unchanged.
# (a|aa)+ = a+ since each repetition consumes one or two a's, and single a's are available.
EQUIVALENT = {
    'execution-alternatives': ('(a|aa)+|a+b', 'a+|a+b'),
    'execution-branches': ('((a|aa)+b|a+c)', 'a+b|a+c'),
    'execution-inherited': ('(a|aa)+|a+b', 'a+|a+b'),
}


def definitions():
    prefix = 'a' * 100
    for name, pattern, valid, invalid in (
        ('alternatives', '(a|aa)+|a+b', (prefix, prefix + 'b'), (prefix + 'c', '')),
        ('branches', '((a|aa)+b|a+c)', (prefix + 'b', prefix + 'c'), (prefix + 'd', prefix, '')),
        ('closures', '(a+)+b|a+c', (prefix + 'b', prefix + 'c'), (prefix + 'd', prefix, '')),
        ('nullable', '(a*)+', ('', prefix), (prefix + 'b',)),
        ('plus-star', '(a+)*', ('', prefix), (prefix + 'b',)),
        ('zero-star', '(a*)*', ('', prefix), (prefix + 'b',)),
        ('count-holes', '(a|aaa){2,3}', ('aa', 'aaa', 'aaaa', 'aaaaaaa', 'aaaaaaaaa'),
            ('', 'a', 'aaaaaaaa', 'aaaaaaaaaa')),
        ('bounded-inner', '(a{2}){1,2}', ('aa', 'aaaa'), ('', 'a', 'aaa', 'aaaaa')),
    ):
        yield lists.ListCase('execution-' + name, 'string', facet('pattern', pattern),
            tuple([(value, True) for value in valid] + [(value, False) for value in invalid]))
    yield lists.ListCase('execution-inherited', 'string', facet('pattern', '(a|aa)+|a+b'),
        ((prefix + 'b', True), (prefix, False), (prefix + 'c', False)), parent=facet('pattern', 'a+b'))
    yield lists.ListCase('execution-siblings', 'string', facet('pattern', '(a+)+b') + facet('pattern', 'a+c'),
        ((prefix + 'b', True), (prefix + 'c', True), (prefix + 'd', False), (prefix, False)))


class RegexExecutionBindingsTest(lists.ListValuesTest):
    case_definitions = staticmethod(definitions)
    case_schema = staticmethod(builtin.schema)
    parse_value = staticmethod(lambda base, text: text)
    provider_value = staticmethod(lambda case, lexical: lexical)

    def check_oracles(self, jobs, expected):
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle['schemas']))
        self.assertEqual(set(expected), set(oracle['documents']))
        derivatives = []
        unassessed = []
        for key, job in jobs.items():
            family = key.split('/')[0]
            result = oracle['schemas'][key]
            self.assertTrue(result['ok'], result)
            self.assertEqual([], result['warnings'])
            validator = etree.XMLSchema(etree.fromstring(job.schema))
            for name, data in job.documents.items():
                result = oracle['documents'][name]
                self.assertEqual(expected[name], result['ok'], result)
                self.assertEqual([], result['warnings'])
                try:
                    accepted = validator.validate(etree.fromstring(data))
                except etree.XMLSchemaValidateError as error:
                    # The pinned libxml2 backtracking guard aborts, not a validity verdict.
                    # Original Xerces and both equivalent-schema verdicts remain mandatory.
                    self.assertIn(family, EQUIVALENT, (name, str(error)))
                    self.assertFalse(expected[name], name)
                    self.assertEqual('Internal error in XML Schema validation.', str(error))
                    self.assertTrue(all(entry.type_name == 'SCHEMAV_INTERNAL' for entry in error.error_log))
                    self.assertIn('xmlSchemaValidateFacets, validating against a pattern facet', str(error.error_log))
                    limited_values = {
                        'execution-alternatives': {'a' * 100 + 'c'},
                        'execution-branches': {'a' * 100 + 'd', 'a' * 100},
                        'execution-inherited': {'a' * 100 + 'c'},
                    }[family]
                    element = etree.fromstring(data)
                    scalars = [part.text or '' for part in element.iter() if len(part) == 0]
                    scalars += [value for part in element.iter() for value in part.attrib.values()]
                    self.assertTrue(scalars)
                    self.assertTrue(all(value in limited_values for value in scalars), name)
                    unassessed.append(name)
                else:
                    self.assertEqual(expected[name], accepted, (name, str(validator.error_log)))
            if family in EQUIVALENT:
                source, replacement = (facet('pattern', pattern).encode() for pattern in EQUIVALENT[family])
                self.assertEqual(1, job.schema.count(source))
                derivatives.append(SchemaJob(key + '/equivalent', job.uri + '.equivalent',
                    job.schema.replace(source, replacement),
                    documents={name + '/equivalent': data for name, data in job.documents.items()}))
        equivalent = run_independent(derivatives)
        self.assertEqual({job.name for job in derivatives}, set(equivalent['schemas']))
        self.assertEqual({name for job in derivatives for name in job.documents}, set(equivalent['documents']))
        for job in derivatives:
            result = equivalent['schemas'][job.name]
            self.assertTrue(result['ok'], result)
            self.assertEqual([], result['warnings'])
            validator = etree.XMLSchema(etree.fromstring(job.schema))
            for name, data in job.documents.items():
                accepted = expected[name.removesuffix('/equivalent')]
                result = equivalent['documents'][name]
                self.assertEqual(accepted, result['ok'], result)
                self.assertEqual([], result['warnings'])
                self.assertEqual(accepted, validator.validate(etree.fromstring(data)), str(validator.error_log))
        # Keep actual document accounting available to the evidence runner.
        self.oracle_accounting = dict(original_schemas=len(jobs), original_documents=len(expected),
            equivalent_schemas=len(derivatives),
            equivalent_documents=sum(len(job.documents) for job in derivatives),
            libxml_unassessed=unassessed)


class RegexExecutionLanguagesTest(unittest.TestCase):
    def test_closure_identities_and_bounded_count_languages(self):
        values = [''.join(chars) for size in range(7) for chars in itertools.product('ab', repeat=size)]
        patterns = []
        for base in ('a', 'ab', 'a|b', 'a|aaa', '|a', ''):
            for inner, outer in itertools.product(('*', '+'), repeat=2):
                patterns.append('((' + base + ')' + inner + ')' + outer)
            for inner, outer in (('{2,}', '*'), ('{2,}', '+'), ('{2}', '{1,2}'), ('{2,3}', '{2,3}')):
                patterns.append('((' + base + ')' + inner + ')' + outer)
        rows = [(pattern, values, [bool(re.fullmatch(pattern, value)) for value in values]) for pattern in patterns]
        counts.StructuralRegexTest.run_patterns(self, rows)


    def test_state_sets_across_nullable_sequences_and_alternatives(self):
        values = [''.join(chars) for size in range(7) for chars in itertools.product('ab', repeat=size)]
        patterns = ('(a?|b?)*a', '(ab|a)*b', 'a?(ba?)*', '(a?b?)*a', '(|a|ab)+b?',
            'a{0}b?', '(a{0,1}|b{1})*', '((a|b)?)*(ab)?', '((a|aa)+|b)*a',
            '(a|b)+|a*', '((a?){0})+b?', '(|a|b)*')
        rows = [(pattern, values, [bool(re.fullmatch(pattern, value)) for value in values]) for pattern in patterns]
        counts.StructuralRegexTest.run_patterns(self, rows)


if __name__ == '__main__':
    unittest.main()
