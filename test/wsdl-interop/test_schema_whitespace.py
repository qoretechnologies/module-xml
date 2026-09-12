#!/usr/bin/env python3
"""Schema declaration whitespace, with native libxml2, lxml and pinned Xerces.

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


def models():
    templates = {
        'complex': '<xs:complexType name="Value">TOKEN</xs:complexType>',
        'sequence': '<xs:complexType name="Value"><xs:sequence>TOKEN</xs:sequence></xs:complexType>',
        'element': '<xs:element name="value" type="xs:string">TOKEN</xs:element>',
        'restriction': '<xs:simpleType name="Value"><xs:restriction base="xs:string">TOKEN</xs:restriction></xs:simpleType>',
        'facet': '<xs:simpleType name="Value"><xs:restriction base="xs:string"><xs:length value="3">TOKEN</xs:length></xs:restriction></xs:simpleType>',
        'schema': 'TOKEN',
    }
    result = []
    for index, token in enumerate((' \t\r\n ', '<![CDATA[ \t\n]]>', '&#32;&#9;&#13;&#10;',
                                   ' <!-- comment --> ', 'unexpected', '&#160;',
                                   '<![CDATA[unexpected]]>', ' \n x \t ')):
        for kind, template in templates.items():
            valid = index < 4
            result.append({'name': f'{kind}-{index}', 'valid': valid,
                           'error': '' if valid else ('XSD-SIMPLETYPE-ERROR' if kind in ('restriction', 'facet')
                                                    else 'WSDL-ERROR'),
                           'schema': '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                           + template.replace('TOKEN', token) + '</xs:schema>'})
    return result + [{**case, 'name': case['name'] + '-preserve',
                       'schema': case['schema'].replace('<xs:schema ', '<xs:schema xml:space="preserve" ', 1)}
                     for case in result]


class SchemaWhitespaceTest(unittest.TestCase):
    def test_declaration_text_against_independent_schema_compilers(self):
        cases = models()
        self.assertEqual(96, len(cases))
        jobs = []
        for case in cases:
            if case['valid']:
                etree.XMLSchema(etree.fromstring(case['schema'].encode()))
            else:
                with self.assertRaises(etree.XMLSchemaParseError, msg=case['name']):
                    etree.XMLSchema(etree.fromstring(case['schema'].encode()))
            jobs.append(SchemaJob(case['name'], f"http://example.invalid/{case['name']}.xsd",
                                  case['schema'].encode()))
        oracle = run_independent(jobs)
        self.assertEqual({c['name'] for c in cases}, set(oracle['schemas']))
        self.assertEqual({}, oracle['documents'])
        for case in cases:
            result = oracle['schemas'][case['name']]
            self.assertEqual(case['valid'], result['ok'], (case['name'], result))
            self.assertEqual([], result['warnings'], result)
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        self.assertIn(mode, ('ast', 'ir', 'jit', 'tiered'))
        worker = os.environ.get('WSDL_SCHEMA_WHITESPACE_WORKER', str(Path(__file__).with_name('schema-whitespace.qr')))
        with tempfile.TemporaryDirectory(prefix='wsdl-schema-whitespace-') as temporary:
            path = Path(temporary) / 'cases.json'
            path.write_text(json.dumps(cases), encoding='utf-8')
            result = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode, worker, str(path)],
                                    capture_output=True, text=True, timeout=60)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout[-2000:])
        self.assertEqual('', result.stderr)
        rows = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual([c['name'] for c in cases], [r['name'] for r in rows])
        for case, row in zip(cases, rows):
            self.assertEqual(case['error'], row['error'], row)
            self.assertEqual('' if case['valid'] else 'XSD-SYNTAX-ERROR', row['native_error'], row)
            self.assertEqual(int(case['valid']), row['copies'], row)
        print(f'{mode}: 96 schemas, four compiler verdicts per schema', flush=True)


if __name__ == '__main__':
    unittest.main()
