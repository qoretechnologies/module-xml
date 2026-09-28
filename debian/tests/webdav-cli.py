#!/usr/bin/python3
# Copyright (C) 2026 David Nichols
# SPDX-License-Identifier: MIT
"""Check the packaged WebDAV CLI through HTTP and graceful SIGTERM shutdown."""
import argparse
import http.client
import os
from pathlib import Path
import signal
import socket
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('script', type=Path)
args = parser.parse_args()
script = args.script.resolve()
subprocess.run(['/usr/bin/qore', str(script), '--help'], check=True, timeout=30)
with tempfile.TemporaryDirectory(prefix='webdav-cli-') as name:
    root = Path(name)
    # The CLI does not expose its ephemeral port in quiet mode. Reserve a port
    # before launch, then probe it and fail with the server log on startup error.
    with socket.socket() as port_socket:
        port_socket.bind(('127.0.0.1', 0))
        port = port_socket.getsockname()[1]
    with tempfile.TemporaryFile(mode='w+') as log, tempfile.TemporaryFile(mode='w+') as errors:
        server = subprocess.Popen(['/usr/bin/qore', str(script), '--root', str(root),
                                   '--port', str(port), '--quiet'], stdout=log, stderr=errors)
        try:
            deadline = time.monotonic() + 30
            while True:
                if server.poll() is not None:
                    raise RuntimeError('WebDAV CLI exited during startup')
                try:
                    with socket.create_connection(('127.0.0.1', port), timeout=0.2):
                        break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError('WebDAV CLI did not start')
                    time.sleep(0.05)
            def request(method, path, body=None, headers=None):
                connection = http.client.HTTPConnection('127.0.0.1', port, timeout=10)
                try:
                    connection.request(method, path, body=body, headers=headers or {})
                    response = connection.getresponse()
                    return response.status, response.read()
                finally:
                    connection.close()
            cases = [(None, 'Žluťoučký'.encode()),
                     ('text/plain; charset=iso-8859-1', 'café'.encode('iso-8859-1')),
                     ('text/plain; charset=utf-8', 'Žluťoučký'.encode()),
                     ('application/octet-stream', bytes(range(256)))]
            for method in ['PUT', 'POST']:
                for content_type, payload in cases:
                    headers = {'Content-Type': content_type} if content_type else {}
                    assert request(method, '/invoice.txt', payload, headers)[0] in (200, 201, 204)
                    received = request('GET', '/invoice.txt')
                    assert received == (200, payload), (method, content_type, received, payload)
                    assert (root / 'invoice.txt').read_bytes() == payload
                    status, body = request('PROPFIND', '/', headers={'Depth': '1'})
                    assert status == 207 and b'invoice.txt' in body, (status, body)
                    assert request('DELETE', '/invoice.txt')[0] in (200, 204)
                    assert not (root / 'invoice.txt').exists()
            server.send_signal(signal.SIGTERM)
            assert server.wait(timeout=15) == 0
            log.seek(0)
            assert not log.read().strip(), 'Quiet mode emitted unexpected output'
        except BaseException:
            log.seek(0)
            print(log.read(), flush=True)
            errors.seek(0)
            print(errors.read(), flush=True)
            raise
        finally:
            if server.poll() is None:
                server.kill()
                server.wait(timeout=10)
print('WebDAV CLI: PUT/GET/PROPFIND/DELETE and SIGTERM passed', flush=True)
