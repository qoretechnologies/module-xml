#!/usr/bin/env python3
"""Independent HTTP and MIME declaration grammar.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / 'regressions/wsdl-http-mime-grammar'
from independent import SchemaJob, run

WSDL = 'http://schemas.xmlsoap.org/wsdl/'


class HttpMimeGrammarTest(unittest.TestCase):
    def test_grammar(self):
        manifest = json.loads((FIXTURES / 'cases.json').read_text())
        rows = manifest['cases']
        self.assertEqual(187, len(rows))
        self.assertEqual(len(rows), len({row['name'] for row in rows}))
        self.assertEqual({'http.xsd', 'mime.xsd'},
                         {source['file'] for source in manifest['schemas']})
        resources = {}
        imports = []
        for source in manifest['schemas']:
            data = (FIXTURES / source['file']).read_bytes()
            self.assertEqual(source['sha256'], hashlib.sha256(data).hexdigest())
            self.assertEqual(source['size'], len(data))
            resources[source['url']] = data
            namespace = WSDL + source['file'].removesuffix('.xsd') + '/'
            imports.append(f'<xs:import namespace="{namespace}" schemaLocation="{source["url"]}"/>')
        core = ROOT / 'regressions/wsdl-grammar'
        core_manifest = json.loads((core / 'cases.json').read_text())
        core_data = (core / core_manifest['schema_file']).read_bytes()
        self.assertEqual(core_manifest['schema_sha256'], hashlib.sha256(core_data).hexdigest())
        resources['urn:wsdl:core'] = core_data
        schema = ('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                  f'<xs:import namespace="{WSDL}" schemaLocation="urn:wsdl:core"/>'
                  + ''.join(imports) + '</xs:schema>').encode()
        results = run([SchemaJob('http-mime', 'urn:http-mime:grammar', schema,
                                {row['name']: row['xml'].encode() for row in rows})], resources)
        self.assertTrue(results['schemas']['http-mime']['ok'], results['schemas'])
        self.assertEqual([], results['schemas']['http-mime']['warnings'])
        differences = set()
        for row in rows:
            with self.subTest(case=row['name']):
                actual = results['documents'][row['name']]
                self.assertEqual(row['schema_valid'], actual['ok'], actual)
                self.assertEqual([], actual['warnings'])
                if row['valid'] != row['schema_valid']:
                    self.assertTrue(row.get('adjudication'))
                    self.assertFalse(row['valid'])
                    differences.add(row['name'])
                else:
                    self.assertNotIn('adjudication', row)
        contexts = ('binding', 'operation', 'address', 'urlEncoded', 'urlReplacement', 'content', 'mimeXml')
        self.assertEqual({kind + '/xsi-hint-odd' for kind in contexts}, differences)


if __name__ == '__main__':
    unittest.main()
