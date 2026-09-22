#!/usr/bin/env python3
"""Pinned sources for MTOM/XOP and attachment references.

Copyright (C) 2026 Qore Technologies, s.r.o.

The XOP 1.0 and SOAP 1.2 MTOM Recommendations and RFC 2392 are kept verbatim in normative/, and
normative/sources.json records each file's SHA-256 and size.
"""
import hashlib
import html
import json
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent / 'normative'


class AttachmentSourcesTest(unittest.TestCase):
    def test_pinned_sources(self):
        attachments = json.loads((ROOT / 'sources.json').read_text())['attachments']
        entries = {k: v for k, v in attachments.items() if isinstance(v, dict)}
        self.assertEqual({'xop10', 'soap12_mtom', 'rfc2392'}, set(entries))
        for name, entry in entries.items():
            with self.subTest(source=name):
                data = (ROOT / entry['path']).read_bytes()
                self.assertEqual((entry['bytes'], entry['sha256']), (len(data), hashlib.sha256(data).hexdigest()))
                self.assertTrue(entry['url'].startswith('https://'))

    @staticmethod
    def text(name):
        return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', (ROOT / name).read_text(encoding='utf-8'))).split())

    def test_sources_state_the_rules_the_implementation_cites(self):
        xop = self.text('xop10.html')
        mtom = self.text('soap12-mtom.html')
        rfc = self.text('rfc2392.txt')
        for phrase in ('Copyright', 'as the sole member of its [children] property, a xop:Include',
                       'The [normalized value] MUST be a valid URI per the cid: URI scheme'):
            self.assertTrue(phrase in xop, phrase)
        for phrase in ('extracted binary parts MUST NOT be referenced by more than one xop:Include',
                       'The startinfo parameter of the content-type header of the outer package MUST specify'):
            self.assertTrue(phrase in mtom, phrase)
        self.assertTrue('%' in rfc and 'cid' in rfc)


if __name__ == '__main__':
    unittest.main()
