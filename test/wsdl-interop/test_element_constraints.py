#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
"""Element default/fixed declaration validity with independent schema compilation."""
from pathlib import Path
import tempfile
import unittest
from xml.sax.saxutils import quoteattr

from independent import SchemaJob, run as independent
import survey
from test_attribute_values import description, NS, XSD


def models():
    scalars = {
        'int': [('17', True), ('', False), ('17tail', False)],
        'byte': [('127', True), ('128', False)],
        'unsignedByte': [('255', True), ('256', False), ('-1', False)],
        'decimal': [('17.000', True), ('1e2', False)],
        'boolean': [('1', True), ('false', True), ('TRUE', False)],
        'date': [('2026-02-28', True), ('2026-02-30', False)],
        'duration': [('PT1S', True), ('PT', False)],
        'hexBinary': [('0A', True), ('A', False)],
        'base64Binary': [('AA==', True), ('AB==', False)],
        'NMTOKENS': [(' one  two ', True), ('', False)],
        'QName': [('p:Item', True), ('missing:Item', False)],
        'string': [('', True), ('  shipment  ', True)],
        'anySimpleType': [('', True), ('text', True)],
        'anyType': [('', True), ('text', True)],
        'ENTITY': [('logo', True)],
        'ID': [('identifier', False)],
    }
    declarations = ('<xs:simpleType name="Small"><xs:restriction base="xs:int">'
                    '<xs:minInclusive value="1"/><xs:maxInclusive value="3"/>'
                    '</xs:restriction></xs:simpleType>'
                    '<xs:simpleType name="Codes"><xs:list itemType="t:Small"/></xs:simpleType>'
                    '<xs:simpleType name="Choice"><xs:union memberTypes="t:Small xs:boolean"/></xs:simpleType>')
    simple = [(name, f'type="xs:{name}"', lexical, valid, '')
              for name, values in scalars.items() for lexical, valid in values]
    simple += [(name, f'type="t:{name}"', lexical, valid, declarations)
               for name, values in {'Small': [('2', True), ('0', False)],
                                    'Codes': [('1 3', True), ('1 4', False)],
                                    'Choice': [('false', True), ('4', False)]}.items()
               for lexical, valid in values]
    complex_models = [
        ('empty', '<xs:complexType/>', False),
        ('empty-sequence', '<xs:complexType><xs:sequence/></xs:complexType>', False),
        ('element-only', '<xs:complexType><xs:sequence><xs:element name="child" minOccurs="0"/>'
         '</xs:sequence></xs:complexType>', False),
        ('mixed-required', '<xs:complexType mixed="true"><xs:sequence><xs:element name="child"/>'
         '</xs:sequence></xs:complexType>', False),
        ('mixed-empty', '<xs:complexType mixed="true"/>', True),
        ('mixed-optional', '<xs:complexType mixed="true"><xs:sequence><xs:element name="child" minOccurs="0"/>'
         '</xs:sequence></xs:complexType>', True),
        ('mixed-choice', '<xs:complexType mixed="true"><xs:choice><xs:element name="first"/>'
         '<xs:sequence><xs:element name="optional" minOccurs="0"/></xs:sequence>'
         '</xs:choice></xs:complexType>', True),
        ('simple-required-attribute', '<xs:complexType><xs:simpleContent><xs:extension base="xs:string">'
         '<xs:attribute name="tag" use="required"/></xs:extension></xs:simpleContent></xs:complexType>', True),
    ]
    for local in (False, True):
        for kind in ('default', 'fixed'):
            cases = [(f'{name}/{index}', f'<xs:element name="value" {datatype} xmlns:p="urn:catalog" '
                      f'{kind}={quoteattr(lexical)}/>', valid, dependencies)
                     for index, (name, datatype, lexical, valid, dependencies) in enumerate(simple)]
            cases += [(name, f'<xs:element name="value" {kind}="text">{body}</xs:element>', valid, '')
                      for name, body, valid in complex_models]
            for name, element, valid, dependencies in cases:
                if local:
                    element = '<xs:complexType name="Container"><xs:sequence>' + element + '</xs:sequence></xs:complexType>'
                schema = (f'<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">'
                          + element + dependencies + '<xs:element name="Submit" type="xs:string"/>'
                          '<xs:element name="Reply" type="xs:string"/></xs:schema>')
                yield {'name': f'{"local" if local else "global"}/{kind}/{name}', 'schema': schema, 'valid': valid}


class ElementConstraintTest(unittest.TestCase):
    def test_schema_declarations_and_both_bindings(self):
        fixtures = list(models())
        expected = {model['name']: model['valid'] for model in fixtures}
        self.assertEqual(len(fixtures), len(expected))
        jobs = [SchemaJob(model['name'], f'http://example.invalid/element-constraints/{index}.xsd',
                          model['schema'].encode()) for index, model in enumerate(fixtures)]
        oracle = independent(jobs)
        self.assertEqual(set(expected), set(oracle['schemas']))
        for name, result in oracle['schemas'].items():
            with self.subTest(oracle=name):
                self.assertEqual(expected[name], result['ok'], result)
                self.assertEqual([], result['warnings'])
        with tempfile.TemporaryDirectory(prefix='wsdl-element-constraints-') as folder:
            cases = []
            for index, model in enumerate(fixtures):
                for version in ('11', '12'):
                    path = Path(folder) / f'{index}-{version}.wsdl'
                    path.write_text(description(version, model['schema']))
                    cases.append({'name': model['name'] + '/' + version, 'wsdl': str(path),
                                  'base': 'http://example.invalid/element-constraints/', 'operation': 'submit',
                                  'binding': 'Soap' + version, 'messages': []})
            rows = survey.run_worker(cases, {})
        self.assertEqual(len(cases), len(rows))
        self.assertEqual({case['name'] for case in cases}, {row['case'] for row in rows})
        for row in rows:
            with self.subTest(wsdl=row['case']):
                self.assertEqual('parse', row['stage'])
                self.assertEqual(expected[row['case'].rsplit('/', 1)[0]], row['ok'], row)
                if not row['ok']:
                    self.assertEqual('WSDL-ERROR', row['err'])
        print(f'{len(fixtures)} schemas, {len(cases)} real SOAP binding descriptions: declaration validity agrees')


if __name__ == '__main__':
    unittest.main()
