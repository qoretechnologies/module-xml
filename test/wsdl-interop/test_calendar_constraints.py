#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
"""Calendar declaration fixtures and explicit pinned-oracle differences."""
from html import escape
import json
from pathlib import Path
import unittest
from independent import SchemaJob, run
from calendar_reference import value as date_value
from temporal_reference import value as clock_value
from test_numeric_defaults import pattern
XSD = 'http://www.w3.org/2001/XMLSchema'
def quote(text):
    return escape(text, quote=True).replace('\t', '&#9;').replace('\n', '&#10;').replace('\r', '&#13;')

def fixtures():
    atoms = [
        ('dateTime-zone', 'dateTime', '2000-01-01T00:00:00.100+01:00', '1999-12-31T23:00:00.1Z'),
        ('dateTime-midnight', 'dateTime', '-0001-12-31T24:00:00Z', '0001-01-01T00:00:00Z'),
        ('dateTime-precision', 'dateTime', '2000-01-01T00:00:00.123456789012345678900Z',
         '2000-01-01T00:00:00.1234567890123456789Z'),
        ('time-zone', 'time', '00:00:00.100+01:00', '23:00:00.1Z'),
        ('time-midnight', 'time', '24:00:00', '00:00:00'),
        ('time-precision', 'time', '00:00:00.123456789012345678900', '00:00:00.1234567890123456789'),
        ('date-positive', 'date', '2002-10-10+13:00', '2002-10-09-11:00'),
        ('date-negative', 'date', '2002-10-10-14:00', '2002-10-11+10:00')]
    values = [(name, '', 'xs:' + builtin, source, canonical) for name, builtin, source, canonical in atoms]
    values += [('time-list', '<xs:simpleType name="List"><xs:list itemType="xs:time"/></xs:simpleType>',
                'List', '24:00:00 01:30:00+01:00', '00:00:00 00:30:00Z'),
               ('mixed-list', '<xs:simpleType name="Item"><xs:union memberTypes="xs:time xs:QName"/></xs:simpleType>'
                '<xs:simpleType name="List"><xs:list itemType="Item"/></xs:simpleType>',
                'List', '24:00:00 p:Part 01:30:00+01:00', '00:00:00 p:Part 00:30:00Z'),
               ('time-union', '<xs:simpleType name="List"><xs:union memberTypes="xs:time xs:string"/></xs:simpleType>',
                'List', '24:00:00', '00:00:00'),
               ('dateTime-union', '<xs:simpleType name="List"><xs:union memberTypes="xs:dateTime xs:string"/></xs:simpleType>',
                'List', '2000-01-01T24:00:00', '2000-01-02T00:00:00')]
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
                                   'oracle_valid': valid and name not in {'dateTime-precision', 'time-precision',
                                       'date-positive', 'date-negative'},
                                   'oracle_reason': ('Xerces truncates fractional seconds to binary64 precision'
                                       if name.endswith('-precision') else 'Xerces omits the recoverable date timezone'
                                       if name in {'date-positive', 'date-negative'} else None)})
    for name, definition, source in [
        ('empty-list', '<xs:list itemType="xs:time"/>', ''),
        ('singleton-list', '<xs:list itemType="xs:time"/>', '24:00:00'),
        ('string-first', '<xs:union memberTypes="xs:string xs:time"/>', '24:00:00'),
        ('duration', '<xs:restriction base="xs:duration"/>', 'P1Y12M'),
        ('gYear', '<xs:restriction base="xs:gYear"/>', '2000+01:00'),
        ('gYearMonth', '<xs:restriction base="xs:gYearMonth"/>', '2000-02+01:00'),
        ('gMonth', '<xs:restriction base="xs:gMonth"/>', '--02+01:00'),
        ('gMonthDay', '<xs:restriction base="xs:gMonthDay"/>', '--02-29+01:00'),
        ('gDay', '<xs:restriction base="xs:gDay"/>', '---01+01:00'),
    ]:
        for kind in ['default', 'fixed']:
            models.append({'name': 'control/' + name + '/' + kind, 'valid': True, 'oracle_valid': True,
                           'oracle_reason': None,
                           'schema': '<xs:schema xmlns:xs="' + XSD + '"><xs:simpleType name="Value">'
                           + definition + '</xs:simpleType><xs:element name="value" type="Value" '
                           + kind + '="' + quote(source) + '"/></xs:schema>',
                           'xml': '<value>' + source + '</value>'})
    for model in models:
        model['oracle_document_valid'] = oracle_document_valid(model, model['xml'])
        model['oracle_document_reason'] = ('Xerces retains the next-day anchor for lexical midnight'
            if model['oracle_document_valid'] is False and '24:00:00' in model['xml']
            else 'Xerces changes the fixed partial-calendar value while canonicalizing its declaration'
            if model['oracle_document_valid'] is False else None)
    return models

def oracle_document_valid(model, xml):
    if not model['oracle_valid']:
        return None
    name = model['name']
    if '/fixed/' in name or name.endswith('/fixed'):
        if name.startswith(('time-midnight/', 'time-list/', 'mixed-list/', 'time-union/', 'control/singleton-list/')):
            return '24:00:00' not in xml
        if name.startswith(('control/gYear/', 'control/gYearMonth/', 'control/gMonth/',
                            'control/gMonthDay/', 'control/gDay/')):
            return False
    return True


def boundaries():
    rows = [
        ('dateTime', '2000-03-01T00:15:02.030+01:00', '2000-02-29T23:15:02.03Z'),
        ('dateTime', '1900-03-01T00:15:02.030+01:00', '1900-02-28T23:15:02.03Z'),
        ('dateTime', '0001-01-01T00:00:00+14:00', '-0001-12-31T10:00:00Z'),
        ('dateTime', '-0001-12-31T23:59:59-00:01', '0001-01-01T00:00:59Z'),
        ('dateTime', '2000-01-01T00:00:00.0000', '2000-01-01T00:00:00'),
        ('dateTime', '2000-03-31T23:59:60+00:00', '2000-03-31T23:59:60Z'),
        ('dateTime', '2000-01-01T00:00:00.100-00:00', '2000-01-01T00:00:00.1Z'),
        ('date', '2000-01-01-12:00', '2000-01-02+12:00'),
        ('date', '2000-01-01+12:01', '1999-12-31-11:59'),
        ('date', '2000-03-01+14:00', '2000-02-29-10:00'),
        ('date', '9999-12-31-14:00', '10000-01-01+10:00'),
        ('date', '-0001-12-31-12:00', '0001-01-01+12:00'),
        ('date', '2000-01-01-00:00', '2000-01-01Z'),
        ('time', '00:00:00-00:01', '00:01:00Z'),
        ('time', '23:59:59.99999999999999999900-00:01', '00:00:59.999999999999999999Z'),
        ('time', '00:00:00.0000', '00:00:00'),
        ('dateTime', '9' * 1000 + '-12-31T24:00:00', '1' + '0' * 1000 + '-01-01T00:00:00'),
        ('date', '-' + '9' * 1000 + '-01-01+14:00', '-1' + '0' * 1000 + '-12-31-10:00'),
    ]
    return [dict(builtin=builtin, source=source, canonical=canonical) for builtin, source, canonical in rows]


FIXTURE = Path(__file__).parent / 'fixtures/calendar-constraints.json'

class CalendarConstraintsTest(unittest.TestCase):
    def test_boundary_values_with_exact_ordinal_reference(self):
        rows = boundaries()
        self.assertEqual(18, len(rows))
        self.assertEqual(rows, json.loads(FIXTURE.with_name('calendar-constraint-boundaries.json').read_text()))
        for row in rows:
            reference = date_value if row['builtin'] == 'date' else clock_value
            self.assertNotEqual(row['source'], row['canonical'])
            self.assertEqual(reference(row['builtin'], row['source']), reference(row['builtin'], row['canonical']), row)

    def test_declarations_against_xerces(self):
        models = fixtures()
        self.assertEqual(306, len(models))
        self.assertEqual(models, json.loads(FIXTURE.read_text()))
        result = run([SchemaJob(m['name'], f'http://example.invalid/calendar-constraints/{i}.xsd',
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
                self.assertEqual(model['oracle_document_valid'], row['ok'], row)
                self.assertEqual([], row['warnings'])
        self.assertEqual(48, len(differences))
        self.assertEqual(30, sum(m['oracle_document_valid'] is False for m in models))

if __name__ == '__main__':
    unittest.main()
