#!/usr/bin/env python3
"""Native-precision time values through both SOAP bindings and detached consumers.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from datetime import time
import unittest

import test_builtin_list_values as atomic
import test_list_values as lists


def definitions():
    # Values are within Qore's microsecond representation. The remaining lexical
    # grammar/arbitrary-fraction/leap-second matrix belongs to the full time work.
    yield lists.ListCase("native-time", "time", "", tuple(
        (clock + zone, True)
        for clock in ("00:00:00", "00:00:00.000001", "12:34:56.123456", "23:59:59.999999")
        for zone in ("Z", "+00:00", "-00:00", "+05:30", "-03:30", "+14:00", "-14:00")))


def clock_value(base, text):
    if base != "time":
        raise ValueError("expected the time primitive")
    parsed = time.fromisoformat(text)
    if parsed.utcoffset() is None:
        raise ValueError("native output lost its explicit timezone")
    # Python's independent ISO parser supplies exact integer microseconds. The
    # daily value is compared on UTC's recurring 24-hour clock, not by spelling.
    micros = ((parsed.hour * 60 + parsed.minute) * 60 + parsed.second) * 1000000 + parsed.microsecond
    offset = parsed.utcoffset()
    offset_seconds = offset.days * 86400 + offset.seconds
    return (micros - offset_seconds * 1000000) % 86400000000


class TimeOutputTest(lists.ListValuesTest):
    case_definitions = staticmethod(definitions)
    case_schema = staticmethod(atomic.schema)
    parse_value = staticmethod(clock_value)

    def check_oracles(self, jobs, expected):
        super().check_oracles(jobs, expected)
        print(f"time output: {len(jobs)} schemas, {len(expected)} independent document verdicts", flush=True)

    @staticmethod
    def provider_value(case, lexical):
        return lexical


if __name__ == "__main__":
    unittest.main()
