#!/usr/bin/env python3
"""Independent SOAP binding grammar and explicit schema adjudications.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import hashlib
import json
from pathlib import Path
import unittest

from independent import SchemaJob, run

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / 'regressions/wsdl-soap-grammar'
WSDL = 'http://schemas.xmlsoap.org/wsdl/'


class SoapGrammarTest(unittest.TestCase):
    def test_grammar(self):
        manifest = json.loads((FIXTURES / 'cases.json').read_text())
        rows = manifest['cases']
        self.assertEqual(303, len(rows))
        self.assertEqual(len(rows), len({row['name'] for row in rows}))
        resources = {}
        urls = {}
        self.assertEqual({'soap11.xsd', 'soap12.xsd'},
                         {source['file'] for source in manifest['schemas']})
        for source in manifest['schemas']:
            data = (FIXTURES / source['file']).read_bytes()
            self.assertEqual(source['sha256'], hashlib.sha256(data).hexdigest())
            self.assertEqual(source['size'], len(data))
            resources[source['url']] = data
            urls[source['file']] = source['url']
        core = ROOT / 'regressions/wsdl-grammar'
        core_manifest = json.loads((core / 'cases.json').read_text())
        core_data = (core / core_manifest['schema_file']).read_bytes()
        self.assertEqual(core_manifest['schema_sha256'], hashlib.sha256(core_data).hexdigest())
        resources['urn:wsdl:core'] = core_data
        jobs = []
        for version in ('11', '12'):
            namespace = WSDL + ('soap12/' if version == '12' else 'soap/')
            schema = ('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                      f'<xs:import namespace="{WSDL}" schemaLocation="urn:wsdl:core"/>'
                      f'<xs:import namespace="{namespace}" schemaLocation="{urls["soap" + version + ".xsd"]}"/>'
                      '</xs:schema>').encode()
            jobs.append(SchemaJob('soap' + version, 'urn:soap' + version + ':schema', schema,
                                  {row['name']: row['xml'].encode() for row in rows
                                   if row['name'].startswith(version + '/')}))
        results = run(jobs, resources)
        for result in results['schemas'].values():
            self.assertTrue(result['ok'], result)
            self.assertEqual([], result['warnings'])
        semantic_hints = set()
        published_schema = set()
        for row in rows:
            with self.subTest(case=row['name']):
                result = results['documents'][row['name']]
                self.assertEqual(row['schema_valid'], result['ok'], result)
                self.assertEqual([], result['warnings'])
                if row['valid'] != row['schema_valid']:
                    self.assertTrue(row.get('adjudication'))
                    if row['name'].endswith('/xsi-hint-odd'):
                        self.assertFalse(row['valid'])
                        semantic_hints.add(row['name'])
                    else:
                        self.assertTrue(row['valid'])
                        published_schema.add(row['name'])
                else:
                    self.assertNotIn('adjudication', row)
        contexts = ('binding', 'operation', 'body', 'fault', 'header', 'headerfault', 'address')
        self.assertEqual({version + '/' + kind + '/xsi-hint-odd'
                          for version in ('11', '12') for kind in contexts}, semantic_hints)
        self.assertEqual({'12/fault/foreign-attribute', '12/fault/xsi-unknown'}, published_schema)


if __name__ == '__main__':
    unittest.main()
