#!/usr/bin/env python3
"""Canonical actual-type defaults and declaration-scoped expanded names.

Copyright (C) 2026 Qore Technologies, s.r.o.
The PSVI interpretation was explicitly approved on 2026-09-13; independent
validator disagreements remain recorded, not substituted for expected values.
"""
from html import escape
import json
import os
from pathlib import Path
import subprocess
import unittest

from test_numeric_defaults import pattern
from independent import SchemaJob, run

XSD = 'http://www.w3.org/2001/XMLSchema'
XSI = 'http://www.w3.org/2001/XMLSchema-instance'
FIXTURE = Path(__file__).parent / 'fixtures/element-defaults.json'


def fixtures():
    models = []
    atoms = [('boolean', '1', 'true'), ('int', '+017', '17'), ('decimal', '+0017.2300', '17.23'),
             ('hexBinary', 'ab', 'AB'), ('base64Binary', 'YQ== ', 'YQ=='), ('float', '1.50', '1.5E0'),
             ('double', '1.50', '1.5E0'), ('dateTime', '2000-01-01T00:00:00.100+01:00',
                                      '1999-12-31T23:00:00.1Z'),
             ('time', '24:00:00', '00:00:00'), ('date', '2002-10-10+13:00', '2002-10-09-11:00')]
    for builtin, source, canonical in atoms:
        for kind in ('default', 'fixed'):
            for actual in ('source', 'canonical'):
                name = '/'.join((builtin, kind, actual))
                facet = pattern(source if actual == 'source' and builtin != 'base64Binary' else canonical)
                schema = (f'<xs:schema xmlns:xs="{XSD}"><xs:simpleType name="Actual">'
                          f'<xs:restriction base="xs:{builtin}"><xs:pattern value="{escape(facet, quote=True)}"/>'
                          f'</xs:restriction></xs:simpleType><xs:element name="value" type="xs:{builtin}" '
                          f'nillable="true" {kind}="{escape(source, quote=True)}"/></xs:schema>')
                docs = []
                for label, content in [('empty', ''), ('comment', '<!--empty-->'), ('cdata', '<![CDATA[]]>'),
                                       ('source', escape(source)), ('canonical', escape(canonical))]:
                    expected = actual == ('source' if label == 'source' else 'canonical')
                    if builtin == 'base64Binary':
                        expected = True  # A whitespace-collapse control, not a distinguishing pattern.
                    docs.append({'name': name + '/' + label, 'xml': f'<value xmlns:xsi="{XSI}" '
                                 f'xsi:type="Actual">{content}</value>', 'expected': expected})
                models.append(dict(name=name, schema=schema, documents=docs, wsdl=True))
    # The canonical boolean spelling is assessed as the explicitly selected type.
    # An IDC makes string/QName/boolean identity observable without a self-round-trip.
    for actual in ('string', 'QName'):
        schema = (f'<xs:schema xmlns:xs="{XSD}"><xs:simpleType name="Base">'
                  f'<xs:union memberTypes="xs:boolean xs:{actual}"/></xs:simpleType>'
                  '<xs:element name="value"><xs:complexType><xs:sequence>'
                  '<xs:element name="item" type="Base" default="1" maxOccurs="unbounded"/>'
                  '</xs:sequence></xs:complexType><xs:unique name="key">'
                  '<xs:selector xpath="item"/><xs:field xpath="."/></xs:unique></xs:element></xs:schema>')
        docs = []
        for kind, lexical in [(actual, 'true'), ('boolean', 'true'), *([('string', '1')] if actual == 'string' else [])]:
            docs.append(dict(name=f'identity/{actual}/{kind}/{lexical}', expected=kind != actual or lexical != 'true',
                             xml=f'<value xmlns:xs="{XSD}" xmlns:xsi="{XSI}"><item xsi:type="xs:{actual}"/>'
                             f'<item xsi:type="xs:{kind}">{lexical}</item></value>'))
        docs.append(dict(name=f'identity/{actual}/alone', expected=True,
                         xml=f'<value xmlns:xs="{XSD}" xmlns:xsi="{XSI}"><item xsi:type="xs:{actual}"/></value>'))
        models.append(dict(name='identity/' + actual, schema=schema, documents=docs, wsdl=False))
    for name, declaration_ns, lexical, equal, different in [
        ('prefix', 'xmlns:p="urn:part"', 'p:item', 'q:item', 'p:item'),
        ('default-namespace', 'xmlns="urn:part"', 'item', 'q:item', 'item'),
        ('no-namespace', 'xmlns=""', 'item', 'item', 'q:item'),
        ('implicit-xml', '', 'xml:lang', 'xml:lang', 'p:lang'),
    ]:
        for kind in ('default', 'fixed'):
            for collection in ('atomic', 'list', 'mixed-list'):
                definitions = '<xs:simpleType name="Member"><xs:union memberTypes="xs:int xs:QName"/></xs:simpleType>'
                definitions += '<xs:simpleType name="Items"><xs:list itemType="' \
                    + ('Member' if collection == 'mixed-list' else 'xs:QName') + '"/></xs:simpleType>'
                typ = 'xs:QName' if collection == 'atomic' else 'Items'
                if collection == 'list':
                    source, same, other = lexical + ' xml:lang', equal + ' xml:lang', different + ' xml:lang'
                elif collection == 'mixed-list':
                    source, same, other = '+017 ' + lexical, '17 ' + equal, '17 ' + different
                else:
                    source, same, other = lexical, equal, different
                item_type = ('<xs:simpleType><xs:list><xs:simpleType><xs:union '
                             'memberTypes="xs:int xs:QName"/></xs:simpleType></xs:list></xs:simpleType>'
                             if collection == 'mixed-list' else '<xs:simpleType><xs:list '
                             'itemType="xs:QName"/></xs:simpleType>' if collection == 'list' else '')
                item = (f'<xs:element name="item" {kind}="{source}" {declaration_ns}'
                        + ('>' + item_type + '</xs:element>' if item_type else ' type="xs:QName"/>'))
                schema = (f'<xs:schema xmlns:xs="{XSD}">{definitions}<xs:element name="value">'
                          '<xs:complexType><xs:sequence>'
                          f'{item}'
                          f'<xs:element name="peer" type="{typ}"/></xs:sequence></xs:complexType>'
                          '<xs:unique name="key"><xs:selector xpath="item|peer"/><xs:field xpath="."/>'
                          '</xs:unique></xs:element></xs:schema>')
                docs = []
                for label, peer, expected in [('same', same, False), ('different', other, True)]:
                    docs.append(dict(name=f'namespace/{name}/{kind}/{collection}/{label}', expected=expected,
                                     xml=f'<value xmlns:p="urn:shadow" xmlns:q="urn:part"><item/>'
                                     f'<peer>{peer}</peer></value>'))
                models.append(dict(name=f'namespace/{name}/{kind}/{collection}', schema=schema,
                                   documents=docs, wsdl=False))
    for kind in ('default', 'fixed'):
        schema = (f'<xs:schema xmlns:xs="{XSD}" targetNamespace="urn:part" xmlns:t="urn:part">'
                  '<xs:notation name="item" public="urn:item"/>'
                  '<xs:simpleType name="Name"><xs:restriction base="xs:NOTATION">'
                  '<xs:enumeration value="t:item"/></xs:restriction></xs:simpleType>'
                  f'<xs:element name="value" type="t:Name" {kind}="item" xmlns="urn:part"/></xs:schema>')
        docs = []
        for label, lexical, expected in [('empty', '', True), ('same', 't:item', True),
                                         ('no-namespace', 'item', False), ('shadow', 'p:item', False)]:
            docs.append(dict(name=f'notation/{kind}/{label}', expected=expected,
                             xml=f'<t:value xmlns:t="urn:part" xmlns:p="urn:shadow">{lexical}</t:value>'))
        models.append(dict(name='notation/' + kind, schema=schema, documents=docs, wsdl=False))
    return models


class ElementDefaultsTest(unittest.TestCase):
    def test_fixture_reproducibility(self):
        self.assertEqual(fixtures(), json.loads(FIXTURE.read_text()))

    def test_native_verdicts_and_original_input(self):
        completed = subprocess.run([os.environ.get('QORE', 'qore'), '-b', '--enable-debug',
                                    str(Path(__file__).parent / 'character-content.qr'), str(FIXTURE)],
                                   text=True, capture_output=True, timeout=120)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual('', completed.stderr)
        rows = {row['name']: row for row in map(json.loads, completed.stdout.splitlines())}
        documents = [d for m in fixtures() for d in m['documents']]
        self.assertEqual(len(documents), len(rows))
        for document in documents:
            row = rows[document['name']]
            for path, error in [('dom', 'PARSE-XML-EXCEPTION'), ('reader', 'PARSE-XML-EXCEPTION'),
                                ('document', 'XSD-ERROR')]:
                with self.subTest(name=document['name'], path=path):
                    self.assertEqual(document['expected'], row[path], row)
                    if document['expected'] and path != 'reader':
                        self.assertTrue(row[path + '_preserved'])
                    elif not document['expected']:
                        self.assertEqual(error, row.get(path + '_error'))

    def test_pinned_xerces_and_explicit_disagreements(self):
        models = fixtures()
        result = run([SchemaJob(m['name'], f'http://example.invalid/element-defaults/{i}.xsd',
                                m['schema'].encode(), {d['name']: d['xml'].encode() for d in m['documents']})
                      for i, m in enumerate(models)])
        known = {'time/fixed/source/source': False, 'date/fixed/source/source': False,
                 'date/fixed/canonical/canonical': False,
                 'identity/string/string/true': True, 'identity/string/boolean/true': False,
                 'identity/QName/QName/true': True, 'identity/QName/boolean/true': False,
                 # Xerces reassesses these unprefixed NOTATION defaults in the
                 # instance's empty default namespace, losing the declaration URI.
                 'notation/default/empty': False, 'notation/fixed/empty': False}
        for kind in ('default', 'fixed'):
            for label in ('empty', 'comment', 'cdata'):
                known[f'date/{kind}/canonical/{label}'] = False
        seen = set()
        for model in models:
            self.assertTrue(result['schemas'][model['name']]['ok'], model['name'])
            self.assertEqual([], result['schemas'][model['name']]['warnings'])
            for document in model['documents']:
                with self.subTest(name=document['name']):
                    row = result['documents'][document['name']]
                    expected = known.get(document['name'], document['expected'])
                    self.assertEqual(expected, row['ok'], row)
                    self.assertEqual([], row['warnings'])
                    if document['name'] in known:
                        self.assertNotEqual(document['expected'], expected)
                        seen.add(document['name'])
        self.assertEqual(set(known), seen)


if __name__ == '__main__':
    unittest.main()
