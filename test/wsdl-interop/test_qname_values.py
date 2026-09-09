#!/usr/bin/env python3
"""Explicit QName identity and providers against independent XSD value constraints.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as run_independent


ROOT = Path(__file__).resolve().parent
XSD = "http://www.w3.org/2001/XMLSchema"
XML = "http://www.w3.org/XML/1998/namespace"
NS = "urn:qname-values"
SOAP = {"11": "http://schemas.xmlsoap.org/soap/envelope/", "12": "http://www.w3.org/2003/05/soap-envelope"}


def schema(choice):
    restriction = ('<xs:restriction base="xs:QName"><xs:enumeration value="'
                   + ("decl:Product" if choice == "catalog" else "Product")
                   + '"/></xs:restriction>') if choice else '<xs:restriction base="xs:QName"/>'
    return (f'<xs:schema xmlns:xs="{XSD}" xmlns:m="{NS}" xmlns:decl="urn:catalog" targetNamespace="{NS}">'
            '<xs:simpleType name="Name">' + restriction + '</xs:simpleType>'
            '<xs:complexType name="Record"><xs:simpleContent><xs:extension base="m:Name">'
            '<xs:attribute name="category" type="m:Name" use="required"/>'
            '</xs:extension></xs:simpleContent></xs:complexType>'
            '<xs:element name="Submit" type="m:Record"/><xs:element name="Reply" type="m:Record"/>'
            '</xs:schema>').encode()


def cases():
    # Each tuple holds declarations at Envelope, Body and payload, respectively.
    scopes = (
        ({"p": "urn:catalog", "q": "urn:catalog"}, {}, {}),
        ({"p": "urn:catalog", "q": "urn:catalog"}, {"p": "urn:other"}, {}),
        ({"p": "urn:catalog"}, {"p": "urn:other"}, {"p": "urn:catalog", "q": "urn:catalog"}),
        ({None: "urn:catalog", "p": "urn:catalog"}, {}, {}),
        ({None: "urn:catalog", "p": "urn:catalog"}, {None: "urn:other"}, {}),
        ({None: "urn:catalog", "p": "urn:catalog"}, {}, {None: ""}),
        ({"p": "URN:catalog", "q": "urn:%63atalog"}, {}, {"é": "urn:catalog"}),
    )
    # Independent grammar expectations; namespace resolution is checked separately.
    texts = (("p:Product", True), ("q:Product", True), ("Product", True), ("xml:lang", True),
             ("p:Other", True), (" \tp:Product\r\n", True), ("missing:Product", True),
             ("p:0name", False), ("a:b:c", False), ("", False), ("p:Product\u00a0", False),
             ("é:中文", True))
    for version, soap in SOAP.items():
        for direction, root in (("request", "Submit"), ("response", "Reply")):
            for index, (outer, middle, inner) in enumerate(scopes):
                for lexical_index, (lexical, grammar) in enumerate(texts):
                    envelope = etree.Element(f"{{{soap}}}Envelope", nsmap={"e": soap, **outer})
                    body = etree.SubElement(envelope, f"{{{soap}}}Body", nsmap=middle)
                    payload = etree.SubElement(body, f"{{{NS}}}{root}", nsmap={"m": NS, **inner})
                    payload.text = lexical
                    payload.set("category", lexical)
                    normalized = lexical.translate(str.maketrans({"\t": " ", "\r": " ", "\n": " "}))
                    normalized = " ".join(item for item in normalized.split(" ") if item)
                    prefix, local = normalized.split(":", 1) if ":" in normalized else ("", normalized)
                    bindings = {**outer, **middle, **inner, "xml": XML, "e": soap, "m": NS}
                    uri = bindings.get(prefix if prefix else None, "")
                    valid = grammar and (not prefix or bool(uri))
                    yield {"name": f"{version}-{direction}-{index}-{lexical_index}",
                           "xml": etree.tostring(envelope, encoding="unicode"),
                           "document": etree.tostring(payload, encoding="utf-8"), "valid": valid,
                           "uri": uri, "local": local, "prefix": prefix, "lexical": normalized,
                           "element": f"{{{NS}}}{root}"}


class QNameValuesTest(unittest.TestCase):
    def test_scoped_values_and_provider_identity(self):
        rows = list(cases())
        self.assertEqual(336, len(rows))
        documents = {row["name"]: row["document"] for row in rows}
        jobs = [SchemaJob(choice or "unrestricted", f"urn:qname-values:{choice or 'unrestricted'}",
                          schema(choice), {f"{choice or 'unrestricted'}-{name}": xml
                                           for name, xml in documents.items()})
                for choice in (None, "catalog", "local_product")]
        independent = run_independent(jobs)
        validators = {job.name: etree.XMLSchema(etree.fromstring(job.schema)) for job in jobs}
        with tempfile.TemporaryDirectory(prefix="wsdl-qname-values-") as temporary:
            manifest = Path(temporary) / "values.json"
            manifest.write_text(json.dumps({"rows": [{key: row[key] for key in ("name", "xml")} for row in rows],
                                            "schemas": {job.name: job.schema.decode() for job in jobs}}))
            process = subprocess.run(["qore", "-b", "--enable-debug", str(ROOT / "qname-values.qr"),
                                      str(manifest)], capture_output=True, text=True, timeout=90)
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual("", process.stderr)
        results = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual([row["name"] for row in rows], [row["name"] for row in results])
        reset_cases = 0
        for row, result in zip(rows, results):
            with self.subTest(name=row["name"]):
                self.assertEqual(row["element"], result["element"])
                expected = {"unrestricted": row["valid"],
                            "catalog": row["valid"] and (row["uri"], row["local"]) == ("urn:catalog", "Product"),
                            "local_product": row["valid"] and (row["uri"], row["local"]) == ("", "Product")}
                for choice, valid in expected.items():
                    self.assertTrue(independent["schemas"][choice]["ok"])
                    verdict = independent["documents"][f"{choice}-{row['name']}"]
                    self.assertEqual(valid, verdict["ok"], verdict)
                    self.assertEqual([], verdict["warnings"])
                    self.assertEqual(valid, result[choice + "_native_valid"])
                    document = etree.fromstring(row["document"])
                    libxml_valid = validators[choice].validate(document)
                    # libxml2 DOM validation can distinguish a null namespace pointer from xmlns="".
                    # Keep its rejection observable; require two other validators and exact expanded identity.
                    reset = choice == "local_product" and valid and document.nsmap.get(None) == ""
                    if reset:
                        reset_cases += 1
                    if reset and not libxml_valid:
                        self.assertEqual(["SCHEMAV_CVC_ENUMERATION_VALID"] * 2,
                                         [error.type_name for error in validators[choice].error_log])
                        self.assertEqual(("", "Product"), (row["uri"], row["local"]))
                    else:
                        self.assertEqual(valid, libxml_valid, (choice, row["document"], str(validators[choice].error_log)))
                for source in ("text", "attribute"):
                    for operation in ("value", "provider", "reconstructed"):
                        key = source + "_" + operation
                        if not row["valid"]:
                            self.assertNotIn(key, result)
                            self.assertEqual("XSD-QNAME-VALUE-ERROR" if operation == "value" else "RUNTIME-TYPE-ERROR",
                                             result[key + "_error"])
                            continue
                        self.assertNotIn(key + "_error", result)
                        value = result[key]
                        for field in ("uri", "local", "lexical", "prefix"):
                            self.assertEqual(row[field], value[field])
                        self.assertEqual("string" if operation != "value" and row["uri"] in ("", XML)
                                         else "object", value["native_type"])
                        self.assertEqual(expected["catalog"], value["catalog"])
                        self.assertEqual(expected["local_product"], value["local_product"])
        self.assertEqual(4, reset_cases)


if __name__ == "__main__":
    unittest.main()
