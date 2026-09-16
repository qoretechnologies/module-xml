#!/usr/bin/env python3
"""Pinned independent observations for scoped tuples and instance attributes.

Copyright (C) 2026 Qore Technologies, s.r.o.
Processor choices and adjudicated differences are explicit fixture data, not skips.
"""
import json
from pathlib import Path
import unittest
from independent import SchemaJob, run


class IdentityTuplesTest(unittest.TestCase):
    def test_pinned_reference(self):
        for fixture, count in [('identity-tuples', 165), ('identity-instance-attributes', 36)]:
            models = json.loads((Path(__file__).parent / 'fixtures' / (fixture + '.json')).read_text())
            self.assertEqual(count, len(models))
            self.assertEqual(count, len({m['name'] for m in models}))
            report = run([SchemaJob(m['name'], f'http://example.invalid/{fixture}/{i}.xsd',
                m['schema'].encode(), {m['name']: m['xml'].encode()}) for i, m in enumerate(models)])
            for model in models:
                with self.subTest(fixture=fixture, name=model['name']):
                    schema = report['schemas'][model['name']]
                    document = report['documents'][model['name']]
                    self.assertTrue(schema['ok'], schema)
                    self.assertEqual([], schema['warnings'])
                    self.assertEqual(model.get('xerces_valid', model['valid']), document['ok'], document)
                    self.assertEqual([], document['warnings'])
                    if model.get('xerces_valid', model['valid']) != model['valid']:
                        self.assertTrue(model.get('comparison_policy') or model.get('reference_difference'))


if __name__ == '__main__':
    unittest.main()
