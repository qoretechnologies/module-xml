"""Independent exact XSD 1.0 duration component parsing.

Component pairs preserve month quantities separately from decimal seconds.
Duration ordering/equality requires the additional four-anchor relation; this
module currently supplies exact lexical/native conversion checks only.
https://www.w3.org/TR/xmlschema-2/#duration

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from fractions import Fraction
import re


GRAMMAR = re.compile(r'(-)?P(?:([0-9]+)Y)?(?:([0-9]+)M)?(?:([0-9]+)D)?'
                     r'(?:T(?:([0-9]+)H)?(?:([0-9]+)M)?(?:([0-9]+(?:\.[0-9]+)?)S)?)?')


def components(text):
    text = re.sub(r'[ \t\r\n]+', ' ', text).strip(' ')
    match = GRAMMAR.fullmatch(text)
    if match is None or text.endswith('T') or not any(match.groups()[1:]):
        raise ValueError('invalid XSD 1.0 duration grammar')
    sign, years, months, days, hours, minutes, seconds = match.groups()
    multiplier = -1 if sign else 1
    month_count = (int(years or 0) * 12 + int(months or 0)) * multiplier
    second_count = (int(days or 0) * 86400 + int(hours or 0) * 3600 + int(minutes or 0) * 60
                    + Fraction(seconds or '0')) * multiplier
    return month_count, second_count
