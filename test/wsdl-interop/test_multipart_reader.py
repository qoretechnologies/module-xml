#!/usr/bin/env python3
"""Independent MIME framing/octet checks and bidirectional SOAP HTTP transport.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import base64
from email import policy
from email.parser import BytesParser
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import subprocess
import threading
import unittest
import xml.etree.ElementTree as ET

from test_cxf_peer import endpoint

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
FIXTURES = ROOT / 'regressions/wsdl-multipart-reader'


def cases():
    return json.loads((FIXTURES / 'cases.json').read_text())['cases']


class MultipartReaderTests(unittest.TestCase):
    def test_independent_framing_and_bytes(self):
        rows = cases()
        self.assertEqual(50, len(rows))
        self.assertEqual(len(rows), len({row['name'] for row in rows}))
        for row in rows:
            if not row['valid']:
                continue
            with self.subTest(case=row['name']):
                wire = base64.b64decode(row['wire'], validate=True)
                message = BytesParser(policy=policy.default).parsebytes(
                    ('Content-Type: ' + row['media'] + '\r\nMIME-Version: 1.0\r\n\r\n').encode() + wire)
                self.assertEqual([], message.defects)
                parts = list(message.iter_parts())
                start = message.get_param('start')
                root = next(part for part in parts if str(part['Content-ID']).strip() == start) if start else parts[0]
                self.assertEqual(base64.b64decode(row['root']), root.get_payload(decode=True))
                self.assertEqual(message.get_param('type').lower(), root.get_content_type())
                self.assertEqual({key: base64.b64decode(value) for key, value in row['parts'].items()},
                                 {str(part['Content-ID']).strip()[1:-1]: part.get_payload(decode=True)
                                  for part in parts if part is not root and part['Content-ID']})
                self.assertEqual(row.get('unidentified', 0),
                                 sum(part is not root and not part['Content-ID'] for part in parts))
                for part in parts:
                    self.assertEqual([], part.defects)

    def test_bidirectional_http(self):
        names = {'root-at-byte-zero', 'root-last', 'base64-root', 'transfer-base64',
                 'transfer-quoted-printable', 'empty-attachment', 'many-attachments', 'case-and-folding', 'xop-root'}
        env = os.environ.copy()
        env['QORE_MODULE_DIR'] = os.pathsep.join(filter(None, (
            str(REPO / 'build-debug'), str(REPO / 'qlib'), env.get('QORE_MODULE_DIR'))))
        qore = [os.environ.get('QORE', 'qore'), '-b', '--enable-debug', str(FIXTURES / 'peer.qr')]
        exchanges = 0
        for row in cases():
            if row['name'] not in names:
                continue
            wire = base64.b64decode(row['wire'])
            for saved in ('source', 'saved', 'source-xml', 'saved-xml'):
                with self.subTest(case=row['name'], saved=saved):
                    observed = []

                    class Handler(BaseHTTPRequestHandler):
                        def do_POST(peer):
                            observed.append(peer.rfile.read(int(peer.headers['Content-Length'])))
                            peer.send_response(200)
                            peer.send_header('Content-Type', row['media'])
                            peer.send_header('Content-Length', str(len(wire)))
                            peer.end_headers()
                            peer.wfile.write(wire)

                        def log_message(peer, *args):
                            pass

                    with HTTPServer(('127.0.0.1', 0), Handler) as server:
                        server.timeout = 15
                        thread = threading.Thread(target=server.handle_request)
                        thread.start()
                        try:
                            result = subprocess.run([*qore, 'client', saved,
                                                     f'http://127.0.0.1:{server.server_port}/service'],
                                                    env=env, capture_output=True, text=True, timeout=20)
                        finally:
                            thread.join(20)
                        self.assertFalse(thread.is_alive())
                        self.assertEqual((0, 'PASS\n', ''),
                                         (result.returncode, result.stdout, result.stderr))
                        self.assertEqual(1, len(observed))
                        self.assertEqual('hello', ET.fromstring(observed[0]).find('.//payload').text)
                    with endpoint([*qore, 'server', saved], env) as (_, port):
                        conn = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
                        try:
                            conn.request('POST', '/service', wire,
                                         {'Content-Type': row['media']}
                                         | ({} if row['name'] == 'xop-root' else {'SOAPAction': 'urn:call'}))
                            response = conn.getresponse()
                            result = response.read()
                            self.assertEqual(200, response.status, result)
                            self.assertEqual('hello', ET.fromstring(result).find('.//payload').text)
                        finally:
                            conn.close()
                    exchanges += 2
        self.assertEqual(72, exchanges)

    def test_http_rejections_and_recovery(self):
        names = {'missing-root', 'duplicate-id', 'invalid-media', 'unknown-transfer'}
        rows = cases()
        valid = next(row for row in rows if row['name'] == 'root-at-byte-zero')
        env = os.environ.copy()
        env['QORE_MODULE_DIR'] = os.pathsep.join(filter(None, (
            str(REPO / 'build-debug'), str(REPO / 'qlib'), env.get('QORE_MODULE_DIR'))))
        qore = [os.environ.get('QORE', 'qore'), '-b', '--enable-debug', str(FIXTURES / 'peer.qr')]
        exchanges = 0
        for row in rows:
            if row['name'] not in names:
                continue
            wire = base64.b64decode(row['wire'])
            for saved in ('source', 'saved'):
                with self.subTest(case=row['name'], saved=saved):
                    class Handler(BaseHTTPRequestHandler):
                        def do_POST(peer):
                            peer.rfile.read(int(peer.headers['Content-Length']))
                            peer.send_response(200)
                            peer.send_header('Content-Type', row['media'])
                            peer.send_header('Content-Length', str(len(wire)))
                            peer.end_headers()
                            peer.wfile.write(wire)

                        def log_message(peer, *args):
                            pass

                    with HTTPServer(('127.0.0.1', 0), Handler) as server:
                        server.timeout = 15
                        thread = threading.Thread(target=server.handle_request)
                        thread.start()
                        try:
                            result = subprocess.run([*qore, 'client-negative', saved,
                                                     f'http://127.0.0.1:{server.server_port}/service'],
                                                    env=env, capture_output=True, text=True, timeout=20)
                        finally:
                            thread.join(20)
                        self.assertFalse(thread.is_alive())
                        self.assertEqual((0, 'PASS\n', ''),
                                         (result.returncode, result.stdout, result.stderr))
                    with endpoint([*qore, 'server', saved], env) as (_, port):
                        for message, status in ((row, 500), (valid, 200)):
                            conn = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
                            try:
                                conn.request('POST', '/service', base64.b64decode(message['wire']),
                                             {'Content-Type': message['media'], 'SOAPAction': 'urn:call'})
                                response = conn.getresponse()
                                result = response.read()
                                self.assertEqual(status, response.status, result)
                                tree = ET.fromstring(result)
                                if status == 500:
                                    self.assertIn('SOAP-MESSAGE-ERROR', tree.find('.//faultstring').text)
                                else:
                                    self.assertEqual('hello', tree.find('.//payload').text)
                            finally:
                                conn.close()
                    exchanges += 3
        self.assertEqual(24, exchanges)


if __name__ == '__main__':
    unittest.main()
