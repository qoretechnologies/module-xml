"""Exact XSD 1.0 calendar reference using integer ordinal days, not native dates.

The six calendar primitives use the first instant of their period. Undefined
components are anchored to leap year 2000, month 1, day 1. Year labels omit zero;
leap years follow the Gregorian divisibility rule in XSD 1.0 Appendix E.
https://www.w3.org/TR/xmlschema-2/#date

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from dataclasses import dataclass
import re


FORMATS = {
    'date': r'(?P<year>-?[0-9]{4,})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})',
    'gYear': r'(?P<year>-?[0-9]{4,})',
    'gYearMonth': r'(?P<year>-?[0-9]{4,})-(?P<month>[0-9]{2})',
    'gMonthDay': r'--(?P<month>[0-9]{2})-(?P<day>[0-9]{2})',
    'gMonth': r'--(?P<month>[0-9]{2})',
    'gDay': r'---(?P<day>[0-9]{2})',
}
ZONE = r'(?P<zone>Z|[+-][0-9]{2}:[0-9]{2})?'
MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def collapse(text):
    return re.sub(r'[ \t\r\n]+', ' ', text).strip(' ')


def leap(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def ordinal(year, month, day):
    """Zero-based days from 0001-01-01; count negative labeled years directly."""
    count = year - 1 if year > 0 else -year
    years = 365 * count + count // 4 - count // 100 + count // 400
    return (years if year > 0 else -years) + sum(MONTH_DAYS[:month - 1]) + (month > 2 and leap(year)) + day - 1


@dataclass(frozen=True)
class CalendarValue:
    zoned: bool
    minute: int

    def compare(self, other):
        if self.zoned == other.zoned:
            return (self.minute > other.minute) - (self.minute < other.minute)
        left = 0 if self.zoned else 840
        right = 0 if other.zoned else 840
        if self.minute + left < other.minute - right:
            return -1
        if self.minute - left > other.minute + right:
            return 1
        return None


def value(builtin, text):
    match = re.fullmatch(FORMATS[builtin] + ZONE, collapse(text))
    if match is None:
        raise ValueError('invalid calendar grammar')
    fields = match.groupdict()
    label = fields.get('year', '2000')
    magnitude = label.removeprefix('-')
    if magnitude == '0000' or len(magnitude) > 4 and magnitude.startswith('0'):
        raise ValueError('year zero or extended leading zeros')
    year, month, day = int(label), int(fields.get('month', '1')), int(fields.get('day', '1'))
    if not 1 <= month <= 12 or not 1 <= day <= MONTH_DAYS[month - 1] + (month == 2 and leap(year)):
        raise ValueError('invalid Gregorian date')
    zone = fields['zone']
    offset = 0
    if zone is not None and zone != 'Z':
        hours, minutes = int(zone[1:3]), int(zone[4:])
        if minutes > 59 or hours > 14 or hours == 14 and minutes:
            raise ValueError('invalid timezone')
        offset = (1 if zone[0] == '+' else -1) * (hours * 60 + minutes)
    return CalendarValue(zone is not None, ordinal(year, month, day) * 1440 - offset)
