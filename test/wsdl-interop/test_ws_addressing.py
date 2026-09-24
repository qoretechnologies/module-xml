#!/usr/bin/env python3
"""Live WS-Addressing exchanges with Apache CXF over the pinned add_numbers.wsdl and add_numbers_soap12.wsdl contracts.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from test_cxf_peer import checked, endpoint

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
PEER = ROOT / "addressing-peer"
CONTRACTS = {"soap11": ROOT / "cxf/add_numbers.wsdl", "soap12": ROOT / "cxf/add_numbers_soap12.wsdl"}
# every port of the contracts: WS-Addressing required, anonymous responses only, and non-anonymous responses only
PORTS = ("AddNumbersPort", "AddNumbersOnlyAnonPort", "AddNumbersNonAnonPort")
# CXF clients only accept a decoupled reply that arrives after the 202 acknowledgement, which SoapHandler cannot
# order yet (see addressing-peer/README.md), so CXF clients exchange with the ports that reply on the back channel
ANONYMOUS_PORTS = ("AddNumbersPort", "AddNumbersOnlyAnonPort")


class WsAddressingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        catalog = json.loads((ROOT / "cxf/catalog.json").read_text())
        for wsdl in CONTRACTS.values():
            entry = next(row for row in catalog["resources"] if row["path"] == wsdl.name)
            if hashlib.sha256(wsdl.read_bytes()).hexdigest() != entry["sha256"]:
                raise ValueError("modified pinned WS-Addressing contract: " + wsdl.name)
        dependency = json.loads((ROOT / "cxf-peer/manifest.json").read_text())
        if (dependency["implementation"], dependency["version"]) != ("Apache CXF", "4.1.3"):
            raise ValueError("unexpected peer")
        expected = set()
        for artifact in dependency["artifacts"]:
            path = ROOT / "cxf-peer" / artifact["path"]
            expected.add(path)
            data = path.read_bytes()
            if len(data) != artifact["size"] or hashlib.sha256(data).hexdigest() != artifact["sha256"]:
                raise ValueError("changed independent dependency: " + str(path))
        if expected != set((ROOT / "cxf-peer/jars").glob("*.jar")):
            raise ValueError("unaccounted dependency")
        cls.directory = tempfile.TemporaryDirectory(prefix="xml-addressing-peer-")
        cls.addClassCleanup(cls.directory.cleanup)
        jars = str(ROOT / "cxf-peer/jars/*")
        java = ["java", "-Dorg.slf4j.simpleLogger.defaultLogLevel=warn"]
        # the two contracts generate the same classes with different bindings, so each has its own build
        cls.generated = {}
        cls.java = {}
        for version, wsdl in CONTRACTS.items():
            build = Path(cls.directory.name) / version
            generated = build / "generated"
            classes = build / "classes"
            generated.mkdir(parents=True)
            classes.mkdir()
            output = checked([*java, "-cp", jars, "org.apache.cxf.tools.wsdlto.WSDLToJava", "-d", str(generated),
                              "-suppress-generated-date", "-faultSerialVersionUID", "1", str(wsdl)])
            if output:
                raise AssertionError("unexpected code generation output: " + output)
            # the generated fault exception keeps the contract's fault bean, which is not serializable
            output = checked(["javac", "--release", "17", "-Xlint:all,-serial", "-Werror", "-cp", jars, "-d",
                              str(classes), *map(str, sorted(generated.rglob("*.java")))])
            if output:
                raise AssertionError("unexpected compiler output: " + output)
            output = checked(["javac", "--release", "17", "-Xlint:all", "-Werror", "-cp",
                              str(classes) + os.pathsep + jars, "-d", str(classes), str(PEER / "AddressingPeer.java")])
            if output:
                raise AssertionError("unexpected compiler output: " + output)
            cls.generated[version] = generated
            cls.java[version] = [*java, "-cp", str(classes) + os.pathsep + jars, "AddressingPeer"]
        cls.qore = [os.environ.get("QORE", "qore"), "-b", "--enable-debug", str(PEER / "qore-peer.qr")]
        cls.env = os.environ.copy()
        cls.env["QORE_MODULE_DIR"] = os.pathsep.join((str(REPO / "build-debug"), str(REPO / "qlib")))

    def test_generated_actions(self):
        # only addNumbers3 declares wsam:Action values, which are kept as written although they are relative; the other
        # operations use the default action pattern
        for version, generated in self.generated.items():
            with self.subTest(version=version):
                service = (generated / "org/apache/cxf/systest/ws/addr_feature/AddNumbersPortType.java").read_text()
                self.assertEqual(1, service.count("@Action("))
                self.assertIn('@Action(input = "3in", output = "3out", fault = {@FaultAction(className = '
                              'AddNumbersFault_Exception.class, value = "3fault")})', service)

    def test_live_qore_clients_and_cxf_server(self):
        for version, wsdl in CONTRACTS.items():
            for port in PORTS:
                with endpoint([*self.java[version], "server", str(wsdl), port]) as (_, listener):
                    url = f"http://127.0.0.1:{listener}/add"
                    for client in ("SoapClient", "SoapClientIo"):
                        with self.subTest(version=version, port=port, client=client):
                            self.assertEqual("PASS\n", checked([*self.qore, "client", str(wsdl), port, url, client],
                                                               env=self.env))

    def test_live_cxf_clients_and_qore_server(self):
        for version, wsdl in CONTRACTS.items():
            for port in ANONYMOUS_PORTS:
                with self.subTest(version=version, port=port):
                    with endpoint([*self.qore, "server", str(wsdl), port], self.env) as (_, listener):
                        self.assertEqual("PASS\n", checked([*self.java[version], "client", str(wsdl),
                                                            f"http://127.0.0.1:{listener}/add", port]))


if __name__ == "__main__":
    unittest.main()
