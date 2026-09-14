#!/usr/bin/env python3
"""Independent XSD 1.0 approved nil-as-missing identity policy.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
from pathlib import Path
import unittest
from independent import SchemaJob, run


class NilIdentitiesTest(unittest.TestCase):
    def test_pinned_xerces(self):
        models = json.loads((Path(__file__).parent / 'fixtures/nil-identities.json').read_text())
        self.assertEqual(148, len(models))
        self.assertTrue(all(m['schema_valid'] for m in models))
        self.assertEqual(96, sum(r['valid'] for m in models for r in m['documents']))
        self.assertEqual(27, sum(r.get('oracle_difference') == 'nil-keyref-stored-as-null' for m in models for r in m['documents']))
        self.assertEqual(2, sum(r.get('oracle_difference') == 'union-counts-same-node-twice' for m in models for r in m['documents']))
        self.assertEqual(len(models), len({m['name'] for m in models}))
        report = run([SchemaJob(m['name'], f'http://example.invalid/nil-identities/{i}.xsd',
            m['schema'].encode(), {r['name']: r['xml'].encode() for r in m['documents']})
            for i, m in enumerate(models)])
        for model in models:
            with self.subTest(name=model['name']):
                schema = report['schemas'][model['name']]
                self.assertEqual(model['schema_valid'], schema['ok'], schema)
                self.assertEqual([], schema['warnings'])
                for row in model['documents']:
                    document = report['documents'][row['name']]
                    self.assertEqual(row.get('xerces_valid', row['valid']), document['ok'], document)
                    if 'xerces_valid' in row:
                        self.assertTrue(row['valid'])
                        message = {
                            'nil-keyref-stored-as-null': "null' not found",
                            'union-counts-same-node-twice': 'matches more than one value',
                        }[row['oracle_difference']]
                        self.assertIn(message, document['desc'])
                    self.assertEqual([], document['warnings'])


if __name__ == '__main__':
    unittest.main()
