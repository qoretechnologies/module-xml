"""Independent exact XSD 1.0 duration parsing and four-reference-date relation.

Component pairs preserve month quantities separately from decimal seconds.
Duration ordering/equality compares all four Appendix E sums. Integer years
and Fraction seconds avoid native limits and floating-point rounding.
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


ANCHORS = ((1696, 9), (1697, 2), (1903, 3), (1903, 7))
MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

def ordinal(year, month):
    # Appendix E adds the numeric year/month components directly. These internal
    # arithmetic years need not be valid XML lexical year labels.
    prior = year - 1
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    return 365 * prior + prior // 4 - prior // 100 + prior // 400 + sum(MONTH_DAYS[:month-1]) + (month > 2 and leap)


def value(text):
    months, seconds = components(text)
    result = []
    for year, month in ANCHORS:
        target_year, target_month = divmod(year * 12 + month - 1 + months, 12)
        result.append(ordinal(target_year, target_month + 1) * 86400 + seconds)
    return tuple(result)


def compare(left, right):
    relations = {(a > b) - (a < b) for a, b in zip(value(left), value(right))}
    return relations.pop() if len(relations) == 1 else None
