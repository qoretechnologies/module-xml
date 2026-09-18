#!/usr/bin/env python3
"""Pinned independent URI/language datatype validation.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
from pathlib import Path
import unittest
from independent import SchemaJob, run

ROOT = Path(__file__).parent


class UriLanguageTest(unittest.TestCase):
    def test_pinned_xerces(self):
        models = json.loads((ROOT / 'fixtures/uri-language.json').read_text())
        self.assertEqual(8, len(models))
        names = [row['name'] for model in models for row in model['documents']]
        self.assertEqual(89, len(names))
        self.assertEqual(len(names), len(set(names)))
        report = run([SchemaJob(m['name'], f'http://example.invalid/uri-language/{i}.xsd',
            m['schema'].encode(), {r['name']: r['xml'].encode() for r in m['documents']})
            for i, m in enumerate(models)])
        for model in models:
            with self.subTest(schema=model['name']):
                schema = report['schemas'][model['name']]
                self.assertTrue(schema['ok'], schema)
                self.assertEqual([], schema['warnings'])
            for row in model['documents']:
                with self.subTest(document=row['name']):
                    document = report['documents'][row['name']]
                    self.assertEqual(row['valid'], document['ok'], document)
                    self.assertEqual([], document['warnings'])


if __name__ == '__main__':
    unittest.main()
