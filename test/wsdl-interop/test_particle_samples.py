#!/usr/bin/env python3
"""Check bounded particle samples against independently enumerated complete languages.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from collections import Counter
import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile
import unittest

from test_particle_ambiguity import generated, source, valid_components, words
from test_particle_model import schema


def bounded_words(expression, cap):
    """Enumerate every word with at most cap nonempty iterations per particle.

    This independently enumerates all derivations of each finite test model;
    it does not construct shortest/preferred words or use production summaries.
    """
    kind = expression[0]
    if kind == 'empty':
        return set()
    if kind == 'epsilon':
        return {()}
    if kind == 'element':
        return {(expression[1],)}
    child = bounded_words(expression[1], cap)
    if kind == 'repeat':
        result, current = set(), {((), 0)}
        for count in range(expression[3] + 1):
            if count >= expression[2]:
                result |= {word for word, _ in current}
            current = {(left + right, active + bool(right)) for left, active in current
                       for right in child if active + bool(right) <= cap}
        return result
    other = bounded_words(expression[2], cap)
    return child | other if kind == 'choice' else {left + right for left in child for right in other}


class ParticleSamplesTest(unittest.TestCase):
    def test_complete_bounded_languages(self):
        rng = random.Random(4103)
        expressions = [generated(rng, 4) for _ in range(300)] + [generated(rng, 5) for _ in range(700)]
        budgets = [{'repetitions': cap, 'children': size}
                   for cap, size in itertools.product((1, 3), (0, 1, 2, 4, 8, 12))]
        expected, cases = {}, []
        for index, expression in enumerate(expressions):
            name = f'finite-{index:04}'
            language = {tuple(name for name, _ in word) for word in words(expression)}
            bounded = {cap: bounded_words(expression, cap) for cap in (1, 3)}
            self.assertEqual(language, bounded[3], name)
            self.assertLessEqual(bounded[1], language, name)
            expected[name] = (valid_components(expression), bounded)
            cases.append({'name': name, 'schema': schema('<xs:sequence>' + source(expression)
                + '</xs:sequence>'), 'budgets': budgets})
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        self.assertIn(mode, ('ast', 'ir', 'jit', 'tiered'))
        count = 0
        outcomes = Counter()
        with tempfile.TemporaryDirectory(prefix='particle-samples-') as temporary:
            for first in range(0, len(cases), 100):
                batch = cases[first:first + 100]
                path = Path(temporary) / f'cases-{first:04}.json'
                path.write_text(json.dumps(batch), encoding='utf-8')
                process = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode,
                    str(Path(__file__).with_name('particle-samples.qr')), str(path)],
                    capture_output=True, text=True, timeout=180)
                self.assertEqual(0, process.returncode, process.stderr + process.stdout[-2000:])
                self.assertEqual('', process.stderr)
                rows = [json.loads(line) for line in process.stdout.splitlines()]
                identities = []
                for case in batch:
                    identities.append((case['name'], None, None, None))
                    if expected[case['name']][0]:
                        identities.extend((case['name'], copy, budget['repetitions'], budget['children'])
                            for copy in (False, True) for budget in budgets)
                self.assertEqual(identities, [(row['case'], row.get('copy'),
                    row.get('budget', {}).get('repetitions'), row.get('budget', {}).get('children')) for row in rows])
                original = {}
                for row in rows:
                    valid, languages = expected[row['case']]
                    if 'copy' not in row:
                        self.assertEqual('' if valid else 'WSDL-ERROR', row['error'], row)
                        outcomes['valid_schema' if valid else 'invalid_schema'] += 1
                        continue
                    budget = row['budget']
                    language = {word for word in languages[budget['repetitions']] if len(word) <= budget['children']}
                    self.assertEqual('' if language else 'XSD-SAMPLE-ERROR', row['error'], row)
                    if language:
                        self.assertIsInstance(row['names'], list, row)
                        self.assertIn(tuple(name[2:] for name in row['names']), language, row)
                        self.assertTrue(all(name.startswith('{}') for name in row['names']), row)
                    else:
                        self.assertIsNone(row['names'], row)
                    outcomes['sample' if language else 'generation_error'] += 1
                    key = (row['case'], budget['repetitions'], budget['children'])
                    if row['copy']:
                        self.assertEqual(original[key], row['names'], row)
                    else:
                        original[key] = row['names']
                count += len(rows)
        self.assertEqual(765, outcomes['valid_schema'])
        self.assertEqual(235, outcomes['invalid_schema'])
        self.assertEqual(19360, count)
        print(f'{mode}: {len(cases)} complete models, {count} rows; {dict(outcomes)}', flush=True)


if __name__ == '__main__':
    unittest.main()
