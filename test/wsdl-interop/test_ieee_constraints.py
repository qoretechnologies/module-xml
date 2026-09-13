#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
"""Native canonical IEEE declarations, with explicit XSD 1.0 oracle differences."""
import json
from html import escape
from pathlib import Path
import unittest
from independent import SchemaJob, run
from test_numeric_defaults import pattern

XSD = 'http://www.w3.org/2001/XMLSchema'
FIXTURE = Path(__file__).parent / 'fixtures/ieee-constraints.json'


def quote(text):
    return escape(text, quote=True).replace('\t', '&#9;').replace('\n', '&#10;').replace('\r', '&#13;')


def fixtures():
    atoms = [('float', 'float', '+017', '1.7E1'),
             ('double', 'double', '+01.2345678901234567', '1.2345678901234567E0'),
             ('float-rounded', 'float', '16777217', '1.6777216E7'),
             ('double-rounded', 'double', '9007199254740993', '9.007199254740992E15'),
             ('float-zero', 'float', '-0', '0.0E0'),
             ('double-zero', 'double', '+0', '0.0E0'),
             ('float-subnormal', 'float', '1e-45', '1.0E-45'),
             ('double-subnormal', 'double', '5e-324', '5.0E-324')]
    values = [(name, '', 'xs:' + builtin, source, canonical) for name, builtin, source, canonical in atoms]
    values += [('float-list', '<xs:simpleType name="List"><xs:list itemType="xs:float"/></xs:simpleType>',
                'List', '+017 0.125', '1.7E1 1.25E-1'),
               ('mixed-list', '<xs:simpleType name="Item"><xs:union memberTypes="xs:float xs:QName"/></xs:simpleType>'
                '<xs:simpleType name="List"><xs:list itemType="Item"/></xs:simpleType>',
                'List', '+017 p:Part 0.125', '1.7E1 p:Part 1.25E-1'),
               ('float-union', '<xs:simpleType name="List"><xs:union memberTypes="xs:float xs:string"/></xs:simpleType>',
                'List', '+017', '1.7E1'),
               ('double-union', '<xs:simpleType name="List"><xs:union memberTypes="xs:double xs:string"/></xs:simpleType>',
                'List', '+017', '1.7E1')]
    models = []
    for name, definitions, base, source, canonical in values:
        for valid in [False, True]:
            for kind in ['default', 'fixed']:
                for location in ['element', 'local-element', 'simple-content', 'attribute', 'global-attribute', 'attribute-use']:
                    facet = pattern(source) + ('|' + pattern(canonical) if valid else '')
                    restriction = '<xs:simpleType name="Value"><xs:restriction base="' + base + '">'
                    restriction += '<xs:pattern value="' + quote(facet) + '"/></xs:restriction></xs:simpleType>'
                    constraint = kind + '="' + quote(source) + '"'
                    declaration = '<xs:element name="value" type="Value" ' + constraint + '/>'
                    xml = '<value xmlns:p="urn:part">' + source + '</value>'
                    if location == 'local-element':
                        declaration = '<xs:element name="value"><xs:complexType><xs:sequence>' \
                            '<xs:element name="item" type="Value" ' + constraint + '/>' \
                            '</xs:sequence></xs:complexType></xs:element>'
                        xml = '<value xmlns:p="urn:part"><item>' + source + '</item></value>'
                    elif location == 'simple-content':
                        declaration = '<xs:element name="value" ' + constraint + '><xs:complexType>' \
                            '<xs:simpleContent><xs:extension base="Value"><xs:attribute name="tag"/>' \
                            '</xs:extension></xs:simpleContent></xs:complexType></xs:element>'
                    elif 'attribute' in location:
                        global_attribute = ''
                        use = '<xs:attribute name="item" type="Value" ' + constraint + '/>'
                        if location == 'global-attribute':
                            global_attribute, use = use, '<xs:attribute ref="item"/>'
                        elif location == 'attribute-use':
                            global_attribute = '<xs:attribute name="item" type="Value"/>'
                            use = '<xs:attribute ref="item" ' + constraint + '/>'
                        declaration = global_attribute + '<xs:element name="value"><xs:complexType>' + use \
                            + '</xs:complexType></xs:element>'
                        xml = '<value xmlns:p="urn:part" item="' + quote(source) + '"/>'
                    models.append({'name': '/'.join([name, kind, location, str(valid)]), 'valid': valid,
                                   'schema': '<xs:schema xmlns:xs="' + XSD + '" xmlns:p="urn:part">'
                                   + definitions + restriction + declaration + '</xs:schema>', 'xml': xml,
                                   'oracle_valid': valid and name not in {'float-zero', 'double-zero',
                                       'float-subnormal', 'double-subnormal'},
                                   'oracle_reason': ('XSD 1.0 zero is 0.0E0; Xerces uses 0.0E1'
                                       if name.endswith('-zero') else 'Different shortest precision policy at the least subnormal'
                                       if name.endswith('-subnormal') else None)})
    for name, definition, source in [
        ('empty-list', '<xs:list itemType="xs:float"/>', ''),
        ('singleton-list', '<xs:list itemType="xs:double"/>', '+017'),
        ('string-first', '<xs:union memberTypes="xs:string xs:float"/>', '+017'),
        ('NaN', '<xs:restriction base="xs:float"/>', 'NaN'),
        ('INF', '<xs:restriction base="xs:double"/>', 'INF'),
        ('negative-INF', '<xs:restriction base="xs:float"/>', '-INF'),
    ]:
        for kind in ['default', 'fixed']:
            models.append({'name': 'control/' + name + '/' + kind, 'valid': True, 'oracle_valid': True,
                           'oracle_reason': None,
                           'schema': '<xs:schema xmlns:xs="' + XSD + '"><xs:simpleType name="Value">'
                           + definition + '</xs:simpleType><xs:element name="value" type="Value" '
                           + kind + '="' + quote(source) + '"/></xs:schema>',
                           'xml': '<value>' + source + '</value>'})
    return models


def lexical_fixtures():
    from test_ieee_scalars import definitions
    return [{'name': model.base + '/' + str(i), 'builtin': model.base, 'lexical': text, 'valid': valid}
            for model in definitions() for i, (text, valid) in enumerate(model.values)]


class IeeeConstraintsTest(unittest.TestCase):
    def test_lexicals_against_xerces(self):
        models = lexical_fixtures()
        self.assertEqual(90, len(models))
        self.assertEqual(models, json.loads(FIXTURE.with_name('ieee-lexicals.json').read_text()))
        jobs = [SchemaJob(builtin, 'http://example.invalid/ieee/' + builtin + '.xsd',
                          ('<xs:schema xmlns:xs="' + XSD + '"><xs:element name="value" type="xs:'
                           + builtin + '"/></xs:schema>').encode(),
                          {m['name']: ('<value>' + escape(m['lexical']) + '</value>').encode()
                           for m in models if m['builtin'] == builtin}) for builtin in ['float', 'double']]
        result = run(jobs)
        self.assertEqual(2, len(result['schemas']))
        self.assertEqual(90, len(result['documents']))
        for row in result['schemas'].values():
            self.assertTrue(row['ok'])
            self.assertEqual([], row['warnings'])
        for model in models:
            row = result['documents'][model['name']]
            self.assertEqual(model['valid'], row['ok'], model['name'])
            self.assertEqual([], row['warnings'])

    def test_declarations_against_xerces(self):
        models = fixtures()
        self.assertEqual(300, len(models))
        self.assertEqual(models, json.loads(FIXTURE.read_text()))
        result = run([SchemaJob(m['name'], f'http://example.invalid/ieee-constraints/{i}.xsd',
                               m['schema'].encode(), {m['name']: m['xml'].encode()})
                      for i, m in enumerate(models)])
        self.assertEqual({m['name'] for m in models}, set(result['schemas']))
        differences = []
        for model in models:
            with self.subTest(name=model['name']):
                row = result['schemas'][model['name']]
                self.assertEqual(model['oracle_valid'], row['ok'], row)
                self.assertEqual([], row['warnings'])
                if model['valid'] != row['ok']:
                    self.assertTrue(model['oracle_reason'])
                    differences.append(model['name'])
                row = result['documents'][model['name']]
                self.assertEqual(True if model['oracle_valid'] else None, row['ok'], row)
                self.assertEqual([], row['warnings'])
        self.assertEqual(48, len(differences))


if __name__ == '__main__':
    unittest.main()
