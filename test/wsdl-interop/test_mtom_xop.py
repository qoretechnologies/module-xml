#!/usr/bin/env python3
"""Live MTOM/XOP exchanges with Apache CXF over the pinned mtom_xop.wsdl contract.

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
PEER = ROOT / "mtom-peer"
WSDL = ROOT / "cxf/mtom_xop.wsdl"


class MtomXopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        catalog = json.loads((ROOT / "cxf/catalog.json").read_text())
        entry = next(row for row in catalog["resources"] if row["path"] == WSDL.name)
        if hashlib.sha256(WSDL.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("modified pinned MTOM contract")
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
        cls.directory = tempfile.TemporaryDirectory(prefix="xml-mtom-peer-")
        cls.addClassCleanup(cls.directory.cleanup)
        build = Path(cls.directory.name)
        cls.generated = build / "generated"
        classes = build / "classes"
        cls.generated.mkdir()
        classes.mkdir()
        jars = str(ROOT / "cxf-peer/jars/*")
        java = ["java", "-Dorg.slf4j.simpleLogger.defaultLogLevel=warn"]
        output = checked([*java, "-cp", jars, "org.apache.cxf.tools.wsdlto.WSDLToJava", "-d", str(cls.generated),
                          "-suppress-generated-date", "-faultSerialVersionUID", "1", "-sn", "TestMtomService",
                          str(WSDL)])
        if output:
            raise AssertionError("unexpected code generation output: " + output)
        output = checked(["javac", "--release", "17", "-Xlint:all", "-Werror", "-cp", jars, "-d", str(classes),
                          *map(str, sorted(cls.generated.rglob("*.java"))), str(PEER / "MtomPeer.java")])
        if output:
            raise AssertionError("unexpected compiler output: " + output)
        cls.java = [*java, "-cp", str(classes) + os.pathsep + jars, "MtomPeer"]
        cls.qore = [os.environ.get("QORE", "qore"), "-b", "--enable-debug", str(PEER / "qore-peer.qr")]
        cls.env = os.environ.copy()
        cls.env["QORE_MODULE_DIR"] = os.pathsep.join((str(REPO / "build-debug"), str(REPO / "qlib")))

    def test_generated_mappings(self):
        # testXop carries octets through a DataHandler; testXopString's base64Binary element is a String holding
        # its lexical form, which JAXB never optimizes
        service = (self.generated / "org/apache/cxf/mime/TestMtom.java").read_text()
        self.assertIn("jakarta.xml.ws.Holder<jakarta.activation.DataHandler> attachinfo", service)
        text = (self.generated / "org/apache/cxf/mime/types/XopStringType.java").read_text()
        self.assertRegex(text, r'@XmlMimeType\("text/plain; charset=utf-8"\)\s+'
                               r'@XmlSchemaType\(name = "base64Binary"\)\s+protected String attachinfo;')

    def test_live_qore_clients_and_cxf_server(self):
        with endpoint([*self.java, "server", str(WSDL)]) as (url, _):
            for graph in ("source", "saved"):
                for client in ("SoapClient", "SoapClientIo"):
                    for form in ("mtom", "plain"):
                        with self.subTest(graph=graph, client=client, form=form):
                            self.assertEqual("PASS\n", checked([*self.qore, "client", graph, url, client, form],
                                                               env=self.env))

    def test_live_cxf_clients_and_qore_server(self):
        for graph in ("source", "saved"):
            for form in ("mtom", "plain"):
                with self.subTest(graph=graph, form=form):
                    with endpoint([*self.qore, "server", graph], self.env) as (url, _):
                        self.assertEqual("PASS\n", checked([*self.java, "client", str(WSDL), url, form]))


if __name__ == "__main__":
    unittest.main()
