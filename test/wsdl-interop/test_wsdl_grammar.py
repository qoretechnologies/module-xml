#!/usr/bin/env python3
"""Independent core WSDL grammar checks, with capability failures kept separate.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import hashlib
import json
from pathlib import Path
import unittest

from lxml import etree
from independent import SchemaJob, run

ROOT = Path(__file__).resolve().parent / 'regressions/wsdl-grammar'


class WsdlGrammarTest(unittest.TestCase):
    def test_core_grammar_and_extension_requirements(self):
        manifest = json.loads((ROOT / 'cases.json').read_text())
        schema = (ROOT / manifest['schema_file']).read_bytes()
        self.assertEqual(manifest['schema_sha256'], hashlib.sha256(schema).hexdigest())
        rows = manifest['cases']
        self.assertEqual(312, len(rows))
        self.assertEqual(len(rows), len({row['name'] for row in rows}))
        oracle = run([SchemaJob('wsdl-core', manifest['schema_url'], schema,
                              {row['name']: row['xml'].encode() for row in rows})])
        self.assertTrue(oracle['schemas']['wsdl-core']['ok'], oracle)
        self.assertEqual([], oracle['schemas']['wsdl-core']['warnings'])
        native_schema = etree.XMLSchema(etree.fromstring(schema))
        disagreements = set()
        unsupported = set()
        for row in rows:
            with self.subTest(case=row['name']):
                result = oracle['documents'][row['name']]
                self.assertEqual(row['schema_valid'], result['ok'], result)
                self.assertEqual([], result['warnings'])
                native = native_schema.validate(etree.fromstring(row['xml'].encode()))
                if native != row['schema_valid']:
                    disagreements.add(row['name'])
                if row['valid'] != row['schema_valid']:
                    # A true wsdl:required is grammatically valid, but its unknown
                    # extension cannot be ignored when compiling a usable contract.
                    self.assertTrue(row['schema_valid'])
                    self.assertIn('/required-', row['name'])
                    required = etree.fromstring(row['xml'].encode()).xpath(
                        '//@w:required', namespaces={'w': 'http://schemas.xmlsoap.org/wsdl/'})
                    self.assertEqual(1, len(required))
                    self.assertIn(required[0].strip(), ('true', '1'))
                    unsupported.add(row['name'])
        self.assertEqual(22, len(unsupported))
        # Already adjudicated in sized-facets-adjudication.md: some libxml2
        # versions accept empty NMTOKENS despite the builtin minimum length.
        self.assertFalse(disagreements - {"operation/parameterOrder-''"}, disagreements)


if __name__ == '__main__':
    unittest.main()
