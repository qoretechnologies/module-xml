#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
"""XSD 1.0 scalar fixed and clock value identity through native XML APIs and pinned Xerces."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from independent import SchemaJob, run as independent

XSD = 'http://www.w3.org/2001/XMLSchema'


def fixed_models():
    # Explicit value equality is independent of the default's lexical spelling.
    families = [
        ('int', 'xs:int', '+0017', '17', '18', ''),
        ('decimal', 'xs:decimal', '-0.00', '0.0', '0.1', ''),
        ('boolean', 'xs:boolean', '1', 'true', 'false', ''),
        ('integer-precision', 'xs:integer', '+0001234567890123456789012345678901234567890',
         '1234567890123456789012345678901234567890', '1234567890123456789012345678901234567891', ''),
        ('decimal-precision', 'xs:decimal', '17.12345678901234567890123456789',
         '+017.123456789012345678901234567890', '17.12345678901234567890123456788', ''),
        ('string', 'xs:string', ' a ', ' a ', 'a', ''),
        ('normalizedString', 'xs:normalizedString', 'a b', 'a\tb', 'a  b', ''),
        ('token', 'xs:token', 'a b', '  a \t b  ', 'a c', ''),
        ('anySimpleType', 'xs:anySimpleType', '17', '17', '18', ''),
        ('anyURI', 'xs:anyURI', 'urn:part', ' urn:part ', 'urn:other', ''),
        ('float', 'xs:float', '+017.0', '1.7E1', '18', ''),
        ('double', 'xs:double', '+017.0', '1.7E1', '18', ''),
        ('float-zero', 'xs:float', '-0', '0', '1', ''),
        ('double-NaN', 'xs:double', 'NaN', 'NaN', 'INF', ''),
        ('double-INF', 'xs:double', 'INF', 'INF', '-INF', ''),
        ('dateTime', 'xs:dateTime', '2026-09-12T12:00:00Z', '2026-09-12T14:00:00+02:00',
         '2026-09-12T14:00:01+02:00', ''),
        ('date', 'xs:date', '2026-09-12Z', '2026-09-12+00:00', '2026-09-13Z', ''),
        ('time', 'xs:time', '12:00:00Z', '14:00:00+02:00', '14:00:01+02:00', ''),
        ('duration', 'xs:duration', 'P1Y', 'P12M', 'P365D', ''),
        ('hexBinary', 'xs:hexBinary', 'aB01', 'Ab01', 'AB02', ''),
        ('base64Binary', 'xs:base64Binary', 'YWI=', 'Y W I =', 'YWM=', ''),
        ('QName', 'xs:QName', 'p:Part', 'q:Part', 'p:Other', ''),
        ('list-empty', 'List', '', ' ', '17', '<xs:simpleType name="List"><xs:list itemType="xs:int"/></xs:simpleType>'),
        ('list-not-empty', 'List', '17', '+017', '', '<xs:simpleType name="List"><xs:list itemType="xs:int"/></xs:simpleType>')]
    for name, type_name, fixed, equivalent, different, types in families:
        for complex_content in (False, True):
            declarations = types
            actual = type_name
            if complex_content:
                declarations += ('<xs:complexType name="Content"><xs:simpleContent><xs:extension base="'
                                 + type_name + '"><xs:attribute name="tag" type="xs:int"/>'
                                 '</xs:extension></xs:simpleContent></xs:complexType>')
                actual = 'Content'
            name_prefix = f'fixed/{name}/{complex_content}'
            schema = (f'<xs:schema xmlns:xs="{XSD}" xmlns:p="urn:declaration">' + declarations
                      + f'<xs:element name="root" type="{actual}" fixed="{fixed}"/></xs:schema>')
            documents = []
            for label, lexical, valid in [('same', fixed, True), ('equivalent', equivalent, True),
                                          ('different', different, different == '')]:
                # An empty element requests its fixed default, independently of its list's length.
                documents.append({'name': name_prefix + '/' + label,
                                  'xml': '<root xmlns:p="urn:declaration" xmlns:q="urn:declaration"'
                                  + (' tag="17"' if complex_content else '') + '>' + lexical + '</root>',
                                  'valid': valid})
            yield {'name': name_prefix, 'schema': schema, 'schema_valid': True, 'documents': documents}


def time_models():
    values = [('00:00:00Z', 0, True), ('24:00:00Z', 0, True),
              ('14:00:00+14:00', 0, True), ('10:00:00-14:00', 0, True),
              ('00:30:00+01:00', 1410, True), ('23:30:00Z', 1410, True),
              ('23:00:00-02:00', 60, True), ('01:00:00Z', 60, True),
              ('12:00:00Z', 720, True), ('14:00:00+02:00', 720, True),
              ('07:00:00-05:00', 720, True), ('12:00:00+00:00', 720, True),
              ('00:00:00', 0, False), ('24:00:00', 0, False), ('12:00:00', 720, False),
              ('12:00:00.123456789Z', (720, '123456789'), True),
              ('14:00:00.123456789+02:00', (720, '123456789'), True)]
    for index, (lexical, point, zoned) in enumerate(values):
        for constraint in ('fixed', 'enumeration'):
            name = f'time-values/{index}/{constraint}'
            if constraint == 'fixed':
                element = f'<xs:element name="root" type="xs:time" fixed="{lexical}"/>'
            else:
                element = ('<xs:element name="root"><xs:simpleType><xs:restriction base="xs:time">'
                           f'<xs:enumeration value="{lexical}"/>'
                           '</xs:restriction></xs:simpleType></xs:element>')
            documents = [{'name': name + '/' + str(i), 'xml': '<root>' + value + '</root>',
                          'valid': point == other_point and zoned == other_zoned}
                         for i, (value, other_point, other_zoned) in enumerate(values)]
            yield {'name': name, 'schema': f'<xs:schema xmlns:xs="{XSD}">' + element + '</xs:schema>',
                   'schema_valid': True, 'documents': documents}


def ordered_time_models():
    for zoned in (False, True):
        threshold = '12:00:00Z' if zoned else '12:00:00'
        for facet in ('minInclusive', 'minExclusive', 'maxInclusive', 'maxExclusive'):
            name = f'time-order/{zoned}/{facet}'
            documents = []
            for index, difference in enumerate((-1, 0, 1)):
                lexical = f'{14 + difference}:00:00+02:00' if zoned else f'{12 + difference}:00:00'
                valid = difference >= 0 if facet == 'minInclusive' else (
                    difference > 0 if facet == 'minExclusive' else (
                    difference <= 0 if facet == 'maxInclusive' else difference < 0))
                documents.append({'name': name + '/' + str(index), 'xml': '<root>' + lexical + '</root>',
                                  'valid': valid})
            schema = (f'<xs:schema xmlns:xs="{XSD}"><xs:element name="root"><xs:simpleType>'
                      '<xs:restriction base="xs:time">'
                      f'<xs:{facet} value="{threshold}"/>'
                      '</xs:restriction></xs:simpleType></xs:element></xs:schema>')
            yield {'name': name, 'schema': schema, 'schema_valid': True, 'documents': documents}


def dynamic_fixed_models():
    # Actual primitive identity matters: a string '1' is not boolean true.
    families = [
        ('anySimple', 'xs:anySimpleType', '17', '',
         [('xs:string', [('17', True), ('18', False)]), ('xs:int', [('17', False), ('18', False)])]),
        ('bool-string', 'Base', '1',
         '<xs:simpleType name="Base"><xs:union memberTypes="xs:boolean xs:string"/></xs:simpleType>',
         [('xs:boolean', [('1', True), ('true', True), ('other', False)]),
          ('xs:string', [('1', False), ('true', False), ('other', False)])]),
        ('bool-integer', 'Base', '1',
         '<xs:simpleType name="Base"><xs:union memberTypes="xs:boolean xs:integer"/></xs:simpleType>',
         [('xs:boolean', [('1', True), ('true', True), ('0', False)]),
          ('xs:integer', [('1', False), ('true', False), ('0', False)])]),
        ('decimal', 'xs:decimal', '17.0', '',
         [('xs:decimal', [('17', True), ('17.00', True), ('18', False)]),
          ('xs:int', [('17', True), ('17.00', False), ('18', False)])]),
        ('token', 'xs:string', ' a ', '',
         [('xs:string', [(' a ', True), ('a', False), ('b', False)]),
          ('xs:token', [(' a ', False), ('a', False), ('b', False)])])]
    for name, base, fixed, declarations, selected in families:
        name = 'dynamic-fixed/' + name
        schema = (f'<xs:schema xmlns:xs="{XSD}">{declarations}'
                  f'<xs:element name="root" type="{base}" fixed="{fixed}"/></xs:schema>')
        documents = [{'name': name + '/' + type_name + '/' + str(index),
                      'xml': f'<root xmlns:xs="{XSD}" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                             f'xsi:type="{type_name}">{value}</root>', 'valid': valid}
                     for type_name, values in selected for index, (value, valid) in enumerate(values)]
        yield {'name': name, 'schema': schema, 'schema_valid': True, 'documents': documents}


class NativeValueSpacesTest(unittest.TestCase):
    def test_value_spaces(self):
        fixtures = list(fixed_models()) + list(time_models()) + list(ordered_time_models()) + list(dynamic_fixed_models())
        self.assertEqual(95, len(fixtures))
        expected = {d['name']: dict(d, schema_valid=model['schema_valid'])
                    for model in fixtures for d in model['documents']}
        self.assertEqual(774, len(expected))
        with tempfile.TemporaryDirectory(prefix='xml-time-values-') as folder:
            manifest = Path(folder) / 'manifest.json'
            manifest.write_text(json.dumps(fixtures))
            worker = Path(__file__).with_name('character-content.qr')
            result = subprocess.run(['qore', '-b', '--enable-debug', str(worker), str(manifest)],
                                    capture_output=True, text=True, timeout=180)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout[-3000:])
        self.assertEqual('', result.stderr)
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(expected), len(rows))
        self.assertEqual(set(expected), {row['name'] for row in rows})
        for row in rows:
            for path, category in (('dom', 'PARSE-XML-EXCEPTION'), ('reader', 'PARSE-XML-EXCEPTION'),
                                   ('document', 'XSD-ERROR')):
                self.assertEqual(expected[row['name']]['valid'], row[path], (path, row))
                if not row[path]:
                    self.assertEqual(category if expected[row['name']]['schema_valid'] else 'XSD-SYNTAX-ERROR',
                                     row[path + '_error'], row)
                elif path != 'reader':
                    self.assertTrue(row[path + '_preserved'], row)
        oracle = independent([SchemaJob(model['name'], f'http://example.invalid/time-values/{index}.xsd',
                              model['schema'].encode(), {d['name']: d['xml'].encode() for d in model['documents']})
                              for index, model in enumerate(fixtures)])
        self.assertEqual({m['name'] for m in fixtures}, set(oracle['schemas']))
        self.assertEqual(set(expected), set(oracle['documents']))
        classification = json.loads(Path(__file__).with_name('xerces-time-midnight.json').read_text())
        known = {row['name']: row for row in classification['rows']}
        self.assertEqual(14, len(known))
        observed = set()
        for model in fixtures:
            self.assertEqual(model['schema_valid'], oracle['schemas'][model['name']]['ok'], model['name'])
            self.assertEqual([], oracle['schemas'][model['name']]['warnings'])
            if model['schema_valid']:
                for doc in model['documents']:
                    if doc['name'] in known:
                        finding = known[doc['name']]
                        self.assertEqual(doc['valid'], finding['normative_valid'], doc['name'])
                        self.assertEqual(finding['xerces_valid'], oracle['documents'][doc['name']]['ok'], doc['name'])
                        self.assertEqual(finding['diagnostic'], oracle['documents'][doc['name']]['desc'], doc['name'])
                        observed.add(doc['name'])
                    else:
                        self.assertEqual(doc['valid'], oracle['documents'][doc['name']]['ok'], doc['name'])
                    self.assertEqual([], oracle['documents'][doc['name']]['warnings'])
        self.assertEqual(set(known), observed)
        print(f'{len(fixtures)} schemas, {len(expected)} documents: native requirements pass; '
              'Xerces agrees except for 14 individually classified midnight defects')


if __name__ == '__main__':
    unittest.main()
