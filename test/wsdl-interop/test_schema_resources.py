#!/usr/bin/env python3
"""Schema URI resolution and access policy against an independent HTTP server.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from contextlib import contextmanager
import http.server
import json
import os
from pathlib import Path
import subprocess
import ssl
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parent
INTEGER = ('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
           '<xs:element name="value" type="xs:int"/></xs:schema>').encode()
INCLUDE = ('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
           '<xs:include schemaLocation="types.xsd"/></xs:schema>').encode()


@contextmanager
def server(routes, address="127.0.0.1", tls=None):
    requests = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            code, headers, body = routes.get(self.path, (404, {}, b"missing"))
            self.send_response(code)
            for name, value in headers.items():
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args):
            pass

    httpd = http.server.ThreadingHTTPServer((address, 0), Handler)
    if tls:
        httpd.socket = tls.wrap_socket(httpd.socket, server_side=True)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()  # Constructor already bound and listened: no readiness polling.
    try:
        yield f"{'https' if tls else 'http'}://{address}:{httpd.server_port}", requests
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)
        if thread.is_alive():
            raise AssertionError("schema HTTP server did not terminate")


def load(schema, **options):
    catalog = options.pop("catalog", "")
    certificate = options.pop("certificate", None)
    fixture = {"schema": schema, "xml": "<value>17</value>", **options}
    return run_fixture(fixture, catalog, certificate)


def run_fixture(fixture, catalog="", certificate=None):
    command = ["qore", "-b", "--enable-debug", "--exec-mode=" + os.getenv("QORE_EXEC_MODE", "jit")]
    timeout = 30
    if log_directory := os.getenv("QORE_SCHEMA_VALGRIND_DIR"):
        command = ["valgrind", "--error-exitcode=90", "--leak-check=full",
                   "--show-leak-kinds=definite,indirect,possible",
                   "--errors-for-leak-kinds=definite,indirect,possible",
                   "--log-file=" + str(Path(log_directory) / "schema-resource-%p.log"), *command]
        timeout = 180
    environment = {**os.environ, "XML_CATALOG_FILES": catalog}
    if certificate:
        environment["SSL_CERT_FILE"] = certificate
    with tempfile.TemporaryDirectory(prefix="xml-schema-resource-") as directory:
        path = Path(directory) / "request.json"
        path.write_text(json.dumps(fixture))
        process = subprocess.run([*command, ROOT / "schema-resource-loader.qr", path],
                                 capture_output=True, text=True, timeout=timeout, env=environment)
    if process.returncode or process.stderr:
        raise AssertionError((process.returncode, process.stdout, process.stderr))
    return json.loads(process.stdout)


class SchemaResourceTest(unittest.TestCase):
    def test_https_verifies_the_server_certificate(self):
        with tempfile.TemporaryDirectory(prefix="xml-schema-tls-") as directory:
            key = Path(directory) / "key.pem"
            certificate = Path(directory) / "certificate.pem"
            subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                            "-keyout", str(key), "-out", str(certificate), "-days", "1",
                            "-subj", "/CN=localhost", "-addext", "subjectAltName=IP:127.0.0.1,DNS:localhost"],
                           check=True, capture_output=True, timeout=30)
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certificate, key)
            with server({"/schema.xsd": (200, {}, INTEGER)}, tls=context) as (base, requests):
                self.assertEqual({"value": {"value": "17"}}, load(base + "/schema.xsd", certificate=str(certificate)))
                rejected = load(base + "/schema.xsd")
                self.assertEqual("SOCKET-SSL-ERROR", rejected["error"])
                self.assertIn("certificate verify failed", rejected["description"])
                self.assertEqual(["/schema.xsd"], requests)

    def test_catalog_files_and_resolved_resources_are_checked(self):
        with tempfile.TemporaryDirectory(prefix="xml-schema-catalog-") as directory:
            catalog = Path(directory) / "catalog.xml"
            schema = Path(directory) / "schema.xsd"
            schema.write_bytes(INTEGER)
            catalog.write_text('<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">'
                               '<system systemId="urn:reader:contract" uri="schema.xsd"/></catalog>')
            self.assertEqual({"value": {"value": "17"}}, load("urn:reader:contract", catalog=str(catalog)))
            self.assertEqual("FILESYSTEM-ACCESS-DENIED", load("urn:reader:contract", catalog=str(catalog),
                                                             policy=True)["error"])
            self.assertEqual("FILESYSTEM-ACCESS-DENIED", load("urn:reader:contract", catalog=str(catalog),
                                                             policy=True, allowed_paths=[str(catalog)])["error"])
            self.assertEqual({"value": {"value": "17"}}, load("urn:reader:contract", catalog=str(catalog),
                                                             policy=True, allowed_paths=[str(catalog), str(schema)]))
            self.assertEqual("ILLEGAL-FILESYSTEM-ACCESS", load("urn:reader:contract", catalog=str(catalog),
                                                              no_filesystem=True)["error"])

    def test_http_base_uri_and_redirects(self):
        routes = {"/tree/main.xsd": (200, {}, INCLUDE), "/tree/types.xsd": (200, {}, INTEGER),
                  "/redirect": (302, {"Location": "/tree/main.xsd"}, b"")}
        with server(routes) as (base, requests):
            for path in ("/tree/main.xsd", "/redirect"):
                with self.subTest(path=path):
                    start = len(requests)
                    self.assertEqual({"value": {"value": "17"}}, load(base + path))
                    self.assertEqual(([path] if path == "/redirect" else [])
                                     + ["/tree/main.xsd", "/tree/types.xsd"], requests[start:])
            self.assertEqual("PARSE-XML-EXCEPTION", load(base + "/redirect", xml="<value>wrong</value>")["error"])

    def test_text_includes_and_document_bytes(self):
        latin = ('<?xml version="1.0" encoding="ISO-8859-1"?>'
                 '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                 '<xs:element name="value"><xs:simpleType><xs:restriction base="xs:string">'
                 '<xs:enumeration value="café"/></xs:restriction></xs:simpleType></xs:element></xs:schema>').encode("latin1")
        with server({"/schema.xsd": (200, {"Content-Type": "application/xml; charset=ISO-8859-1"}, latin)}) as (base, requests):
            text = f'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:include schemaLocation="{base}/schema.xsd"/></xs:schema>'
            self.assertEqual({"value": {"value": "café"}}, load(text, text=True, xml="<value>café</value>"))
            self.assertEqual("PARSE-XML-EXCEPTION", load(text, text=True, xml="<value>cafe</value>")["error"])
            self.assertEqual(["/schema.xsd", "/schema.xsd"], requests)

    def test_network_restrictions_and_recovery(self):
        with server({"/schema.xsd": (200, {}, INTEGER)}) as (base, requests):
            self.assertEqual("ILLEGAL-NETWORK-ACCESS", load(base + "/schema.xsd", no_network=True)["error"])
            self.assertEqual("NETWORK-ACCESS-DENIED", load(base + "/schema.xsd", policy=True)["error"])
            self.assertEqual("NETWORK-ACCESS-DENIED", load(base + "/schema.xsd", policy=True, allow_network=True,
                                                         denied_ips=["127.0.0.0/8"])["error"])
            self.assertEqual([], requests)
            self.assertEqual({"value": {"value": "17"}}, load(base + "/schema.xsd", policy=True, allow_network=True,
                                                             no_filesystem=True))
            self.assertEqual(["/schema.xsd"], requests)

    def test_redirect_destination_policy(self):
        with server({"/schema.xsd": (200, {}, INTEGER)}, "127.0.0.2") as (destination, destination_requests):
            with server({"/redirect": (302, {"Location": destination + "/schema.xsd"}, b"")}) as (base, requests):
                self.assertEqual("NETWORK-ACCESS-DENIED", load(base + "/redirect", policy=True, allow_network=True,
                                                             denied_ips=["127.0.0.2/32"])["error"])
                self.assertEqual(["/redirect"], requests)
                self.assertEqual([], destination_requests)
                self.assertEqual({"value": {"value": "17"}}, load(base + "/redirect", policy=True, allow_network=True))
                self.assertEqual(["/schema.xsd"], destination_requests)

    def test_http_schema_and_transport_errors(self):
        with server({"/bad.xsd": (200, {}, b"<not-schema/>"), "/good.xsd": (200, {}, INTEGER)}) as (base, requests):
            # All three run in one Qore process: failed loads must restore resource state.
            results = run_fixture([{"schema": base + path, "xml": "<value>17</value>"}
                                   for path in ("/bad.xsd", "/missing.xsd", "/good.xsd")])
            self.assertEqual("XSD-SYNTAX-ERROR", results[0]["error"])
            self.assertEqual("HTTP-CLIENT-RECEIVE-ERROR", results[1]["error"])
            self.assertEqual({"value": {"value": "17"}}, results[2])
            self.assertEqual(["/bad.xsd", "/missing.xsd", "/good.xsd"], requests)


if __name__ == "__main__":
    unittest.main()
