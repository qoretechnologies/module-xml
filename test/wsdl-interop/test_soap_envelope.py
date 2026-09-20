#!/usr/bin/env python3
"""SOAP envelope peers and W3C fault schema oracles. Copyright (C) 2026 Qore Technologies, s.r.o."""
import hashlib
import http.client
import json
import os
from pathlib import Path
import queue
import subprocess
import unittest

from lxml import etree
from test_cxf_peer import endpoint
from test_http_request_url import origin

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
PEER = ROOT / "soap-envelope-peer"
URI = {"11": "http://schemas.xmlsoap.org/soap/envelope/", "12": "http://www.w3.org/2003/05/soap-envelope"}
ENV = dict(os.environ, QORE_MODULE_DIR=str(REPO / "build-debug") + ":" + str(REPO / "qlib"))


def envelope(version, content=None, root="Envelope", uri=None):
    return f'<e:{root} xmlns:e="{uri or URI[version]}" xmlns:t="urn:soap-envelope-test">{content if content is not None else body()}</e:{root}>'


def body():
    return '<e:Body><t:value>invoice-71</t:value></e:Body>'


class LocalSchemas(etree.Resolver):
    def resolve(self, url, public_id, context):
        if url == "http://www.w3.org/2001/xml.xsd":
            return self.resolve_filename(str(PEER / "xml.xsd"), context)
        raise OSError("unexpected schema import: " + url)


class SoapEnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = json.loads((PEER / "schemas.json").read_text())
        for entry in manifest["schemas"]:
            data = (PEER / entry["path"]).read_bytes()
            if len(data) != entry["size"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise ValueError("changed pinned schema")
        cls.schemas = {}
        for version in URI:
            parser = etree.XMLParser(no_network=True, resolve_entities=False)
            parser.resolvers.add(LocalSchemas())
            cls.schemas[version] = etree.XMLSchema(etree.fromstring((PEER / f"soap{version}.xsd").read_bytes(), parser))

    def test_operation_faults_validate_against_pinned_schemas(self):
        result = subprocess.run(["qore", "-b", "--enable-debug", str(PEER / "peer.qr"), "faults"],
                                capture_output=True, text=True, env=ENV, timeout=30)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("", result.stderr)
        for version, xml in zip(URI, json.loads(result.stdout), strict=True):
            parsed = etree.fromstring(xml.encode())
            self.schemas[version].assertValid(parsed)
            fault = parsed.find(f"{{{URI[version]}}}Body/{{{URI[version]}}}Fault")
            reason = fault.find("faultstring") if version == "11" else fault.find(f"{{{URI['12']}}}Reason/{{{URI['12']}}}Text")
            self.assertEqual("Invoice not found", reason.text)
            if version == "12":
                self.assertEqual("en", reason.get("{http://www.w3.org/XML/1998/namespace}lang"))

    def test_external_sender_and_schema_valid_faults(self):
        for state in ("source", "saved", "data"):
            for version in URI:
                other = "11" if version == "12" else "12"
                rows = [(envelope(other), "11", "VersionMismatch"),
                        (envelope(version, uri="urn:future"), version, "VersionMismatch"),
                        (envelope(version, root="Container"), version, "VersionMismatch"),
                        (envelope(version, body() + "<e:Header/>"), version, "Sender"),
                        (envelope(version, "<e:Header><unqualified/></e:Header>" + body()), version, "Sender"),
                        (envelope(version, "<e:Header/>" * 2 + body()), version, "Sender"),
                        (envelope(version, body() * 2), version, "Sender"),
                        (envelope(version, "bad" + body()), version, "Sender"),
                        ('<?work prohibited?>' + envelope(version), version, "Sender"),
                        ('<!DOCTYPE e:Envelope>' + envelope(version), version, "Sender")]
                command = ["qore", "-b", "--enable-debug", str(PEER / "peer.qr"), "server", version, state, str(len(rows))]
                with endpoint(command, ENV) as (_, port):
                    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
                    self.addCleanup(conn.close)
                    for xml, fault_version, code in rows:
                        if fault_version == "11" and code == "Sender":
                            code = "Client"
                        conn.request("POST", "/service", xml.encode(), {"Content-Type": "application/soap+xml" if version == "12" else "text/xml", "SOAPAction": "urn:echo"})
                        response = conn.getresponse()
                        wire = response.read()
                        self.assertEqual(400 if fault_version == "12" and code == "Sender" else 500, response.status, wire)
                        parsed = etree.fromstring(wire)
                        self.schemas[fault_version].assertValid(parsed)
                        fault = parsed.find(f"{{{URI[fault_version]}}}Body/{{{URI[fault_version]}}}Fault")
                        node = fault.find("faultcode") if fault_version == "11" else fault.find(f"{{{URI['12']}}}Code/{{{URI['12']}}}Value")
                        prefix, local = node.text.split(":")
                        self.assertEqual(code, local)
                        self.assertEqual(URI[fault_version], node.nsmap[prefix])
                        if code == "VersionMismatch":
                            supported = parsed.find(f"{{{URI[fault_version]}}}Header/{{{URI['12']}}}Upgrade/{{{URI['12']}}}SupportedEnvelope")
                            prefix, local = supported.get("qname").split(":")
                            self.assertEqual("Envelope", local)
                            self.assertEqual(URI[version], supported.nsmap[prefix])
                        conn.request("POST", "/service", envelope(version).encode(), {"Content-Type": "application/soap+xml" if version == "12" else "text/xml", "SOAPAction": "urn:echo"})
                        response = conn.getresponse()
                        wire = response.read()
                        self.assertEqual(200, response.status, wire)
                        parsed = etree.fromstring(wire)
                        self.schemas[version].assertValid(parsed)
                        self.assertEqual("invoice-71", parsed.find(f"{{{URI[version]}}}Body/{{urn:soap-envelope-test}}value").text)
                    conn.close()

    def test_external_responses_and_client_recovery(self):
        received = queue.Queue()
        replies = queue.Queue()
        expected = []
        jobs = []
        with origin("server", received, lambda request: (200, {}, replies.get_nowait())) as url:
            for state in ("source", "saved", "data"):
                for version in URI:
                    for retained in (False, True):
                        for xml, error in [(envelope("11" if version == "12" else "12"), "SOAP-VERSION-MISMATCH"),
                                           (envelope(version, body() + "<e:Header/>"), "SOAP-DESERIALIZATION-ERROR"),
                                           ('<?work prohibited?>' + envelope(version), "SOAP-DESERIALIZATION-ERROR"),
                                           (envelope(version), None)]:
                            replies.put(xml.encode())
                            jobs.append({"state":state, "version":version, "retained":retained, "url":url + "/service"})
                            expected.append({"error":error} if error else {"value":"invoice-71"})
            run = subprocess.run(["qore", "-b", "--enable-debug", str(PEER / "peer.qr"), "client"],
                                 input=json.dumps({"jobs":jobs}), capture_output=True, text=True, env=ENV, timeout=60)
            self.assertEqual(0, run.returncode, run.stdout + run.stderr)
            self.assertEqual("", run.stderr)
            self.assertEqual(expected, json.loads(run.stdout))
            self.assertTrue(replies.empty())
            for job in jobs:
                request = received.get_nowait()
                parsed = etree.fromstring(request["body"])
                self.assertEqual(f"{{{URI[job['version']]}}}Envelope", parsed.tag)
                self.schemas[job["version"]].assertValid(parsed)
                self.assertEqual("invoice-71", parsed.find(f"{{{URI[job['version']]}}}Body/{{urn:soap-envelope-test}}value").text)
            self.assertTrue(received.empty())


if __name__ == "__main__":
    unittest.main(verbosity=2)
