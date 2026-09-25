#!/usr/bin/env python3
"""SOAP role/capability oracle and forwarding. Copyright (C) 2026 Qore Technologies, s.r.o."""
import hashlib
import http.client
import json
import os
import queue
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree
from test_cxf_peer import endpoint
from test_http_request_url import origin
from test_soap_envelope import ENV, URI, LocalSchemas, PEER as ENVELOPE_PEER
import jvm

ROOT = Path(__file__).resolve().parent
PEER = ROOT / "soap-node-peer"
TRACKING = "{urn:tracking}Tracking"
NEXT = {"11":"http://schemas.xmlsoap.org/soap/actor/next", "12":URI["12"] + "/role/next"}
NONE = URI["12"] + "/role/none"
ULTIMATE = URI["12"] + "/role/ultimateReceiver"


def wire(version, role=None, mandatory=False, relay=False, name="Tracking"):
    root = etree.Element(f"{{{URI[version]}}}Envelope", nsmap={"e":URI[version], "t":"urn:tracking"})
    container = etree.SubElement(root, f"{{{URI[version]}}}Header")
    block = etree.SubElement(container, f"{{urn:tracking}}{name}")
    if role is not None:
        block.set(f"{{{URI[version]}}}" + ("role" if version == "12" else "actor"), role)
    block.set(f"{{{URI[version]}}}mustUnderstand", "1" if mandatory else "0")
    if version == "12":
        block.set(f"{{{URI[version]}}}relay", "true" if relay else "false")
    block.text = "invoice-71"
    body = etree.SubElement(root, f"{{{URI[version]}}}Body")
    etree.SubElement(body, "{urn:soap-node-test}value").text = "invoice-71"
    return etree.tostring(root).decode()


def run_jobs(jobs):
    result = subprocess.run(["qore", "-b", "--enable-debug", str(PEER / "node.qr")],
                            input=json.dumps({"jobs":jobs}), capture_output=True, text=True, env=ENV, timeout=60)
    if result.returncode or result.stderr:
        raise AssertionError(result.stdout + result.stderr)
    return json.loads(result.stdout)


class SoapNodeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dependencies = ROOT / "cxf-peer"
        manifest = json.loads((dependencies / "manifest.json").read_text())
        if (manifest["implementation"], manifest["version"]) != ("Apache CXF", "4.1.3"):
            raise AssertionError("unexpected independent peer")
        for entry in manifest["artifacts"]:
            data = (dependencies / entry["path"]).read_bytes()
            if len(data) != entry["size"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise AssertionError("modified pinned CXF dependency")
        cls.directory = tempfile.TemporaryDirectory(prefix="xml-soap-node-")
        cls.addClassCleanup(cls.directory.cleanup)
        jars = str(dependencies / "jars/*")
        result = subprocess.run(["javac", "--release", "17", "-Xlint:all", "-Werror", "-cp", jars,
                                 "-d", cls.directory.name, str(PEER / "NodePeer.java")],
                                capture_output=True, text=True, timeout=60, env=jvm.environment())
        if result.returncode or result.stdout or result.stderr:
            raise AssertionError(result.stdout + result.stderr)
        # Deliberate negative requests produce CXF warning-level fault logs; assertions inspect the actual faults.
        cls.java = ["java", "-Dorg.slf4j.simpleLogger.defaultLogLevel=error", "-cp",
                    cls.directory.name + os.pathsep + jars, "NodePeer"]

    def test_ultimate_receiver_matches_independent_cxf(self):
        jobs, expected = [], []
        for version in URI:
            for known in (False, True):
                with endpoint([*self.java, version, str(known).lower()]) as (_, port):
                    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
                    self.addCleanup(connection.close)
                    for role in (None, NEXT[version], ULTIMATE, NONE, "urn:billing", "urn:other"):
                        for mandatory in (False, True):
                            for name in ("Tracking", "Other"):
                                xml = wire(version, role, mandatory, name=name)
                                jobs.append({"xml":xml,"roles":["urn:billing"],"known":[TRACKING] if known else []})
                                target = role in (None, NEXT[version], "urn:billing") or (version == "12" and role == ULTIMATE)
                                reject = target and mandatory and (not known or name != "Tracking")
                                expected.append(reject)
                                connection.request("POST", "/service", xml.encode(), {"SOAPAction":'"urn:echo"',
                                    "Content-Type":"application/soap+xml; action=\"urn:echo\"" if version == "12" else "text/xml"})
                                response = connection.getresponse()
                                body = response.read()
                                self.assertEqual(500 if reject else 200, response.status, (version, role, mandatory, name, body))
                                root = etree.fromstring(body)
                                if reject:
                                    fault = root.find(f"{{{URI[version]}}}Body/{{{URI[version]}}}Fault")
                                    code = fault.find(f"{{{URI[version]}}}Code/{{{URI[version]}}}Value") if version == "12" else fault.find("faultcode")
                                    prefix, local = code.text.split(":")
                                    self.assertEqual((URI[version], "MustUnderstand"), (code.nsmap[prefix], local))
                                else:
                                    self.assertEqual("invoice-71", root.find(f"{{{URI[version]}}}Body/{{urn:soap-node-test}}value").text)
                    connection.close()
        for row, reject in zip(run_jobs(jobs), expected, strict=True):
            self.assertEqual(reject, row.get("error") == "SOAP-MUST-UNDERSTAND", row)
            if reject:
                self.assertEqual([], row["called"])
            else:
                self.assertNotIn("error", row)

    def test_qore_handler_faults_against_pinned_schemas(self):
        parser = etree.XMLParser(no_network=True, resolve_entities=False)
        parser.resolvers.add(LocalSchemas())
        schemas = {version:etree.XMLSchema(etree.fromstring((ENVELOPE_PEER / f"soap{version}.xsd").read_bytes(), parser))
                   for version in URI}
        for state in ("source", "saved", "data"):
            for version in URI:
                for known in (False, True):
                    for retained in (False, True):
                        rows = []
                        for role in (None, NEXT[version], NONE, "urn:billing", "urn:other"):
                            for name in ("Tracking", "Other"):
                                targeted = role in (None, NEXT[version], "urn:billing")
                                rejected = targeted and (not known or name != "Tracking")
                                xml = wire(version, role, True, name=name).replace("urn:soap-node-test", "urn:soap-envelope-test")
                                rows.append((xml, rejected, name))
                        command = ["qore", "-b", "--enable-debug", str(PEER / "http.qr"), version, state,
                                   "known" if known else "unknown", "retained" if retained else "native",
                                   str(sum(not row[1] for row in rows))]
                        with endpoint(command, ENV) as (_, port):
                            connection = http.client.HTTPConnection("127.0.0.1",port,timeout=10)
                            self.addCleanup(connection.close)
                            for xml, rejected, name in rows:
                                connection.request("POST", "/service", xml.encode(), {"SOAPAction":"urn:echo",
                                    "Content-Type":"application/soap+xml" if version == "12" else "text/xml"})
                                response = connection.getresponse()
                                body = response.read()
                                self.assertEqual(500 if rejected else 200, response.status, body)
                                root = etree.fromstring(body)
                                schemas[version].assertValid(root)
                                if rejected:
                                    fault = root.find(f"{{{URI[version]}}}Body/{{{URI[version]}}}Fault")
                                    code = fault.find(f"{{{URI[version]}}}Code/{{{URI[version]}}}Value") if version == "12" else fault.find("faultcode")
                                    prefix, local = code.text.split(":")
                                    self.assertEqual((URI[version],"MustUnderstand"),(code.nsmap[prefix],local))
                                    if version == "12":
                                        blocks = root.findall(f"{{{URI[version]}}}Header/{{{URI[version]}}}NotUnderstood")
                                        self.assertEqual(1,len(blocks))
                                        prefix, local = blocks[0].get("qname").split(":")
                                        self.assertEqual(("urn:tracking",name),(blocks[0].nsmap[prefix],local))
                                else:
                                    self.assertEqual("invoice-71",root.find(f"{{{URI[version]}}}Body/{{urn:soap-envelope-test}}value").text)
                            connection.close()

    def test_client_relative_roles_follow_effective_redirect_url(self):
        requests = queue.Queue()
        root = etree.fromstring(wire("12","billing",True).replace("urn:soap-node-test","urn:soap-envelope-test").encode())
        root.set("{http://www.w3.org/XML/1998/namespace}base","../billing/")
        root[0].set("{http://www.w3.org/XML/1998/namespace}base","roles/")
        response_xml = etree.tostring(root)
        with origin("final", requests, lambda request:(200,{},response_xml), content_type="application/soap+xml") as final_url:
            destination = final_url + "/branch/reply"
            with origin("redirect", requests, lambda request:(307,{"Location":destination},b"")) as original_url:
                role = final_url + "/billing/roles/billing"
                jobs = [{"state":state,"retained":retained,"url":original_url + "/original","roles":[role]}
                        for state in ("source","saved","data") for retained in (False,True)]
                result = subprocess.run(["qore","-b","--enable-debug",str(PEER / "client.qr")],
                    input=json.dumps({"jobs":jobs}),capture_output=True,text=True,env=ENV,timeout=60)
                self.assertEqual(0,result.returncode,result.stdout + result.stderr)
                self.assertEqual("",result.stderr)
                self.assertEqual([{"value":"invoice-71","role":role,"processed":True,"targeted":True,"url":destination}]
                                 * len(jobs),json.loads(result.stdout))
                for _ in jobs:
                    self.assertEqual("redirect",requests.get_nowait()["origin"])
                    self.assertEqual("final",requests.get_nowait()["origin"])
                self.assertTrue(requests.empty())

    def test_intermediary_relay_table_and_second_hop(self):
        jobs, expected = [], []
        for version in URI:
            for role in (None, NEXT[version], ULTIMATE, NONE, "urn:billing", "urn:other"):
                for known in (False, True):
                    for relay in (False, True):
                        for mandatory in (False, True):
                            target = role in (NEXT[version], "urn:billing")
                            reject = target and mandatory and not known
                            keep = not target or (not known and version == "12" and relay)
                            jobs.append({"xml":wire(version,role,mandatory,relay),"ultimate":False,
                                "roles":["urn:billing"],"known":[TRACKING] if known else [],"base":"https://example.org/original"})
                            expected.append((version,reject,keep,known and target))
        forwarded_jobs = []
        for job, row, (version,reject,keep,processed) in zip(jobs,run_jobs(jobs),expected,strict=True):
            if reject:
                self.assertEqual("SOAP-MUST-UNDERSTAND",row["error"])
                self.assertEqual([],row["called"])
                continue
            self.assertNotIn("error",row)
            self.assertEqual(processed,row["headers"][0]["processed"])
            self.assertEqual(keep,row["headers"][0]["forwarded"])
            root = etree.fromstring(row["forward"].encode())
            original = etree.fromstring(job["xml"].encode())
            self.assertEqual("https://example.org/original",root.get("{http://www.w3.org/XML/1998/namespace}base"))
            headers = root.find(f"{{{URI[version]}}}Header")
            self.assertEqual(1 if keep else 0,len(headers))
            if keep:
                self.assertEqual(etree.tostring(original[0][0], method="c14n"),etree.tostring(headers[0],method="c14n"))
            self.assertEqual(etree.tostring(original[1],method="c14n"),etree.tostring(root[1],method="c14n"))
            forwarded_jobs.append({"xml":row["forward"],"known":[TRACKING],"roles":["urn:billing"]})
        for row in run_jobs(forwarded_jobs):
            self.assertNotIn("error",row)


if __name__ == "__main__":
    unittest.main(verbosity=2)
