#!/usr/bin/env python3
"""SOAP transport interruption boundaries. Copyright (C) 2026 Qore Technologies, s.r.o."""
import contextlib
import http.client
import json
from pathlib import Path
import queue
import selectors
import socket
import socketserver
import subprocess
import threading
import unittest
from lxml import etree
from test_cxf_peer import endpoint
from test_soap_http_binding import ENV, envelope, media
import test_soap_oneway

PEER = Path(__file__).resolve().parent / 'soap-transport-peer'


def response_headers(version, framing, status='200 OK'):
    return (f'HTTP/1.1 {status}\r\nConnection: close\r\nContent-Type: {media(version)}\r\n'
            f'{framing}\r\n\r\n').encode()


@contextlib.contextmanager
def interrupted_peer(replies, validate, *, method="POST"):
    """Accept complete requests, deliver scripted bytes and join through a stop socket.

    The cancellation peer waits for client EOF after delivering response headers;
    neither readiness nor cancellation relies on a sleep or repeated state checks.
    """
    received = queue.Queue()
    errors = queue.Queue()

    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            try:
                self.request.settimeout(15)
                data = b''
                while b'\r\n\r\n' not in data:
                    chunk = self.request.recv(65536)
                    if not chunk:
                        raise EOFError('incomplete request headers')
                    data += chunk
                    if len(data) > 1024 * 1024:
                        raise ValueError('unexpectedly large request')
                headers, body = data.split(b'\r\n\r\n', 1)
                if not headers.startswith(method.encode() + b' '):
                    raise ValueError('unexpected request method')
                length = int(next((line.split(b':', 1)[1] for line in headers.split(b'\r\n')
                                  if line.lower().startswith(b'content-length:')), b'0'))
                if not 0 <= length < 1024 * 1024 or (method == 'POST' and not length):
                    raise ValueError('unexpected request length')
                while len(body) < length:
                    chunk = self.request.recv(length - len(body))
                    if not chunk:
                        raise EOFError('incomplete request body')
                    body += chunk
                if len(body) != length:
                    raise ValueError('unexpected extra request bytes')
                validate(body)
                name, reply = replies.get_nowait()
                received.put(name)
                if reply:
                    self.request.sendall(reply)
                if name == 'cancel':
                    if self.request.recv(1) != b'':
                        raise AssertionError('cancellation did not close the interrupted transport')
            except BaseException as error:
                errors.put(error)

    with socketserver.TCPServer(('127.0.0.1', 0), Handler) as server:
        stopping, stopped = socket.socketpair()
        with stopping, stopped, selectors.DefaultSelector() as selector:
            selector.register(server, selectors.EVENT_READ, 'request')
            selector.register(stopped, selectors.EVENT_READ, 'stop')

            def serve():
                try:
                    while True:
                        for key, _ in selector.select():
                            if key.data == 'stop':
                                return
                            server.handle_request()
                except BaseException as error:
                    errors.put(error)

            worker = threading.Thread(target=serve)
            worker.start()
            try:
                yield f'http://127.0.0.1:{server.server_address[1]}', received
            finally:
                stopping.sendall(b'STOP')
                worker.join(20)
                if worker.is_alive():
                    raise AssertionError('raw SOAP peer did not finish')
                if not errors.empty():
                    raise AssertionError('raw SOAP peer failed') from errors.get_nowait()


class SoapTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_soap_oneway.OneWayTests.setUpClass()
        cls.schemas = test_soap_oneway.OneWayTests.schemas

    def client_case(self, version, one_way, cancel, soap_response=False):
        xml = envelope(version)
        good = (response_headers(version, 'Content-Length: 0', '202 Accepted') if one_way else
                response_headers(version, f'Content-Length: {len(xml)}') + xml)
        if cancel:
            # Both length and chunk framing leave a receive operation pending after headers.
            bad = [('cancel', response_headers(version, f'Content-Length: {len(xml)}')),
                   ('cancel', response_headers(version, 'Transfer-Encoding: chunked'))]
        else:
            bad = [('before-headers', b''), ('status-prefix', b'HTTP/1.1 20'),
                   ('short-body', response_headers(version, f'Content-Length: {len(xml)}') + xml[:60]),
                   ('short-chunk', response_headers(version, 'Transfer-Encoding: chunked') + b'20\r\nabc')]
        replies = queue.Queue()
        names = []
        expected = []
        for _ in range(6):
            for name, reply in bad:
                replies.put((name, reply))
                replies.put(('recovery', good))
                names.extend((name, 'recovery'))
                error = {'error': 'THREAD-CANCELLED' if cancel else 'SOCKET-CLOSED',
                         'status': None, 'headers_processed': 0}
                if cancel:
                    error.update(cancelled=True, reason_preserved=True)
                expected.append(error)
                expected.append({'error': 'OK', 'status': 202 if one_way else 200,
                                 'value': None if one_way else 'response', 'headers_processed': 0 if one_way else 1})

        def validate(body):
            if soap_response:
                self.assertEqual(b'', body)
                return
            document = etree.fromstring(body)
            self.schemas[version].assertValid(document)
            self.assertEqual('invoice', document.find('.//{urn:soap-envelope-test}value').text)

        with interrupted_peer(replies, validate, method='GET' if soap_response else 'POST') as (url, received):
            result = subprocess.run(['qore', '-b', '--enable-debug', str(PEER / 'client.qr')],
                input=json.dumps({'version': version, 'url': url, 'one_way': one_way,
                                  'count': 2 * len(bad), 'cancel': cancel, 'soap_response':soap_response}),
                env=ENV, text=True, capture_output=True, timeout=120)
            self.assertEqual((0, ''), (result.returncode, result.stderr), result.stdout + result.stderr)
            actual = json.loads(result.stdout)
            self.assertEqual(len(expected), len(actual))
            for name, want, row in zip(names, expected, actual):
                self.assertEqual(want, row, (version, one_way, name))
            self.assertEqual(names, [received.get_nowait() for _ in names])
            self.assertTrue(received.empty())
            self.assertTrue(replies.empty())
        return len(expected)

    def test_client_eof_and_recovery(self):
        self.assertEqual(192, sum(self.client_case(version, one_way, False)
                                 for version in ('11', '12') for one_way in (False, True)))

    def test_client_cancel_and_recovery(self):
        self.assertEqual(96, sum(self.client_case(version, one_way, True)
                                for version in ('11', '12') for one_way in (False, True)))

    def test_get_response_interruption_and_recovery(self):
        self.assertEqual(72, sum(self.client_case('12', False, cancel, True) for cancel in (False, True)))

    def test_handler_incomplete_requests_and_recovery(self):
        count = 0
        for version in ('11', '12'):
            xml = envelope(version)
            prefix = f'POST /service HTTP/1.1\r\nHost: localhost\r\nContent-Type: {media(version)}\r\n'
            partial = [b'POST /service HTTP/1.',
                       (prefix + f'Content-Length: {len(xml)}\r\n\r\n').encode() + xml[:60],
                       (prefix + 'Transfer-Encoding: chunked\r\n\r\n20\r\nabc').encode()]
            for state in ('source', 'saved', 'data'):
                for mode in ('native', 'retained'):
                    for one_way in (False, True):
                        with endpoint(['qore', '-b', '--enable-debug', str(PEER / 'handler.qr'), version,
                                       state, mode, str(len(partial)), 'one-way' if one_way else 'two-way'], ENV) as (_, port):
                            for payload in partial:
                                with socket.create_connection(('127.0.0.1', port), timeout=10) as connection:
                                    connection.sendall(payload)
                                    connection.shutdown(socket.SHUT_WR)
                                    reply = b''
                                    while True:
                                        chunk = connection.recv(65536)
                                        if not chunk:
                                            break
                                        reply += chunk
                                        self.assertLess(len(reply), 1024 * 1024)
                                    self.assertNotIn(b'Envelope', reply)
                                connection = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
                                try:
                                    connection.request('POST', '/service', xml, {'Content-Type': media(version)})
                                    response = connection.getresponse()
                                    raw = response.read()
                                    self.assertEqual(202 if one_way else 200, response.status, raw)
                                    if one_way:
                                        self.assertEqual(b'', raw)
                                    else:
                                        document = etree.fromstring(raw)
                                        self.schemas[version].assertValid(document)
                                        self.assertEqual('response', document.find('.//{urn:soap-envelope-test}value').text)
                                finally:
                                    connection.close()
                                count += 2
        self.assertEqual(144, count)


if __name__ == '__main__':
    unittest.main(verbosity=2)
