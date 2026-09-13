#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
"""Canonical API syntax and precision checked by an exact rational reference."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cmake'))
from ieee_reference_cases import cases


class IeeeCanonicalTest(unittest.TestCase):
    def test_exact_canonical_boundaries(self):
        rows = cases()
        self.assertEqual(1314, len(rows))
        inputs = [dict(id=i, wide=wide, text=text) for i, (wide, text, _, _) in enumerate(rows)]
        worker = Path(os.environ.get('QORE_IEEE_CANONICAL_WORKER', Path(__file__).with_name('ieee-canonical.qr')))
        with tempfile.TemporaryDirectory(prefix='xml-ieee-canonical-') as temporary:
            source = Path(temporary) / 'cases.json'
            source.write_text(json.dumps(inputs))
            result = subprocess.run(['qore', '-b', '--enable-debug', str(worker), str(source)],
                                    capture_output=True, text=True, timeout=90)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('', result.stderr)
        observed = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(rows), len(observed))
        for i, ((wide, lexical, _, expected), actual) in enumerate(zip(rows, observed)):
            with self.subTest(id=i, wide=wide):
                self.assertEqual(i, actual['id'])
                self.assertEqual(expected, actual['canonical'], lexical)
                self.assertEqual('XSD-FLOAT-LEXICAL-ERROR' if expected is None else None, actual['error'], lexical)


if __name__ == '__main__':
    unittest.main()
