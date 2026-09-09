#!/usr/bin/env python3
"""Integer-rational reference for direct IEEE conversion, independently of libc/MPFR.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from fractions import Fraction
import json
import math
from pathlib import Path
import random
import struct
import subprocess
import tempfile
import unittest


from ieee_reference import decimal_text, rounded_value


def boundary_values(wide):
    precision, minimum, maximum = (53, -1022, 1023) if wide else (24, -126, 127)
    # Midpoints around zero, subnormal/normal transitions, both tie parities,
    # exponent transitions and overflow, plus reproducible ordinary significands.
    rng = random.Random(0x1EEE2026 + wide)
    for exponent in (minimum - 1, minimum, minimum + 1, -10, -1, 0, 1, 10, maximum - 1, maximum):
        unit = Fraction(2) ** (max(exponent, minimum) - precision + 1)
        lower = 0 if exponent < minimum else 1 << (precision - 1)
        top = 1 << (precision - 1) if exponent < minimum else 1 << precision
        for significand in (lower, lower + 1, lower + 2, top - 2, top - 1, rng.randrange(lower, top)):
            midpoint = (Fraction(significand) + Fraction(1, 2)) * unit
            # Far below the precision of a binary64 intermediate, but representable
            # exactly in Qore's source-length-based number precision in the second test.
            epsilon = unit / (1 << 100)
            for value in (midpoint - epsilon, midpoint, midpoint + epsilon):
                yield value
                yield -value


class IeeeConversionTest(unittest.TestCase):
    def check_cases(self, rows):
        identities = set()
        for index, row in enumerate(rows):
            row['id'] = index
        with tempfile.TemporaryDirectory(prefix='xml-ieee-conversion-') as temporary:
            path = Path(temporary) / 'cases.json'
            path.write_text(json.dumps(rows))
            result = subprocess.run(['qore', '--enable-debug', str(Path(__file__).with_name('ieee-conversion.qr')),
                                     str(path)], text=True, capture_output=True, timeout=90)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('', result.stderr)
        observed = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(rows), len(observed))
        for expected, actual in zip(rows, observed):
            self.assertEqual(expected['id'], actual['id'])
            self.assertNotIn(actual['id'], identities)
            identities.add(actual['id'])
            reference = rounded_value(expected['text'], expected['wide'])
            self.assertEqual(struct.pack('!d', reference), struct.pack('!d', float(actual['value'])),
                             (expected, actual, reference))
        self.assertEqual(set(range(len(rows))), identities)

    def test_decimal_lexical_boundaries(self):
        rows = []
        for wide in (False, True):
            values = [decimal_text(value) for value in boundary_values(wide)]
            values += ['0', '-0', '1e-10000', '-1e-10000', '1e10000', '-1e10000', '0.1', '-0.1']
            rng = random.Random(0xDEC1A12026 + wide)
            for _ in range(256):
                digits = str(rng.randrange(1, 10**80))
                values.append(digits + 'e' + str(rng.randrange(-450, 350)))
            rows.extend(dict(text=text, wide=wide, kind='string') for text in values)
        self.assertEqual(1248, len(rows))
        self.check_cases(rows)

    def test_exact_native_number_and_integer_boundaries(self):
        rows = []
        for wide in (False, True):
            rows.extend(dict(text=decimal_text(value), wide=wide, kind='number') for value in boundary_values(wide))
            for exponent in (24, 25, 52, 53, 54, 60, 61, 62):
                midpoint = (1 << exponent) + (1 << max(0, exponent - (53 if wide else 24)))
                for delta in (-1, 0, 1):
                    for sign in (1, -1):
                        rows.append(dict(text=str(sign * (midpoint + delta)), wide=wide, kind='int'))
        self.assertEqual(816, len(rows))
        self.check_cases(rows)

    def test_exact_native_binary64_to_binary32(self):
        rows = []
        # Binary32 midpoints fit binary64. Choose immediate binary64 neighbors so
        # decimal display rounding cannot substitute for the exact native input.
        for value in boundary_values(False):
            native = float(value)
            for source in (math.nextafter(native, -math.inf), native, math.nextafter(native, math.inf)):
                rows.append(dict(text=decimal_text(Fraction(source)), wide=False, kind='float'))
        self.assertEqual(1080, len(rows))
        self.check_cases(rows)


if __name__ == '__main__':
    unittest.main()
