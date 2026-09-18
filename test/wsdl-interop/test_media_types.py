#!/usr/bin/env python3
"""Independent HTTP media-type grammar and MIME parameter interpretation.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from collections import defaultdict
from email.message import Message
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent
TOKEN = r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+"
QUOTED = r'"(?:[\x09\x20-\x21\x23-\x5b\x5d-\x7e\x80-\U0010ffff]|\\[\x09\x20-\x7e\x80-\U0010ffff])*"'
PARAMETER = TOKEN + '=(?:' + TOKEN + '|' + QUOTED + ')'
MEDIA = re.compile(r'[ \t]*(' + TOKEN + ')/(' + TOKEN + r')(?:[ \t]*;[ \t]*(?:'
                   + PARAMETER + r')?)*[ \t]*')


def read(value, *, pattern=False, nested=False):
    """RFC 9110 ABNF, with email's separate MIME parameter/quoted-pair parser."""
    if value is None:
        if not pattern:
            return None
        value = '*/*'
    grammar = MEDIA.fullmatch(value)
    if grammar is None:
        return None
    major, minor = (part.lower() for part in grammar.groups())
    if any('*' in part and not (pattern and part == '*') for part in (major, minor)):
        return None
    message = Message()
    message['Content-Type'] = value.strip(' \t')
    parameters = defaultdict(list)
    for name, item in message.get_params()[1:]:
        # Empty parameter slots are permitted by HTTP but represented as empty
        # names by the email parser. No actual named parameter is discarded.
        if name:
            parameters[name.lower()].append(item.lower() if name.lower() == 'charset' else item)
    if (major, minor) in (('multipart', 'related'), ('application', 'xop+xml')):
        types = []
        for item in parameters.get('type', []):
            parsed = read(item, nested=True)
            if parsed is None or (major == 'multipart' and parsed[2]):
                return None
            types.append((parsed[:2], tuple(sorted((key, tuple(sorted(set(values))))
                                                   for key, values in parsed[2].items()))))
        if types:
            parameters['type'] = types
    if (pattern or nested) and any(len(set(values)) != 1 for values in parameters.values()):
        return None
    return major, minor, dict(parameters)


def matches(actual, pattern):
    if actual is None:
        return False
    if any(wanted != '*' and found != wanted for found, wanted in zip(actual[:2], pattern[:2])):
        return False
    return all(name in actual[2] and set(actual[2][name]) == set(values)
               for name, values in pattern[2].items())


class MediaTypesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / 'regressions/wsdl-media-types/cases.json').read_text())

    def test_declarations_and_messages(self):
        rows = self.manifest['cases']
        self.assertEqual(91, len(rows))
        self.assertEqual(len(rows), len({row['name'] for row in rows}))
        for row in rows:
            with self.subTest(case=row['name']):
                pattern = read(row['pattern'], pattern=True)
                self.assertEqual(row['valid'], pattern is not None)
                actual = read(row['wire'])
                self.assertEqual(row['matches'], pattern is not None and matches(actual, pattern))

    def test_classification(self):
        rows = self.manifest['classification']
        self.assertEqual(18, len(rows))
        for row in rows:
            with self.subTest(content_type=row['type']):
                actual = read(row['type'])
                base = '/'.join(actual[:2]) if actual is not None else None
                self.assertEqual(row['soap'], base in ('text/xml', 'application/xml', 'application/soap+xml'))
                self.assertEqual(row['xop'], base == 'application/xop+xml')

    def test_independent_quoted_values(self):
        actual = read('TEXT/PLAIN;note="a;\\\"b\\\\c";Charset="UTF-8";empty=""')
        self.assertEqual(('text', 'plain', {'note':['a;"b\\c'], 'charset':['utf-8'], 'empty':['']}), actual)
        self.assertIsNone(read('text/plain;note="unclosed'))
        self.assertIsNone(read('text/plain;note =value'))


if __name__ == '__main__':
    unittest.main()
