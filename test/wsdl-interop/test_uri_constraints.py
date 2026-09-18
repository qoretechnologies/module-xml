#!/usr/bin/env python3
"""Independent WSDL URI classification and pinned grammar checks.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import hashlib
import json
from pathlib import Path
import unittest
from urllib.parse import urlsplit

from independent import SchemaJob, run

ROOT = Path(__file__).resolve().parent
WSDL = 'http://schemas.xmlsoap.org/wsdl/'


class UriConstraintsTest(unittest.TestCase):
    def test_uri_semantics_and_grammar(self):
        rows = json.loads((ROOT / 'regressions/wsdl-uri-constraints/cases.json').read_text())['cases']
        self.assertEqual(33, len(rows))
        self.assertEqual(len(rows), len({row['name'] for row in rows}))
        rejected = []
        for row in rows:
            lexical = ' '.join((row['value'] or '').split())
            absolute = bool(urlsplit(lexical).scheme)
            expected = row['value'] is None or absolute if row['kind'] == 'namespace' else not absolute
            self.assertEqual(expected and row['schema_valid'], row['valid'], row['name'])
            if not expected:
                rejected.append(row['name'])
        self.assertEqual(14, len(rejected))

        resources = {}
        grammar = ROOT / 'regressions/wsdl-http-mime-grammar'
        sources = json.loads((grammar / 'cases.json').read_text())['schemas']
        imports = []
        for source in sources:
            data = (grammar / source['file']).read_bytes()
            self.assertEqual(source['sha256'], hashlib.sha256(data).hexdigest())
            resources[source['url']] = data
            namespace = WSDL + source['file'].removesuffix('.xsd') + '/'
            imports.append(f'<xs:import namespace="{namespace}" schemaLocation="{source["url"]}"/>')
        core = ROOT / 'regressions/wsdl-grammar'
        manifest = json.loads((core / 'cases.json').read_text())
        data = (core / manifest['schema_file']).read_bytes()
        self.assertEqual(manifest['schema_sha256'], hashlib.sha256(data).hexdigest())
        resources['urn:wsdl:core'] = data
        schema = ('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                  f'<xs:import namespace="{WSDL}" schemaLocation="urn:wsdl:core"/>'
                  + ''.join(imports) + '</xs:schema>').encode()
        oracle = run([SchemaJob('uri', 'urn:wsdl:uri-constraints', schema,
                                {row['name']: row['xml'].encode() for row in rows})], resources)
        self.assertTrue(oracle['schemas']['uri']['ok'], oracle['schemas'])
        self.assertEqual([], oracle['schemas']['uri']['warnings'])
        for row in rows:
            result = oracle['documents'][row['name']]
            self.assertEqual(row['schema_valid'], result['ok'], (row['name'], result))
            self.assertEqual([], result['warnings'])
        # The XSD grammar accepts URI references in both contexts. WSDL's
        # opposite absolute/relative requirements are explicit semantic rules.
        self.assertEqual(13, sum(row['schema_valid'] and not row['valid'] for row in rows))
        self.assertEqual(2, sum(not row['schema_valid'] for row in rows))


if __name__ == '__main__':
    unittest.main()
