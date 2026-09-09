#!/usr/bin/env python3
"""FTP schema loading for libxml2 builds advertising LIBXML_FTP_ENABLED.

Copyright (C) 2026 Qore Technologies, s.r.o.
Run explicitly with the legacy module build in QORE_MODULE_DIR. This test is not
a waiver for newer libxml2 builds, which do not advertise native FTP support.
"""
from contextlib import contextmanager
import socket
import socketserver
import threading
import unittest

from test_schema_resources import INTEGER, INCLUDE, load


@contextmanager
def ftp_server(routes):
    commands = []
    errors = []

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.connection.settimeout(20)
            data_socket = None

            def reply(message):
                self.wfile.write(message.encode("ascii") + b"\r\n")

            try:
                reply("220 Schema fixture")
                for _index in range(20):
                    line = self.rfile.readline(8192)
                    if not line:
                        break
                    command, _, argument = line.decode("utf-8").rstrip("\r\n").partition(" ")
                    commands.append((command, argument))
                    if command == "USER":
                        reply("331 Password required")
                    elif command == "PASS":
                        reply("230 Logged in")
                    elif command == "TYPE":
                        if argument != "I":
                            raise AssertionError("schema transport must preserve bytes")
                        reply("200 Binary type")
                    elif command == "EPSV":
                        if data_socket is not None:
                            raise AssertionError("duplicate data channel")
                        data_socket = socket.socket()
                        data_socket.settimeout(20)
                        data_socket.bind(("127.0.0.1", 0))
                        data_socket.listen()
                        reply(f"229 Entering Extended Passive Mode (|||{data_socket.getsockname()[1]}|)")
                    elif command == "RETR":
                        if argument not in routes:
                            reply("550 Schema not found")
                            continue
                        reply("150 Data follows")
                        with data_socket.accept()[0] as data:
                            data.settimeout(20)
                            data.sendall(routes[argument])
                        data_socket.close()
                        data_socket = None
                        reply("226 Complete")
                    elif command == "QUIT":
                        reply("221 Goodbye")
                        break
                    else:
                        raise AssertionError(f"unexpected FTP command: {command}")
                else:
                    raise AssertionError("too many FTP commands")
            except BaseException as error:
                errors.append(error)
            finally:
                if data_socket is not None:
                    data_socket.close()

    with socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"ftp://127.0.0.1:{server.server_address[1]}", commands
        finally:
            server.shutdown()
            thread.join(timeout=5)
            if thread.is_alive():
                raise AssertionError("FTP fixture did not terminate")
    if errors:
        raise errors[0]


class LegacySchemaFtpTest(unittest.TestCase):
    def test_relative_imports_bytes_and_transport_errors(self):
        routes = {"/tree/main.xsd": INCLUDE, "/tree/types.xsd": INTEGER}
        with ftp_server(routes) as (base, commands):
            self.assertEqual({"value": {"value": "17"}}, load(base + "/tree/main.xsd"))
            self.assertEqual(["/tree/main.xsd", "/tree/types.xsd"],
                             [argument for command, argument in commands if command == "RETR"])
            self.assertEqual("PARSE-XML-EXCEPTION", load(base + "/tree/main.xsd", xml="<value>x</value>")["error"])
            self.assertEqual("FTP-GET-ERROR", load(base + "/missing.xsd")["error"])
            self.assertEqual({"value": {"value": "17"}}, load(base + "/tree/main.xsd"))

    def test_denied_network_does_not_connect(self):
        with ftp_server({"/schema.xsd": INTEGER}) as (base, commands):
            self.assertEqual("ILLEGAL-NETWORK-ACCESS", load(base + "/schema.xsd", no_network=True)["error"])
            self.assertEqual("NETWORK-ACCESS-DENIED", load(base + "/schema.xsd", policy=True)["error"])
            self.assertEqual("NETWORK-ACCESS-DENIED", load(base + "/schema.xsd", policy=True,
                                                         allow_network=True, denied_ips=["127.0.0.0/8"])["error"])
            self.assertEqual([], commands)
            self.assertEqual({"value": {"value": "17"}}, load(base + "/schema.xsd", policy=True,
                                                             allow_network=True, no_filesystem=True))


if __name__ == "__main__":
    unittest.main()
