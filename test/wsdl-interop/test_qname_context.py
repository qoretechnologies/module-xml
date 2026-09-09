#!/usr/bin/env python3
"""QName instance scopes, typed providers and both SOAP bindings against two validators.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS, XSD


ROOT = Path(__file__).resolve().parent
SOAP = {"11": "http://schemas.xmlsoap.org/soap/envelope/", "12": "http://www.w3.org/2003/05/soap-envelope"}
XML = "http://www.w3.org/XML/1998/namespace"
CONSUMERS = ("native", "element", "element-restored", "message", "message-restored", "retained", "retained-restored")


def wsdl_description(version, source):
    document = description(version, source)
    # Description defaults must never become instance QName bindings.
    return document.replace('<w:definitions ', '<w:definitions xmlns="urn:wsdl-default" ', 1) if version == "12" else document


def qname(uri, local):
    return {"kind": "qname", "uri": uri, "local": local}


def string_value(text, scoped=False):
    return {"kind": "string", "text": text, "scoped": scoped}


def scoped_schema(kind):
    value_type = {"atomic": "xs:QName", "union": "t:Value", "list": "t:Names", "list-union": "t:Items", "list-union-restriction": "t:Collection",
                  "list-qname-union-restriction": "t:QNameCollection"}[kind]
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}" elementFormDefault="qualified">
      <xs:simpleType name="Either"><xs:union memberTypes="xs:QName xs:string"/></xs:simpleType>
      <xs:simpleType name="Value"><xs:restriction base="t:Either"><xs:pattern value=".*"/></xs:restriction></xs:simpleType>
      <xs:simpleType name="Names"><xs:list itemType="xs:QName"/></xs:simpleType>
      <xs:simpleType name="Items"><xs:list itemType="t:Value"/></xs:simpleType>
      <xs:simpleType name="CollectionBase"><xs:union memberTypes="t:Items xs:int"/></xs:simpleType>
      <xs:simpleType name="Collection"><xs:restriction base="t:CollectionBase"><xs:pattern value=".*"/></xs:restriction></xs:simpleType>
      <xs:simpleType name="QNameCollectionBase"><xs:union memberTypes="t:Names xs:int"/></xs:simpleType>
      <xs:simpleType name="QNameCollection"><xs:restriction base="t:QNameCollectionBase"><xs:pattern value=".*"/></xs:restriction></xs:simpleType>
      <xs:complexType name="Record"><xs:sequence>
        <xs:element name="one" type="{value_type}"/><xs:element name="two" type="{value_type}"/>
        <xs:element name="three" type="{value_type}"/></xs:sequence>
        <xs:attribute name="category" type="{value_type}" use="required"/>
      </xs:complexType><xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/>
    </xs:schema>'''


def scoped_fixtures():
    schemas, cases, expected = {}, [], {}
    for kind in ("atomic", "union", "list", "list-union", "list-union-restriction", "list-qname-union-restriction"):
        schema = schemas[kind] = scoped_schema(kind)
        is_list = kind.startswith("list")
        for version, soap in SOAP.items():
            case = {"name": kind + "-" + version, "group": kind, "wsdl": wsdl_description(version, schema), "binding": "Soap" + version, "inputs": []}
            cases.append(case)
            for direction, root in (("request", "Submit"), ("response", "Reply")):
                for scope in ("Envelope", "Body", "Payload"):
                    for default in (False, True):
                        name = f"{kind}-{version}-{direction}-{scope}-{default}"
                        binding = {None: "urn:outer"} if default else {"ns": "urn:outer"}
                        envelope = etree.Element(f"{{{soap}}}Envelope", nsmap={"soap": soap, "t": NS,
                            **(binding if scope == "Envelope" else {})})
                        body = etree.SubElement(envelope, f"{{{soap}}}Body", nsmap=binding if scope == "Body" else {})
                        payload = etree.SubElement(body, f"{{{NS}}}{root}", nsmap=binding if scope == "Payload" else {})
                        def lexical(local):
                            return ("" if default else "ns:") + local
                        payload.set("category", lexical("Category") + (" " + lexical("Other") if is_list else ""))
                        members = {}
                        for local, uri in (("one", "urn:outer"), ("two", "urn:inner"),
                                           ("three", "" if default else "urn:outer")):
                            bindings = ({None: uri} if default else {"ns": uri}) if local == "two" else (
                                {None: ""} if local == "three" and default else {})
                            child = etree.SubElement(payload, f"{{{NS}}}{local}", nsmap=bindings)
                            child.text = lexical("Name") + (" " + lexical("Other") if is_list else "")
                            values = [qname(uri, "Name"), qname(uri, "Other")] if is_list else qname(uri, "Name")
                            members[local] = values
                        attributes = {"category": [qname("urn:outer", "Category"), qname("urn:outer", "Other")]
                                      if is_list else qname("urn:outer", "Category")}
                        metadata = {"group": kind, "valid": True, "root": root, "members": members,
                                    "attributes": attributes, "document": etree.tostring(payload).decode()}
                        case["inputs"].append({"name": name, "xml": etree.tostring(envelope).decode(),
                                               "response": direction == "response"})
                        expected[name] = metadata
                        if scope != "Payload" or default:
                            continue
                        for variant, text in (("unbound", "missing:Name"), ("malformed", "bad:name:again"), ("empty", "")):
                            changed = copy.deepcopy(envelope)
                            changed_payload = changed.find("{*}Body")[0]
                            changed_payload[0].text = text
                            changed_metadata = copy.deepcopy(metadata)
                            valid = kind in ("union", "list-union", "list-union-restriction") or (is_list and not text)
                            changed_metadata["valid"] = valid
                            scalar = string_value(text, variant == "unbound")
                            changed_metadata["members"]["one"] = ([] if not text else [scalar]) if is_list else scalar
                            changed_metadata["document"] = etree.tostring(changed_payload).decode()
                            changed_name = name + "-" + variant
                            expected[changed_name] = changed_metadata
                            case["inputs"].append({"name": changed_name, "xml": etree.tostring(changed).decode(),
                                                   "response": direction == "response"})
    return schemas, cases, expected


def fallback_schema(shape):
    member = {
        "scalar": '<xs:simpleType name="StringOnly"><xs:restriction base="t:Either"><xs:enumeration value="ns:Product"/></xs:restriction></xs:simpleType>',
        "list": '<xs:simpleType name="StringOnly"><xs:list itemType="t:StringItem"/></xs:simpleType>',
        "restricted-list": '<xs:simpleType name="StringOnly"><xs:restriction base="t:StringList"><xs:length value="1"/><xs:pattern value="ns:Product"/><xs:enumeration value="ns:Product"/></xs:restriction></xs:simpleType>',
        "union-list": '<xs:simpleType name="StringOnly"><xs:union memberTypes="t:StringList xs:int"/></xs:simpleType>',
        "nested-union": '<xs:simpleType name="StringOnly"><xs:union memberTypes="t:StringItem xs:int"/></xs:simpleType>',
    }[shape]
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" xmlns:c="urn:catalog" targetNamespace="{NS}" elementFormDefault="qualified">
      <xs:simpleType name="Either"><xs:union memberTypes="xs:QName xs:string"/></xs:simpleType>
      <xs:simpleType name="StringItem"><xs:restriction base="t:Either"><xs:enumeration value="ns:Product"/></xs:restriction></xs:simpleType>
      <xs:simpleType name="StringList"><xs:list itemType="t:StringItem"/></xs:simpleType>{member}
      <xs:simpleType name="QNameOnly"><xs:restriction base="t:Either"><xs:enumeration value="c:Product"/></xs:restriction></xs:simpleType>
      <xs:complexType name="Record"><xs:sequence><xs:element name="product" type="t:QNameOnly"/>
        <xs:element name="text" type="t:StringOnly"/></xs:sequence><xs:attribute name="category" type="t:StringOnly" use="required"/>
      </xs:complexType><xs:element name="Submit" type="t:Record"/><xs:element name="Reply" type="t:Record"/>
    </xs:schema>'''


def fallback_fixtures():
    schemas, cases, expected = {}, [], {}
    for shape in ("scalar", "list", "restricted-list", "union-list", "nested-union"):
        group = "fallback-" + shape
        source = schemas[group] = fallback_schema(shape)
        for version, soap in SOAP.items():
            case = {"name": group + "-" + version, "group": group, "wsdl": wsdl_description(version, source), "binding": "Soap" + version, "inputs": []}
            cases.append(case)
            for direction, root in (("request", "Submit"), ("response", "Reply")):
                for bound in (False, True):
                    for local_context in (False, True):
                        name = f"{group}-{version}-{direction}-{bound}-{local_context}"
                        nsmap = {"soap": soap, "t": NS, "a": "urn:catalog"}
                        if bound:
                            nsmap["ns"] = "urn:catalog"
                        envelope = etree.Element(f"{{{soap}}}Envelope", nsmap=nsmap)
                        body = etree.SubElement(envelope, f"{{{soap}}}Body")
                        payload = etree.SubElement(body, f"{{{NS}}}{root}")
                        payload.set("category", "ns:Product")
                        etree.SubElement(payload, f"{{{NS}}}product").text = "a:Product"
                        etree.SubElement(payload, f"{{{NS}}}text", nsmap={"unused": "urn:unused"}
                                         if local_context else {}).text = "ns:Product"
                        value = qname("urn:catalog", "Product") if bound else string_value("ns:Product", True)
                        if shape in ("list", "restricted-list", "union-list"):
                            value = [value]
                        expected[name] = {"group": group, "valid": not bound or shape == "nested-union", "root": root,
                            "members": {"product": qname("urn:catalog", "Product"), "text": value},
                            "attributes": {"category": value}, "document": etree.tostring(payload).decode()}
                        case["inputs"].append({"name": name, "xml": etree.tostring(envelope).decode(),
                                               "response": direction == "response"})
    return schemas, cases, expected


def sample_metadata(case, root):
    group = case["group"]
    if group.startswith("fallback-"):
        shape = group.removeprefix("fallback-")
        value = qname("", "abc") if shape == "nested-union" else string_value("ns:Product", True)
        if shape in ("list", "restricted-list", "union-list"):
            value = [value]
        members = {"product": qname("urn:catalog", "Product"), "text": value}
    else:
        value = [qname("", "abc")] if group.startswith("list") else qname("", "abc")
        members = dict.fromkeys(("one", "two", "three"), value)
    return {"group": group, "root": root, "members": members, "attributes": {"category": value},
            "valid": True, "sample": True}


class QNameContextTest(unittest.TestCase):
    def check_native(self, expected, value):
        if isinstance(expected, list):
            self.assertIsInstance(value, list)
            self.assertEqual(len(expected), len(value))
            for item, converted in zip(expected, value, strict=True):
                self.check_native(item, converted)
        elif expected["kind"] == "qname":
            if isinstance(value, str):
                uri, local = (XML, value[4:]) if value.startswith("xml:") else ("", value)
            else:
                self.assertEqual("qname", value["kind"])
                uri, local = value["uri"], value["local"]
            self.assertEqual((expected["uri"], expected["local"]), (uri, local))
        elif expected["scoped"]:
            self.assertEqual("scoped", value["kind"])
            self.assertEqual(expected["text"], value["lexical"])
            self.assertNotIn(expected["text"].split(":")[0], value["bindings"])
        else:
            self.assertEqual(expected["text"], value)

    def check_text(self, expected, text, node):
        if isinstance(expected, list):
            tokens = (text or "").split()
            self.assertEqual(len(expected), len(tokens))
            for item, token in zip(expected, tokens, strict=True):
                self.check_text(item, token, node)
        elif expected["kind"] == "qname":
            text = " ".join((text or "").split())
            prefix, local = text.split(":") if ":" in text else (None, text)
            uri = XML if prefix == "xml" else node.nsmap.get(prefix, "")
            self.assertEqual((expected["uri"], expected["local"]), (uri, local))
        else:
            self.assertEqual(expected["text"], text or "")
            if expected["scoped"]:
                self.assertNotIn(expected["text"].split(":")[0], node.nsmap)

    def matrix(self, fixture_factory, expected_inputs, expected_valid):
        schemas, cases, expected = fixture_factory()
        self.assertEqual(expected_inputs, len(expected))
        self.assertEqual(expected_valid, sum(row["valid"] for row in expected.values()))
        documents = {name: {"group": row["group"], "xml": row["document"], "valid": row["valid"]}
                     for name, row in expected.items()}
        for case in cases:
            for value in case["inputs"]:
                value["payload"] = expected[value["name"]]["document"]
        with tempfile.TemporaryDirectory(prefix="wsdl-qname-context-") as temporary:
            manifest = Path(temporary) / "bindings.json"
            manifest.write_text(json.dumps({"cases": cases}))
            process = subprocess.run(["qore", "-b", "--enable-debug", str(ROOT / "qname-context.qr"), str(manifest)],
                                     text=True, capture_output=True, timeout=300)
            self.assertEqual(0, process.returncode, process.stderr)
            self.assertEqual("", process.stderr)
            rows = [json.loads(line) for line in process.stdout.splitlines()]
            self.assertEqual(2 * expected_inputs + 2 * len(CONSUMERS) * expected_valid + 8 * len(cases), len(rows))
            for case in cases:
                for direction, root in (("request", "Submit"), ("response", "Reply")):
                    expected[case["name"] + "-sample-" + direction] = sample_metadata(case, root)
            seen = set()
            for row in rows:
                key = (row["name"], row["copy"], row["stage"])
                self.assertNotIn(key, seen)
                seen.add(key)
                metadata = expected[row["name"]]
                with self.subTest(key=key):
                    if not metadata["valid"]:
                        self.assertEqual("decode", row["stage"])
                        self.assertEqual("SOAP-DESERIALIZATION-ERROR", row.get("err"), row)
                        continue
                    self.assertNotIn("err", row, row)
                    self.assertIn(row["copy"], (0, 1))
                    self.assertIn(row["stage"], ("sample-native", "sample-xml") if metadata.get("sample")
                                  else ("decode", *CONSUMERS))
                    if row["stage"].startswith("retained"):
                        self.assertEqual(metadata["document"], row["source_xml"])
                    value = row["value"]
                    for member, wanted in metadata["members"].items():
                        self.check_native(wanted, value[member])
                    for attribute, wanted in metadata["attributes"].items():
                        self.check_native(wanted, value["^attributes^"][attribute])
                    if row["stage"] == "decode":
                        continue
                    envelope = etree.fromstring(row["xml"].encode())
                    payload = envelope.find("{*}Body")[0]
                    self.assertEqual(f"{{{NS}}}{metadata['root']}", payload.tag)
                    self.assertEqual([f"{{{NS}}}{name}" for name in metadata["members"]], [node.tag for node in payload])
                    for node, wanted in zip(payload, metadata["members"].values(), strict=True):
                        self.check_text(wanted, node.text, node)
                    for attribute, wanted in metadata["attributes"].items():
                        self.check_text(wanted, payload.get(attribute), payload)
                    name = "/".join(map(str, key))
                    documents[name] = {"group": metadata["group"], "xml": etree.tostring(payload).decode(), "valid": True}
            expected_keys = {(name, copied, stage) for name, row in expected.items() for copied in (0, 1)
                             for stage in (("sample-native", "sample-xml") if row.get("sample") else
                                           ("decode", *CONSUMERS) if row["valid"] else ("decode",))}
            self.assertEqual(expected_keys, seen)
            jobs = [SchemaJob(group, f"http://example.invalid/{group}.xsd", source.encode(),
                              {name: row["xml"].encode() for name, row in documents.items() if row["group"] == group})
                    for group, source in schemas.items()]
            oracle = run_independent(jobs)
            self.assertEqual(set(schemas), set(oracle["schemas"]))
            self.assertEqual(set(documents), set(oracle["documents"]))
            for name, row in oracle["schemas"].items():
                self.assertTrue(row["ok"], row)
                if name == "fallback-restricted-list":
                    # Xerces 2.12.2 XSDAbstractTraverser measures enumeration text
                    # as characters here, although XSD list length counts items.
                    # Retain and assert the exact diagnostic; document verdicts
                    # and all six native validation paths remain mandatory.
                    self.assertEqual(1, len(row["warnings"]), row)
                    self.assertRegex(row["warnings"][0],
                        r"FacetsContradict: For simpleType definition 'StringOnly', the enumeration value "
                        r"'ns:Product' contradicts with value of 'length' facet\.$")
                else:
                    self.assertEqual([], row["warnings"])
            for name, row in oracle["documents"].items():
                self.assertEqual(documents[name]["valid"], row["ok"], (name, row))
                self.assertEqual([], row["warnings"])
            native_manifest = Path(temporary) / "native.json"
            native_manifest.write_text(json.dumps({"rows": [{"name": name, "group": row["group"],
                "schema": schemas[row["group"]], "xml": row["xml"]} for name, row in documents.items()]}))
            directory = Path(str(native_manifest) + ".schemas")
            directory.mkdir()
            for group, source in schemas.items():
                (directory / (group + ".xsd")).write_text(source)
            native = subprocess.run(["qore", "-b", "--enable-debug", str(ROOT / "qname-union-validator.qr"),
                                     str(native_manifest)], text=True, capture_output=True, timeout=180)
            self.assertEqual(0, native.returncode, native.stderr)
            self.assertEqual("", native.stderr)
            verdicts = [json.loads(line) for line in native.stdout.splitlines()]
            self.assertEqual(list(documents), [row["name"] for row in verdicts])
            for row in verdicts:
                for path in ("parse", "reader", "cursor", "grouped", "attached-text", "attached-file"):
                    self.assertEqual(documents[row["name"]]["valid"], row[path], (row["name"], path, row))
                    if not row[path]:
                        self.assertEqual("PARSE-XML-EXCEPTION", row[path + "_error"])

    def test_scopes_values_and_detached_consumers(self):
        schemas, cases, expected = scoped_fixtures()
        self.assertEqual(216, len(expected))
        self.assertEqual(188, sum(row["valid"] for row in expected.values()))
        # Bound each worker by one schema shape, retaining both bindings and all
        # consumers/reused providers. Matrix growth must not multiply the work
        # assigned to a single fixed process deadline.
        valid_counts = {"atomic": 24, "union": 36, "list": 28, "list-union": 36,
                        "list-union-restriction": 36, "list-qname-union-restriction": 28}
        self.assertEqual(set(valid_counts), set(schemas))
        for group, valid in valid_counts.items():
            selected_cases = [case for case in cases if case["group"] == group]
            selected_expected = {name: row for name, row in expected.items() if row["group"] == group}
            with self.subTest(group=group):
                self.matrix(lambda: ({group: schemas[group]}, selected_cases, selected_expected), 36, valid)

    def test_ordered_union_enumeration_and_list_context(self):
        self.matrix(fallback_fixtures, 80, 48)


if __name__ == "__main__":
    unittest.main()
