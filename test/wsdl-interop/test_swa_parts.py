#!/usr/bin/env python3
"""Independent Apache CXF replay and live SOAP attachment bindings.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import base64
import contextlib
import http.client
import http.server
import queue
import threading
import email.parser
import email.policy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from urllib.parse import unquote

from test_cxf_peer import checked, endpoint, infoset

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
PEER = ROOT / "swa-peer"


def parts(wire):
    """Check related framing and select each part by identity, independently of Qore."""
    media = [value for key, value in wire["headers"].items() if key.lower() == "content-type"]
    if len(media) != 1:
        raise ValueError("one Content-Type is required")
    message = email.parser.BytesParser(policy=email.policy.default).parsebytes(
        ("Content-Type: " + media[0] + "\r\n\r\n").encode("ascii") + base64.b64decode(wire["body"], validate=True))
    if message.defects or message.get_content_type() != "multipart/related":
        raise ValueError("invalid related message")
    start = message.get_param("start")
    root = None
    attachments = {}
    ids = set()
    for part in message.iter_parts():
        identifier = str(part["Content-ID"])
        if part.defects or identifier in ids or not (identifier.startswith("<") and identifier.endswith(">")):
            raise ValueError("invalid MIME entity")
        ids.add(identifier)
        body = part.get_payload(decode=True)
        if identifier == start:
            if root is not None or part.get_content_type() != message.get_param("type"):
                raise ValueError("conflicting related root")
            root = infoset(body)
        else:
            name, unique = identifier[1:-1].split("=", 1)
            name = unquote(name, errors="strict")
            if name in attachments or "@" not in unique:
                raise ValueError("conflicting part identity")
            attachments[name] = part.get_content_type(), body
    if root is None:
        raise ValueError("missing SOAP root")
    return root, attachments


def altered(wire, problem):
    media = next(value for key, value in wire["headers"].items() if key.lower() == "content-type")
    message = email.parser.BytesParser(policy=email.policy.default).parsebytes(
        ("Content-Type: " + media + "\r\n\r\n").encode() + base64.b64decode(wire["body"]))
    entities = []
    for part in message.iter_parts():
        headers = {key: str(value) for key, value in part.items()
                   if key.lower() not in {"content-length", "content-transfer-encoding"}}
        entities.append([headers, part.get_payload(decode=True)])
    target = next(index for index, (headers, _) in enumerate(entities)
                  if headers["Content-ID"] != message.get_param("start"))
    if problem == "missing":
        del entities[target]
    elif problem == "duplicate":
        headers, body = entities[target]
        headers = dict(headers)
        headers["Content-ID"] = headers["Content-ID"].split("=", 1)[0] + "=duplicate@example.test>"
        entities.append([headers, body])
    elif problem == "media":
        entities[target][0]["Content-Type"] = "image/unexpected"
    else:
        raise ValueError(problem)
    boundary = message.get_boundary().encode()
    blocks = []
    for headers, body in entities:
        header = "\r\n".join(key + ": " + value for key, value in headers.items()).encode("ascii")
        blocks.append(b"--" + boundary + b"\r\n" + header + b"\r\nContent-Transfer-Encoding: binary\r\n\r\n"
                      + body + b"\r\n")
    return {"headers": wire["headers"], "body": base64.b64encode(
        b"".join(blocks) + b"--" + boundary + b"--\r\n").decode()}


class SwaPartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((PEER / "golden.json").read_text())
        if (cls.manifest["implementation"], cls.manifest["version"]) != ("Apache CXF", "4.1.3"):
            raise ValueError("unexpected peer")
        cls.wsdl = ROOT / cls.manifest["wsdl"]
        if hashlib.sha256(cls.wsdl.read_bytes()).hexdigest() != cls.manifest["wsdl_sha256"]:
            raise ValueError("changed WSDL derivative")
        dependency = json.loads((ROOT / "cxf-peer/manifest.json").read_text())
        expected = set()
        for entry in dependency["artifacts"]:
            path = ROOT / "cxf-peer" / entry["path"]
            expected.add(path)
            data = path.read_bytes()
            if len(data) != entry["size"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise ValueError("changed independent dependency: " + str(path))
        if expected != set((ROOT / "cxf-peer/jars").glob("*.jar")):
            raise ValueError("unaccounted dependency")
        cls.directory = tempfile.TemporaryDirectory(prefix="xml-swa-peer-")
        cls.addClassCleanup(cls.directory.cleanup)
        build = Path(cls.directory.name)
        generated = build / "generated"
        classes = build / "classes"
        generated.mkdir()
        classes.mkdir()
        jars = str(ROOT / "cxf-peer/jars/*")
        java = ["java", "-Dorg.slf4j.simpleLogger.defaultLogLevel=warn"]
        output = checked([*java, "-cp", jars, "org.apache.cxf.tools.wsdlto.WSDLToJava",
                          "-d", str(generated), "-suppress-generated-date", "-faultSerialVersionUID", "1",
                          "-mimeMethods=echoData,echoDataWithHeader,echoAllAttachmentTypes",
                          "-sn", "SwAService", str(cls.wsdl)])
        if output:
            raise AssertionError("unexpected code generation output: " + output)
        output = checked(["javac", "--release", "17", "-Xlint:all", "-Werror", "-cp", jars,
                          "-d", str(classes), *map(str, sorted(generated.rglob("*.java"))),
                          str(PEER / "SwAPeer.java")])
        if output:
            raise AssertionError("unexpected compiler output: " + output)
        cls.java = [*java, "-cp", str(classes) + os.pathsep + jars, "SwAPeer"]
        cls.qore = [os.environ.get("QORE", "qore"), "-b", "--enable-debug", str(PEER / "qore-peer.qr")]
        cls.env = os.environ.copy()
        cls.env["QORE_MODULE_DIR"] = os.pathsep.join((str(REPO / "build-debug"), str(REPO / "qlib")))

    def test_derivative_changes_are_explicit(self):
        original = (ROOT / "cxf/swa-mime.wsdl").read_text()
        annotation = ' type="wsi:swaRef" xmime:expectedContentTypes="application/octet-stream"'
        self.assertEqual(1, original.count(annotation))
        expected = original.replace(annotation, ' type="wsi:swaRef"').replace('<wsdl:definitions ',
            '<!-- Qore derivative correction: Copyright (C) 2026 Qore Technologies, s.r.o. -->\n<wsdl:definitions ', 1)
        expected = "\n".join(line.rstrip() for line in expected.splitlines()) + "\n"
        self.assertEqual(expected, self.wsdl.read_text())

    def test_capture_inventory(self):
        rows = self.manifest["cases"]
        self.assertEqual(["echoData", "echoDataWithHeader", "echoAllAttachmentTypes"], [row["operation"] for row in rows])
        for row, count in zip(rows, (1, 1, 5)):
            self.assertEqual(200, row["status"])
            for direction in ("request", "response"):
                _, attachments = parts(row[direction])
                self.assertEqual(count, len(attachments))
                values = row[direction + "_value"]
                for name, (media, body) in attachments.items():
                    expected = values[name]
                    self.assertEqual(base64.b64decode(expected["binary"], validate=True)
                                     if isinstance(expected, dict) else expected.encode(), body)
                    self.assertIn(media, {"application/octet-stream", "text/plain", "text/html", "text/xml", "image/jpeg", "image/gif"})

    def test_qore_serialization_matches_cxf_and_decodes_captures(self):
        for graph in ("source", "saved"):
            with self.subTest(graph=graph):
                output = json.loads(checked([*self.qore, "encode", graph], env=self.env))
                self.assertEqual([row["operation"] for row in self.manifest["cases"]], [row["operation"] for row in output])
                for expected, actual in zip(self.manifest["cases"], output):
                    for direction in ("request", "response"):
                        self.assertEqual(parts(expected[direction]), parts(actual[direction]),
                                         expected["operation"] + " " + direction)

    def test_live_qore_client_and_cxf_server(self):
        with endpoint([*self.java, "server", str(self.wsdl)]) as (url, _):
            for graph in ("source", "saved"):
                for representation in ("native", "xml"):
                    with self.subTest(graph=graph, representation=representation):
                        self.assertEqual("PASS\n", checked(
                            [*self.qore, "client", graph, representation, url], env=self.env))

    def test_live_cxf_client_and_qore_server(self):
        for graph in ("source", "saved"):
            for representation in ("native", "xml"):
                with self.subTest(graph=graph, representation=representation):
                    # echoDataRef's swaRef values reference parts: native values are their contents, retained XML
                    # keeps the URIs and exchanges the parts through SoapXmlMessageInfo::parts and ^parts^
                    with endpoint([*self.qore, "server", graph, representation, "reference"], self.env) as (url, _):
                        self.assertEqual("PASS\n", checked([*self.java, "client", str(self.wsdl), url, "reference"]))

    def test_handler_rejects_bad_parts_and_recovers(self):
        for graph in ("source", "saved"):
            with endpoint([*self.qore, "server", graph, "native"], self.env) as (_, port):
                for row in self.manifest["cases"]:
                    for problem in ("missing", "duplicate", "media"):
                        wire = altered(row["request"], problem)
                        with contextlib.closing(http.client.HTTPConnection("127.0.0.1", port, timeout=30)) as client:
                            client.request("POST", "/service", base64.b64decode(wire["body"]), wire["headers"])
                            response = client.getresponse()
                            body = response.read()
                            self.assertEqual(500, response.status, body)
                            self.assertIn(b"SOAP-MESSAGE-ERROR" if problem == "media" else b"SOAP-DESERIALIZATION-ERROR", body)
                    with contextlib.closing(http.client.HTTPConnection("127.0.0.1", port, timeout=30)) as client:
                        wire = row["request"]
                        client.request("POST", "/service", base64.b64decode(wire["body"]), wire["headers"])
                        response = client.getresponse()
                        actual = {"headers": dict(response.getheaders()), "body": base64.b64encode(response.read()).decode()}
                        self.assertEqual(200, response.status)
                        self.assertEqual(parts(row["response"]), parts(actual))

    def test_client_rejects_bad_parts_and_recovers(self):
        for graph in ("source", "saved"):
            replies = queue.Queue()
            failures = queue.Queue()
            for row in self.manifest["cases"]:
                for problem in ("missing", "duplicate", "media"):
                    replies.put((row["request"], altered(row["response"], problem)))
                    replies.put((row["request"], row["response"]))

            class Handler(http.server.BaseHTTPRequestHandler):
                def log_message(self, *args):
                    pass

                def do_POST(self):
                    try:
                        expected, reply = replies.get_nowait()
                        body = self.rfile.read(int(self.headers["Content-Length"]))
                        actual = {"headers": dict(self.headers.items()), "body": base64.b64encode(body).decode()}
                        if parts(expected) != parts(actual):
                            raise AssertionError("client request differs from independent capture")
                        self.send_response(200)
                        for key, value in reply["headers"].items():
                            if key.lower() not in {"content-length", "transfer-encoding", "connection"}:
                                self.send_header(key, value)
                        body = base64.b64decode(reply["body"])
                        self.send_header("Content-Length", str(len(body)))
                        self.end_headers()
                        self.wfile.write(body)
                    except BaseException as error:
                        failures.put(error)
                        self.close_connection = True

            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                self.assertEqual("PASS\n", checked([*self.qore, "client-invalid", graph, "native",
                    f"http://127.0.0.1:{server.server_port}/service"], env=self.env))
            finally:
                server.shutdown()
                server.server_close()
                thread.join(10)
                self.assertFalse(thread.is_alive())
            self.assertTrue(replies.empty())
            self.assertTrue(failures.empty(), list(failures.queue))


if __name__ == "__main__":
    unittest.main()
