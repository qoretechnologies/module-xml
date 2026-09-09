#!/usr/bin/env python3
"""QName lexical grammar, patterns and examples at real SOAP binding boundaries.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as run_independent
from test_facet_declarations import facet
from test_attribute_values import description, NS, XSD
import test_builtin_list_values as atomic
import test_list_values as lists
import survey


def definitions():
    yield lists.ListCase("qname-grammar", "QName", "", (
        ("Name", True), (" xml:lang\t", True), ("_0", True), ("é", True), ("Αλφα", True),
        ("中文", True), ("a\u0301", True), ("a\u00b7b", True), ("xml:中文", True),
        ("", False), (" \t\r\n", False), (":", False), (":Name", False), ("xml:", False),
        ("a:b:c", False), ("0name", False), ("xml:0name", False), ("a b", False),
        ("xml :Name", False), ("xml: Name", False), ("a\u00a0b", False),
        ("\u0301a", False), ("xml:\u0301a", False), ("\u0370", False),
        ("xml:\u0370", False), ("\U00010000", False), ("xml:\U00010000", False), ("a/b", False)))
    yield lists.ListCase("qname-pattern", "QName", facet("pattern", "xml:[a-z]+"),
        ((" xml:lang\n", True), ("xml:space", True), ("xml:0bad", False), ("Name", False)))
    yield lists.ListCase("qname-inherited", "QName", facet("pattern", "Name"),
        ((" Name ", True), ("Other", False), ("name", False), ("NAME", False)),
        parent=facet("pattern", "[A-Z][a-z]+"))
    yield lists.ListCase("qname-impossible-pattern", "QName", facet("pattern", "[0-9]+"),
        (("123", False), ("Name", False), ("xml:lang", False)), example=False)
    for kind, count in (("length", 0), ("maxLength", 0), ("minLength", 1000)):
        yield lists.ListCase("qname-ignored-" + kind, "QName", facet(kind, count),
            (("Name", True), ("xml:lang", True), ("", False), ("a:b:c", False)))


class QNameLexicalBindingsTest(lists.ListValuesTest):
    case_definitions = staticmethod(definitions)
    case_schema = staticmethod(atomic.schema)

    @staticmethod
    def parse_value(base, text):
        normalized = " ".join(lists.tokens(text))
        # These binding fixtures use no default namespace and only the implicit xml prefix.
        # Assert namespace/local identity independently; arbitrary prefix remapping is tracked separately.
        if normalized.startswith("xml:"):
            return ("http://www.w3.org/XML/1998/namespace", normalized[4:])
        return ("", normalized)

    @staticmethod
    def provider_value(case, lexical):
        return lexical

    def check_output(self, body, case, model, version, direction, lexical=None, count=2):
        element = super().check_output(body, case, model, version, direction, lexical, count)
        if lexical is not None:
            expected = self.parse_value(case.base, lexical)
            parts = list(element) if model == "repeated" else [element]
            for part in parts:
                texts = [part.text or ""]
                if model == "record":
                    texts.append(part.get("choice"))
                for text in texts:
                    normalized = " ".join(lists.tokens(text))
                    if ":" in normalized:
                        prefix, local = normalized.split(":")
                        uri = "http://www.w3.org/XML/1998/namespace" if prefix == "xml" else part.nsmap[prefix]
                    else:
                        uri, local = part.nsmap.get(None, ""), normalized
                    self.assertEqual(expected, (uri, local))
        return element


class QNameCharacterBoundariesTest(unittest.TestCase):
    def test_enumeration_declaration_grammar_without_string_alias_comparison(self):
        definitions = [("invalid-" + str(index), facet("enumeration", value), "", False)
                       for index, value in enumerate(("", ":Name", "a:b:c", "0name", "xml:"))]
        definitions += [("local", facet("enumeration", "Name"), "", True),
            ("equivalent-alias", facet("enumeration", "b:Name", ' xmlns:b="urn:alias"'),
                facet("enumeration", "a:Name", ' xmlns:a="urn:alias"'), True)]
        jobs, cases, expected = [], [], {}
        with tempfile.TemporaryDirectory(prefix="wsdl-qname-declarations-") as temporary:
            for name, own, parent, valid in definitions:
                source = f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">
                    <xs:simpleType name="Base"><xs:restriction base="xs:QName">{parent}</xs:restriction></xs:simpleType>
                    <xs:simpleType name="Value"><xs:restriction base="t:Base">{own}</xs:restriction></xs:simpleType>
                    <xs:element name="Submit" type="t:Value"/><xs:element name="Reply" type="t:Value"/>
                    </xs:schema>'''
                jobs.append(SchemaJob(name, f"http://example.invalid/{name}.xsd", source.encode()))
                expected[name] = valid
                try:
                    etree.XMLSchema(etree.fromstring(source.encode()))
                    accepted = True
                except etree.XMLSchemaParseError:
                    accepted = False
                self.assertEqual(valid, accepted, name)
                for version in ("11", "12"):
                    path = Path(temporary) / f"{name}-{version}.wsdl"
                    path.write_text(description(version, source))
                    cases.append({"name": name + "/" + version, "wsdl": str(path),
                        "base": "http://example.invalid/", "operation": "submit", "binding": "Soap" + version,
                        "messages": []})
            rows = survey.run_worker(cases, {})
        self.assertEqual(14, len(rows))
        self.assertEqual({case["name"] for case in cases}, {row["case"] for row in rows})
        for row in rows:
            valid = expected[row["case"].split("/")[0]]
            self.assertEqual("parse", row["stage"])
            self.assertEqual(valid, row["ok"], row)
            if not valid:
                self.assertEqual("XSD-SIMPLETYPE-ERROR", row["err"])
        oracle = run_independent(jobs)
        self.assertEqual(set(expected), set(oracle["schemas"]))
        for name, valid in expected.items():
            self.assertEqual(valid, oracle["schemas"][name]["ok"], oracle["schemas"][name])
            self.assertEqual([], oracle["schemas"][name]["warnings"])

    def test_second_edition_qname_local_character_boundaries(self):
        ranges = json.loads(Path(__file__).with_name("xml10-second-name-ranges.json").read_text())["ranges"]
        points = sorted({point for parts in ranges.values() for low, high in parts
                         for point in (low - 1, low, high, high + 1) if point > 32})
        self.assertEqual(1009, len(points))

        def member(point, groups):
            return any(low <= point <= high for group in groups for low, high in ranges[group])

        source = b'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:element name="value" type="xs:QName"/></xs:schema>'
        job = SchemaJob("QName", "http://example.invalid/QName.xsd", source)
        rows = []
        for point in points:
            start = point == 95 or member(point, ("BaseChar", "Ideographic"))
            continuation = start or point in (45, 46) or member(point, ("Digit", "CombiningChar", "Extender"))
            for prefix in ("", "A", "xml:", "xml:A"):
                name = f"QName/{point}/{prefix}"
                text = prefix + chr(point)
                valid = continuation if prefix.endswith("A") else start
                rows.append({"name": name, "builtin": "QName", "value": text, "expected": valid})
                element = etree.Element("value")
                element.text = text
                job.documents[name] = etree.tostring(element)
        with tempfile.TemporaryDirectory(prefix="wsdl-qname-boundaries-") as temporary:
            manifest = Path(temporary) / "manifest.json"
            manifest.write_text(json.dumps(rows))
            process = subprocess.run(["qore", "-b", "--enable-debug",
                str(Path(__file__).with_name("name-value-boundaries.qr")), str(manifest)],
                text=True, capture_output=True, timeout=60)
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual("", process.stderr)
        observed = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(4036, len(observed))
        self.assertEqual([row["name"] for row in rows], [row["name"] for row in observed])
        oracle = run_independent([job])
        self.assertEqual({"QName"}, set(oracle["schemas"]))
        self.assertTrue(oracle["schemas"]["QName"]["ok"])
        self.assertEqual([], oracle["schemas"]["QName"]["warnings"])
        self.assertEqual({row["name"] for row in rows}, set(oracle["documents"]))
        validator = etree.XMLSchema(etree.fromstring(source))
        for row, result in zip(rows, observed):
            with self.subTest(character=row["name"]):
                self.assertEqual(row["expected"], oracle["documents"][row["name"]]["ok"])
                self.assertEqual([], oracle["documents"][row["name"]]["warnings"])
                self.assertEqual(row["expected"], validator.validate(etree.fromstring(job.documents[row["name"]])))
                for operation, error in (("serialize", "SOAP-SERIALIZATION-ERROR"),
                        ("deserialize", "SOAP-DESERIALIZATION-ERROR"), ("provider", "RUNTIME-TYPE-ERROR")):
                    if row["expected"]:
                        self.assertNotIn(operation + "_error", result)
                        self.assertEqual(row["value"], result[operation])
                    else:
                        self.assertNotIn(operation, result)
                        self.assertEqual(error, result[operation + "_error"])


if __name__ == "__main__":
    unittest.main()
