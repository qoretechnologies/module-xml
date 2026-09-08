#!/usr/bin/env python3
"""XML whitespace in SOAP containers does not change scalar payloads.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from pathlib import Path
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS, XSD
import survey


class SoapContainerWhitespaceTest(unittest.TestCase):
    def test_document_and_rpc_container_boundaries(self):
        self.check_boundaries(False)

    def test_header_part_round_trip_requirement_p6(self):
        self.check_boundaries(True)

    def test_single_rpc_parameter_round_trip_requirement_p6(self):
        self.check_boundaries(False, True)

    def check_boundaries(self, headers, scalar_rpc=False):
        jobs, contracts, expected, lookup = {}, [], {}, {}
        value = " A\tB\r\n "
        with tempfile.TemporaryDirectory(prefix="wsdl-soap-space-") as temporary:
            root = Path(temporary)
            for style in ("document", "rpc"):
                if scalar_rpc and style != "rpc":
                    continue
                marker = style == "rpc" and not headers and not scalar_rpc
                source = f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
                    <xs:simpleType name="Value"><xs:union memberTypes="xs:string xs:int"/></xs:simpleType>
                    <xs:simpleType name="Marker"><xs:restriction base="xs:int"/></xs:simpleType>
                    <xs:complexType name="Call"><xs:sequence><xs:element name="body" type="t:Value"/>
                    <xs:element name="marker" type="t:Marker" minOccurs="0"/>
                    </xs:sequence></xs:complexType>
                    <xs:element name="Submit" type="t:Value"/><xs:element name="Reply" type="t:Value"/>
                    <xs:element name="submit" type="t:Call"/><xs:element name="submitResponse" type="t:Call"/>
                    <xs:element name="Context" type="xs:string"/></xs:schema>'''.encode()
                jobs[style] = SchemaJob(style, f"http://example.invalid/{style}.xsd", source)
                for version, namespace in zip(("11", "12"), survey.SOAP_NAMESPACES):
                    name = style + version
                    wsdl = description(version, source.decode()).replace('style="document"', f'style="{style}"')
                    for direction, message, local in (("input", "Request", "Submit"), ("output", "Response", "Reply")):
                        part = f'<w:part name="body" element="t:{local}"/>'
                        body_part = '<w:part name="body" type="t:Value"/>' if style == "rpc" else part
                        if marker:
                            body_part += '<w:part name="marker" type="t:Marker"/>'
                        wsdl = wsdl.replace(part, body_part + ('<w:part name="context" element="t:Context"/>' if headers else ''))
                        wsdl = wsdl.replace(f'<w:{direction}><s:body use="literal"/></w:{direction}>',
                                            f'<w:{direction}><s:body use="literal"'
                                            + (' parts="body"' if headers else '') + f' namespace="{NS}"/>'
                                            + (f'<s:header message="t:{message}" part="context" use="literal"/>' if headers else '')
                                            + f'</w:{direction}>')
                    path = root / (name + ".wsdl")
                    path.write_text(wsdl)
                    messages = []
                    cases = [("formatting", "", " \t\n", True), ("body-text", "Body", "bad", False),
                             ("body-nbsp", "Body", "\u00a0", False), ("header-text", "Header", "bad", False),
                             ("header-nbsp", "Header", "\u00a0", False), ("empty-header", "empty", " \t\n", True)]
                    if not headers:
                        cases = [case for case in cases if case[1] != "Header"]
                    if style == "rpc":
                        cases += [("wrapper-text", "wrapper", "bad", False), ("wrapper-nbsp", "wrapper", "\u00a0", False)]
                    for case, location, text, valid in cases:
                        for direction, local in (("request", "Submit"), ("response", "Reply")):
                            key = name + "/" + case + "/" + direction
                            envelope = etree.Element(f"{{{namespace}}}Envelope", nsmap={"s": namespace, "t": NS})
                            envelope.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                            header = etree.SubElement(envelope, f"{{{namespace}}}Header")
                            header.text = text if location in {"Header", "empty"} else " \t\n"
                            if location != "empty":
                                context = etree.SubElement(header, f"{{{NS}}}Context")
                                context.text, context.tail = " header ", "\n "
                            body = etree.SubElement(envelope, f"{{{namespace}}}Body")
                            body.text = text if location == "Body" else " \t\n"
                            wire_name = local if style == "document" else "submit" + ("Response" if direction == "response" else "")
                            payload = etree.SubElement(body, f"{{{NS}}}{wire_name}")
                            payload.tail = "\n "
                            if style == "rpc":
                                payload.text = text if location == "wrapper" else " \t\n"
                                item = etree.SubElement(payload, "body")
                                item.text, item.tail = value, "\n "
                                if marker:
                                    item = etree.SubElement(payload, "marker")
                                    item.text, item.tail = "9", "\n "
                            else:
                                payload.text = value
                            message_path = root / key.replace("/", "-")
                            message_path.write_bytes(etree.tostring(envelope))
                            messages.append({"file": key, "path": str(message_path), "direction": direction})
                            expected[key] = valid
                            lookup[key] = style, version, wire_name
                    contracts.append({"name": name, "wsdl": str(path), "base": "http://example.invalid/",
                                      "operation": "submit", "binding": "Soap" + version, "messages": messages})
            rows = survey.run_worker(contracts, {})
        accounting = survey.stage_accounting(contracts, rows)["counts"]
        self.assertEqual(len(contracts), accounting["parse"]["ok"])
        for stage in accounting.values():
            self.assertEqual(0, stage["missing"])
            self.assertEqual(0, stage["skipped"])
        outputs = set()
        for row in rows:
            with self.subTest(case=row.get("file", row["case"]), stage=row["stage"]):
                if row["stage"] == "parse":
                    self.assertTrue(row["ok"], row)
                elif row["stage"] == "deserialize":
                    self.assertEqual(expected[row["file"]], row["ok"], row)
                    if not expected[row["file"]]:
                        self.assertEqual("SOAP-DESERIALIZATION-ERROR", row["err"], row)
                elif row["stage"] == "serialize":
                    self.assertTrue(row["ok"], row)
                    style, version, wire_name = lookup[row["file"]]
                    emitted = etree.fromstring(row["body"].encode())
                    self.assertEqual(f"{{{survey.SOAP_NAMESPACES[int(version == '12')]}}}Envelope", emitted.tag)
                    body = emitted.find("{*}Body")
                    self.assertIsNotNone(body, row)
                    self.assertEqual(1, len(body), row)
                    payload = body[0]
                    self.assertEqual(f"{{{NS}}}{wire_name}", payload.tag)
                    self.assertEqual(value, payload[0].text if style == "rpc" else payload.text)
                    if style == "rpc" and not headers and not scalar_rpc:
                        self.assertEqual(2, len(payload))
                        self.assertEqual("marker", payload[1].tag)
                        self.assertEqual(9, int(payload[1].text))
                    jobs[style].documents[row["file"]] = etree.tostring(payload)
                    outputs.add(row["file"])
        self.assertEqual({name for name, valid in expected.items() if valid}, outputs)
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle["schemas"]))
        self.assertEqual(outputs, set(oracle["documents"]))
        for job in jobs.values():
            self.assertTrue(oracle["schemas"][job.name]["ok"], oracle["schemas"][job.name])
            self.assertEqual([], oracle["schemas"][job.name]["warnings"])
            validator = etree.XMLSchema(etree.fromstring(job.schema))
            for name, document in job.documents.items():
                self.assertTrue(validator.validate(etree.fromstring(document)), str(validator.error_log))
                self.assertTrue(oracle["documents"][name]["ok"], oracle["documents"][name])
                self.assertEqual([], oracle["documents"][name]["warnings"])


if __name__ == "__main__":
    unittest.main()
