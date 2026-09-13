#!/usr/bin/env python3
"""XSD 1.0 notation declaration/use constraints and expanded-name values.

Copyright (C) 2026 Qore Technologies, s.r.o.
Expected verdicts follow Part 1 3.12 and Part 2 3.2.19. The explicit Xerces
schema disagreements do not change the module's required rejection.
"""
import json
import os
from pathlib import Path
import subprocess
import unittest
from independent import SchemaJob, run

ROOT = Path(__file__).parent
FIXTURE = ROOT / 'fixtures/notations.json'


class NotationsTest(unittest.TestCase):
    def test_native_and_preserved_input(self):
        models = json.loads(FIXTURE.read_text())
        documents = [d for m in models for d in m['documents']]
        self.assertEqual(64, len(models))
        self.assertEqual(231, len(documents))
        self.assertEqual(231, len({d['name'] for d in documents}))
        completed = subprocess.run([os.environ.get('QORE', 'qore'), '-b', '--enable-debug',
                                    str(ROOT / 'notations.qr'), str(FIXTURE)],
                                   text=True, capture_output=True, timeout=120)
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual('', completed.stderr)
        rows = list(map(json.loads, completed.stdout.splitlines()))
        self.assertEqual([d['name'] for d in documents], [r['name'] for r in rows])
        results = iter(rows)
        for model in models:
            for document in model['documents']:
                row = next(results)
                for path, error in [('dom', 'PARSE-XML-EXCEPTION'), ('reader', 'PARSE-XML-EXCEPTION'),
                                    ('document', 'XSD-ERROR')]:
                    with self.subTest(name=document['name'], path=path):
                        self.assertEqual(document['expected'], row[path], row)
                        if not document['expected']:
                            self.assertEqual(error if model['schema_valid'] else 'XSD-SYNTAX-ERROR',
                                             row.get(path + '_error'), row)
                        elif path != 'reader':
                            self.assertTrue(row[path + '_preserved'])

    def test_pinned_independent_verdicts(self):
        models = json.loads(FIXTURE.read_text())
        resources = {k: v.encode() for m in models for k, v in m.get('resources', {}).items()}
        self.assertEqual((ROOT / 'fixtures/notations-import.xsd').read_text().rstrip('\n').encode(),
                         resources['http://example.invalid/notations/notations-import.xsd'])
        report = run([SchemaJob(m['name'], f'http://example.invalid/notations/{i}.xsd',
                               m['schema'].encode(), {d['name']: d['xml'].encode() for d in m['documents']})
                      for i, m in enumerate(models)], resources)
        disagreements = set()
        for model in models:
            expected = model.get('xerces_schema_valid', model['schema_valid'])
            row = report['schemas'][model['name']]
            self.assertEqual(expected, row['ok'], (model['name'], row))
            self.assertEqual([], row['warnings'])
            if 'xerces_schema_valid' in model:
                self.assertNotEqual(model['schema_valid'], expected)
                disagreements.add(model['name'])
            for document in model['documents']:
                with self.subTest(name=document['name']):
                    row = report['documents'][document['name']]
                    self.assertEqual(document.get('xerces_expected', document['expected']) if expected else None,
                                     row['ok'], row)
                    self.assertEqual([], row['warnings'])
        self.assertEqual({'union-direct', 'list-direct', 'unrestricted-simple-content',
                          'unrestricted-list', 'unrestricted-union', 'unrestricted-unused-list',
                          'unrestricted-unused-union'}, disagreements)


if __name__ == '__main__':
    unittest.main()
