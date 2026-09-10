#!/usr/bin/env python3
"""Independent XML-RPC character data and loopback HTTP checks.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import base64
from contextlib import contextmanager
import http.client
import http.server
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
import xml.etree.ElementTree as ET
import xmlrpc.client
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
VALUES = ["", " \t\r\n ", "before\rafter", "é<&\r", -2147483648, 2147483647,
          {"": "empty", " \t ": "spaces", "A\rB": "return", "!!empty-hash-key!!": "literal"},
          ["\r", {"key": "\t"}, "next"]]
FAULT = "é\r\n \t fault"


def run(fixture):
    command = ["qore", "-b", "--enable-debug", "--exec-mode=" + os.getenv("QORE_EXEC_MODE", "jit")]
    if directory := os.getenv("QORE_XMLRPC_VALGRIND_DIR"):
        command = ["valgrind", "--error-exitcode=90", "--leak-check=full",
                   "--show-leak-kinds=definite,indirect,possible",
                   "--errors-for-leak-kinds=definite,indirect,possible",
                   "--log-file=" + str(Path(directory) / "xmlrpc-text-%p.log"), *command]
    with tempfile.TemporaryDirectory(prefix="xmlrpc-text-") as directory:
        path = Path(directory) / "fixture.json"
        path.write_text(json.dumps(fixture))
        result = subprocess.run([*command, ROOT / "xmlrpc-text-peer.qr", path],
                                capture_output=True, text=True, timeout=180)
    if result.returncode or result.stderr:
        raise AssertionError((result.returncode, result.stdout, result.stderr))
    return json.loads(result.stdout)


def characters(value):
    # Authored fixture escaping follows XML 1.0 section 2.11. CPython's
    # XML-RPC marshaller's separate literal-CR defect is tested below.
    return escape(value).replace("\r", "&#13;")


def value_xml(value):
    if isinstance(value, str):
        typed = "<string>" + characters(value) + "</string>"
    elif isinstance(value, int):
        typed = "<int>" + str(value) + "</int>"
    elif isinstance(value, list):
        typed = "<array><data>" + "".join(map(value_xml, value)) + "</data></array>"
    elif isinstance(value, dict):
        typed = "<struct>" + "".join("<member><name>" + characters(key) + "</name>"
                                    + value_xml(item) + "</member>" for key, item in value.items()) + "</struct>"
    else:
        raise TypeError(type(value))
    return "<value>" + typed + "</value>"


def response_xml(value):
    return ("<?xml version='1.0' encoding='UTF-8'?><methodResponse><params><param>" + value_xml(value)
            + "</param></params></methodResponse>").encode()


def request_xml(value, encoding="UTF-8", method="echo"):
    return ("<?xml version='1.0' encoding='" + encoding + "'?><methodCall><methodName>" + method
            + "</methodName><params><param>" + value_xml(value)
            + "</param></params></methodCall>").encode(encoding)


@contextmanager
def server(callback):
    errors = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            try:
                response = callback(self.path, body)
                self.send_response(200)
            except Exception as error:
                errors.append(error)
                response = json.dumps({"ok": False, "error": repr(error)}).encode()
                self.send_response(500)
            self.send_header("Content-Type", "text/xml")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        def log_message(self, *_args):
            pass

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()  # The constructor has bound and listened; no readiness polling.
    try:
        yield "http://127.0.0.1:" + str(httpd.server_port)
        if errors:
            raise AssertionError(errors)
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)
        if thread.is_alive():
            raise AssertionError("XML-RPC peer did not terminate")


class XmlRpcTextTest(unittest.TestCase):
    def test_serialized_bytes_decode_exactly_with_expat_and_xmlrpc(self):
        rows = run({"action": "serialize", "values": VALUES, "fault": FAULT,
                    "encodings": ["UTF-8", "ISO-8859-1", "UTF-16LE", "UTF-16BE"]})
        self.assertEqual(144, len(rows))
        for row in rows:
            with self.subTest(encoding=row["encoding"], flags=row["flags"], value=row.get("value")):
                if "fault" in row:
                    body = base64.b64decode(row["fault"], validate=True)
                    with self.assertRaises(xmlrpc.client.Fault) as fault:
                        xmlrpc.client.loads(body)
                    self.assertEqual((23, FAULT), (fault.exception.faultCode, fault.exception.faultString))
                    continue
                for kind in ("call", "response"):
                    body = base64.b64decode(row[kind], validate=True)
                    params, method = xmlrpc.client.loads(body)
                    self.assertEqual(({"value": row["value"]},), params)
                    self.assertEqual("echo" if kind == "call" else None, method)
                    xml = ET.fromstring(body)
                    self.assertEqual(row["value"], params[0]["value"])
                    if isinstance(row["value"], int):
                        self.assertEqual(str(row["value"]), xml.find(".//i4").text)

    def test_qore_client_against_independent_decoder_and_authored_responses(self):
        received = []

        def callback(path, body):
            self.assertEqual("/RPC2", path)
            params, method = xmlrpc.client.loads(body)
            if method == "fail":
                self.assertEqual((FAULT,), params)
                return ("<methodResponse><fault>" + value_xml({"faultCode": 23, "faultString": FAULT})
                        + "</fault></methodResponse>").encode()
            self.assertEqual("echo", method)
            self.assertEqual(1, len(params))
            received.append(params[0])
            return response_xml(params[0])

        with server(callback) as url:
            self.assertEqual([{"value": value} for value in VALUES],
                             run({"action": "client", "url": url + "/RPC2", "values": VALUES, "fault": FAULT}))
        self.assertEqual([{"value": value} for value in VALUES], received)

    def test_independent_requests_against_qore_handler(self):
        count = 0

        def callback(path, body):
            nonlocal count
            self.assertEqual("/ready", path)
            port = json.loads(body)["port"]
            for encoding in ("UTF-8", "UTF-16LE", "UTF-16BE"):
                for value in VALUES:
                    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
                    try:
                        connection.request("POST", "/RPC2", request_xml({"value": value}, encoding),
                                           {"Content-Type": "text/xml; charset=" + encoding})
                        response = connection.getresponse()
                        output = response.read()
                        self.assertEqual(200, response.status, (encoding, value, output))
                        self.assertEqual((({"value": value},), None), xmlrpc.client.loads(output))
                        count += 1
                    finally:
                        connection.close()
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
            try:
                connection.request("POST", "/RPC2", request_xml(FAULT, method="fail"),
                                   {"Content-Type": "text/xml; charset=UTF-8"})
                response = connection.getresponse()
                self.assertEqual(200, response.status)
                with self.assertRaises(xmlrpc.client.Fault) as fault:
                    xmlrpc.client.loads(response.read())
                self.assertEqual("TEXT-PEER-ERROR: " + FAULT, fault.exception.faultString)
                count += 1
            finally:
                connection.close()
            return b'{"ok": true}'

        with server(callback) as url:
            self.assertEqual({"ok": True}, run({"action": "server", "url": url}))
        self.assertEqual(25, count)

    def test_reference_marshaller_literal_cr_reduction(self):
        body = xmlrpc.client.dumps(("A\rB",), methodname="echo")
        self.assertIn("A\rB", body)
        self.assertEqual((("A\nB",), "echo"), xmlrpc.client.loads(body))
        self.assertEqual((("A\rB",), "echo"), xmlrpc.client.loads(request_xml("A\rB")))


if __name__ == "__main__":
    unittest.main()
