"""Exact integer-rational IEEE reference shared by scalar tests and corpus checks.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from fractions import Fraction
import math


def decimal_text(value):
    """Write a finite binary rational exactly, without a floating-point conversion."""
    numerator, denominator = abs(value).as_integer_ratio()
    places = denominator.bit_length() - 1
    assert denominator == 1 << places
    digits = str(numerator * 5**places).rjust(places + 1, '0')
    text = digits if not places else digits[:-places] + '.' + digits[-places:]
    return ('-' if value < 0 else '') + text


def rounded_value(text, wide):
    """Quantize the exact rational to an integer significand, including subnormals."""
    value = Fraction(text)
    negative = text.startswith('-')
    if not value:
        return -0.0 if negative else 0.0
    value = abs(value)
    precision, minimum, maximum = (53, -1022, 1023) if wide else (24, -126, 127)
    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    if value < Fraction(2) ** exponent:
        exponent -= 1
    unit = Fraction(2) ** (max(exponent, minimum) - precision + 1)
    scaled = value / unit
    integer, remainder = divmod(scaled.numerator, scaled.denominator)
    twice = remainder * 2
    if twice > scaled.denominator or (twice == scaled.denominator and integer % 2):
        integer += 1
    rounded = integer * unit
    if rounded >= Fraction(2) ** (maximum + 1):
        return -math.inf if negative else math.inf
    # Only the final already-exact binary64 value is converted for comparing bits.
    result = float(rounded)
    return -result if negative else result
