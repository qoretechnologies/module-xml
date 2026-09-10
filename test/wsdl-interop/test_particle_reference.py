#!/usr/bin/env python3
"""Mutation checks for complete P4 element/string observations.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from copy import deepcopy
import unittest

from lxml import etree

import coverage
import particle_reference


class ParticleReferenceTest(unittest.TestCase):
    def test_complete_values_counts_names_and_order(self):
        left = etree.fromstring(b'<root xmlns="urn:p"><group><a> 0 </a><b>1</b><a>2</a><b>3</b>'
                                b'</group><empty/></root>')
        assertion = {'elements': ['{urn:p}root'], 'datatype': 'particle',
                     'leaves': ['{urn:p}a', '{urn:p}b'], 'order': 'per-name'}
        variants = [(deepcopy(left), True, True)]
        reordered = deepcopy(left)
        reordered[0][:] = [reordered[0][0], reordered[0][2], reordered[0][1], reordered[0][3]]
        variants.append((reordered, True, False))
        for change in ('value', 'string-space', 'namespace', 'lost', 'extra', 'same-name-order',
                       'attribute', 'container-text', 'nested-leaf', 'empty-container'):
            node = deepcopy(left)
            if change == 'value':
                node[0][0].text = '9'
            elif change == 'string-space':
                node[0][0].text = '0'
            elif change == 'namespace':
                node[0][0].tag = '{urn:other}a'
            elif change == 'lost':
                node[0].remove(node[0][1])
            elif change == 'extra':
                node[0].append(deepcopy(node[0][1]))
            elif change == 'same-name-order':
                node[0][:] = [node[0][2], node[0][1], node[0][0], node[0][3]]
            elif change == 'attribute':
                node[0][0].set('{urn:p}unit', 'kg')
            elif change == 'container-text':
                node[0].text = '\u00a0'
            elif change == 'nested-leaf':
                node[0][0].append(etree.Element('unexpected'))
            else:
                node.remove(node[1])
            variants.append((node, False, False))
        for node, native, exact in variants:
            for order, expected in (('per-name', native), ('exact', exact)):
                with self.subTest(xml=etree.tostring(node), order=order):
                    result = coverage.value_checks(left, node, [dict(assertion, order=order)])
                    self.assertEqual(expected, result['ok'], result)

    def test_prefix_indentation_empty_string_and_deep_containers(self):
        left = etree.fromstring(b'<r xmlns="urn:p">\n<g><a> <!--note-->x</a><a/></g>\n</r>')
        right = etree.fromstring(b'<q:r xmlns:q="urn:p"><q:g>\n<q:a> x</q:a><q:a></q:a>\n</q:g></q:r>')
        assertion = {'elements': ['{urn:p}r'], 'datatype': 'particle', 'leaves': ['{urn:p}a'], 'order': 'exact'}
        self.assertTrue(coverage.value_checks(left, right, [assertion])['ok'])
        right[0][1].text = ' '
        self.assertFalse(coverage.value_checks(left, right, [assertion])['ok'])
        root = etree.Element('container')
        current = root
        for _ in range(2000):
            current = etree.SubElement(current, 'container')
        etree.SubElement(current, 'leaf').text = 'exact'
        signature = particle_reference.observe(root, ['leaf'], 'exact')
        self.assertEqual(2002, len(signature))
        self.assertEqual(('leaf', [], 'exact', 0), signature[-1])

    def test_malformed_assertions_and_missing_paths(self):
        valid = {'elements': ['root'], 'datatype': 'particle', 'leaves': ['a'], 'order': 'per-name'}
        variants = [{}, {**valid, 'extra': True}]
        for key, value in (('elements', []), ('elements', ['p:root']), ('elements', [False]),
                           ('leaves', []), ('leaves', ['a', 'a']), ('leaves', ['']),
                           ('order', 'sorted-values'), ('datatype', 'string')):
            variants.append(dict(valid, **{key: value}))
        for assertion in variants:
            with self.subTest(assertion=assertion), self.assertRaises(ValueError):
                particle_reference.validate_assertion(assertion)
        records = {'fixture': {'source_decision': {'valid': True},
                              'messages': {'message': {'decision': {'valid': True}}}}}
        selection = {'format': 1, 'cases': {'fixture': {'messages': {'message': [valid]}}}}
        coverage.validate_selection(selection, records)
        for assertion in variants:
            if assertion.get('datatype') == 'particle':
                selection['cases']['fixture']['messages']['message'] = [assertion]
                with self.subTest(selection=selection), self.assertRaises(ValueError):
                    coverage.validate_selection(selection, records)
        root = etree.fromstring(b'<root><a>1</a></root>')
        for path in (['missing'], ['root', 'missing']):
            self.assertFalse(coverage.value_checks(root, root, [dict(valid, elements=path)])['ok'])
        with self.assertRaises(ValueError):
            particle_reference.observe(root, ['a'], 'unknown')


if __name__ == '__main__':
    unittest.main()
