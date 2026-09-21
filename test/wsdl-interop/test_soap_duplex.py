#!/usr/bin/env python3
"""SOAP full-duplex buffered requests and early responses. Copyright (C) 2026 Qore Technologies, s.r.o."""
import contextlib
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
from test_soap_envelope import ENV, URI
from test_soap_http_binding import media
import test_soap_oneway

PEER = Path(__file__).resolve().parent / 'soap-duplex-peer'

# The peer bounds both socket buffers so a request of REQUEST bytes cannot be absorbed while the peer is
# not reading, and a response of RESPONSE bytes cannot be absorbed while the client is not reading.  A
# serialized send-then-receive client cannot complete these exchanges at all; completion requires both
# directions to progress together.  The measured threshold for a serialized reference client on this
# transport is a 512 KiB request with a 256 KiB response, so the scripted sizes keep a factor of two.
BUFFER = 2048
REQUEST = 1024 * 1024
RESPONSE = 512 * 1024
TIMEOUT = 60000
SHORT_TIMEOUT = 3000
RELEASE_DEADLINE = 120

FAULT_REASON = 'duplex fault'
FAULT_CODE = {'11': 'Server', '12': 'Receiver'}
DRAINING = ('respond', 'respond-chunked', 'fault')


def response_envelope(version, size):
    return (f'<s:Envelope xmlns:s="{URI[version]}"><s:Body>'
            f'<t:value xmlns:t="urn:soap-envelope-test">{"y" * size}</t:value>'
            '</s:Body></s:Envelope>').encode()


def fault_envelope(version, size):
    detail = 'z' * size
    if version == '11':
        body = (f'<s:Fault><faultcode>s:{FAULT_CODE[version]}</faultcode>'
                f'<faultstring>{FAULT_REASON}</faultstring>'
                f'<detail><d:info xmlns:d="urn:soap-envelope-test">{detail}</d:info></detail></s:Fault>')
    else:
        body = (f'<s:Fault><s:Code><s:Value>s:{FAULT_CODE[version]}</s:Value></s:Code>'
                f'<s:Reason><s:Text xml:lang="en">{FAULT_REASON}</s:Text></s:Reason>'
                f'<s:Detail><d:info xmlns:d="urn:soap-envelope-test">{detail}</d:info></s:Detail></s:Fault>')
    return f'<s:Envelope xmlns:s="{URI[version]}"><s:Body>{body}</s:Body></s:Envelope>'.encode()


def headers(version, framing, status='200 OK', keep=False):
    return (f'HTTP/1.1 {status}\r\nConnection: {"keep-alive" if keep else "close"}\r\n'
            f'Content-Type: {media(version)}\r\n{framing}\r\n\r\n').encode()


def chunked(payload):
    return b'%x\r\n' % len(payload) + payload + b'\r\n0\r\n\r\n'


class Exchange:
    """One scripted request/response on a peer connection."""

    def __init__(self, step, behavior, keep=False):
        self.step = step
        self.behavior = behavior
        self.keep = keep


def script():
    """Ordered peer connections for one web-service graph and value mode.

    ``cancel`` and ``timeout`` answer on keep-alive connections, so an interrupted exchange leaves a
    connection the client is invited to reuse.  Each recovery step is scripted as a new connection, so a
    client that reused a connection carrying an incomplete upload would never be served.
    """
    return [
        [Exchange('duplex', 'respond')],
        [Exchange('chunked', 'respond-chunked')],
        [Exchange('fault', 'fault')],
        [Exchange('fault-recovery', 'respond')],
        [Exchange('eof', 'eof')],
        [Exchange('eof-recovery', 'respond')],
        [Exchange('cancel', 'hold', keep=True)],
        [Exchange('cancel-recovery', 'respond')],
        [Exchange('timeout', 'hold', keep=True)],
        [Exchange('timeout-recovery', 'respond')],
        [Exchange('keepalive', 'respond', keep=True), Exchange('keepalive-reuse', 'respond')],
    ]


STEPS = [exchange.step for connection in script() for exchange in connection]
HELD = [exchange.step for connection in script() for exchange in connection
        if exchange.behavior == 'hold']


def read_headers(sock):
    data = b''
    while b'\r\n\r\n' not in data:
        chunk = sock.recv(65536)
        if not chunk:
            raise EOFError('incomplete request headers')
        data += chunk
        if len(data) > 1024 * 1024:
            raise ValueError('unexpectedly large request headers')
    head, body = data.split(b'\r\n\r\n', 1)
    if not head.startswith(b'POST '):
        raise ValueError('unexpected request method')
    length = int(next(line.split(b':', 1)[1] for line in head.split(b'\r\n')
                      if line.lower().startswith(b'content-length:')))
    return length, body


def drain(sock, length, body):
    while len(body) < length:
        chunk = sock.recv(262144)
        if not chunk:
            raise EOFError('incomplete request body')
        body += chunk
    if len(body) != length:
        raise ValueError('unexpected extra request bytes')
    return body


@contextlib.contextmanager
def served(server):
    """Serve connections until an explicit stop signal, without polling for readiness."""
    stopping, stopped = socket.socketpair()
    failures = queue.Queue()
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
            except BaseException as error:  # noqa: BLE001 - reported to the owning test thread
                failures.put(error)

        worker = threading.Thread(target=serve)
        worker.start()
        try:
            yield server.server_address[1]
        finally:
            stopping.sendall(b'STOP')
            worker.join(60)
            if worker.is_alive():
                raise AssertionError('raw SOAP peer did not finish')
            if not failures.empty():
                raise AssertionError('raw SOAP peer accept loop failed') from failures.get_nowait()


@contextlib.contextmanager
def duplex_peer(version, connections, observed, requests, errors, releases, capture=False):
    """Answer each scripted request before the buffered request body has been drained."""
    pending = queue.Queue()
    for index, connection in enumerate(connections):
        pending.put((index, connection))
    # Each accepted socket carries its own scripted connection. The accept thread assigns it before
    # the handler thread starts, so overlapping accepts cannot race over a shared attribute.
    assignments = {}
    payload = response_envelope(version, RESPONSE)
    fault = fault_envelope(version, RESPONSE)

    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            try:
                self.request.settimeout(120)
                index, connection_script = assignments.pop(self.request)
                for position, exchange in enumerate(connection_script):
                    length, body = read_headers(self.request)
                    # Records are queued when a handler finishes, and a draining handler can outlive
                    # the client call it answered, so each record carries its accept order.
                    record = {'step': exchange.step, 'length': length, 'behavior': exchange.behavior,
                              'order': (index, position)}
                    if exchange.behavior == 'respond':
                        reply = headers(version, f'Content-Length: {len(payload)}', keep=exchange.keep) + payload
                    elif exchange.behavior == 'respond-chunked':
                        reply = headers(version, 'Transfer-Encoding: chunked', keep=exchange.keep) + chunked(payload)
                    elif exchange.behavior == 'fault':
                        reply = headers(version, f'Content-Length: {len(fault)}',
                                        '500 Internal Server Error') + fault
                    elif exchange.behavior == 'eof':
                        reply = headers(version, f'Content-Length: {len(payload)}') + payload[:64]
                    elif exchange.behavior == 'hold':
                        reply = headers(version, f'Content-Length: {len(payload)}', keep=exchange.keep)
                    else:
                        raise ValueError('unknown peer behavior')
                    self.request.sendall(reply)
                    # Request-body bytes read at the moment the whole response had been written: a value
                    # below the declared length is only reachable when the client consumed the response
                    # while it was still sending, which a serialized client cannot do.
                    record['before'] = len(body)
                    record['sent'] = len(reply)
                    if exchange.behavior in DRAINING:
                        body = drain(self.request, length, body)
                        record['drained'] = len(body)
                        if capture:
                            requests.put(body)
                    elif exchange.behavior == 'hold':
                        # The peer never drains a held request, so the client announces its own
                        # completion over the control channel instead.
                        releases[exchange.step].get(timeout=RELEASE_DEADLINE)
                    observed.put(record)
                    if not exchange.keep:
                        break
            except BaseException as error:  # noqa: BLE001 - reported to the owning test thread
                errors.put(error)

    class Server(socketserver.ThreadingTCPServer):
        daemon_threads = True
        allow_reuse_address = True

        def server_bind(self):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFFER)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, BUFFER)
            super().server_bind()

        def process_request(self, request, client_address):
            try:
                assignments[request] = pending.get_nowait()
            except queue.Empty:
                errors.put(AssertionError('unscripted peer connection'))
                self.close_request(request)
                return
            super().process_request(request, client_address)

    with Server(('127.0.0.1', 0), Handler) as server, served(server) as port:
        yield f'http://127.0.0.1:{port}/service'


@contextlib.contextmanager
def control_channel(releases, errors):
    """Accept the client's completion announcements for exchanges the peer never drains."""

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            try:
                releases[self.rfile.readline().decode().strip()].put(True)
            except BaseException as error:  # noqa: BLE001 - reported to the owning test thread
                errors.put(error)

    class Server(socketserver.ThreadingTCPServer):
        daemon_threads = True
        allow_reuse_address = True

    with Server(('127.0.0.1', 0), Handler) as server, served(server) as port:
        yield port


class SoapDuplexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_soap_oneway.OneWayTests.setUpClass()
        cls.schemas = test_soap_oneway.OneWayTests.schemas

    @staticmethod
    def expectations(version):
        recovery = {'error': 'OK', 'status': 200, 'value_size': RESPONSE}
        rows = {
            'fault': {'error': 'SOAP-SERVER-FAULT-RESPONSE', 'status': 500,
                      'fault_code': f's:{FAULT_CODE[version]}', 'fault_text': FAULT_REASON,
                      'fault_detail_size': RESPONSE, 'fault_detail_ns': 'urn:soap-envelope-test'},
            # Both directions are active when the peer closes, so either side may observe the
            # closure first depending on how much of the request the transport had buffered; both
            # are correct and both are terminal. This is safe to accept only because the peer
            # step-accounting assertion above runs first and would already have failed if the client
            # had skipped the exchange instead of performing it.
            'eof': {'error': ('SOCKET-SEND-ERROR', 'SOCKET-CLOSED'), 'status': None},
            'cancel': {'error': 'THREAD-CANCELLED', 'status': None,
                       'cancelled': True, 'reason_preserved': True},
            'timeout': {'error': 'SOCKET-TIMEOUT', 'status': None},
        }
        return [rows.get(step, recovery) for step in STEPS]

    def drive(self, version, states, modes, steps, connections, observed, requests, errors, capture=False):
        releases = {step: queue.Queue() for step in HELD}
        with control_channel(releases, errors) as control_port, \
                duplex_peer(version, connections, observed, requests, errors, releases, capture) as url:
            job = {'version': version, 'url': url, 'control_port': control_port, 'states': states,
                   'modes': modes, 'request_size': REQUEST, 'steps': steps,
                   'timeout': TIMEOUT, 'short_timeout': SHORT_TIMEOUT}
            result = subprocess.run(['qore', '-b', '--enable-debug', str(PEER / 'client.qr')],
                                    input=json.dumps(job), env=ENV, text=True, capture_output=True,
                                    timeout=900)
            self.assertEqual((0, ''), (result.returncode, result.stderr), result.stdout + result.stderr)
            rows = json.loads(result.stdout)
        if not errors.empty():
            raise AssertionError('raw duplex peer failed') from errors.get_nowait()
        return rows

    def run_matrix(self, version, states, modes):
        cells = len(states) * len(modes)
        connections = [connection for _ in range(cells) for connection in script()]
        observed, requests, errors = queue.Queue(), queue.Queue(), queue.Queue()
        actual = self.drive(version, states, modes, STEPS, connections, observed, requests, errors)

        records = []
        while not observed.empty():
            records.append(observed.get_nowait())
        records.sort(key=lambda record: record['order'])
        # Checked before the per-call outcomes: every scripted step must have reached the peer. A
        # client that reused a pooled connection the peer had already closed would fail a call
        # without opening a connection, and this is the assertion that says so plainly instead of
        # surfacing as an unexplained transport error on the next row.
        self.assertEqual([step for _ in range(cells) for step in STEPS],
                         [record['step'] for record in records],
                         f'{version}: the peer was not asked for every scripted step')
        for record in records:
            self.assertLess(record['before'], record['length'], record['step'])
            if record['behavior'] in DRAINING:
                self.assertGreater(record['sent'], RESPONSE, record['step'])
                self.assertEqual(record['length'], record['drained'], record['step'])

        expected = [dict(row, name=step, state=state, retained=mode)
                    for state in states for mode in modes
                    for step, row in zip(STEPS, self.expectations(version))]
        self.assertEqual(len(expected), len(actual))
        for want, row in zip(expected, actual):
            context = (version, row['name'], row['state'], row['retained'])
            if isinstance(want['error'], tuple):
                self.assertIn(row['error'], want['error'], context)
                self.assertEqual({k: v for k, v in want.items() if k != 'error'},
                                 {k: v for k, v in row.items() if k != 'error'}, context)
            else:
                self.assertEqual(want, row, context)
        return len(actual)

    def test_duplex_matrix(self):
        """Every graph state and value mode completes buffered requests against early responses."""
        self.assertEqual(144, sum(self.run_matrix(version, ['source', 'saved', 'data'], [False, True])
                                  for version in ('11', '12')))

    def test_duplex_request_is_conforming(self):
        """The request delivered under full duplex is a schema-valid envelope carrying the whole value."""
        count = 0
        for version in ('11', '12'):
            observed, requests, errors = queue.Queue(), queue.Queue(), queue.Queue()
            connections = [[Exchange('duplex', 'respond')]]
            rows = self.drive(version, ['source'], [False], ['duplex'], connections, observed,
                              requests, errors, capture=True)
            self.assertEqual([{'name': 'duplex', 'state': 'source', 'retained': False, 'error': 'OK',
                               'status': 200, 'value_size': RESPONSE}], rows)
            body = requests.get_nowait()
            self.assertTrue(requests.empty())
            document = etree.fromstring(body)
            self.schemas[version].assertValid(document)
            value = document.find('.//{urn:soap-envelope-test}value')
            self.assertEqual(REQUEST, len(value.text))
            self.assertEqual({'x'}, set(value.text))
            count += 1
        self.assertEqual(2, count)


if __name__ == '__main__':
    unittest.main(verbosity=2)
