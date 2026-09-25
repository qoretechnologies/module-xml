#!/usr/bin/env python3
"""Offline, independent CXF/Qore WSDL binding interoperability.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import contextlib
from decimal import Decimal
import email.parser
import email.policy
import hashlib
import http.client
import json
import os
from pathlib import Path
import selectors
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
import jvm

ROOT = Path(__file__).resolve().parent
PEER = ROOT / "cxf-peer"
REPO = ROOT.parent.parent
FLOAT_NAME = "{http://apache.org/hello_world_doc_lit_bare/types}tickerPrice"


def root_entity(content_type, body):
    """Return a response's root entity; a request that is a XOP package is answered with one."""
    if not (content_type or "").lower().startswith("multipart/"):
        return body
    message = email.parser.BytesParser(policy=email.policy.default).parsebytes(
        ("Content-Type: " + content_type + "\r\n\r\n").encode("ascii") + body)
    start = message.get_param("start")
    for part in message.iter_parts():
        if start is None or str(part["Content-ID"]) == start:
            return part.get_payload(decode=True)
    raise AssertionError("multipart response without a root entity")


def infoset(xml):
    """Compare expanded names, attributes, order and values; the one xs:float is typed."""
    def node(element):
        children = list(element)
        value = element.text or ""
        if children:
            if value.strip():
                raise ValueError("unexpected mixed content")
            value = ""
        if element.tag == FLOAT_NAME:
            value = Decimal(value)
        for child in children:
            if (child.tail or "").strip():
                raise ValueError("unexpected mixed tail")
        return element.tag, sorted(element.attrib.items()), value, tuple(node(child) for child in children)
    return node(ET.fromstring(xml))


def checked(command, *, env=None, timeout=90):
    # child processes, including the Java peers, run without ambient JVM options; see jvm.py
    result = subprocess.run(command, capture_output=True, text=True, env=jvm.environment(env), timeout=timeout)
    if result.returncode or result.stderr:
        raise AssertionError(f"{command}: exit {result.returncode}\n{result.stdout}\n{result.stderr}")
    return result.stdout


@contextlib.contextmanager
def endpoint(command, env=None):
    """Read a readiness event and send STOP; every exit path reaps the owned process."""
    with tempfile.TemporaryFile(mode="w+") as diagnostics:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=diagnostics, text=True, env=jvm.environment(env))
        failure = None
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                if not selector.select(45):
                    raise TimeoutError("endpoint readiness deadline")
                ready = process.stdout.readline().rstrip("\n")
            if not ready.startswith("READY\t"):
                raise AssertionError("invalid readiness event: " + ready)
            port = int(ready.split("\t")[1])
            if not 0 < port < 65536:
                raise AssertionError("invalid listener port")
            yield f"http://127.0.0.1:{port}/service", port
        except BaseException as error:
            failure = error
            raise
        finally:
            try:
                output, _ = process.communicate("STOP\n", timeout=15)
            except (subprocess.TimeoutExpired, BrokenPipeError):
                process.kill()
                output, _ = process.communicate(timeout=10)
            diagnostics.seek(0)
            errors = diagnostics.read()
            if failure is not None and errors:
                raise AssertionError(f"endpoint diagnostics:\n{errors}") from failure
            if failure is None and (process.returncode or output or errors):
                raise AssertionError(f"endpoint exit {process.returncode}: {output}\n{errors}")


def execution_wsdl(row):
    # Pinned captures remain original; live SOAP 1.2 uses the explicit standards-corrected action.
    return ROOT / ('cxf-derived/hello_world_soap12_absolute_action.wsdl' if row['fixture'] == 'soap12' else row['wsdl'])


def execution_headers(row):
    headers = dict(row['request_headers'])
    if row['fixture'] == 'soap12' and row['operation'] == 'sayHi':
        headers['Content-Type'] = headers['Content-Type'].replace('action="sayHiAction"','action="urn:cxf:sayHiAction"')
    return headers


class CxfPeerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = json.loads((PEER / "manifest.json").read_text())
        if (manifest["implementation"], manifest["version"]) != ("Apache CXF", "4.1.3"):
            raise ValueError("unexpected independent peer version")
        paths = set()
        for artifact in manifest["artifacts"]:
            path = PEER / artifact["path"]
            if path.parent != PEER / "jars" or path in paths:
                raise ValueError("invalid or duplicate artifact path")
            paths.add(path)
            data = path.read_bytes()
            if len(data) != artifact["size"] or hashlib.sha256(data).hexdigest() != artifact["sha256"]:
                raise ValueError("modified independent peer artifact: " + str(path))
        if set((PEER / "jars").glob("*.jar")) != paths:
            raise ValueError("unaccounted peer dependency")
        for notice in manifest["notices"]:
            data = (PEER / notice["path"]).read_bytes()
            if len(data) != notice["size"] or hashlib.sha256(data).hexdigest() != notice["sha256"]:
                raise ValueError("modified dependency notice: " + notice["path"])
        if hashlib.sha256((PEER / "golden.json").read_bytes()).hexdigest() != manifest["golden_sha256"]:
            raise ValueError("modified CXF message capture")
        catalog = json.loads((ROOT / "cxf/catalog.json").read_text())
        for entry in catalog["resources"]:
            if hashlib.sha256((ROOT / "cxf" / entry["path"]).read_bytes()).hexdigest() != entry["sha256"]:
                raise ValueError("modified pinned CXF resource")
        cls.cases = json.loads((PEER / "golden.json").read_text())["cases"]
        cls.groups = {}
        for row in cls.cases:
            cls.groups.setdefault(row["fixture"], []).append(row)
        if len({row["id"] for row in cls.cases}) != 19 or {
                key: len(rows) for key, rows in cls.groups.items()} != {
                "bare": 5, "rpc": 4, "soap12": 2, "header-rpc": 4, "header-doc": 4}:
            raise ValueError("incomplete or duplicate case inventory")
        cls.directory = tempfile.TemporaryDirectory(prefix="xml-cxf-peer-")
        cls.addClassCleanup(cls.directory.cleanup)
        build = Path(cls.directory.name)
        generated = build / "generated"
        classes = build / "classes"
        generated.mkdir()
        classes.mkdir()
        jars = str(PEER / "jars/*")
        java = ["java", "-Dorg.slf4j.simpleLogger.defaultLogLevel=warn"]
        for rows in cls.groups.values():
            row = rows[0]
            output = checked([*java, "-cp", jars, "org.apache.cxf.tools.wsdlto.WSDLToJava",
                              "-d", str(generated), "-suppress-generated-date", "-faultSerialVersionUID", "1",
                              "-b", str(PEER / "serializable.xjb"),
                              "-sn", row["service"], str(execution_wsdl(row))])
            if output:
                raise AssertionError("unexpected code generation output: " + output)
        output = checked(["javac", "--release", "17", "-Xlint:all", "-Werror", "-cp", jars,
                          "-d", str(classes), *map(str, sorted(generated.rglob("*.java"))),
                          str(PEER / "CxfPeer.java")])
        if output:
            raise AssertionError("unexpected compiler output: " + output)
        cls.java = [*java, "-cp", str(classes) + os.pathsep + jars, "CxfPeer"]
        cls.qore = [os.environ.get("QORE", "qore"), "-b", "--enable-debug", str(PEER / "qore-peer.qr")]
        cls.env = os.environ.copy()
        cls.env["QORE_MODULE_DIR"] = os.pathsep.join(filter(None, (
            str(REPO / "build-debug"), str(REPO / "qlib"), cls.env.get("QORE_MODULE_DIR"))))

    def test_derivative_changes_are_explicit(self):
        source = (ROOT / "cxf/header_doc_lit.wsdl").read_text()
        expected = source.replace('schemaLocation="./header.xsd"', 'schemaLocation="../cxf/header.xsd"')
        # Only inoutHeader's two wrong part references change; unrelated in/out parts remain original.
        document = ET.fromstring(source)
        ns = {"w": "http://schemas.xmlsoap.org/wsdl/", "s": "http://schemas.xmlsoap.org/wsdl/soap/"}
        self.assertEqual(["in", "out"], [body.attrib["parts"] for body in document.findall(
            "w:binding[@name='headerTesterSOAPBinding']/w:operation[@name='inoutHeader']/*/s:body", ns)])
        start = expected.index('<operation name="inoutHeader">', expected.index('<binding name="headerTesterSOAPBinding"'))
        end = expected.index('</operation>', start)
        expected = expected[:start] + expected[start:end].replace('parts="in"', 'parts="inout"').replace(
            'parts="out"', 'parts="inout"') + expected[end:]
        expected = expected.replace('<definitions ',
            '<!-- Qore derivative corrections: Copyright (C) 2026 Qore Technologies, s.r.o. -->\n<definitions ', 1)
        self.assertEqual(expected, (ROOT / "cxf-derived/header_doc_lit_corrected_parts.wsdl").read_text())

    def test_qore_serialization_matches_cxf(self):
        for fixture, rows in self.groups.items():
            for graph in ("source", "saved"):
                with self.subTest(fixture=fixture, graph=graph):
                    output = json.loads(checked([*self.qore, "encode", fixture, graph], env=self.env))
                    self.assertEqual([row["id"] for row in rows], [row["id"] for row in output])
                    for expected, actual in zip(rows, output):
                        for direction in ("request", "response"):
                            self.assertEqual(infoset(expected[direction]), infoset(actual[direction]["body"]),
                                             expected["id"] + " " + direction)

    def test_soap12_absolute_action_derivative(self):
        provenance = json.loads((ROOT / "cxf-derived/soap12-action.json").read_text())
        source = (ROOT / provenance['source']).read_bytes()
        derived = (ROOT / provenance['derived']).read_bytes()
        self.assertEqual(provenance['source_sha256'],hashlib.sha256(source).hexdigest())
        self.assertEqual(provenance['derived_sha256'],hashlib.sha256(derived).hexdigest())
        transform = provenance['transform']
        self.assertEqual(1,source.count(transform['from'].encode()))
        expected = source.replace(transform['from'].encode(),transform['to'].encode()).replace(
            b'<definitions ',provenance['modification_notice'].encode()+b'<definitions ',1)
        self.assertEqual(expected,derived)
        captured = next(row for row in self.cases if row['fixture']=='soap12' and row['operation']=='sayHi')
        self.assertIn('action="sayHiAction"',captured['request_headers']['Content-Type'])
        self.assertIn('action="urn:cxf:sayHiAction"',execution_headers(captured)['Content-Type'])

    def test_cxf_server_accepts_reference_and_qore_requests(self):
        for fixture, rows in self.groups.items():
            with self.subTest(fixture=fixture):
                with endpoint([*self.java, "server", fixture, str(execution_wsdl(rows[0]))]) as (url, port):
                    for row in rows:
                        with contextlib.closing(http.client.HTTPConnection("127.0.0.1", port, timeout=30)) as client:
                            client.request("POST", "/service", row["request"].encode(), execution_headers(row))
                            response = client.getresponse()
                            body = response.read()
                            self.assertEqual(row["status"], response.status)
                            self.assertEqual(infoset(row["response"]), infoset(body))
                    for graph in ("source", "saved"):
                        self.assertEqual("PASS\t" + fixture + "\n", checked(
                            [*self.qore, "client", fixture, graph, url], env=self.env))

    def test_cxf_client_accepts_qore_responses(self):
        for fixture, rows in self.groups.items():
            for graph in ("source", "saved"):
                with self.subTest(fixture=fixture, graph=graph):
                    with endpoint([*self.qore, "server", fixture, graph], self.env) as (url, port):
                        if fixture == "soap12":
                            # The historical captured relative action is a required negative control.
                            original = next(row for row in rows if row['operation']=='sayHi')
                            with contextlib.closing(http.client.HTTPConnection("127.0.0.1",port,timeout=30)) as peer:
                                peer.request("POST","/service",original['request'].encode(),original['request_headers'])
                                response = peer.getresponse(); body = response.read()
                                self.assertEqual(400,response.status,body)
                                self.assertIn(b"invalid SOAP 1.2 action URI",body)
                        self.assertEqual("PASS\t" + fixture + "\n", checked(
                            [*self.java, "client", fixture, str(execution_wsdl(rows[0])), url]))

    def test_infoset_comparison_keeps_semantics(self):
        self.assertEqual(infoset('<p:r xmlns:p="urn:r"><x> a </x></p:r>'),
                         infoset('<r xmlns="urn:r"><x xmlns=""> a </x></r>'))
        for other in ('<r xmlns="urn:wrong"><x xmlns=""> a </x></r>',
                      '<r xmlns="urn:r"><x xmlns="">a</x></r>',
                      '<r xmlns="urn:r"><x> a </x></r>'):
            self.assertNotEqual(infoset('<r xmlns="urn:r"><x xmlns=""> a </x></r>'), infoset(other))
        with self.assertRaises(ValueError):
            infoset('<r>mixed<x/></r>')

    def test_endpoint_reports_startup_failure(self):
        import sys
        with self.assertRaisesRegex(AssertionError, "deliberate endpoint startup failure"):
            with endpoint([sys.executable, "-c", "import sys; "
                           "sys.stderr.write('deliberate endpoint startup failure'); sys.exit(3)"]):
                self.fail("failed endpoint was reported ready")


if __name__ == "__main__":
    unittest.main()
