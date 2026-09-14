#!/usr/bin/env python3
"""Independent XSD 1.0 identity XPath grammar and explicit oracle differences.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
from pathlib import Path
import unittest
from independent import SchemaJob, run

ROOT = Path(__file__).parent


class IdentityPathTest(unittest.TestCase):
    def test_pinned_xerces(self):
        models = json.loads((ROOT / 'fixtures/identity-paths.json').read_text())
        self.assertEqual(54, len(models))
        self.assertEqual(len(models), len({m['name'] for m in models}))
        report = run([SchemaJob(m['name'], f'http://example.invalid/identity-paths/{i}.xsd',
            m['schema'].encode(), {r['name']: r['xml'].encode() for r in m['documents']})
            for i, m in enumerate(models)])
        for model in models:
            with self.subTest(name=model['name']):
                schema = report['schemas'][model['name']]
                self.assertEqual(model.get('xerces_schema_valid', model['schema_valid']), schema['ok'], schema)
                self.assertEqual([], schema['warnings'])
                for row in model['documents']:
                    document = report['documents'][row['name']]
                    self.assertEqual(True if model.get('xerces_schema_valid', model['schema_valid']) else None, document['ok'], document)
                    self.assertEqual([], document['warnings'])


if __name__ == '__main__':
    unittest.main()
