#!/usr/bin/env python3
"""Independent WSDL HTTP request targets. Copyright (C) 2026 Qore Technologies, s.r.o."""
import base64
import contextlib
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import unittest
import xml.etree.ElementTree as ET

from test_cxf_peer import endpoint

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
PEER = ROOT / "http-request-url-peer"
W = "{http://schemas.xmlsoap.org/wsdl/}"
H = "{http://schemas.xmlsoap.org/wsdl/http/}"
M = "{http://schemas.xmlsoap.org/wsdl/mime/}"


def contract(base, reference, *, verb="GET", mode="urlEncoded", empty=False):
    tree = ET.parse(PEER / "contract.wsdl")
    tree.find(f".//{H}address").set("location", base)
    tree.find(f".//{H}operation").set("location", reference)
    tree.find(f".//{H}binding").set("verb", verb)
    node = tree.find(f".//{W}binding/{W}operation/{W}input")
    node.clear()
    if mode == "binary":
        ET.SubElement(node, M + "content", {"part": "id", "type": "application/octet-stream"})
    else:
        ET.SubElement(node, H + mode)
    if empty:
        tree.find(f"{W}message[@name='Input']").clear()
        tree.find(f"{W}message").set("name", "Input")
    # ElementTree must retain prefixes used in QName-valued WSDL attributes.
    tree.getroot().set("xmlns:t", "urn:request-url")
    tree.getroot().set("xmlns:x", "http://www.w3.org/2001/XMLSchema")
    return ET.tostring(tree.getroot(), encoding="unicode")


@contextlib.contextmanager
def origin(name, received, behavior=None, *, content_type="text/xml;charset=UTF-8"):
    stopped = threading.Event()
    failures = queue.Queue()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path == "/__stop__":
                stopped.set()
                self.send_response(200)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.exchange()

        def do_POST(self):
            self.exchange()

        def exchange(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            record = {"origin": name, "path": self.path, "method": self.command,
                      "headers": dict((k.lower(), v) for k, v in self.headers.items()), "body": body}
            received.put(record)
            try:
                status, headers, output = behavior(record) if behavior else (200, {}, f"<result>{name}</result>".encode())
                self.send_response(status)
                if content_type is not None:
                    self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(output)))
                for key, value in headers.items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(output)
            except BaseException as error:
                failures.put(error)
                raise

    with HTTPServer(("127.0.0.1", 0), Handler) as server:
        server.timeout = 30

        def serve():
            while not stopped.is_set():
                server.handle_request()

        worker = threading.Thread(target=serve)
        worker.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            try:
                connection.request("GET", "/__stop__")
                connection.getresponse().read()
            finally:
                connection.close()
                worker.join(15)
            if worker.is_alive():
                raise TimeoutError("HTTP peer did not finish after the stop request")
            if not failures.empty():
                raise failures.get_nowait()


def run(jobs):
    env = dict(os.environ, QORE_MODULE_DIR=str(REPO / "build-debug") + ":" + str(REPO / "qlib"))
    result = subprocess.run(["qore", "-b", "--enable-debug", str(PEER / "client.qr")],
                            cwd=REPO, env=env, input=json.dumps({"jobs": jobs}), text=True,
                            capture_output=True, timeout=120)
    if result.returncode or result.stderr:
        raise AssertionError((result.returncode, result.stdout, result.stderr))
    return json.loads(result.stdout)


class RequestUrlTests(unittest.TestCase):
    def test_reference_matrix(self):
        received = queue.Queue()
        with origin("A", received) as a, origin("B", received) as b:
            rows = [("/base/", "/send", "/send?id=A%2FB", "A"),
                    ("/base/", "send", "/base/send?id=A%2FB", "A"),
                    ("/base/file", "send", "/base/send?id=A%2FB", "A"),
                    ("/base/dir/", "../send", "/base/send?id=A%2FB", "A"),
                    ("/base/", "./x/../send", "/base/send?id=A%2FB", "A"),
                    ("/base/file?old=1", "?rev=2", "/base/file?rev=2&id=A%2FB", "A"),
                    ("/base/file?old=1", "", "/base/file?id=A%2FB", "A"),
                    ("/base/", b.removeprefix("http:") + "/send", "/send?id=A%2FB", "B"),
                    ("/base/", "/%2e/a%2Fb", "/%2e/a%2Fb?id=A%2FB", "A")]
            jobs = [{"xml": contract(a + base, ref), "state": state, "calls": [{"value": {"id": "A/B"}}]}
                    for state in ("source", "saved", "data") for base, ref, _, _ in rows]
            results = run(jobs)
            for result, (_, _, target, expected_origin) in zip(results, rows * 3, strict=True):
                record = received.get_nowait()
                self.assertEqual((expected_origin, target), (record["origin"], record["path"]))
                self.assertEqual({"result": expected_origin}, result["calls"][0]["value"])
                self.assertEqual((a if expected_origin == "A" else b) + target,
                                 result["calls"][0]["info"]["effective-url"])
                self.assertTrue(result["unchanged"])
            self.assertTrue(received.empty())

    def test_empty_queries_and_replacement(self):
        received = queue.Queue()
        with origin("A", received) as a:
            rows = [("", "/base/file?old=1"), ("?", "/base/file?"), ("?new=2", "/base/file?new=2")]
            jobs = [{"xml": contract(a + "/base/file?old=1", ref, empty=True), "calls": [{"value": {}}]}
                    for ref, _ in rows]
            jobs += [{"xml": contract(a + "/base/dir/", "../items/(id)?fixed=1", mode="urlReplacement"),
                      "calls": [{"value": {"id": "A/B ?#č"}}]}]
            jobs += [{"xml": contract(a + "/base/", "items/(id)/view", mode="urlReplacement"),
                      "calls": [{"value": {"id": value}}]} for value in (".", "..")]
            for result in run(jobs):
                self.assertEqual({"result": "A"}, result["calls"][0]["value"])
            paths = [received.get_nowait()["path"] for _ in jobs]
            self.assertEqual([path for _, path in rows] + ["/base/items/A%2FB%20%3F%23%C4%8D?fixed=1",
                "/base/items/%2E/view", "/base/items/%2E%2E/view"], paths)

    def test_redirects_default_headers_and_recovery(self):
        received = queue.Queue()
        with origin("B", received) as b:
            def behavior(record):
                if record["path"].startswith("/jump?"):
                    return 307, {"Location": b + "/final?"}, b""
                if record["path"].endswith("id=fail"):
                    return 500, {}, b"<error>fixture failure</error>"
                return 200, {}, b"<result>A</result>"
            with origin("A", received, behavior) as a:
                defaults = {"Authorization": "Bearer fixture-default", "Cookie": "base=1", "Host": "base.example"}
                jobs = [{"xml": contract(a + "/base/", "/jump"), "options": {"headers": defaults},
                         "calls": [{"value": {"id": "ok"}}]},
                        {"xml": contract(a + "/base/", b.removeprefix("http:") + "/target"),
                         "options": {"headers": defaults}, "calls": [{"value": {"id": "ok"}},
                            {"value": {"id": "ok"}, "options": {"http_header": {"Authorization": "Bearer fixture-call"}}}]},
                        {"xml": contract(a + "/base/", "../recover"), "calls": [
                            {"value": {"id": "fail"}}, {"value": {"id": "ok"}}]}]
                results = run(jobs)
                records = [received.get_nowait() for _ in range(6)]
                self.assertEqual("Bearer fixture-default", records[0]["headers"]["authorization"])
                for index in (1, 2):
                    self.assertNotIn("authorization", records[index]["headers"])
                    self.assertNotIn("cookie", records[index]["headers"])
                    self.assertNotEqual("base.example", records[index]["headers"]["host"])
                self.assertEqual("Bearer fixture-call", records[3]["headers"]["authorization"])
                self.assertEqual(b + "/final?", results[0]["calls"][0]["info"]["effective-url"])
                self.assertEqual(1, len(results[0]["calls"][0]["info"]["redirects"]))
                self.assertEqual("HTTP-CLIENT-RECEIVE-ERROR", results[2]["calls"][0]["error"])
                self.assertEqual({"result": "A"}, results[2]["calls"][1]["value"])
                self.assertTrue(all(r["unchanged"] and r["headers_unchanged"] for r in results))

    def test_independent_handler_requests(self):
        contracts = [contract("http://example.invalid/base/dir/", "../č/(id)/é", mode="urlReplacement"),
                     contract("http://example.invalid/query/file?old=1", ""),
                     contract("http://example.invalid/form/file", "send", verb="POST"),
                     contract("http://example.invalid/empty/file?old=1", "?", empty=True)]
        requests = [("GET", "/base/%C4%8D/A%2FB/%C3%A9", None, {}),
                    ("GET", "/query/file?id=hello", None, {}),
                    ("POST", "/form/send", b"id=A%20%26%20%C4%8D",
                     {"Content-Type": "application/x-www-form-urlencoded"}),
                    ("GET", "/empty/file?", None, {})]
        env = dict(os.environ, QORE_MODULE_DIR=str(REPO / "build-debug") + ":" + str(REPO / "qlib"))
        for state in ("source", "saved", "data"):
            job = {"contracts": contracts, "state": state,
                   "expected": [{"id": "A/B"}, {"id": "hello"}, {"id": "A & č"}, {}]}
            cmd = ["qore", "-b", "--enable-debug", str(PEER / "handler.qr"), json.dumps(job)]
            with endpoint(cmd, env=env) as (_, port):
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
                try:
                    connection.request("GET", "/wrong/A%2FB/%C3%A9")
                    response = connection.getresponse()
                    self.assertEqual(501, response.status)
                    response.read()
                    for method, path, body, headers in requests:
                        connection.request(method, path, body, headers)
                        response = connection.getresponse()
                        data = response.read()
                        self.assertEqual(200, response.status, data)
                        self.assertEqual("received", ET.fromstring(data).text)
                finally:
                    connection.close()

    def test_post_values_and_provider(self):
        received = queue.Queue()
        with origin("A", received) as a:
            data = bytes.fromhex("00ff0d0a")
            jobs = [{"xml": contract(a + "/base/file", "../binary", verb="POST", mode="binary"),
                     "calls": [{"binary": base64.b64encode(data).decode()}]},
                    {"xml": contract("http://example.invalid/unused/", "send", verb="POST"),
                     "options": {"url": a + "/selected/file"},
                     "calls": [{"value": {"id": "A & č"}, "provider": True}]}]
            results = run(jobs)
            binary, form = received.get_nowait(), received.get_nowait()
            self.assertEqual(("POST", "/binary", data), (binary["method"], binary["path"], binary["body"]))
            self.assertEqual(("/selected/send", b"id=A%20%26%20%C4%8D"), (form["path"], form["body"]))
            self.assertTrue(all(r["calls"][0]["value"] == {"result": "A"} and r["unchanged"] for r in results))


if __name__ == "__main__":
    unittest.main(verbosity=2)
