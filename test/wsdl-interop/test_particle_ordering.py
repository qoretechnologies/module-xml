#!/usr/bin/env python3
"""Verify reconstructed native order against complete independent finite languages.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from collections import Counter, defaultdict
import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile
import time
import unittest

from lxml import etree

from test_particle_ambiguity import generated, source, valid_components, words
from test_particle_model import schema


class ParticleOrderingTest(unittest.TestCase):
    def test_complete_language_collections(self):
        rng = random.Random(4103)
        expressions = [generated(rng, 4) for _ in range(300)] + [generated(rng, 5) for _ in range(700)]
        cases, expected = [], {}
        for index, expression in enumerate(expressions):
            name = f'finite-{index:04}'
            language = {tuple(name for name, _ in word) for word in words(expression)}
            maximum = {letter: max((word.count(letter) for word in language), default=0) for letter in 'ab'}
            # Every count pair through one beyond each exact maximum, plus an unknown name.
            probes = [['{}a'] * a + ['{}b'] * b for a, b in itertools.product(
                range(maximum['a'] + 2), range(maximum['b'] + 2))] + [['{}unknown']]
            cases.append({'name': name, 'schema': schema('<xs:sequence>' + source(expression)
                + '</xs:sequence>'), 'probes': probes})
            expected[name] = (valid_components(expression), language,
                {tuple(sorted(Counter(word).items())) for word in language}, len(probes))
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        self.assertIn(mode, ('ast', 'ir', 'jit', 'tiered'))
        row_count = 0
        with tempfile.TemporaryDirectory(prefix='particle-ordering-') as temporary:
            for first in range(0, len(cases), 100):
                path = Path(temporary) / f'cases-{first:04}.json'
                batch = cases[first:first + 100]
                path.write_text(json.dumps(batch), encoding='utf-8')
                started = time.monotonic()
                process = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode,
                    str(Path(__file__).with_name('particle-ordering.qr')), str(path)],
                    capture_output=True, text=True, timeout=180)
                self.assertEqual(0, process.returncode, process.stderr + process.stdout[-2000:])
                self.assertEqual('', process.stderr)
                rows = [json.loads(line) for line in process.stdout.splitlines()]
                wanted = []
                for case in batch:
                    wanted.append((case['name'], None, None))
                    if expected[case['name']][0]:
                        wanted.extend((case['name'], copy, tuple(probe)) for copy in (False, True)
                            for probe in case['probes'])
                self.assertEqual(wanted, [(row['case'], row.get('copy'),
                    tuple(row['names']) if 'names' in row else None) for row in rows])
                seen = Counter()
                for row in rows:
                    valid, language, collections, probes = expected[row['case']]
                    if 'copy' not in row:
                        self.assertEqual('' if valid else 'WSDL-ERROR', row['error'], row)
                        seen[(row['case'], 'construction')] += 1
                        continue
                    self.assertTrue(valid, row)
                    seen[(row['case'], row['copy'])] += 1
                    names = [name[2:] for name in row['names']]
                    accepted = tuple(sorted(Counter(names).items())) in collections
                    self.assertEqual(accepted, row['ordered'] is not None, row)
                    self.assertEqual('' if accepted else 'SOAP-SERIALIZATION-ERROR', row['error'], row)
                    if accepted:
                        ordered = tuple(name[2:] for name in row['ordered'])
                        self.assertIn(ordered, language, row)
                        self.assertEqual(Counter(names), Counter(ordered), row)
                        root = etree.fromstring(row['xml'].encode())
                        self.assertIn(tuple(child.tag for child in root), language, row)
                        values = defaultdict(list)
                        for child in root:
                            values[child.tag].append(child.text)
                        self.assertEqual({letter: [f'{letter}-{index + 1}' for index in range(count)]
                            for letter, count in Counter(names).items()}, dict(values), row)
                    else:
                        self.assertIsNone(row['xml'], row)
                for case in batch:
                    name = case['name']
                    self.assertEqual(1, seen[(name, 'construction')])
                    for copy in (False, True):
                        self.assertEqual(expected[name][3] if expected[name][0] else 0, seen[(name, copy)])
                row_count += len(rows)
                print(f'{mode}: models {first}-{first + len(batch) - 1}: {len(rows)} rows '
                      f'in {time.monotonic() - started:.3f}s', flush=True)
        print(f'{mode}: {len(cases)} complete models, {row_count} rows', flush=True)


if __name__ == '__main__':
    unittest.main()
