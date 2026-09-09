#!/usr/bin/env python3
"""Selected ENTITY instance constraints through real WSDL SOAP bindings.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as run_independent
from test_attribute_values import NS, XSD, description

HERE = Path(__file__).resolve().parent
DEFINITIONS = '''<xs:simpleType name="Photo"><xs:restriction base="xs:ENTITY">
  <xs:enumeration value="photo"/></xs:restriction></xs:simpleType>
<xs:simpleType name="EntityText"><xs:union memberTypes="xs:ENTITY xs:string"/></xs:simpleType>
<xs:simpleType name="TextEntity"><xs:union memberTypes="xs:string xs:ENTITY"/></xs:simpleType>
<xs:simpleType name="PhotoText"><xs:union memberTypes="t:Photo xs:string"/></xs:simpleType>
<xs:simpleType name="EntityInt"><xs:union memberTypes="xs:ENTITY xs:int"/></xs:simpleType>
<xs:simpleType name="Items"><xs:list itemType="xs:ENTITY"/></xs:simpleType>
<xs:simpleType name="MixedItems"><xs:list itemType="t:EntityInt"/></xs:simpleType>
<xs:simpleType name="Restricted"><xs:restriction base="t:MixedItems"><xs:maxLength value="2"/>
  </xs:restriction></xs:simpleType>
<xs:simpleType name="ListText"><xs:union memberTypes="t:Restricted xs:string"/></xs:simpleType>
<xs:simpleType name="Enumerated"><xs:restriction base="t:EntityText">
  <xs:enumeration value="photo"/></xs:restriction></xs:simpleType>'''
VALUES = ("photo", "17", "", "other", "photo 17", "17 18", "17 18 19", "!", "  photo  ")
# Expected instance validity, independent of conversion/provider acceptance.
VALID = {
    "xs:ENTITY": (), "xs:ENTITIES": (), "t:Photo": (), "t:Enumerated": (),
    "t:EntityText": (1, 2, 4, 5, 6, 7), "t:TextEntity": tuple(range(len(VALUES))),
    "t:PhotoText": (1, 2, 3, 4, 5, 6, 7), "t:EntityInt": (1,), "t:Items": (2,),
    "t:MixedItems": (1, 2, 5, 6), "t:Restricted": (1, 2, 5),
    "t:ListText": (1, 2, 5, 6, 7),
}
LISTS = {"t:Items", "t:MixedItems", "t:Restricted"}
SOAP = {"11": "http://schemas.xmlsoap.org/soap/envelope/", "12": "http://www.w3.org/2003/05/soap-envelope"}


def schema(datatype, model):
    content = DEFINITIONS
    root_type = datatype
    if model == "record":
        root_type = "t:Record"
        content += f'''<xs:complexType name="Record"><xs:simpleContent><xs:extension base="{datatype}">
          <xs:attribute name="choice" type="{datatype}" use="required"/>
          </xs:extension></xs:simpleContent></xs:complexType>'''
    elif model == "repeated":
        root_type = "t:Record"
        content += f'''<xs:complexType name="Record"><xs:sequence><xs:element name="item" type="{datatype}"
          maxOccurs="3"/></xs:sequence></xs:complexType>'''
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">{content}
      <xs:element name="Submit" type="{root_type}"/><xs:element name="Reply" type="{root_type}"/></xs:schema>'''


def payload(model, text, response):
    root = etree.Element(f"{{{NS}}}" + ("Reply" if response else "Submit"), nsmap={"t": NS})
    if model == "repeated":
        for _ in range(2):
            etree.SubElement(root, "item").text = text
    else:
        root.text = text
        if model == "record":
            root.set("choice", text)
    return root


def envelope(root, version):
    result = etree.Element(f"{{{SOAP[version]}}}Envelope", nsmap={"s": SOAP[version]})
    etree.SubElement(result, f"{{{SOAP[version]}}}Body").append(root)
    return etree.tostring(result).decode()


def run_worker(worker, manifest, root):
    path = root / (worker + ".json")
    path.write_text(json.dumps(manifest))
    result = subprocess.run(["qore", "-b", "--enable-debug", str(HERE / (worker + ".qr")), str(path)],
                            text=True, capture_output=True, timeout=300)
    if result.returncode or result.stderr:
        raise AssertionError((result.returncode, result.stderr))
    rows = [json.loads(line) for line in result.stdout.splitlines()]
    if os.environ.get("WSDL_ENTITY_ARTIFACT_DIR"):
        archive = Path(os.environ["WSDL_ENTITY_ARTIFACT_DIR"])
        archive.mkdir(parents=True, exist_ok=True)
        if isinstance(manifest, list):
            for item in manifest:
                source = Path(item["wsdl"])
                (archive / source.name).write_bytes(source.read_bytes())
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        (archive / (worker + "-" + digest + "-manifest.json")).write_bytes(path.read_bytes())
        (archive / (worker + "-" + digest + "-rows.json")).write_text(json.dumps(rows, indent=2))
    return rows


class EntityWsdlTest(unittest.TestCase):
    def check_oracle(self, jobs, expected):
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle["schemas"]))
        self.assertEqual(set(expected), set(oracle["documents"]))
        for name, result in oracle["schemas"].items():
            self.assertTrue(result["ok"], (name, result))
            self.assertEqual([], result["warnings"])
        for name, valid in expected.items():
            self.assertEqual(valid, oracle["documents"][name]["ok"], (name, oracle["documents"][name]))
            self.assertEqual([], oracle["documents"][name]["warnings"])

    def test_outbound_values_and_generated_examples(self):
        jobs, expected = {}, {}
        outcomes = 0
        with tempfile.TemporaryDirectory(prefix="wsdl-entity-outbound-") as temporary:
            root = Path(temporary)
            for model in ("scalar", "record", "repeated"):
                manifest = []
                for datatype in VALID:
                    key = datatype.replace(":", "-") + "-" + model
                    source = schema(datatype, model)
                    jobs[key] = SchemaJob(key, "urn:qore:entity:" + key, source.encode())
                    for version in SOAP:
                        path = root / (key + "-" + version + ".wsdl")
                        path.write_text(description(version, source))
                        manifest.append({"name": key + "-" + version, "wsdl": str(path), "binding": "Soap" + version,
                            "model": model, "message_provider": True,
                            "values": [{"value": text.split() if datatype in LISTS else text, "count": 2}
                                       for text in VALUES]})
                rows = run_worker("sized-facet-consumers", manifest, root)
                self.assertEqual(len(VALID) * 2 * 2 * 2 * (len(VALUES) + 1), len(rows))
                outcomes += len(rows)
                expected_rows = {(item["name"], copy, direction, index) for item in manifest
                                 for copy in (0, 1) for direction in ("request", "response")
                                 for index in (*range(len(VALUES)), "example")}
                seen = set()
                for row in rows:
                    identity = (row["name"], row["copy"], row["direction"], row["index"])
                    self.assertNotIn(identity, seen)
                    seen.add(identity)
                    key, version = row["name"].rsplit("-", 1)
                    datatype = key.rsplit("-", 1)[0].replace("-", ":", 1)
                    valid = row["index"] in VALID[datatype]
                    with self.subTest(row=row):
                        if "err" in row:
                            self.assertIn(row["err"], {"SOAP-SERIALIZATION-ERROR", "RUNTIME-TYPE-ERROR",
                                                      "FIELD-VALUE-ERROR", "XSD-SAMPLE-ERROR"})
                            if row["index"] != "example":
                                self.assertFalse(valid)
                            else:
                                self.assertNotEqual("t:TextEntity", datatype)
                                self.assertIn(row["err"], {"SOAP-SERIALIZATION-ERROR", "XSD-SAMPLE-ERROR"})
                            continue
                        if row["index"] != "example":
                            self.assertTrue(valid)
                        content = self.check_output(row["body"], row["direction"] == "response", version,
                                                    jobs[key], expected, f"output/{outcomes}/{len(expected)}")
                        if row["index"] != "example":
                            text = VALUES[row["index"]]
                            if datatype in LISTS:
                                text = " ".join(text.split())
                            self.check_value(content, model, text)
                self.assertEqual(expected_rows, seen)
        self.assertEqual(2880, outcomes)
        self.check_oracle(jobs, expected)
        print(f"outbound: {outcomes} outcomes, {len(expected)} independently valid documents", flush=True)

    def check_output(self, xml, response, version, job, expected, name):
        root = etree.fromstring(xml.encode())
        self.assertEqual(f"{{{SOAP[version]}}}Envelope", root.tag)
        content = root.find("{*}Body")[0]
        self.assertEqual(f"{{{NS}}}" + ("Reply" if response else "Submit"), content.tag)
        job.documents[name] = etree.tostring(content)
        expected[name] = True
        return content

    def check_value(self, content, model, text):
        fields = list(content) if model == "repeated" else [content]
        self.assertEqual(2 if model == "repeated" else 1, len(fields))
        for field in fields:
            self.assertEqual(text, field.text or "")
            if model == "record":
                self.assertEqual(text, field.get("choice"))

    def test_inbound_selection_reconstruction_and_retained_values(self):
        jobs, expected = {}, {}
        outcomes = 0
        with tempfile.TemporaryDirectory(prefix="wsdl-entity-inbound-") as temporary:
            root = Path(temporary)
            for model in ("scalar", "record", "repeated"):
                cases, inputs = [], {}
                for datatype in VALID:
                    key = datatype.replace(":", "-") + "-" + model
                    source = schema(datatype, model)
                    jobs[key] = SchemaJob(key, "urn:qore:entity:" + key, source.encode())
                    for version in SOAP:
                        case = {"name": key + "-" + version, "wsdl": description(version, source),
                                "binding": "Soap" + version, "inputs": []}
                        cases.append(case)
                        for response in (False, True):
                            for index, text in enumerate(VALUES):
                                name = f"{case['name']}/{response}/{index}"
                                content = payload(model, text, response)
                                raw = etree.tostring(content)
                                jobs[key].documents[name] = raw
                                expected[name] = index in VALID[datatype]
                                inputs[name] = (key, version, response, text, index in VALID[datatype], raw.decode())
                                case["inputs"].append({"name": name, "response": response,
                                                      "xml": envelope(content, version), "payload": raw.decode()})
                rows = run_worker("qname-context", {"cases": cases}, root)
                outcomes += len(rows)
                seen = set()
                for row in rows:
                    identity = (row["name"], row["copy"], row["stage"])
                    self.assertNotIn(identity, seen)
                    seen.add(identity)
                    if row["stage"].startswith("sample-"):
                        key_version, direction = row["name"].split("-sample-")
                        key, version = key_version.rsplit("-", 1)
                        if "err" in row:
                            self.assertNotEqual("t-TextEntity-" + model, key)
                            self.assertIn(row["err"], {"SOAP-SERIALIZATION-ERROR", "XSD-SAMPLE-ERROR"}, row)
                        else:
                            self.check_output(row["xml"], direction == "response", version, jobs[key], expected,
                                              "/".join(map(str, identity)))
                        continue
                    key, version, response, text, valid, original = inputs[row["name"]]
                    with self.subTest(identity=identity):
                        if not valid:
                            self.assertEqual("decode", row["stage"])
                            self.assertEqual("SOAP-DESERIALIZATION-ERROR", row.get("err"), row)
                        else:
                            self.assertNotIn("err", row)
                            if row["stage"] != "decode":
                                content = self.check_output(row["xml"], response, version, jobs[key], expected,
                                                            "/".join(map(str, identity)))
                                self.check_value(content, model, text)
                                if row["stage"].startswith("retained"):
                                    self.assertEqual(original, row["source_xml"])
                expected_samples = {(case["name"] + "-sample-" + direction, copy, "sample-" + kind)
                                    for case in cases for direction in ("request", "response")
                                    for copy in (0, 1) for kind in ("native", "xml")}
                self.assertEqual(expected_samples, {item for item in seen if item[2].startswith("sample-")})
                for name, info in inputs.items():
                    for copy in (0, 1):
                        stages = ("decode", "native", "element", "element-restored", "message",
                                  "message-restored", "retained", "retained-restored") if info[4] else ("decode",)
                        self.assertEqual(set(stages), {stage for found, c, stage in seen if found == name and c == copy})
        self.assertEqual(9216, outcomes)
        self.check_oracle(jobs, expected)
        print(f"inbound: {outcomes} outcomes, {len(expected)} independent document verdicts, "
              f"{sum(expected.values())} valid and {len(expected) - sum(expected.values())} invalid", flush=True)


if __name__ == "__main__":
    unittest.main()
