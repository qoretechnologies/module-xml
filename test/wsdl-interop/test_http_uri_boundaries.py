#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
"""Independent HTTP URI observation and pinned-schema checks.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import hashlib
import json
import re
import unittest
from pathlib import Path
from urllib.parse import parse_qs, unquote
from independent import SchemaJob, run

ROOT = Path(__file__).resolve().parent
WSDL = 'http://schemas.xmlsoap.org/wsdl/'


class BoundariesTest(unittest.TestCase):
    def test_boundaries(self):
        rows = json.loads((ROOT / 'regressions/wsdl-http-uri-boundaries/cases.json').read_text())['cases']
        self.assertEqual(16, len(rows))
        for row in rows:
            expected = row['value'].get('id', '')
            if row['mode'] == 'urlEncoded':
                if row['verb'] == 'GET':
                    wire = row['path'][len(row['location']):].lstrip('?&')
                else:
                    wire = row['body']
                self.assertEqual({k:[v] for k,v in row['value'].items()}, parse_qs(wire, keep_blank_values=True))
            elif row['mode'] == 'urlReplacement':
                pieces = row['location'].split('(id)')
                if len(pieces) == 1:
                    self.assertEqual(row['location'], row['path'])
                else:
                    a, b = pieces
                    self.assertTrue(row['path'].startswith(a))
                    self.assertTrue(row['path'].endswith(b))
                    self.assertEqual(expected, unquote(row['path'][len(a):len(row['path'])-len(b) if b else None]))
            else:
                self.assertEqual(expected, row['body'])
        grammar = ROOT / 'regressions/wsdl-http-mime-grammar'
        sources = json.loads((grammar / 'cases.json').read_text())['schemas']
        resources = {}
        imports = []
        for source in sources:
            data = (grammar / source['file']).read_bytes()
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
        documents = {row['name']: row['xml'].encode() for row in rows}
        for row in rows:
            documents[row['name'] + '-missing'] = re.sub(r'<h:operation location="[^"]*"/>', '<h:operation/>', row['xml']).encode()
        result = run([SchemaJob('uri-boundary', 'urn:http:uri-boundary', schema, documents)], resources)
        self.assertTrue(result['schemas']['uri-boundary']['ok'], result['schemas'])
        self.assertEqual([], result['schemas']['uri-boundary']['warnings'])
        for row in rows:
            with self.subTest(schema=row['name']):
                actual = result['documents'][row['name']]
                self.assertTrue(actual['ok'], actual)
                self.assertEqual([], actual['warnings'])
                self.assertFalse(result['documents'][row['name'] + '-missing']['ok'])


if __name__ == '__main__':
    unittest.main()
