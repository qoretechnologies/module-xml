#!/usr/bin/env python3
"""Live SOAP 1.1 rpc/encoded interop with Apache Axis 1.4 in both directions.

Copyright (C) 2026 Qore Technologies, s.r.o.

The pinned SOAPBuilders round 2 contract is rejected as published: it uses Apache SOAP's xml-soap:Map without
declaring it. The derived contract adds the schema that Axis 1.4's own Java2WSDL emits (axis_interop.py).
Qore's async SoapClientIo client calls the Axis service with the values of Axis's TestClient, and Axis's
TestClient calls a Qore SoapHandler echo service; each side verifies every operation. Java 17 or later is required.
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest

from lxml import etree

import axis_interop
from test_axis_peer import AxisPeer, PEER, classpath
from test_cxf_peer import endpoint
import jvm

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
WSDL_NS = {'w': 'http://schemas.xmlsoap.org/wsdl/'}
QORE = [os.environ.get('QORE', 'qore'), '-b', '--enable-debug']
JAVA = ['java', '-Dorg.apache.commons.logging.Log=org.apache.commons.logging.impl.NoOpLog']
# Each exchange of 31 operations takes 1.3-2.0 s alone, and the whole gate under 9 s in the eight-lane full
# suite; the deadline only bounds a hang.
EXCHANGE_TIMEOUT = 120
# The HTTP/1.0 request headers Axis 1.4's HTTPSender writes (captured from its interop client).
AXIS_HTTP10 = ('POST /axis/services/echo HTTP/1.0\r\nContent-Type: text/xml; charset=utf-8\r\n'
               'Accept: application/soap+xml, application/dime, multipart/related, text/*\r\nUser-Agent: Axis/1.4\r\n'
               'Host: 127.0.0.1:%d\r\nCache-Control: no-cache\r\nPragma: no-cache\r\n'
               'SOAPAction: "http://soapinterop.org/"\r\nContent-Length: %d\r\n\r\n')


def operations():
    wsdl = etree.parse(str(axis_interop.DERIVED))
    return sorted(set(wsdl.xpath('//w:portType/w:operation/@name', namespaces=WSDL_NS)))


def http10(port, body):
    """Sends one request as Axis does; returns the status line, the headers and whether the server closed."""
    with socket.create_connection(('127.0.0.1', port), timeout=30) as sock:
        sock.sendall((AXIS_HTTP10 % (port, len(body))).encode() + body)
        data = b''
        while b'\r\n\r\n' not in data:
            chunk = sock.recv(65536)
            if not chunk:
                raise AssertionError('connection closed before the response header: %r' % data)
            data += chunk
        head, rest = data.split(b'\r\n\r\n', 1)
        lines = head.decode('iso-8859-1').split('\r\n')
        headers = {k.strip().lower(): v.strip() for k, v in (line.split(':', 1) for line in lines[1:])}
        # A server that keeps the connection says so in Connection; waiting for its end of stream would only hang.
        if headers.get('connection', '').lower() != 'close':
            return lines[0], headers, False
        while len(rest) < int(headers['content-length']):
            chunk = sock.recv(65536)
            if not chunk:
                raise AssertionError('connection closed inside the response body')
            rest += chunk
        return lines[0], headers, sock.recv(1) == b''


class AxisInteropTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='axis-interop-')
        # Registered first, so the directory is removed even when building the peer fails.
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.peer = AxisPeer(cls.temporary.name)
        cls.java = JAVA + ['-cp', classpath(cls.peer.classes)]
        cls.env = dict(os.environ)
        cls.env['QORE_MODULE_DIR'] = os.pathsep.join(filter(None, (
            str(REPO / 'build-debug'), str(REPO / 'qlib'), os.environ.get('QORE_MODULE_DIR'))))

    def test_derived_contract_is_reproducible(self):
        self.assertEqual(axis_interop.MAP_SCHEMA.read_text(), axis_interop.generate_map_schema())
        self.assertEqual(axis_interop.DERIVED.read_text(),
                         axis_interop.derive(axis_interop.ORIGINAL.read_text(), axis_interop.MAP_SCHEMA.read_text()))
        self.assertEqual(json.loads(axis_interop.PROVENANCE.read_text()), axis_interop.provenance())
        manifest = json.loads((PEER / 'manifest.json').read_text())
        self.assertIn(('contracts/InteropTest.wsdl', axis_interop.provenance()['source']['sha256']),
                      [(c['path'], c['sha256']) for c in manifest['contracts']])
        self.assertEqual(31, len(operations()))

    def test_published_contract_is_rejected(self):
        code = ('%modern\n%requires ./qlib/WSDL.qm\n'
                'try { new WebService(ReadOnlyFile::readTextFile(ARGV[0])); printf("accepted\\n"); }\n'
                'catch (hash<ExceptionInfo> ex) { printf("%s: %s\\n", ex.err, ex.desc); }\n')
        for path, expected in ((axis_interop.ORIGINAL, 'WSDL-ERROR: schema component QName "xml-soap:Map" references '
                                'namespace "http://xml.apache.org/xml-soap" without a corresponding import in this '
                                'schema document\n'), (axis_interop.DERIVED, 'accepted\n')):
            with self.subTest(path=path.name):
                result = subprocess.run(QORE + ['-e', code, str(path)], cwd=REPO, env=self.env, capture_output=True,
                                        text=True, timeout=300)
                self.assertEqual((0, expected, ''), (result.returncode, result.stdout, result.stderr))

    def test_qore_client_to_axis_server(self):
        with endpoint(self.java + ['AxisPeer', 'server', str(PEER / 'contracts' / 'deploy.wsdd')]) as (_, port):
            result = subprocess.run(QORE + [str(PEER / 'qore-client.qr'), 'http://127.0.0.1:%d/axis/services/echo' % port],
                                    env=self.env, capture_output=True, text=True, timeout=EXCHANGE_TIMEOUT)
        self.assertEqual((0, 'VERIFIED %d FAILURES 0\n' % len(operations()), ''),
                         (result.returncode, result.stdout, result.stderr))

    def test_axis_client_to_qore_server(self):
        capture = Path(self.temporary.name) / 'qore-server.jsonl'
        with endpoint(QORE + [str(PEER / 'qore-server.qr')], self.env) as (_, port):
            # Axis 1.4 sends HTTP/1.0 without keep-alive and reads each response until the connection closes
            # (RFC 9112 section 9.3). The request names no operation, so the server's dispatch record is unchanged.
            status, headers, closed = http10(port, b'<e:Envelope xmlns:e="http://schemas.xmlsoap.org/soap/envelope/">'
                                                   b'<e:Body><o:absent xmlns:o="http://soapinterop.org/"/></e:Body>'
                                                   b'</e:Envelope>')
            self.assertEqual(('HTTP/1.1 500 Internal Server Error', 'close', True),
                             (status, headers.get('connection', '').lower(), closed),
                             'the server must close an HTTP/1.0 connection without keep-alive')
            client = subprocess.run(self.java + ['-Daxis.ClientConfigFile=%s' % (self.peer.work / 'client-config.wsdd'),
                                                 '-Dqore.axis.capture=%s' % capture, 'AxisPeer', 'client',
                                                 'http://127.0.0.1:%d/axis/services/echo' % port],
                                    cwd=self.peer.work, capture_output=True, text=True, timeout=EXCHANGE_TIMEOUT,
                                    env=jvm.environment())
        self.assertEqual((0, 'VERIFIED %d FAILURES 0\n' % len(operations()), ''),
                         (client.returncode, client.stdout, client.stderr))
        captured = [json.loads(line) for line in capture.read_text().splitlines()]
        self.assertEqual(operations(), sorted(c['operation'] for c in captured))
        for row in captured:
            with self.subTest(operation=row['operation']):
                body = etree.fromstring(row['response'].encode()).find('{http://schemas.xmlsoap.org/soap/envelope/}Body')
                self.assertEqual('{http://soapinterop.org/}%sResponse' % row['operation'], body[0].tag)
                self.assertEqual('http://schemas.xmlsoap.org/soap/encoding/',
                                 body[0].get('{http://schemas.xmlsoap.org/soap/envelope/}encodingStyle'))


if __name__ == '__main__':
    unittest.main()
