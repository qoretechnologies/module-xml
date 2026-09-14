#!/usr/bin/env python3
"""Pinned independent identity table diagnostics; normative expectations stay separate.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
from pathlib import Path
import unittest
from independent import SchemaJob, run


class IdentityTablesTest(unittest.TestCase):
    def test_pinned_xerces(self):
        models = json.loads((Path(__file__).parent / 'fixtures/identity-tables.json').read_text())
        rows = [r for m in models for r in m['documents']]
        self.assertEqual(54, len(rows))
        self.assertEqual(54, len({r['name'] for r in rows}))
        self.assertEqual(38, sum(r['valid'] for r in rows))
        self.assertEqual(21, sum(r.get('oracle_difference') == 'sibling-key-store-aliasing' for r in rows))
        self.assertEqual(1, sum(r.get('oracle_difference') == 'empty-keyref-store' for r in rows))
        report = run([SchemaJob(m['name'], f'http://example.invalid/identity-tables/{i}.xsd',
            m['schema'].encode(), {r['name']: r['xml'].encode() for r in m['documents']})
            for i, m in enumerate(models)])
        for model in models:
            with self.subTest(schema=model['name']):
                schema = report['schemas'][model['name']]
                self.assertTrue(schema['ok'], schema)
                self.assertEqual([], schema['warnings'])
            for row in model['documents']:
                with self.subTest(document=row['name']):
                    result = report['documents'][row['name']]
                    self.assertEqual(row['xerces_valid'], result['ok'], result)
                    self.assertEqual([], result['warnings'])
                    if row.get('oracle_difference') == 'empty-keyref-store':
                        self.assertIn('out of scope', result['desc'])
                    elif row['valid'] and not row['xerces_valid']:
                        self.assertIn('not found', result['desc'])
                    self.assertEqual(row['valid'] != row['xerces_valid'], 'oracle_difference' in row)


if __name__ == '__main__':
    unittest.main()
