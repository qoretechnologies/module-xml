"""Independent integer-rational expectations for native IEEE conversion.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from fractions import Fraction
import math
from pathlib import Path
import random
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'wsdl-interop'))
from ieee_reference import decimal_text, rounded_value
from test_ieee_conversion import boundary_values


def bits(value, wide):
    return int.from_bytes(struct.pack('>d' if wide else '>f', value), 'big')


def canonical(value, wide):
    """Shortest nearest decimal mapping back to the exact selected IEEE value."""
    if math.isnan(value):
        return 'NaN'
    if math.isinf(value):
        return '-INF' if value < 0 else 'INF'
    if value == 0:
        return '0.0E0'
    exact = Fraction(abs(value))
    exponent = len(str(exact.numerator)) - len(str(exact.denominator))
    if exact < Fraction(10) ** exponent:
        exponent -= 1
    for precision in range(1, 18 if wide else 10):
        unit = Fraction(10) ** (exponent - precision + 1)
        scaled = exact / unit
        lower = scaled.numerator // scaled.denominator
        candidates = [n for n in (lower, lower + 1)
                      if rounded_value(str(n) + 'e' + str(exponent - precision + 1), wide) == abs(value)]
        if not candidates:
            continue
        selected = min(candidates, key=lambda n: (abs(n * unit - exact), n % 2))
        digits = str(selected)
        power = exponent - precision + len(digits)
        digits = digits.rstrip('0')
        return ('-' if value < 0 else '') + digits[0] + '.' + (digits[1:] or '0') + 'E' + str(power)
    raise AssertionError((value, wide))


def cases():
    rows = []
    for wide in (False, True):
        values = [decimal_text(value) for value in boundary_values(wide)]
        values += ['0', '-0', '1e-10000', '-1e-10000', '1e10000', '-1e10000', '0.1', '-0.1']
        rng = random.Random(0xDEC1A12026 + wide)
        for _ in range(256):
            values.append(str(rng.randrange(1, 10**80)) + 'e' + str(rng.randrange(-450, 350)))
        for text in values:
            value = rounded_value(text, wide)
            rows.append((wide, text, bits(value, wide), canonical(value, wide)))
        for text, value in [('NaN', math.nan), ('INF', math.inf), ('-INF', -math.inf),
                            (' \tNaN\t', math.nan), (' -INF ', -math.inf),
                            ('+.125e+1', 1.25), ('1.', 1.0), ('.5', 0.5), ('1.e2', 100.0),
                            ('1e9999999999999999999999999999', math.inf),
                            ('-1e-9999999999999999999999999999', -0.0),
                            ('1' + '0' * 5000 + 'e-5000', 1.0),
                            ('0.' + '0' * 4999 + '1e5000', 1.0)]:
            rows.append((wide, text, bits(value, wide), canonical(value, wide)))
        for text in ['', ' ', '1e', '1e+', '1e-', '1e2e3', '1.2.3', '1e2.0', '1tail',
                     '0x1p0', '1,2', '1 2', '+INF', 'nan', 'inf', '-NaN', '+NaN', '١', '１', '1\u00a0']:
            rows.append((wide, text, None, None))
    return rows


def check(test, rows, output):
    observed = [line.split('\t') for line in output.splitlines()]
    test.assertEqual(len(rows) * 4, len(observed))
    for i, (wide, text, expected_bits, expected_text) in enumerate(rows):
        for mode in range(4):
            row = observed[i * 4 + mode]
            test.assertEqual([str(i), str(mode)], row[:2])
            test.assertEqual(7, len(row))
            if expected_bits is None:
                test.assertGreater(int(row[2]), 0, (wide, text, row))
                test.assertGreater(int(row[3]), 0, (wide, text, row))
                test.assertEqual(['-1', '0000000000000000', '-'], row[4:])
            else:
                test.assertEqual(['0', '0', '0'], row[2:5], (wide, text, row))
                if expected_text != 'NaN':
                    test.assertEqual(expected_bits, int(row[5], 16), (wide, text, row))
                test.assertEqual(expected_text, row[6], (wide, text, row))
