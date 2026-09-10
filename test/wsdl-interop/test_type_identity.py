#!/usr/bin/env python3
"""Check native type wrappers, annotations and values in both actual SOAP bindings.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS, XSD
import survey

XSI = "http://www.w3.org/2001/XMLSchema-instance"


def source(content, definitions="", root_type="t:Record"):
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
      {definitions}<xs:complexType name="Record">{content}</xs:complexType>
      <xs:element name="Submit" type="{root_type}"/><xs:element name="Reply" type="{root_type}"/>
    </xs:schema>'''


def expanded_qname(element, text):
    text = text.strip(" \t\r\n")
    parts = text.split(":")
    if len(parts) == 1:
        return element.nsmap.get(None, ""), text
    if len(parts) != 2 or not all(parts) or parts[0] not in element.nsmap:
        raise AssertionError(f"unbound or malformed QName: {text!r}")
    return element.nsmap[parts[0]], parts[1]


def expanded_type(element):
    text = element.get(f"{{{XSI}}}type")
    return None if text is None else expanded_qname(element, text)


class TypeIdentityTest(unittest.TestCase):
    def test_values_and_selected_types_in_both_bindings(self):
        models = {
            "integer": (source('<xs:sequence><xs:element name="item" type="xs:int"/></xs:sequence>'),
                        {"item": 17}, {"item": "bad"}, ["17"], {"item": 17}, "int"),
            "repeated": (source('<xs:sequence><xs:element name="item" type="xs:int" minOccurs="2"'
                                ' maxOccurs="3"/></xs:sequence>'),
                         {"item": [1, 2]}, {"item": [1]}, ["1", "2"], {"item": [1, 2]}, "int"),
            "restriction": (source('<xs:sequence><xs:element name="item" type="t:Small"/></xs:sequence>',
                '<xs:simpleType name="Small"><xs:restriction base="xs:int"><xs:maxInclusive value="9"/>'
                '</xs:restriction></xs:simpleType>'), {"item": 7}, {"item": 10}, ["7"], {"item": 7}, "Small"),
            "list": (source('<xs:sequence><xs:element name="item" type="t:Items"/></xs:sequence>',
                '<xs:simpleType name="Items"><xs:list itemType="xs:int"/></xs:simpleType>'),
                {"item": [1, 2]}, {"item": [1, "bad"]}, ["1 2"], {"item": [1, 2]}, "Items"),
            "union": (source('<xs:sequence><xs:element name="item" type="t:Either"/></xs:sequence>',
                '<xs:simpleType name="Either"><xs:union memberTypes="xs:int xs:boolean"/></xs:simpleType>'),
                {"item": False}, {"item": "bad"}, ["false"], {"item": False}, "Either"),
            "qname": (source('<xs:sequence><xs:element name="item" type="xs:QName"/></xs:sequence>'),
                {"item": "unused"}, None, ["xsd:Token"], {"item": {"uri": "urn:data", "local": "Token"}}, "QName"),
            "simple-content": (source('<xs:simpleContent><xs:extension base="xs:int">'
                '<xs:attribute name="unit" use="required"/></xs:extension></xs:simpleContent>'),
                {"^value^": 7, "^attributes^": {"unit": "kg"}}, {"^value^": 7},
                ["7"], {"^value^": 7, "^attributes^": {"unit": "kg"}}, None),
            "derived": (source('<xs:sequence><xs:element name="item" type="xs:int"/></xs:sequence>',
                '<xs:complexType name="Derived"><xs:complexContent><xs:extension base="t:Record">'
                '<xs:attribute name="unit" use="required"/></xs:extension></xs:complexContent></xs:complexType>'),
                {"item": 7, "^attributes^": {"unit": "kg"}}, {"item": 7},
                ["7"], {"item": 7, "^attributes^": {"unit": "kg"}}, "int"),
        }
        for name, prefix in (("derived-qname", "ns"), ("derived-qname-xsi", "xsi")):
            models[name] = (source('<xs:simpleContent><xs:extension base="xs:QName"/></xs:simpleContent>',
                '<xs:complexType name="Derived"><xs:simpleContent><xs:extension base="t:Record">'
                '<xs:attribute name="unit" use="required"/></xs:extension></xs:simpleContent></xs:complexType>'),
                {"^value^": "unused", "^attributes^": {"unit": "kg"}}, {"^value^": "unused"},
                [prefix + ":Token"], {"^value^": {"uri": "urn:data", "local": "Token"},
                                     "^attributes^": {"unit": "kg"}}, None)
        cases = []
        expected_ids = []
        compilers = {name: etree.XMLSchema(etree.fromstring(model[0].encode())) for name, model in models.items()}
        for name, (schema, value, invalid, _, _, _) in models.items():
            for version in ("11", "12"):
                trials = [{"name": "valid", "value": value}]
                if invalid is not None:
                    trials += [{"name": "invalid", "value": invalid}, {"name": "reuse", "value": value}]
                case = {"name": name + "/" + version, "wsdl": description(version, schema),
                        "binding": "Soap" + version, "trials": trials, "qname": "qname" in name,
                        "wrap_children": name != "simple-content" and not name.startswith("derived")}
                if name.startswith("derived"):
                    case["selected"] = "Derived"
                if name.startswith("derived-qname"):
                    case.update(qname_field="^value^", qname_prefix="xsi" if name.endswith("-xsi") else "ns")
                cases.append(case)
                expected_ids += [(case["name"], copy, response, trial["name"])
                                 for copy in (False, True) for response in (False, True) for trial in trials]
        mode = os.environ.get("QORE_EXEC_MODE", "jit")
        self.assertIn(mode, ("ast", "ir", "jit", "tiered"))
        with tempfile.TemporaryDirectory(prefix="wsdl-type-identity-") as temporary:
            path = Path(temporary) / "cases.json"
            path.write_text(json.dumps(cases), encoding="utf-8")
            process = subprocess.run(["qore", "-b", "--enable-debug", "--exec-mode=" + mode,
                str(Path(__file__).with_name("type-identity.qr")), str(path)],
                text=True, capture_output=True, timeout=180)
        self.assertEqual(0, process.returncode, process.stderr + process.stdout[-3000:])
        self.assertEqual("", process.stderr)
        rows = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(expected_ids, [(r["case"], r["copy"], r["response"], r["trial"]) for r in rows])
        documents = {name: {} for name in models}
        rejected = 0
        for index, row in enumerate(rows):
            invalid = row["trial"] == "invalid"
            self.assertEqual("SOAP-SERIALIZATION-ERROR" if invalid else "", row["error"], row)
            if invalid:
                self.assertNotIn("xml", row)
                rejected += 1
                continue
            name, version = row["case"].split("/")
            _, _, _, text, native, item_type = models[name]
            envelope = etree.fromstring(row["xml"].encode())
            self.assertEqual("{" + survey.SOAP_NAMESPACES[int(version == "12")] + "}Envelope", envelope.tag)
            payload = envelope.find("{*}Body")[0]
            self.assertEqual(native, row["native"], row)
            outputs = {"soap": payload, "detached": etree.fromstring(row["detached"].encode())}
            if "qname" not in name:
                outputs["annotated"] = etree.fromstring(row["annotated"].encode())
            for label, output in outputs.items():
                self.assertEqual(f"{{{NS}}}" + ("Reply" if row["response"] else "Submit"), output.tag)
                values = [output] if name == "simple-content" or name.startswith("derived-qname") else list(output)
                self.assertEqual(len(text), len(values), row)
                if "qname" in name:
                    self.assertEqual(("urn:data", "Token"), expanded_qname(values[0], values[0].text or ""))
                else:
                    self.assertEqual(text, [node.text or "" for node in values], row)
                if name == "simple-content" or name.startswith("derived"):
                    self.assertEqual("kg", output.get("unit"))
                if label == "annotated" or name.startswith("derived"):
                    self.assertEqual((NS, "Derived" if name.startswith("derived") else "Record"), expanded_type(output))
                else:
                    self.assertIsNone(expanded_type(output))
                if label == "annotated" and item_type:
                    for node in output:
                        self.assertEqual((NS if item_type in ("Small", "Items", "Either") else XSD, item_type),
                                         expanded_type(node))
                self.assertTrue(compilers[name].validate(output), str(compilers[name].error_log))
                documents[name][f"{index}/{label}"] = etree.tostring(output)
        jobs = [SchemaJob(name, f"http://example.invalid/{name}.xsd", models[name][0].encode(), outputs)
                for name, outputs in documents.items()]
        oracle = run_independent(jobs)
        for name, result in {**oracle["schemas"], **oracle["documents"]}.items():
            self.assertTrue(result["ok"], (name, result))
            self.assertEqual([], result["warnings"])
        self.assertEqual(224, len(rows))
        self.assertEqual(72, rejected)
        self.assertEqual(416, len(oracle["documents"]))
        print(f"{mode}: {len(rows)} rows; {rejected} required serialization errors; "
              f"{len(oracle['documents'])} independently validated outputs", flush=True)


if __name__ == "__main__":
    unittest.main()
