#!/usr/bin/env python3
"""Pinned independent instance attribute and list identity diagnostics; normative expectations stay separate.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
from pathlib import Path
import unittest
from independent import SchemaJob, run


class InstanceIdentitiesTest(unittest.TestCase):
    def test_pinned_xerces(self):
        models = json.loads((Path(__file__).parent / 'fixtures/instance-identities.json').read_text())
        rows = [r for m in models for r in m['documents']]
        self.assertEqual(121, len(rows))
        self.assertEqual(121, len({r['name'] for r in rows}))
        self.assertEqual(51, sum(r['valid'] for r in rows))
        self.assertEqual(3, sum(r.get('oracle_difference') == 'attribute-field-first-match' for r in rows))
        report = run([SchemaJob(m['name'], f'http://example.invalid/instance-identities/{i}.xsd',
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
                    self.assertEqual(row['valid'] != row['xerces_valid'], 'oracle_difference' in row)


if __name__ == '__main__':
    unittest.main()
