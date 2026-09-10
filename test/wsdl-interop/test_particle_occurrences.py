#!/usr/bin/env python3
"""Complete finite languages independently verify exact occurrence projections.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from collections import Counter
import json
import os
from pathlib import Path
import random
import subprocess
import tempfile
import time
import unittest

from test_particle_ambiguity import generated, source, valid_components, words
from test_particle_model import schema


class ParticleOccurrencesTest(unittest.TestCase):
    def test_complete_language_extrema(self):
        rng = random.Random(4103)
        expressions = [generated(rng, 4) for _ in range(300)] + [generated(rng, 5) for _ in range(700)]
        cases, expected = [], []
        for index, expression in enumerate(expressions):
            name = f'finite-{index:04}'
            valid = valid_components(expression)
            cases.append({'name': name, 'schema': schema('<xs:sequence>' + source(expression) + '</xs:sequence>')})
            expected.append({'case': name, 'error': '' if valid else 'WSDL-ERROR'})
            if not valid:
                continue
            language = words(expression)
            counts = [Counter(name for name, _ in word) for word in language]
            names = set().union(*(count.keys() for count in counts))
            ranges = {'{}' + name: {'minimum': str(min(count[name] for count in counts)),
                                   'maximum': str(max(count[name] for count in counts))}
                      for name in names} if counts else None
            for copy in (False, True):
                expected.append({'case': name, 'copy': copy, 'ranges': ranges})
        self.assertEqual(2530, len(expected))
        mode = os.environ.get('QORE_EXEC_MODE', 'jit')
        self.assertIn(mode, ('ast', 'ir', 'jit', 'tiered'))
        actual = []
        with tempfile.TemporaryDirectory(prefix='particle-occurrences-') as temporary:
            for first in range(0, len(cases), 250):
                path = Path(temporary) / f'cases-{first:04}.json'
                batch = cases[first:first + 250]
                path.write_text(json.dumps(batch), encoding='utf-8')
                started = time.monotonic()
                process = subprocess.run(['qore', '-b', '--enable-debug', '--exec-mode=' + mode,
                    str(Path(__file__).with_name('particle-occurrences.qr')), str(path)],
                    capture_output=True, text=True, timeout=180)
                self.assertEqual(0, process.returncode, process.stderr + process.stdout[-2000:])
                self.assertEqual('', process.stderr)
                rows = [json.loads(line) for line in process.stdout.splitlines()]
                actual.extend(rows)
                print(f'{mode}: models {first}-{first + len(batch) - 1}: {len(rows)} rows '
                      f'in {time.monotonic() - started:.3f}s', flush=True)
        self.assertEqual(len(expected), len(actual), 'missing or extra occurrence rows')
        for wanted, received in zip(expected, actual):
            self.assertEqual(wanted, received)


if __name__ == '__main__':
    unittest.main()
