#!/usr/bin/env python3
"""Pinned sources for MTOM/XOP and attachment references.

Copyright (C) 2026 Qore Technologies, s.r.o.

The XOP 1.0 and SOAP 1.2 MTOM Recommendations and RFC 2392 are kept verbatim in normative/, and
normative/sources.json records each file's SHA-256 and size.

The SOAP with Attachments Note and the WS-I Attachments Profile 1.0 may not be redistributed. The Note
is pinned by digest together with the section 3 phrases the href resolution follows; run
"test_attachment_sources.py --verify-swa-note <copy>" to check them against a retrieved copy. The
profile is pinned as the reproducible requirement extract that wsi_requirements.py produces.
"""
import hashlib
import html
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
import unittest

import wsi_requirements

ROOT = Path(__file__).resolve().parent / 'normative'
VERBATIM = {'xop10', 'soap12_mtom', 'rfc2392'}


def note_text(data):
    """The whitespace-normalized text of the SwA Note's HTML."""
    return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', data.decode('utf-8'))).split())


def verify_swa_note(path):
    """Return the problems found checking a retrieved copy of the SwA Note against its pin."""
    entry = json.loads((ROOT / 'sources.json').read_text())['attachments']['swa_note']
    data = Path(path).read_bytes()
    if (len(data), hashlib.sha256(data).hexdigest()) != (entry['html_bytes'], entry['html_sha256']):
        return [f'{path} does not match the pinned digest']
    text = note_text(data)
    return [f'quote not present verbatim: {quote!r}' for quote in entry['quotes'] if quote not in text]


class AttachmentSourcesTest(unittest.TestCase):
    def test_pinned_sources(self):
        attachments = json.loads((ROOT / 'sources.json').read_text())['attachments']
        entries = {k: v for k, v in attachments.items() if isinstance(v, dict)}
        self.assertEqual(VERBATIM | {'swa_note', 'wsi_ap10'}, set(entries))
        for name in VERBATIM:
            entry = entries[name]
            with self.subTest(source=name):
                data = (ROOT / entry['path']).read_bytes()
                self.assertEqual((entry['bytes'], entry['sha256']), (len(data), hashlib.sha256(data).hexdigest()))
                self.assertTrue(entry['url'].startswith('https://'))

    def test_non_redistributable_sources_are_pinned_without_copies(self):
        attachments = json.loads((ROOT / 'sources.json').read_text())['attachments']
        note = attachments['swa_note']
        self.assertFalse(note['redistributed'])
        self.assertRegex(note['html_sha256'], r'^[0-9a-f]{64}$')
        self.assertGreater(note['html_bytes'], 0)
        self.assertTrue(note['url'].startswith('https://'))
        # each quote must be specific enough to locate one rule, and none may repeat another
        self.assertTrue(all(len(q) >= 12 for q in note['quotes']))
        self.assertEqual(len(note['quotes']), len(set(note['quotes'])))
        self.assertFalse(any(p.name.lower().startswith(('soap-attachments', 'wsi-ap', 'attachmentsprofile'))
                             and p.suffix in ('.html', '.htm', '.txt') for p in ROOT.iterdir()))

    def test_attachments_profile_extract(self):
        entry = json.loads((ROOT / 'sources.json').read_text())['attachments']['wsi_ap10']
        pinned = json.loads((ROOT / entry['path']).read_text())
        requirements = {k: v['statement'] for k, v in pinned['requirements'].items()}
        self.assertEqual(pinned['requirement_count'], len(requirements))
        # the digest covers the statements exactly as wsi_requirements.extract() returns them
        self.assertEqual(pinned['extract_sha256'], wsi_requirements.digest(requirements))
        self.assertEqual((entry['url'], entry['title']), (pinned['url'], pinned['title']))
        for rid in entry['cited']:
            self.assertIn(rid, requirements)
        self.assertIn('ref:swaRef schema type MUST resolve to a MIME part in the same message',
                      requirements['R2928'])
        self.assertIn('root part of multipart/related MESSAGE MUST be a soap:Envelope', requirements['R2931'])
        self.assertIn('MUST have the type parameter with a value of "text/xml"', requirements['R2932'])

    def test_extractor_reads_quoted_statement_classes(self):
        # the Attachments Profile quotes the class attribute and is published in iso-8859-1
        document = ('<p class="statement"><span class="statement-id"><a name="R1">R1</a></span>\n'
                    'A <span>MESSAGE</span> MUST be \xa9 marked.</p><p class=statement>R2 Unquoted.</p>'
                    '<p class="explanation">R3 Not a statement.</p>').encode('iso-8859-1')
        path = Path(self.tmp) / 'profile.html'
        path.write_bytes(document)
        self.assertEqual({'R1': 'A MESSAGE MUST be \xa9 marked.', 'R2': 'Unquoted.'},
                         wsi_requirements.extract(path))

    def test_note_verifier_rejects_a_different_copy(self):
        path = Path(self.tmp) / 'note.html'
        path.write_bytes(b'<html>SOAP Messages with Attachments</html>')
        self.assertEqual([f'{path} does not match the pinned digest'], verify_swa_note(path))

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

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
    if len(sys.argv) == 3 and sys.argv[1] == '--verify-swa-note':
        problems = verify_swa_note(sys.argv[2])
        for problem in problems:
            print(problem)
        sys.exit(1 if problems else 0)
    unittest.main()
