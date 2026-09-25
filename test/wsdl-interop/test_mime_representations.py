#!/usr/bin/env python3
"""Independent WSDL MIME alternatives and bidirectional HTTP representation checks.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import hashlib
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
import xml.etree.ElementTree as ET

from independent import SchemaJob, run
from test_cxf_peer import endpoint
import jvm

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
FIXTURES = ROOT / 'regressions/wsdl-mime-representations'
WSDL = 'http://schemas.xmlsoap.org/wsdl/'
MIME = WSDL + 'mime/'


def cases():
    return json.loads((FIXTURES / 'cases.json').read_text())['cases']


def document(charset):
    return ('<?xml version="1.0" encoding="' + charset
            + '"?><payload>é &lt; &amp;</payload>').encode(charset)


def decoded_text(wire, charset):
    # RFC 2781: absent a BOM, the byte-order-neutral label defaults to big-endian.
    if charset == 'UTF-16' and not wire.startswith((b'\xff\xfe', b'\xfe\xff')):
        charset = 'utf-16-be'
    return wire.decode(charset)


class MimeRepresentationTests(unittest.TestCase):
    def test_independent_part_and_format_mapping(self):
        rows = cases()
        self.assertEqual(17, len(rows))
        self.assertEqual(17, len({row['name'] for row in rows}))
        for row in rows:
            tree = ET.fromstring(row['xml'])
            parts = {node.attrib['name'] for node in tree.find(f'{{{WSDL}}}message')}
            self.assertEqual(set(row['parts']), parts)
            for direction in ('input', 'output'):
                actual = {}
                for declaration in tree.find(f'{{{WSDL}}}binding/{{{WSDL}}}operation/{{{WSDL}}}{direction}'):
                    part = declaration.get('part')
                    media = declaration.get('type', '*/*')
                    kind = ('xml' if declaration.tag == f'{{{MIME}}}mimeXml' else
                            'form' if media == 'application/x-www-form-urlencoded' else 'content')
                    if kind != 'form':
                        self.assertIn(part, parts)
                    if kind == 'xml':
                        media = 'text/xml'
                    selector = 'form' if kind == 'form' else kind + ':' + part
                    if selector not in actual:
                        actual[selector] = dict(kind=kind, part=None if kind == 'form' else part, media_types=[media])
                    elif kind != 'xml':
                        actual[selector]['media_types'].append(media)
                with self.subTest(case=row['name'], direction=direction):
                    self.assertEqual(row['expected_formats'][direction], actual)
                    self.assertEqual(set(row.get('output_selectors', row['selectors'])
                                         if direction == 'output' else row['selectors']), set(actual))

    def test_published_grammar(self):
        sources = []
        core = ROOT / 'regressions/wsdl-grammar'
        data = json.loads((core / 'cases.json').read_text())
        sources.append((core, dict(file=data['schema_file'], sha256=data['schema_sha256'], url=WSDL), WSDL))
        http = ROOT / 'regressions/wsdl-http-mime-grammar'
        for source in json.loads((http / 'cases.json').read_text())['schemas']:
            if source['file'] == 'http.xsd':
                sources.append((http, source, WSDL + 'http/'))
        mime = ROOT / 'regressions/wsdl-mime-part-grammar'
        sources.append((mime, json.loads((mime / 'cases.json').read_text())['schema'], MIME))
        resources, imports = {}, []
        for directory, source, namespace in sources:
            content = (directory / source['file']).read_bytes()
            self.assertEqual(source['sha256'], hashlib.sha256(content).hexdigest())
            resources[source['url']] = content
            imports.append(f'<x:import namespace="{namespace}" schemaLocation="{source["url"]}"/>')
        schema = ('<x:schema xmlns:x="http://www.w3.org/2001/XMLSchema">' + ''.join(imports) + '</x:schema>').encode()
        result = run([SchemaJob('formats', 'urn:mime:formats', schema,
                                {row['name']: row['xml'].encode() for row in cases()})], resources)
        self.assertTrue(result['schemas']['formats']['ok'], result['schemas'])
        self.assertEqual([], result['schemas']['formats']['warnings'])
        for row in cases():
            with self.subTest(case=row['name']):
                # The published WS-I schema requires part; WSDL's form maps all parts without it.
                self.assertEqual(row['schema_valid'], result['documents'][row['name']]['ok'])
                self.assertEqual([], result['documents'][row['name']]['warnings'])

    def test_wsdl4j_representations(self):
        oracle = ROOT / 'oracle'
        for artifact in json.loads((oracle / 'wsdl4j-manifest.json').read_text())['artifacts']:
            self.assertEqual(artifact['sha256'], hashlib.sha256((oracle / artifact['path']).read_bytes()).hexdigest())
        with tempfile.TemporaryDirectory(prefix='wsdl-mime-formats-') as directory:
            jar = oracle / 'wsdl4j-1.6.3.jar'
            result = subprocess.run(['javac', '-Xlint:all', '-Werror', '-cp', str(jar), '-d', directory,
                                     str(oracle / 'WsdlMimePartsOracle.java')], capture_output=True,
                                    text=True, timeout=60, check=True, env=jvm.environment())
            self.assertEqual('', result.stdout + result.stderr)
            path = Path(directory) / 'contract.wsdl'
            for row in cases():
                with self.subTest(case=row['name']):
                    path.write_text(row['xml'])
                    result = subprocess.run(['java', '-cp', directory + os.pathsep + str(jar),
                                             'WsdlMimePartsOracle', str(path)], capture_output=True,
                                            text=True, timeout=30, check=True, env=jvm.environment())
                    self.assertEqual('', result.stderr)
                    tree, expected = ET.fromstring(row['xml']), []
                    for direction in ('input', 'output'):
                        for node in tree.find(f'{{{WSDL}}}binding/{{{WSDL}}}operation/{{{WSDL}}}{direction}'):
                            expected.append([direction, 'XML', node.get('part', 'null')]
                                            if node.tag == f'{{{MIME}}}mimeXml' else
                                            [direction, 'CONTENT', node.get('part', 'null'), node.get('type', 'null')])
                    self.assertEqual(expected, [line.split('\t') for line in result.stdout.splitlines()])

    def test_wire_peers(self):
        env = os.environ.copy()
        env['QORE_MODULE_DIR'] = os.pathsep.join(filter(None, (
            str(REPO / 'build-debug'), str(REPO / 'qlib'), env.get('QORE_MODULE_DIR'))))
        qore = [os.environ.get('QORE', 'qore'), '-b', '--enable-debug', str(FIXTURES / 'peer.qr')]
        rows, exchanges = cases(), 0
        with tempfile.TemporaryDirectory(prefix='xml-mime-peer-') as directory:
            path = Path(directory) / 'config.json'
            for overlap in (False, True):
                for selector in ('content:payload', 'xml:payload'):
                    for charset in ('UTF-8', 'ISO-8859-1', 'UTF-16'):
                        for saved in ('source', 'saved'):
                            row = rows[4 if overlap else 0]
                            media = ('text/xml' if selector.startswith('xml:') or overlap else 'text/plain')
                            media += ';charset=' + charset
                            path.write_text(json.dumps(dict(xml=row['xml'], overlap=overlap,
                                                           selector=selector, media=media)))
                            body = document(charset) if selector.startswith('xml:') else 'é < &'.encode(charset)
                            observed = []

                            class Handler(BaseHTTPRequestHandler):
                                def do_POST(peer):
                                    received = peer.rfile.read(int(peer.headers['Content-Length']))
                                    observed.append((peer.path, peer.headers.get_all('Content-Type'), received))
                                    peer.send_response(200)
                                    peer.send_header('Content-Type', media)
                                    peer.send_header('Content-Length', str(len(body)))
                                    peer.end_headers()
                                    peer.wfile.write(body)

                                def log_message(peer, *args):
                                    pass

                            with self.subTest(overlap=overlap, selector=selector, charset=charset, saved=saved):
                                with HTTPServer(('127.0.0.1', 0), Handler) as server:
                                    server.timeout = 15
                                    thread = threading.Thread(target=server.handle_request)
                                    thread.start()
                                    try:
                                        result = subprocess.run([*qore, 'client', str(path), saved,
                                                                 f'http://127.0.0.1:{server.server_port}/'], env=env,
                                                                capture_output=True, text=True, timeout=20)
                                    finally:
                                        thread.join(20)
                                    self.assertFalse(thread.is_alive())
                                    self.assertEqual((0, 'PASS\n', ''),
                                                     (result.returncode, result.stdout, result.stderr))
                                    self.assertEqual(1, len(observed))
                                    target, types, wire = observed[0]
                                    self.assertEqual('/call', target)
                                    self.assertEqual([media], types)
                                    if selector.startswith('xml:'):
                                        element = ET.fromstring(wire)
                                        self.assertEqual(('payload', 'é < &'), (element.tag, element.text))
                                        if charset == 'UTF-16':
                                            self.assertTrue(wire.startswith((b'\xff\xfe', b'\xfe\xff')))
                                        else:
                                            self.assertIn('é'.encode(charset), wire)
                                    else:
                                        self.assertEqual('é < &', decoded_text(wire, charset))
                                        if charset != 'UTF-16':
                                            self.assertEqual(body, wire)
                                with endpoint([*qore, 'server', str(path), saved], env) as (_, port):
                                    conn = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
                                    try:
                                        conn.request('POST', '/call', body, {'Content-Type': media})
                                        response = conn.getresponse()
                                        wire = response.read()
                                        self.assertEqual(200, response.status, wire)
                                        if selector.startswith('xml:'):
                                            element = ET.fromstring(wire)
                                            self.assertEqual(('payload', 'é < &'), (element.tag, element.text))
                                        else:
                                            self.assertEqual(media, response.getheader('Content-Type'))
                                            self.assertEqual('é < &', decoded_text(wire, charset))
                                            if charset != 'UTF-16':
                                                self.assertEqual(body, wire)
                                    finally:
                                        conn.close()
                                exchanges += 2
        self.assertEqual(48, exchanges)


if __name__ == '__main__':
    unittest.main()
