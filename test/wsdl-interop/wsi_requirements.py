#!/usr/bin/env python3
"""Extract WS-I Basic Profile requirement statements into a stable, quotable form.

Copyright (C) 2026 Qore Technologies, s.r.o.

The published profiles are served through a CDN that rewrites contributor email addresses into
per-response obfuscation tokens. Two fetches of the same document therefore have the same length but
different bytes, so a digest of the raw HTML is not reproducible and cannot be used to pin the source.

What is stable is the requirement text itself. This module extracts each numbered requirement
statement and normalizes it; the extract is what the ledger quotes from and what carries a digest.
Re-running this module against a fresh download reproduces the extract exactly, which is the property
the pinning actually needs.
"""
import hashlib
import html as htmllib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROFILES = HERE / 'normative'
# Basic Profile 1.2 and 2.0 leave the class unquoted; Attachments Profile 1.0 quotes it.
STATEMENT = re.compile(r'<p class="?statement"?\s*>(.*?)</p>', re.S | re.I)
# The rendered statement always begins with its own identifier. The anchor is not reliable: R4005's
# anchor sits on the preceding rationale paragraph rather than on the statement itself.
IDENT = re.compile(r'^(R\d+)\b')
# The CDN rewrites contributor addresses per response; drop them so the extract is reproducible.
CF_EMAIL = re.compile(r'<a[^>]*?/cdn-cgi/l/email-protection.*?</a>', re.S | re.I)


def strip_markup(fragment):
    fragment = CF_EMAIL.sub('', fragment)
    fragment = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', '', fragment)
    fragment = re.sub(r'(?s)<[^>]+>', ' ', fragment)
    return htmllib.unescape(fragment)


def normalize(value):
    value = re.sub(r'\s+', ' ', value).strip()
    value = re.sub(r'\s+([)\].,;:])', r'\1', value)
    value = re.sub(r'([(\[])\s+', r'\1', value)
    return value


def extract(path):
    """Return {requirement id: statement text} for one profile document."""
    raw = Path(path).read_bytes()
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        # Attachments Profile 1.0 declares iso-8859-1 (its copyright sign is the byte 0xA9)
        text = raw.decode('iso-8859-1')
    out = {}
    for match in STATEMENT.finditer(text):
        statement = normalize(strip_markup(match.group(1)))
        ident = IDENT.match(statement)
        if not ident:
            continue
        body = statement[ident.end():].strip()
        if body:
            out[ident.group(1)] = body
    return out


def load(profile):
    """Load the pinned extract for a profile."""
    return json.loads((PROFILES / f'{profile}-requirements.json').read_text())['requirements']


def digest(mapping):
    canonical = json.dumps(mapping, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(canonical).hexdigest()


if __name__ == '__main__':
    for path in sys.argv[1:]:
        found = extract(path)
        print(f'{path}: {len(found)} requirements, extract sha256 {digest(found)[:16]}')
