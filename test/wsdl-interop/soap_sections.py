#!/usr/bin/env python3
"""Deterministic section extraction from the pinned SOAP 1.2 specification HTML.

Copyright (C) 2026 Qore Technologies, s.r.o.

The assertion ledger cites requirements by section number and quotes them verbatim. Both the ledger
and its verifier read the specification through this module so a quote is always checked against the
same text the ledger was written from.

Headings are taken from the documents' own heading elements rather than from flattened text. A
flattened document cannot distinguish a heading from a cross-reference to it -- "see 2.6 Processing
SOAP Messages" reads exactly like the heading it points at -- and picking the wrong one silently
truncates or relocates a section.
"""
import hashlib
import html as htmllib
import json
import re
from pathlib import Path

NORMATIVE = Path(__file__).resolve().parent / 'normative'
HEADING = re.compile(r'<h([1-6])\b[^>]*>(.*?)</h\1>', re.S | re.I)
ANCHOR = re.compile(r'<a\b[^>]*?name="([^"]+)"', re.I)
NUMBER = re.compile(r'^((?:[0-9]+|[A-E])(?:\.[0-9]+)*)\.?\s+(.*)$', re.S)


def strip_markup(fragment):
    fragment = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', '', fragment)
    fragment = re.sub(r'(?s)<[^>]+>', ' ', fragment)
    return htmllib.unescape(fragment)


def normalize(value):
    """Collapse whitespace, including the spaces markup removal leaves around punctuation."""
    value = re.sub(r'\s+', ' ', value).strip()
    value = re.sub(r'\s+([)\].,;:])', r'\1', value)
    value = re.sub(r'([(\[])\s+', r'\1', value)
    return value


def load(document):
    """Return {section number: {anchor, title, text}} for a pinned document."""
    raw = (NORMATIVE / f'{document}.html').read_bytes()
    text = raw.decode('utf-8', 'replace')
    found = []
    for match in HEADING.finditer(text):
        inner = match.group(2)
        anchor = ANCHOR.search(inner)
        label = normalize(strip_markup(inner))
        numbered = NUMBER.match(label)
        if not numbered:
            continue
        found.append({'number': numbered.group(1), 'title': numbered.group(2).strip(),
                      'anchor': anchor.group(1) if anchor else None,
                      'start': match.start(), 'body_start': match.end()})
    sections = {}
    for i, head in enumerate(found):
        end = found[i + 1]['start'] if i + 1 < len(found) else len(text)
        sections[head['number']] = {
            'anchor': head['anchor'], 'title': head['title'],
            'text': normalize(strip_markup(text[head['body_start']:end])),
        }
    return sections


def digest(document):
    return hashlib.sha256((NORMATIVE / f'{document}.html').read_bytes()).hexdigest()


if __name__ == '__main__':
    for document in ('soap12-part1', 'soap12-part2'):
        sections = load(document)
        print(document, 'sections:', len(sections), 'sha256:', digest(document)[:16])
    print(json.dumps({n: s['title'] for n, s in sorted(load('soap12-part1').items())[:6]}, indent=1))
