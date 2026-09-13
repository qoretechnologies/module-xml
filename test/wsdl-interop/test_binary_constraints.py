#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
"""Canonical binary constraints and strict XSD Base64 lexical validation."""
import json
from html import escape
from pathlib import Path
import unittest
from independent import SchemaJob, run

XSD = 'http://www.w3.org/2001/XMLSchema'
FIXTURE = Path(__file__).parent / 'fixtures/binary-constraints.json'


def quote(text):
    return escape(text, quote=True).replace('\t', '&#9;').replace('\n', '&#10;').replace('\r', '&#13;')


def fixtures():
    atoms = [('hex', 'hexBinary', 'ab00ff', 'AB00FF'),
             ('base64-full', 'base64Binary', 'Y W J j', 'YWJj'),
             ('base64-one', 'base64Binary', 'Y Q = =', 'YQ=='),
             ('base64-two', 'base64Binary', 'Y W I =', 'YWI=')]
    values = [(name, '', 'xs:' + builtin, source, canonical) for name, builtin, source, canonical in atoms]
    values += [('hex-list', '<xs:simpleType name="List"><xs:list itemType="xs:hexBinary"/></xs:simpleType>',
                'List', 'ab00ff 00aa', 'AB00FF 00AA'),
               ('mixed-list', '<xs:simpleType name="Item"><xs:union memberTypes="xs:hexBinary xs:QName"/></xs:simpleType>'
                '<xs:simpleType name="List"><xs:list itemType="Item"/></xs:simpleType>',
                'List', 'ab00ff p:Part 00aa', 'AB00FF p:Part 00AA'),
               ('hex-union', '<xs:simpleType name="List"><xs:union memberTypes="xs:hexBinary xs:string"/></xs:simpleType>',
                'List', 'ab00ff', 'AB00FF'),
               ('base64-union', '<xs:simpleType name="List"><xs:union memberTypes="xs:base64Binary xs:string"/></xs:simpleType>',
                'List', 'Y W J j', 'YWJj')]
    models = []
    for name, definitions, base, source, canonical in values:
        for valid in [False, True]:
            for kind in ['default', 'fixed']:
                for location in ['element', 'local-element', 'simple-content', 'attribute', 'global-attribute', 'attribute-use']:
                    facet = source + ('|' + canonical if valid else '')
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
                                   + definitions + restriction + declaration + '</xs:schema>', 'xml': xml})
    for name, definition, source in [
        ('empty-hex', '<xs:restriction base="xs:hexBinary"/>', ''),
        ('empty-base64', '<xs:restriction base="xs:base64Binary"/>', ''),
        ('empty-list', '<xs:list itemType="xs:hexBinary"/>', ''),
        ('singleton-list', '<xs:list itemType="xs:hexBinary"/>', 'ab00ff'),
        ('base64-list', '<xs:list itemType="xs:base64Binary"/>', 'YQ== Yg=='),
        ('string-first', '<xs:union memberTypes="xs:string xs:hexBinary"/>', 'ab00ff'),
        ('base64-whitespace', '<xs:restriction base="xs:base64Binary"/>', ' Y\tW\nJ\rj '),
    ]:
        for kind in ['default', 'fixed']:
            models.append({'name': 'control/' + name + '/' + kind, 'valid': True,
                           'schema': '<xs:schema xmlns:xs="' + XSD + '"><xs:simpleType name="Value">'
                           + definition + '</xs:simpleType><xs:element name="value" type="Value" '
                           + kind + '="' + quote(source) + '"/></xs:schema>',
                           'xml': '<value>' + source + '</value>'})
    return models


def instances():
    return [('base64Binary', text, valid) for text, valid in [
        ('YWJj', True), (' Y\tW\nJ\rj ', True), ('YQ==', True), ('YWI=', True), ('', True),
        ('Y W J j', True), ('YW!Jj', False), ('YQ==!', False), ('YWJj\u00a0', False),
        ('YWJj\u2003', False), ('!YWJj', False), ('!!!', False), ('YR==', False),
        ('YWJ=', False), ('YQ=', False), ('YQ===', False), ('YQ==YQ==', False)]] \
        + [('hexBinary', text, valid) for text, valid in [
            ('ab00FF', True), ('', True), ('00ff', True), ('0g', False), ('f', False), ('ab ff', False)]]


class BinaryConstraintsTest(unittest.TestCase):
    def test_declarations_and_lexicals_against_xerces(self):
        models = fixtures()
        self.assertEqual(206, len(models))
        self.assertEqual(models, json.loads(FIXTURE.read_text()))
        self.assertEqual([{'builtin': b, 'lexical': t, 'valid': v} for b, t, v in instances()],
                         json.loads(FIXTURE.with_name('binary-lexicals.json').read_text()))
        jobs = [SchemaJob(m['name'], 'http://example.invalid/binary/' + str(i) + '.xsd', m['schema'].encode(),
                          {m['name']: m['xml'].encode()}) for i, m in enumerate(models)]
        for builtin in ['hexBinary', 'base64Binary']:
            jobs.append(SchemaJob(builtin, 'http://example.invalid/' + builtin + '.xsd',
                                  ('<xs:schema xmlns:xs="' + XSD + '"><xs:element name="value" type="xs:'
                                   + builtin + '"/></xs:schema>').encode(),
                                  {f'{builtin}/{i}': ('<value>' + text + '</value>').encode()
                                   for i, (name, text, valid) in enumerate(instances()) if name == builtin}))
        result = run(jobs)
        self.assertEqual(len(jobs), len(result['schemas']))
        for model in models:
            self.assertEqual(model['valid'], result['schemas'][model['name']]['ok'], model['name'])
            self.assertEqual(True if model['valid'] else None, result['documents'][model['name']]['ok'], model['name'])
        for i, (builtin, text, valid) in enumerate(instances()):
            self.assertEqual(valid, result['documents'][f'{builtin}/{i}']['ok'], (builtin, text))
        self.assertTrue(all(not row['warnings'] for group in ['schemas', 'documents'] for row in result[group].values()))


if __name__ == '__main__':
    unittest.main()
