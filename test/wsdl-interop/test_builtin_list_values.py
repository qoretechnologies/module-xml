#!/usr/bin/env python3
"""XSD name grammar and builtin list values at actual SOAP binding boundaries.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree
from independent import SchemaJob, run as run_independent

import test_list_values as lists
import test_union_value_identity as unions
from test_facet_declarations import facet


def definitions():
    yield lists.ListCase("builtin-enum", "NMTOKENS", facet("enumeration", " A  B "),
        (("A B", True), (" A\tB ", True), ("A\r\nB", True), ("B A", False), ("A C", False), ("", False)))
    yield lists.ListCase("builtin-pattern", "NMTOKENS", facet("pattern", "Αλφα 中文"),
        (("Αλφα 中文", True), (" Αλφα\t中文 ", True), ("Αλφα !", False), ("A B", False)))
    yield lists.ListCase("builtin-inherited", "NMTOKENS", facet("length", 2),
        (("A B", True), (" A\tB ", True), ("B A", False), ("A", False)),
        parent=facet("enumeration", " A B "))
    yield lists.ListCase("builtin-count", "NMTOKENS", facet("maxLength", 2),
        (("A", True), ("A B", True), ("A B C", False), ("", False), ("A !", False)))
    for base in ("Name", "NCName", "NMTOKEN", "NMTOKENS"):
        valid = ["Alpha", "_a", "Αλφα", "中文", "a\u0301", "a\u00b7b"]
        invalid = ["", "!", "a/b", "\u0370", "\U00010000", "a\u00a0b"]
        values = [(text, True) for text in valid] + [(text, False) for text in invalid]
        values += [("a:b", base != "NCName"), ("1-name", base in {"NMTOKEN", "NMTOKENS"}),
                   ("\u0301", base in {"NMTOKEN", "NMTOKENS"}), ("A B", base == "NMTOKENS")]
        yield lists.ListCase("name-" + base, base, "", tuple(values))
    for label, pattern, valid, invalid in (
        ("start", r"\i", ("Α", "中", ":", "_"), ("1", "\u0301", "\u0370", "\U00010000")),
        ("char", r"\c", ("Α", "中", ":", "1", "\u0301", "\u00b7"), ("!", "\u0370", "\U00010000")),
        ("name", r"\i\c*", ("Αλφα", "中文", "a\u0301", "a:b"), ("1-a", "a/b", "\u0370", "\U00010000")),
        ("class", r"[\i][\c]*", ("Αλφα", "中文", "a\u0301"), ("1-a", "a/b", "\u0370", "\U00010000")),
    ):
        yield lists.ListCase("regex-" + label, "string", facet("pattern", pattern),
                             tuple([(text, True) for text in valid] + [(text, False) for text in invalid]))


def schema(case, model):
    original = lists.schema(case, model).decode()
    declaration = f'<xs:simpleType name="List"><xs:list itemType="xs:{case.base}"/></xs:simpleType>'
    assert original.count(declaration) == 1
    return original.replace(declaration, f'<xs:simpleType name="List"><xs:restriction base="xs:{case.base}"/></xs:simpleType>').encode()


def value(base, text):
    return lists.tokens(text) if base == "NMTOKENS" else text if base == "string" else " ".join(lists.tokens(text))


class BuiltinListValuesTest(lists.ListValuesTest):
    case_definitions = staticmethod(definitions)
    case_schema = staticmethod(schema)
    parse_value = staticmethod(value)

    @staticmethod
    def provider_value(case, lexical):
        return lexical

    def check_oracles(self, jobs, expected):
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle["schemas"]))
        self.assertEqual(set(expected), set(oracle["documents"]))
        false_positives = set()
        for key, job in jobs.items():
            self.assertTrue(oracle["schemas"][key]["ok"], oracle["schemas"][key])
            self.assertEqual([], oracle["schemas"][key]["warnings"])
            validator = etree.XMLSchema(etree.fromstring(job.schema))
            for name, document in job.documents.items():
                with self.subTest(oracle_document=name):
                    self.assertEqual(expected[name], oracle["documents"][name]["ok"], oracle["documents"][name])
                    self.assertEqual([], oracle["documents"][name]["warnings"])
                    element = etree.fromstring(document)
                    valid = validator.validate(element)
                    if valid and not expected[name]:
                        # Source-adjudicated libxml2 omission of inherited builtin minLength=1.
                        # builtin-list-values-evidence.md retains the exact reproducer and source path.
                        self.assertIn(key.split("/")[0], {"builtin-count", "name-NMTOKENS"})
                        parts = list(element) or [element]
                        self.assertTrue(all(not lists.tokens(part.text or "") for part in parts))
                        self.assertTrue(all(not lists.tokens(part.get("choice", "")) for part in parts))
                        self.assertEqual(0, len(validator.error_log))
                        false_positives.add(name)
                    else:
                        self.assertEqual(expected[name], valid, str(validator.error_log))
        self.assertEqual(24 if any(not value for value in expected.values()) else 0, len(false_positives))


def union_definitions():
    yield unions.IdentityCase("builtin-union-enum", "builtin-list", "xs:NMTOKENS xs:string",
        (("A B", True), (" A\tB ", True), ("A\r\nB", True), ("B A", False), ("A C", False), ("", False)),
        facets=facet("enumeration", "A B"))
    yield unions.IdentityCase("builtin-single-list", "builtin-list", "xs:NMTOKENS xs:string",
        ((" A ", True), ("A", True), ("B", False), ("A B", False), ("!", False)),
        facets=facet("enumeration", "A"))
    yield unions.IdentityCase("builtin-union-plain", "builtin-list", "xs:NMTOKENS xs:string",
        ((" A\tB ", True), ("Αλφα 中文", True), ("A !", True), ("", True), ("\u0370", True), ("\U00010000", True)))


def union_value(base, text):
    parts = lists.tokens(text)
    # These authored alternatives are invalid NMTOKENs and select xs:string.
    return ("string", text) if not parts or any("!" in part or "\u0370" in part or "\U00010000" in part for part in parts) else ("list", parts)


class BuiltinListUnionValuesTest(lists.ListValuesTest):
    case_definitions = staticmethod(union_definitions)
    case_schema = staticmethod(unions.schema)
    parse_value = staticmethod(union_value)

    @staticmethod
    def provider_value(case, lexical):
        return lexical


class NameGrammarBoundariesTest(unittest.TestCase):
    def test_xml10_second_edition_character_boundaries(self):
        ranges = json.loads(Path(__file__).with_name("xml10-second-name-ranges.json").read_text())["ranges"]
        self.assertEqual(326, sum(len(parts) for parts in ranges.values()))
        points = sorted({point for parts in ranges.values() for low, high in parts
                         for point in (low - 1, low, high, high + 1) if point > 32})
        self.assertEqual(1009, len(points))

        def member(point, groups):
            return any(low <= point <= high for group in groups for low, high in ranges[group])

        rows, jobs = [], {}
        for builtin in ("Name", "NCName", "NMTOKEN"):
            source = ('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                      f'<xs:element name="value" type="xs:{builtin}"/></xs:schema>').encode()
            jobs[builtin] = SchemaJob(builtin, f"http://example.invalid/{builtin}.xsd", source)
            for point in points:
                start = point == 95 or member(point, ("BaseChar", "Ideographic"))
                continuation = start or point in (45, 46) or member(point, ("Digit", "CombiningChar", "Extender"))
                if builtin != "NCName":
                    start = start or point == 58
                    continuation = continuation or point == 58
                for prefix in ("", "A"):
                    name = f"{builtin}/{point}/{len(prefix)}"
                    text = prefix + chr(point)
                    valid = continuation if prefix or builtin == "NMTOKEN" else start
                    rows.append({"name": name, "builtin": builtin, "value": text, "expected": valid})
                    element = etree.Element("value")
                    element.text = text
                    jobs[builtin].documents[name] = etree.tostring(element)
        with tempfile.TemporaryDirectory(prefix="wsdl-name-boundaries-") as temporary:
            manifest = Path(temporary) / "manifest.json"
            manifest.write_text(json.dumps(rows))
            process = subprocess.run(["qore", "-b", "--enable-debug",
                str(Path(__file__).with_name("name-value-boundaries.qr")), str(manifest)],
                text=True, capture_output=True, timeout=60)
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual("", process.stderr)
        observed = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(6054, len(observed))
        self.assertEqual([row["name"] for row in rows], [row["name"] for row in observed])
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle["schemas"]))
        self.assertEqual({row["name"] for row in rows}, set(oracle["documents"]))
        validators = {name: etree.XMLSchema(etree.fromstring(job.schema)) for name, job in jobs.items()}
        for name in jobs:
            self.assertTrue(oracle["schemas"][name]["ok"])
            self.assertEqual([], oracle["schemas"][name]["warnings"])
        for row, result in zip(rows, observed):
            with self.subTest(character=row["name"]):
                self.assertEqual(row["expected"], oracle["documents"][row["name"]]["ok"])
                self.assertEqual([], oracle["documents"][row["name"]]["warnings"])
                self.assertEqual(row["expected"], validators[row["builtin"]].validate(
                    etree.fromstring(jobs[row["builtin"]].documents[row["name"]])))
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
