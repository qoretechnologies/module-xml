#!/usr/bin/env python3
"""XSD 1.0 ID binding rules with explicit independent-validator disagreements.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
import os
from pathlib import Path
import subprocess
import unittest

from independent import SchemaJob, run as run_independent

ROOT = Path(__file__).resolve().parent
# These verdicts follow XSD 1.0 3.3.4 and 3.15.5; see the evidence document.
# An ID-valued child identifies its parent, including the validation-root edge.
XERCES_DISAGREEMENTS = {
    'IDREF/elements/duplicate', 'IDREFS/elements/duplicate',
    'siblings/same-parent', 'siblings/attribute-and-child',
    'root-id/unbound', 'root-id-with-attribute/unbound',
    'root-id-with-attribute/bound', 'root-id-with-attribute/unbound-reference',
    'default-IDREF/missing', 'default-IDREFS/missing',
}


class NativeIdBindingTest(unittest.TestCase):
    def test_native_rules_and_independent_verdicts(self):
        models = json.loads((ROOT / 'fixtures/id-bindings.json').read_text())['models']
        jobs = [SchemaJob(model['name'], f'http://example.invalid/ids/{index}.xsd', model['schema'].encode(),
                          {doc['name']: doc['xml'].encode() for doc in model['documents']})
                for index, model in enumerate(models)]
        oracle = run_independent(jobs)
        self.assertEqual(68, len(oracle['documents']))
        expected = {doc['name']: doc['valid'] for model in models for doc in model['documents']}
        self.assertEqual(set(expected), set(oracle['documents']))
        disagreements = set()
        for model in models:
            verdict = oracle['schemas'][model['name']]
            self.assertTrue(verdict['ok'], verdict)
            self.assertEqual([], verdict['warnings'])
            for doc in model['documents']:
                result = oracle['documents'][doc['name']]
                self.assertEqual([], result['warnings'])
                if result['ok'] != doc['valid']:
                    disagreements.add(doc['name'])
        self.assertEqual(XERCES_DISAGREEMENTS, disagreements)
        # Native behavior is checked against the normative verdicts, including
        # the cases where the independent implementation disagrees.
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        self.assertIn(mode, ('ast', 'ir', 'jit', 'tiered'))
        run = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode,
                              str(ROOT.parent / 'xml-id-bindings.qtest')],
                             text=True, capture_output=True, timeout=60)
        self.assertEqual(0, run.returncode, run.stdout + run.stderr)
        self.assertEqual('', run.stderr)
        self.assertIn('Ran 2 test cases, 2 succeeded (275 assertions)', run.stdout)
        self.assertNotIn('warning', run.stdout.lower())


if __name__ == '__main__':
    unittest.main()
