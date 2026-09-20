#!/usr/bin/env python3
"""SOAP header boolean datatype and HTTP checks. Copyright (C) 2026 Qore Technologies, s.r.o."""
import http.client
import json
import queue
import subprocess
import unittest

from lxml import etree

from test_cxf_peer import endpoint
from test_http_request_url import origin
from test_soap_envelope import ENV, PEER, URI, LocalSchemas, body, envelope

VALUES = ("0", "1", "true", "false", " 1 ", "&#x9;false&#xA;", "", "True", "FALSE", "2", "01", "-1", "yes", "0 1", "\u00a01\u00a0")
VALID = {"11": {"0", "1", " 1 "}, "12": {"0", "1", "true", "false", " 1 ", "&#x9;false&#xA;"}}


def attributes(version):
    return ("mustUnderstand", "relay") if version == "12" else ("mustUnderstand",)


def header(version, attribute, lexical):
    target = "role" if version == "12" else "actor"
    return (f'<t:Context xmlns:t="urn:soap-envelope-test" xmlns:p="{URI[version]}" '
            f'p:{target}="urn:another-node" p:{attribute}="{lexical}">tracking</t:Context>')


def wire(version, attribute, lexical):
    return envelope(version, "<e:Header>" + header(version, attribute, lexical) + "</e:Header>" + body())


class HeaderSchemas(LocalSchemas):
    def resolve(self, url, public_id, context):
        if url in ("urn:pinned:soap11", "urn:pinned:soap12"):
            return self.resolve_filename(str(PEER / (url.removeprefix("urn:pinned:") + ".xsd")), context)
        return super().resolve(url, public_id, context)


class SoapProcessingAttributeTests(unittest.TestCase):
    def test_lexical_matrix_against_pinned_attribute_declarations(self):
        for version, uri in URI.items():
            names = (*attributes(version), "role" if version == "12" else "actor")
            declarations = "".join(f'<xs:attribute ref="p:{name}"/>' for name in names)
            source = (f'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:p="{uri}" '
                      'targetNamespace="urn:soap-envelope-test"><xs:import '
                      f'namespace="{uri}" schemaLocation="urn:pinned:soap{version}"/>'
                      '<xs:element name="Context"><xs:complexType><xs:simpleContent>'
                      f'<xs:extension base="xs:string">{declarations}</xs:extension>'
                      '</xs:simpleContent></xs:complexType></xs:element></xs:schema>')
            parser = etree.XMLParser(no_network=True, resolve_entities=False)
            parser.resolvers.add(HeaderSchemas())
            schema = etree.XMLSchema(etree.fromstring(source.encode(), parser))
            for attribute in attributes(version):
                for lexical in VALUES:
                    with self.subTest(version=version, attribute=attribute, lexical=lexical):
                        self.assertEqual(lexical in VALID[version], schema.validate(
                            etree.fromstring(header(version, attribute, lexical).encode())))

    def test_external_sender_rejections_and_recovery(self):
        for state in ("source", "saved", "data"):
            for version in URI:
                rows = [(attribute, lexical) for attribute in attributes(version) for lexical in VALUES]
                # Every negative is followed by a valid body; every positive reaches the callback once.
                command = ["qore", "-b", "--enable-debug", str(PEER / "peer.qr"), "server", version, state, str(len(rows))]
                with endpoint(command, ENV) as (_, port):
                    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
                    self.addCleanup(connection.close)
                    headers = {"Content-Type": "application/soap+xml" if version == "12" else "text/xml", "SOAPAction": "urn:echo"}
                    for attribute, lexical in rows:
                        connection.request("POST", "/service", wire(version, attribute, lexical).encode(), headers)
                        response = connection.getresponse()
                        content = response.read()
                        if lexical in VALID[version]:
                            self.assertEqual(200, response.status, content)
                        else:
                            self.assertEqual(400 if version == "12" else 500, response.status, content)
                            fault = etree.fromstring(content).find(f"{{{URI[version]}}}Body/{{{URI[version]}}}Fault")
                            code = fault.find(f"{{{URI[version]}}}Code/{{{URI[version]}}}Value") if version == "12" else fault.find("faultcode")
                            prefix, local = code.text.split(":")
                            self.assertEqual(URI[version], code.nsmap[prefix])
                            self.assertEqual("Sender" if version == "12" else "Client", local)
                            connection.request("POST", "/service", envelope(version).encode(), headers)
                            response = connection.getresponse()
                            content = response.read()
                            self.assertEqual(200, response.status, content)
                        self.assertEqual("invoice-71", etree.fromstring(content).find(
                            f"{{{URI[version]}}}Body/{{urn:soap-envelope-test}}value").text)
                    connection.close()

    def test_external_responses_and_persistent_client_recovery(self):
        received, replies = queue.Queue(), queue.Queue()
        jobs, expected = [], []
        with origin("server", received, lambda request: (200, {}, replies.get_nowait())) as url:
            for state in ("source", "saved", "data"):
                for version in URI:
                    for retained in (False, True):
                        for attribute in attributes(version):
                            for lexical in ("invalid", "1"):
                                replies.put(wire(version, attribute, lexical).encode())
                                jobs.append({"state":state,"version":version,"retained":retained,"url":url + "/service"})
                                expected.append({"error":"SOAP-DESERIALIZATION-ERROR"} if lexical == "invalid"
                                                else {"value":"invoice-71"})
            result = subprocess.run(["qore", "-b", "--enable-debug", str(PEER / "peer.qr"), "client"],
                                    input=json.dumps({"jobs":jobs}), capture_output=True, text=True, env=ENV, timeout=60)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual("", result.stderr)
            self.assertEqual(expected, json.loads(result.stdout))
            self.assertTrue(replies.empty())
            for _ in jobs:
                request = received.get_nowait()
                root = etree.fromstring(request["body"])
                self.assertEqual("invoice-71", root.find(
                    f"{{{etree.QName(root).namespace}}}Body/{{urn:soap-envelope-test}}value").text)
            self.assertTrue(received.empty())


if __name__ == "__main__":
    unittest.main(verbosity=2)
