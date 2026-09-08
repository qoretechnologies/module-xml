#!/usr/bin/env python3
"""Independent ordered list values, lexical patterns and provider reconstruction.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import json
import re
import subprocess
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS, XSD
from test_facet_declarations import facet
import survey


def tokens(text):
    return tuple(re.findall(r"[^ \t\r\n]+", text))


def value(base, text):
    parts = tokens(text)
    if base in {"integer", "decimal", "int"}:
        return tuple(Decimal(part) for part in parts)
    if base == "boolean":
        if any(part not in {"true", "false", "1", "0"} for part in parts):
            raise ValueError("invalid boolean token")
        return tuple(part in {"true", "1"} for part in parts)
    return parts


@dataclass(frozen=True)
class ListCase:
    name: str
    base: str
    facets: str
    values: tuple[tuple[str, bool], ...]
    parent: str = ""
    item_facets: str = ""
    example: bool = True


def definitions():
    yield ListCase("integer-enum", "integer", facet("enumeration", "01 +2"),
                   (("1 2", True), (" +001\t02 ", True), ("2 1", False), ("1 3", False), ("1", False)))
    yield ListCase("large-integer-enum", "integer", facet("enumeration", "18446744073709551616 -2"),
                   (("+018446744073709551616 -02", True), ("18446744073709551617 -2", False)))
    yield ListCase("decimal-enum", "decimal", facet("enumeration", "+0001.2300 -.000000000000000000001"),
                   (("1.23 -0.0000000000000000000010", True), ("1.23 -0.000000000000000000002", False)))
    yield ListCase("boolean-enum", "boolean", facet("enumeration", "1 0"),
                   (("true false", True), (" 1\r0 ", True), ("false true", False), ("yes no", False)))
    yield ListCase("empty-enum", "integer", facet("enumeration", ""), ((" \t\n", True), ("0", False)))
    yield ListCase("token-enum", "token", facet("enumeration", " A  B "),
                   (("A\tB", True), ("A\u00a0B", False), ("B A", False)))
    yield ListCase("string-nbsp", "string", facet("enumeration", "A\u00a0B C"),
                   (("A\u00a0B\tC", True), ("A B C", False)))
    yield ListCase("whole-pattern", "integer", facet("pattern", "00[0-9] 00[0-9]"),
                   (("001 002", True), ("000\t009", True), ("1 2", False)))
    yield ListCase("boolean-pattern", "boolean", facet("pattern", "1 0"),
                   (("1\t0", True), ("true false", False)))
    yield ListCase("enum-own-pattern", "integer", facet("enumeration", "01 +2") + facet("pattern", "001 002"),
                   (("001 002", True), ("01 +2", False), ("002 001", False)))
    yield ListCase("boolean-enum-own-pattern", "boolean",
                   facet("enumeration", "true false") + facet("pattern", "1 0"),
                   (("1 0", True), ("true false", False)))
    yield ListCase("pattern-alternatives", "integer", facet("pattern", "001 002") + facet("pattern", "003 004"),
                   (("001 002", True), ("003 004", True), ("005 006", False)))
    yield ListCase("inherited-enum", "integer", facet("length", 2),
                   (("01 02", True), ("2 1", False)), parent=facet("enumeration", "1 2"))
    yield ListCase("inherited-pattern", "boolean", facet("enumeration", "1 0"),
                   (("1 0", True), ("true false", False)), parent=facet("pattern", "1 0"))
    yield ListCase("restricted-items", "int", facet("pattern", "001 002"),
                   (("001 002", True), ("001 000", False), ("1 2", False)),
                   item_facets=facet("minInclusive", 1) + facet("maxInclusive", 9))
    yield ListCase("enum-length-warning", "integer", facet("enumeration", "1 2") + facet("length", 2),
                   (("01 +2", True), ("1", False), ("1 3", False)))
    yield ListCase("empty-intersection", "integer", facet("enumeration", "1 2") + facet("length", 1),
                   (("1 2", False), ("1", False)), example=False)
    yield ListCase("plain-list", "string", "", (("", True), ("A\u00a0B C", True), (" A\nB ", True)))


def schema(case, model):
    item = "xs:" + case.base
    declarations = ""
    if case.item_facets:
        item = "t:Item"
        declarations += f'<xs:simpleType name="Item"><xs:restriction base="xs:{case.base}">{case.item_facets}</xs:restriction></xs:simpleType>'
    declarations += f'<xs:simpleType name="List"><xs:list itemType="{item}"/></xs:simpleType>'
    declarations += f'<xs:simpleType name="Base"><xs:restriction base="t:List">{case.parent}</xs:restriction></xs:simpleType>'
    declarations += f'<xs:simpleType name="Value"><xs:restriction base="t:Base">{case.facets}</xs:restriction></xs:simpleType>'
    root_type = "t:Value"
    if model == "record":
        root_type = "t:Record"
        declarations += '''<xs:complexType name="Record"><xs:simpleContent><xs:extension base="t:Value">
            <xs:attribute name="choice" type="t:Value" use="required"/>
            </xs:extension></xs:simpleContent></xs:complexType>'''
    elif model == "repeated":
        root_type = "t:Record"
        declarations += '''<xs:complexType name="Record"><xs:sequence><xs:element name="item" type="t:Value"
            maxOccurs="3"/></xs:sequence></xs:complexType>'''
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">{declarations}
        <xs:element name="Submit" type="{root_type}"/><xs:element name="Reply" type="{root_type}"/></xs:schema>'''.encode()


def payload(model, local, lexical, count=2):
    element = etree.Element(f"{{{NS}}}{local}")
    if model == "repeated":
        for _ in range(count):
            etree.SubElement(element, "item").text = lexical
    else:
        element.text = lexical
        if model == "record":
            element.set("choice", lexical)
    return element


class ListValuesTest(unittest.TestCase):
    case_definitions = staticmethod(definitions)
    case_schema = staticmethod(schema)
    parse_value = staticmethod(value)

    @staticmethod
    def provider_value(case, lexical):
        return tokens(lexical)

    def check_output(self, body, case, model, version, direction, lexical=None, count=2):
        root = etree.fromstring(body.encode())
        self.assertEqual(f"{{{survey.SOAP_NAMESPACES[int(version == '12')]}}}Envelope", root.tag)
        element = root.find("{*}Body")[0]
        self.assertEqual(f"{{{NS}}}" + ("Submit" if direction == "request" else "Reply"), element.tag)
        if lexical is not None:
            parts = list(element) if model == "repeated" else [element]
            if model == "repeated":
                self.assertEqual(count, len(parts))
                self.assertTrue(all(part.tag == "item" for part in parts))
            for part in parts:
                self.assertEqual(self.parse_value(case.base, lexical), self.parse_value(case.base, part.text or ""))
            if model == "record":
                self.assertEqual(self.parse_value(case.base, lexical), self.parse_value(case.base, element.get("choice")))
        return element

    def check_oracles(self, jobs, expected):
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle["schemas"]))
        self.assertTrue(all(result["ok"] for result in oracle["schemas"].values()), oracle["schemas"])
        self.assertEqual(set(expected), set(oracle["documents"]))
        for key, job in jobs.items():
            warnings = oracle["schemas"][key]["warnings"]
            if key.split("/")[0] in {"empty-intersection", "enum-length-warning"}:
                self.assertEqual(1, len(warnings), (key, warnings))
                self.assertIn("FacetsContradict", warnings[0])
                self.assertIn("length", warnings[0])
            else:
                self.assertEqual([], warnings, key)
            try:
                validator = etree.XMLSchema(etree.fromstring(job.schema))
            except etree.XMLSchemaParseError as error:
                # libxml2 represents an empty list by a null value, which its enumeration compiler rejects.
                self.assertEqual("empty-enum", key.split("/")[0], (key, str(error)))
                self.assertIn("value was not computed", str(error))
                validator = None
            for name, document in job.documents.items():
                with self.subTest(oracle_document=name):
                    if validator is not None:
                        self.assertEqual(expected[name], validator.validate(etree.fromstring(document)), str(validator.error_log))
                    self.assertEqual(expected[name], oracle["documents"][name]["ok"], oracle["documents"][name])
                    self.assertEqual([], oracle["documents"][name]["warnings"], name)

    def test_binding_inputs_and_preserved_ordered_values(self):
        jobs, contracts, expected, lookup = {}, [], {}, {}
        with tempfile.TemporaryDirectory(prefix="wsdl-list-values-") as temporary:
            root = Path(temporary)
            for case in self.case_definitions():
                for model in ("atomic", "record", "repeated"):
                    key = case.name + "/" + model
                    source = self.case_schema(case, model)
                    jobs[key] = SchemaJob(key, f"http://example.invalid/{key}.xsd", source)
                    for version, namespace in zip(("11", "12"), survey.SOAP_NAMESPACES):
                        name = key + "/" + version
                        path = root / (name.replace("/", "-") + ".wsdl")
                        path.write_text(description(version, source.decode()))
                        messages = []
                        for index, (lexical, valid) in enumerate(case.values):
                            for direction, local in (("request", "Submit"), ("response", "Reply")):
                                identifier = name + f"/{index}/{direction}"
                                expected[identifier] = valid
                                lookup[identifier] = case, model, version, direction, lexical
                                element = payload(model, local, lexical)
                                jobs[key].documents[identifier] = etree.tostring(element)
                                envelope = etree.Element(f"{{{namespace}}}Envelope", nsmap={"s": namespace})
                                etree.SubElement(envelope, f"{{{namespace}}}Body").append(element)
                                message = root / identifier.replace("/", "-")
                                message.write_bytes(etree.tostring(envelope))
                                messages.append({"file": identifier, "path": str(message), "direction": direction})
                        contracts.append({"name": name, "wsdl": str(path), "base": "http://example.invalid/",
                                          "operation": "submit", "binding": "Soap" + version, "messages": messages})
            rows = survey.run_worker(contracts, {})
        accounting = survey.stage_accounting(contracts, rows)["counts"]
        self.assertEqual(len(contracts), accounting["parse"]["ok"],
                         [row for row in rows if row["stage"] == "parse" and not row["ok"]])
        for stages in accounting.values():
            self.assertEqual(0, stages["missing"])
            self.assertEqual(0, stages["skipped"])
        outputs = 0
        for row in rows:
            with self.subTest(row=row.get("file", row["case"]), stage=row["stage"]):
                if row["stage"] == "parse":
                    self.assertTrue(row["ok"], row)
                    continue
                if row["stage"] == "deserialize":
                    self.assertEqual(expected[row["file"]], row["ok"], row)
                    if not expected[row["file"]]:
                        self.assertEqual("SOAP-DESERIALIZATION-ERROR", row["err"], row)
                elif row["stage"] == "serialize":
                    self.assertTrue(row["ok"], row)
                    self.assertTrue(expected[row["file"]])
                    element = self.check_output(row["body"], *lookup[row["file"]])
                    identifier = row["file"] + "/output"
                    jobs[row["case"].rsplit("/", 1)[0]].documents[identifier] = etree.tostring(element)
                    expected[identifier] = True
                    outputs += 1
        self.assertEqual(sum(valid for name, valid in expected.items() if not name.endswith("/output")), outputs)
        self.check_oracles(jobs, expected)

    def test_detached_element_and_message_providers_and_examples(self):
        jobs, expected, manifest_rows, lookup = {}, {}, [], {}
        with tempfile.TemporaryDirectory(prefix="wsdl-list-consumers-") as temporary:
            root = Path(temporary)
            for case in self.case_definitions():
                for model in ("atomic", "record", "repeated"):
                    key = case.name + "/" + model
                    source = self.case_schema(case, model)
                    jobs[key] = SchemaJob(key, f"http://example.invalid/{key}.xsd", source)
                    variants = []
                    for lexical, valid in case.values:
                        for count in ((1, 2) if model == "repeated" else (1,)):
                            variants.append({"value": self.provider_value(case, lexical), "lexical": lexical, "expected": valid, "count": count})
                    # Native boundaries cannot encode a single empty/SPACE/TAB/LF/CR-containing item.
                    if case.name == "plain-list":
                        variants += [{"value": [item], "expected": False, "count": 1}
                                     for item in ("", "A B", "A\tB", "A\rB", "A\nB")]
                    for version in ("11", "12"):
                        path = root / (key.replace("/", "-") + version + ".wsdl")
                        path.write_text(description(version, source.decode()))
                        for scope in ("element", "message"):
                            name = key + f"/{version}/{scope}"
                            manifest_rows.append({"name": name, "wsdl": str(path), "binding": "Soap" + version,
                                                  "model": model, "message_provider": scope == "message", "values": variants})
                            lookup[name] = case, model, version, variants
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(manifest_rows))
            process = subprocess.run(["qore", "--enable-debug", str(Path(__file__).with_name("sized-facet-consumers.qr")),
                                      str(manifest)], text=True, capture_output=True, timeout=90)
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual("", process.stderr)
        rows = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(sum(4 * (len(entry[3]) + 1) for entry in lookup.values()), len(rows))
        seen = set()
        for row in rows:
            name = f"{row['name']}/{row['copy']}/{row['direction']}/{row['index']}"
            self.assertNotIn(name, seen)
            seen.add(name)
            self.assertIn(row["copy"], (0, 1))
            self.assertIn(row["direction"], ("request", "response"))
            case, model, version, variants = lookup[row["name"]]
            with self.subTest(consumer=name):
                if row["index"] == "example":
                    if not case.example:
                        self.assertEqual("XSD-SAMPLE-ERROR", row.get("err"), row)
                        continue
                    lexical, count = None, 0
                else:
                    variant = variants[row["index"]]
                    if not variant["expected"]:
                        self.assertEqual("RUNTIME-TYPE-ERROR", row.get("err"), row)
                        self.assertNotIn("body", row)
                        continue
                    lexical, count = variant["lexical"], variant["count"]
                self.assertNotIn("err", row)
                element = self.check_output(row["body"], case, model, version, row["direction"], lexical, count)
                key = case.name + "/" + model
                jobs[key].documents[name] = etree.tostring(element)
                expected[name] = True
        self.check_oracles(jobs, expected)


if __name__ == "__main__":
    unittest.main()
