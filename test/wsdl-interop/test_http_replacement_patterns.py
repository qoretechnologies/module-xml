#!/usr/bin/env python3
"""Independent WSDL URI replacement and schema checks.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import hashlib
import json
from pathlib import Path
import re
import unittest
from urllib.parse import quote

from independent import SchemaJob, run

ROOT = Path(__file__).resolve().parent
WSDL = 'http://schemas.xmlsoap.org/wsdl/'


class ReplacementPatternsTest(unittest.TestCase):
    def test_patterns(self):
        manifest = json.loads((ROOT / 'regressions/wsdl-http-replacement/cases.json').read_text())
        rows = manifest['cases']
        self.assertEqual(19, len(rows))
        self.assertEqual(len(rows), len({row['name'] for row in rows}))
        rejected = set()
        for row in rows:
            with self.subTest(case=row['name']):
                parts = row['value']
                patterns = {'(' + part + ')': part for part in parts}
                missing = {part for pattern, part in patterns.items() if pattern not in row['location']}
                self.assertEqual(row['valid'], not missing)
                if missing:
                    self.assertIsNone(row['path'])
                    self.assertTrue(row['adjudication'])
                    rejected.add(row['name'])
                    continue
                self.assertNotIn('adjudication', row)
                # One regex substitution searches the original URI only. Substitution
                # values never enter pattern discovery, as required by WSDL 1.1 §4.7.
                pattern = '|'.join(re.escape(token) for token in patterns)
                actual = re.sub(pattern, lambda match: quote(parts[patterns[match[0]]], safe=''),
                                row['location']) if patterns else row['location']
                self.assertEqual(row['path'], actual)
        self.assertEqual({'missing-part', 'one-missing-part', 'wrong-case-only',
                          'encoded-pattern-only'}, rejected)

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
        result = run([SchemaJob('replacement', 'urn:http:replacement', schema,
                               {row['name']: row['xml'].encode() for row in rows})], resources)
        self.assertTrue(result['schemas']['replacement']['ok'], result['schemas'])
        self.assertEqual([], result['schemas']['replacement']['warnings'])
        for row in rows:
            with self.subTest(schema=row['name']):
                actual = result['documents'][row['name']]
                self.assertTrue(row['schema_valid'])
                self.assertTrue(actual['ok'], actual)
                self.assertEqual([], actual['warnings'])


if __name__ == '__main__':
    unittest.main()
