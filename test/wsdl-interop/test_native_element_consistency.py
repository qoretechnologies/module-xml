#!/usr/bin/env python3
"""Independent explicit/implicit XSD declaration consistency checks.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from lxml import etree
from independent import SchemaJob, run as run_independent

URI = 'urn:edc'


def fixture(name, definitions, content, valid, children='', unused=False):
    if unused:
        definitions += f'<xs:group name="Unused">{content}</xs:group>'
        content = '<xs:sequence/>'
        children = ''
    schema = ('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:t="urn:edc" targetNamespace="urn:edc">'
              + definitions + '<xs:element name="root"><xs:complexType>' + content
              + '</xs:complexType></xs:element></xs:schema>')
    return {'name': name, 'schema': schema, 'valid': valid, 'unused': unused, 'uri': URI,
            'document': f'<t:root xmlns:t="{URI}">{children}</t:root>'}


def definitions():
    for first in ('xs:int', 'xs:decimal', 't:Named'):
        for second in ('xs:int', 'xs:decimal', 't:Named'):
            for unused in (False, True):
                yield fixture(f'explicit/{first}/{second}/{unused}',
                    '<xs:simpleType name="Named"><xs:restriction base="xs:int"/></xs:simpleType>',
                    f'<xs:sequence><xs:element name="x" type="{first}"/><xs:element name="x" type="{second}"/></xs:sequence>',
                    first == second, '<x>17</x><x>18</x>', unused)
    for block in ('', 'extension', 'restriction', 'substitution', '#all'):
        for qualified in (False, True):
            for unused in (False, True):
                declarations = (f'<xs:element name="head" type="xs:decimal" block="{block}"/>'
                    '<xs:element name="middle" type="xs:decimal" abstract="true" substitutionGroup="t:head"/>'
                    '<xs:element name="member" type="xs:int" substitutionGroup="t:middle"/>')
                content = ('<xs:sequence><xs:element ref="t:head"/><xs:element name="member" type="xs:string" form="'
                           + ('qualified' if qualified else 'unqualified') + '"/></xs:sequence>')
                prefix = 't:' if qualified else ''
                yield fixture(f'implicit/{block}/{qualified}/{unused}', declarations, content,
                    not qualified or block not in ('', 'extension'),
                    f'<t:head>17</t:head><{prefix}member>text</{prefix}member>', unused)
    anonymous = '<xs:simpleType><xs:restriction base="xs:int"/></xs:simpleType>'
    yield fixture('anonymous-conflict', '', '<xs:sequence><xs:element name="x">' + anonymous
                  + '</xs:element><xs:element name="x">' + anonymous + '</xs:element></xs:sequence>', False)
    yield fixture('anonymous-identity', '<xs:element name="x">' + anonymous + '</xs:element>',
                  '<xs:sequence><xs:element ref="t:x"/><xs:element ref="t:x"/></xs:sequence>', True,
                  '<t:x>17</t:x><t:x>18</t:x>')
    yield fixture('zero-count', '', '<xs:sequence><xs:element name="x" type="xs:int"/>'
                  '<xs:element name="x" type="xs:string" minOccurs="0" maxOccurs="0"/></xs:sequence>', True, '<x>17</x>')
    yield fixture('nested-scope', '', '<xs:sequence><xs:element name="x" type="xs:int"/>'
                  '<xs:element name="child"><xs:complexType><xs:sequence><xs:element name="x" type="xs:string"/>'
                  '</xs:sequence></xs:complexType></xs:element></xs:sequence>', True, '<x>17</x><child><x>text</x></child>')
    yield fixture('nested-conflict', '', '<xs:sequence><xs:element name="child"><xs:complexType><xs:sequence>'
                  '<xs:element name="x" type="xs:int"/><xs:element name="x" type="xs:string"/>'
                  '</xs:sequence></xs:complexType></xs:element></xs:sequence>', False)


class ElementConsistencyTest(unittest.TestCase):
    def test_explicit_implicit_scopes_and_preserved_values(self):
        cases = list(definitions())
        self.assertEqual(43, len(cases))
        self.assertEqual(25, sum(case['valid'] for case in cases))
        self.assertEqual(len(cases), len({case['name'] for case in cases}))
        oracle = run_independent([SchemaJob(c['name'], f'http://example.invalid/edc/{index}.xsd', c['schema'].encode(),
            {c['name']: c['document'].encode()} if c['valid'] else {}) for index, c in enumerate(cases)])
        for case in cases:
            # libxml2 omits EDC; Xerces omits independent checks of unused groups.
            validator = etree.XMLSchema(etree.fromstring(case['schema'].encode()))
            result = oracle['schemas'][case['name']]
            self.assertEqual(case['valid'] or case['unused'], result['ok'], (case, result))
            self.assertEqual([], result['warnings'])
            if case['valid']:
                self.assertTrue(validator.validate(etree.fromstring(case['document'].encode())))
                self.assertTrue(oracle['documents'][case['name']]['ok'], case)
                self.assertEqual([], oracle['documents'][case['name']]['warnings'])
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        worker = os.environ.get('WSDL_ELEMENT_CONSISTENCY_WORKER', str(Path(__file__).with_name('element-consistency.qr')))
        with tempfile.TemporaryDirectory(prefix='wsdl-element-consistency-') as directory:
            path = Path(directory) / 'cases.json'
            path.write_text(json.dumps(cases))
            process = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode, worker, str(path)],
                capture_output=True, text=True, timeout=120)
        self.assertEqual(0, process.returncode, process.stderr + process.stdout[-4000:])
        self.assertEqual('', process.stderr)
        rows = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(len(cases), len(rows))
        for case, row in zip(cases, rows):
            expected = {'name': case['name'], 'reader_error': '', 'dom_error': '', 'wsdl_error': ''}
            if case['valid']:
                expected.update(reader_valid=True, dom_value_preserved=True, retained_copies=2)
            else:
                expected.update(reader_error='XSD-SYNTAX-ERROR', dom_error='XSD-SYNTAX-ERROR', wsdl_error='WSDL-ERROR')
            self.assertEqual(expected, row)
        print(f'{mode}: 43 schemas, 18 required construction errors per parser, '
              '25 independent documents, 50 retained original/reconstructed values', flush=True)


if __name__ == '__main__':
    unittest.main()
