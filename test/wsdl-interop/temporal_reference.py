"""Exact XSD 1.0 clock reference using ordinal days and rational seconds.

Minute/second pairs distinguish a leap second from the following minute. Daily
clock identity discards the date after timezone normalization. This uses the
leap-second value interpretation approved on 2026-09-10; Appendix E's duration
addition does not define timezone-equivalent leap seconds consistently.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from dataclasses import dataclass
from fractions import Fraction
import re

from calendar_reference import collapse, ordinal, leap, MONTH_DAYS

CLOCK = r'(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})(?:\.(?P<fraction>[0-9]+))?'
DAY = r'(?P<year>-?[0-9]{4,})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})T'
ZONE = r'(?P<zone>Z|[+-][0-9]{2}:[0-9]{2})?'


@dataclass(frozen=True)
class TemporalValue:
    zoned: bool
    minute: int
    second: Fraction

    def compare(self, other):
        left = self.minute, self.second
        right = other.minute, other.second
        if self.zoned == other.zoned:
            return (left > right) - (left < right)
        uncertainty_left = 0 if self.zoned else 840
        uncertainty_right = 0 if other.zoned else 840
        if (self.minute + uncertainty_left, self.second) < (other.minute - uncertainty_right, other.second):
            return -1
        if (self.minute - uncertainty_left, self.second) > (other.minute + uncertainty_right, other.second):
            return 1
        return None


def value(builtin, text):
    if builtin not in ('dateTime', 'time'):
        raise ValueError('expected a clock datatype')
    match = re.fullmatch((DAY if builtin == 'dateTime' else '') + CLOCK + ZONE, collapse(text))
    if not match:
        raise ValueError('invalid XML clock grammar')
    f = match.groupdict()
    year = f.get('year', '2000')
    magnitude = year.removeprefix('-')
    if magnitude == '0000' or len(magnitude) > 4 and magnitude.startswith('0'):
        raise ValueError('invalid XML year')
    year, month, day = int(year), int(f.get('month', 1)), int(f.get('day', 1))
    if not 1 <= month <= 12 or not 1 <= day <= MONTH_DAYS[month - 1] + (month == 2 and leap(year)):
        raise ValueError('invalid Gregorian date')
    hour, minute, second = map(int, (f['hour'], f['minute'], f['second']))
    fraction = f['fraction'] or ''
    seconds = Fraction(second) + Fraction(int(fraction or '0'), 10 ** len(fraction))
    if hour > 24 or minute > 59 or second > 60 or hour == 24 and (minute or seconds):
        raise ValueError('invalid clock fields')
    zone = f['zone']
    offset = 0
    if zone and zone != 'Z':
        h, m = int(zone[1:3]), int(zone[4:])
        if h > 14 or m > 59 or h == 14 and m:
            raise ValueError('invalid XML timezone')
        offset = (h * 60 + m) * (1 if zone[0] == '+' else -1)
    result = ordinal(year, month, day) * 1440 + hour * 60 + minute - offset
    if second == 60:
        # Candidate UTC instants use exact ordinal arithmetic, independent of the
        # production implementation's calendar carry and string comparisons.
        quarter_days = {ordinal(y, m, d) for y in (year - 1 or -1, year, year + 1 or 1)
                        for m, d in ((3, 31), (6, 30), (9, 30), (12, 31))}
        if zone:
            candidate_day, candidate_minute = divmod(result, 1440)
            possible = candidate_minute == 1439 and (builtin == 'time' or candidate_day in quarter_days)
        else:
            possible = builtin == 'time' or any(abs(result - (day * 1440 + 1439)) <= 840
                                                 for day in quarter_days)
        if not possible:
            result += 1
            seconds -= 60
    if builtin == 'time':
        result %= 1440
    return TemporalValue(zone is not None, result, seconds)
