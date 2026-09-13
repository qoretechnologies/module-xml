#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
"""XSD 1.0 canonical numeric/boolean value-constraint declaration checks."""
import json
from pathlib import Path
import unittest

from independent import SchemaJob, run

XSD = 'http://www.w3.org/2001/XMLSchema'
FIXTURE = Path(__file__).parent / 'fixtures/numeric-defaults.json'


def pattern(text):
    return text.replace('+', r'\+').replace('.', r'\.').replace('-', r'\-')


def fixtures():
    # Expected canonical strings are literal specification-derived values; no
    # floating-point arithmetic or implementation conversion supplies the oracle.
    atoms = [(name, '0017', '17') for name in
             ['integer', 'nonNegativeInteger', 'positiveInteger', 'long', 'int', 'short',
              'byte', 'unsignedLong', 'unsignedInt', 'unsignedShort', 'unsignedByte']]
    atoms += [('negativeInteger', '-0017', '-17'), ('nonPositiveInteger', '-0', '0'),
              ('decimal', '+0017.2300', '17.23'), ('decimal', '-00.00', '0.0'),
              ('decimal', '+.0012300', '0.00123'), ('boolean', '1', 'true'), ('boolean', '0', 'false'),
              ('integer', '+00012345678901234567890123456789012345678901234567890',
               '12345678901234567890123456789012345678901234567890'),
              ('decimal', '+00123456789012345678901234567890.123456789012345678900',
               '123456789012345678901234567890.1234567890123456789')]
    values = [(f'atomic-{i}-{name}', '', 'xs:' + name, original, canonical)
              for i, (name, original, canonical) in enumerate(atoms)]
    for name, definitions, base, original, canonical in [
        ('list-int', '<xs:list itemType="xs:int"/>', 'List', '+017 -0', '17 0'),
        ('list-single', '<xs:list itemType="xs:boolean"/>', 'List', '1', 'true'),
        ('list-bool', '<xs:list itemType="xs:boolean"/>', 'List', '1 0', 'true false'),
        ('list-decimal', '<xs:list itemType="xs:decimal"/>', 'List', '017.00 -0.00', '17.0 0.0'),
        ('union-bool-first', '<xs:union memberTypes="xs:boolean xs:string"/>', 'List', '1', 'true'),
        ('union-int-first', '<xs:union memberTypes="xs:int xs:QName"/>', 'List', '+017', '17'),
        ('list-union', '<xs:list itemType="Item"/>', 'List', '1 p:Part 0', 'true p:Part false'),
    ]:
        prefix = '<xs:simpleType name="Item"><xs:union memberTypes="xs:boolean xs:QName"/></xs:simpleType>'
        values.append((name, prefix + '<xs:simpleType name="List">' + definitions + '</xs:simpleType>',
                       base, original, canonical))
    models = []
    for name, definitions, base, original, canonical in values:
        for valid in [False, True]:
            facet = pattern(original) + ('|' + pattern(canonical) if valid else '')
            restriction = '<xs:simpleType name="Value"><xs:restriction base="' + base + '">' \
                '<xs:pattern value="' + facet + '"/></xs:restriction></xs:simpleType>'
            for kind in ['default', 'fixed']:
                # All declaration paths are covered for representative families;
                # every builtin integer family also has an atomic element case.
                locations = ['element'] if name.startswith('atomic-') and int(name.split('-')[1]) < 13 \
                    else ['element', 'local-element', 'simple-content', 'attribute', 'global-attribute', 'attribute-use']
                for location in locations:
                    constraint = kind + '="' + original + '"'
                    declaration = '<xs:element name="value" type="Value" ' + constraint + '/>'
                    xml = '<value xmlns:p="urn:part">' + original + '</value>'
                    if location == 'local-element':
                        declaration = '<xs:element name="value"><xs:complexType><xs:sequence>' \
                            '<xs:element name="item" type="Value" ' + constraint + '/>' \
                            '</xs:sequence></xs:complexType></xs:element>'
                        xml = '<value xmlns:p="urn:part"><item>' + original + '</item></value>'
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
                        declaration = global_attribute + '<xs:element name="value"><xs:complexType>' \
                            + use + '</xs:complexType></xs:element>'
                        xml = '<value xmlns:p="urn:part" item="' + original + '"/>'
                    models.append({'name': f'{name}/{kind}/{location}/{valid}', 'valid': valid,
                                   'schema': f'<xs:schema xmlns:xs="{XSD}" xmlns:p="urn:part">'
                                   + definitions + restriction + declaration + '</xs:schema>', 'xml': xml})
    # A string selected before a numeric union member must keep its spelling.
    # QName text must keep its declaration context, including inside lists.
    for name, definition, value in [
        ('string-first', '<xs:union memberTypes="xs:string xs:boolean"/>', '1'),
        ('QName', '<xs:restriction base="xs:QName"/>', 'p:Part'),
        ('QName-list', '<xs:list itemType="xs:QName"/>', 'p:Part p:Other'),
        ('empty-list', '<xs:list itemType="xs:int"/>', ''),
    ]:
        for kind in ['default', 'fixed']:
            models.append({'name': f'control/{name}/{kind}', 'valid': True,
                           'schema': f'<xs:schema xmlns:xs="{XSD}" xmlns:p="urn:part">'
                           '<xs:simpleType name="Value">' + definition + '</xs:simpleType>'
                           '<xs:element name="value" type="Value" ' + kind + '="' + value + '"/></xs:schema>',
                           'xml': '<value xmlns:p="urn:part">' + value + '</value>'})
    return models


class NumericDefaultsTest(unittest.TestCase):
    def test_declarations_against_xerces(self):
        models = fixtures()
        self.assertEqual(396, len(models))
        self.assertEqual(models, json.loads(FIXTURE.read_text()))
        result = run([SchemaJob(m['name'], f'http://example.invalid/numeric-defaults/{i}.xsd',
                               m['schema'].encode(), {m['name']: m['xml'].encode()})
                      for i, m in enumerate(models)])
        self.assertEqual({m['name'] for m in models}, set(result['schemas']))
        for model in models:
            with self.subTest(name=model['name']):
                row = result['schemas'][model['name']]
                self.assertEqual(model['valid'], row['ok'], row)
                self.assertEqual([], row['warnings'])
                row = result['documents'][model['name']]
                self.assertEqual(True if model['valid'] else None, row['ok'], row)
                self.assertEqual([], row['warnings'])


if __name__ == '__main__':
    unittest.main()
