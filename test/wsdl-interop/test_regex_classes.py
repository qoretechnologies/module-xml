#!/usr/bin/env python3
"""XSD regex set operations and grammar through actual SOAP bindings.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
import test_builtin_list_values as builtin
import test_list_values as lists
from test_facet_declarations import facet


def definitions():
    for name, pattern, valid, invalid, example in (
        ("name-complement", r"[\I]", ("!", "1", "́", "𐀀"), ("A", "Α", "中", "_", ":", ""), True),
        ("char-complement", r"[\C]", ("!", "𐀀", " "), ("A", "Α", "1", "١", "́", "_", ":", ""), True),
        ("block-complement", r"[\P{IsGreek}]", ("A", "中", "𐀀", "!"), ("Α", "Ͱ", ""), True),
        ("digit-complement", r"[\D]", ("A", "Α", "!"), ("0", "١", "१", ""), True),
        ("word", r"[\w]", ("Α", "١", "中", "́"), ("!", "_", " ", ""), True),
        ("nonword", r"[\W]", ("!", "_", " "), ("Α", "١", "中", "́", ""), True),
        ("union", r"[\i\I]", ("A", "Α", "!", "1", "𐀀"), ("", "AB"), True),
        ("empty-set", r"[^\i\I]", (), ("A", "Α", "!", "1", "𐀀", ""), False),
        ("subtract-complement", r"[\I-[0-9]]", ("!", "́", "𐀀"), ("A", "Α", "1", ""), True),
        ("subtract-range", "[a-z-[aeiou]]", ("b", "z"), ("a", "e", "A", ""), True),
        ("nested-subtraction", "[a-z-[a-z-[aeiou]]]", ("a", "e"), ("b", "z", ""), True),
        ("double-complement", r"[^\P{IsGreek}]", ("Α", "Ͱ"), ("A", "中", "!", ""), False),
        ("xml-dot", ".", ("A", "Α", "𐀀", "\t"), ("\r", "\n", "\r\n", "", "AB"), True),
        ("groups", "(a|b){1,2}", ("a", "b", "ab", "ba"), ("", "aaa", "c"), True),
        ("empty-branch", "(a|)", ("a", ""), ("aa", "b"), True),
        ("empty-group", "()", ("",), ("a",), True),
        ("count-zeroes", "a{0001,0002}", ("a", "aa"), ("", "aaa"), True),
        ("hyphen-start", "[-a]", ("-", "a"), ("b", ""), True),
        ("hyphen-end", "[a-]", ("-", "a"), ("b", ""), True),
        ("hyphen-subtraction", "[a--[a]]", ("-",), ("a", "b", ""), True),
        ("escaped-range", r"[\--/]", ("-", ".", "/"), ("0", "", "a"), True),
        ("escaped-brackets", r"[\[-\]]", ("[", "\\", "]"), ("a", "^", ""), True),
        ("literal-caret", "[a^]", ("a", "^"), ("b", ""), True),
        ("literal-anchors", "^a$", ("^a$",), ("a", "^a", "a$"), True),
    ):
        yield lists.ListCase("regex-" + name, "string", facet("pattern", pattern),
            tuple([(text, True) for text in valid] + [(text, False) for text in invalid]), example=example)
    yield lists.ListCase("regex-inherited", "string", facet("pattern", r"[\I]"),
        (("!", True), ("1", False), ("A", False), ("Α", False)), parent=facet("pattern", r"[\D]"))
    yield lists.ListCase("regex-alternatives", "string", facet("pattern", r"[\I]") + facet("pattern", r"[\i]"),
        (("!", True), ("1", True), ("A", True), ("Α", True), ("AB", False), ("", False)))


class RegexClassesTest(lists.ListValuesTest):
    case_definitions = staticmethod(definitions)
    case_schema = staticmethod(builtin.schema)
    parse_value = staticmethod(lambda base, text: text)

    @staticmethod
    def provider_value(case, lexical):
        return lexical

    def check_oracles(self, jobs, expected):
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle["schemas"]))
        self.assertEqual(set(expected), set(oracle["documents"]))
        # Explicit set-equivalent spellings provide independent document checks for the
        # source-adjudicated validator defects. Original schema and document verdicts remain required.
        equivalent = {
            "regex-block-complement": (r"[\P{IsGreek}]", "[^Ͱ-Ͽ]"),
            "regex-double-complement": (r"[^\P{IsGreek}]", "[Ͱ-Ͽ]"),
            "regex-nested-subtraction": ("[a-z-[a-z-[aeiou]]]", "[aeiou]"),
            "regex-hyphen-subtraction": ("[a--[a]]", "[-]"),
            "regex-escaped-range": (r"[\--/]", "[-./]"),
            "regex-escaped-brackets": (r"[\[-\]]", r"[\[\\\]]"),
        }
        derivatives = []
        for key, job in jobs.items():
            family = key.split("/")[0]
            hyphen = family == "regex-hyphen-subtraction"
            schema_result = oracle["schemas"][key]
            self.assertEqual([], schema_result["warnings"])
            self.assertEqual(not hyphen, schema_result["ok"], schema_result)
            if hyphen:
                self.assertIn("invalid character range", schema_result["desc"])
                try:
                    validator = etree.XMLSchema(etree.fromstring(job.schema))
                except etree.XMLSchemaParseError as error:
                    self.assertIn("not a valid regular expression", str(error))
                    validator = None
            else:
                validator = etree.XMLSchema(etree.fromstring(job.schema))
            if family in equivalent:
                original, replacement = (facet("pattern", value).encode() for value in equivalent[family])
                self.assertEqual(1, job.schema.count(original))
                derivatives.append(SchemaJob(key + "/equivalent", job.uri + ".equivalent",
                    job.schema.replace(original, replacement),
                    documents={name + "/equivalent": data for name, data in job.documents.items()}))
            for name, document in job.documents.items():
                with self.subTest(oracle_document=name):
                    element = etree.fromstring(document)
                    parts = list(element) or [element]
                    texts = [part.text or "" for part in parts]
                    if element.get("choice") is not None:
                        texts.append(element.get("choice"))
                    if validator is not None:
                        libxml_expected = expected[name]
                        if family == "regex-block-complement":
                            libxml_expected = all(len(value) == 1 and 0x370 <= ord(value) <= 0x3ff for value in texts)
                        elif family == "regex-double-complement":
                            libxml_expected = all(len(value) == 1 and not 0x370 <= ord(value) <= 0x3ff for value in texts)
                        elif family == "regex-nested-subtraction":
                            libxml_expected = False
                        elif family == "regex-escaped-range":
                            libxml_expected = all(value in {"-", "/"} for value in texts)
                        elif family == "regex-escaped-brackets":
                            libxml_expected = all(value in {"[", "]"} for value in texts)
                        observed = validator.validate(element)
                        if observed != expected[name]:
                            known_results = {libxml_expected}
                            if family == "regex-escaped-range":
                                # 2.15.4 recognizes escaped endpoints but drops an escaped leading hyphen.
                                known_results.add(all(value == "/" for value in texts))
                            self.assertIn(family, equivalent)
                            self.assertIn(observed, known_results, str(validator.error_log))
                    result = oracle["documents"][name]
                    self.assertEqual([], result["warnings"])
                    if hyphen:
                        self.assertIsNone(result["ok"])
                        self.assertEqual("unreachable", result["status"])
                        self.assertEqual("schema compilation failed: " + key, result["desc"])
                    else:
                        self.assertEqual(expected[name], result["ok"], result)
        corrected = run_independent(derivatives)
        self.assertEqual({job.name for job in derivatives}, set(corrected["schemas"]))
        self.assertEqual({name for job in derivatives for name in job.documents}, set(corrected["documents"]))
        for job in derivatives:
            result = corrected["schemas"][job.name]
            self.assertTrue(result["ok"], result)
            self.assertEqual([], result["warnings"])
            validator = etree.XMLSchema(etree.fromstring(job.schema))
            for name, data in job.documents.items():
                result = corrected["documents"][name]
                self.assertEqual(expected[name.removesuffix("/equivalent")], result["ok"], result)
                self.assertEqual([], result["warnings"])
                self.assertEqual(expected[name.removesuffix("/equivalent")],
                    validator.validate(etree.fromstring(data)), str(validator.error_log))


class RegexGrammarTest(unittest.TestCase):
    def test_invalid_schema_patterns_with_source_adjudicated_oracles(self):
        patterns = ("[]", "[]]", "[^]]", "[a-b-c]", "[a-z-[aeiou]", "[a-z-[b]c]", "[a[b]]",
            r"[\d-a]", r"[a-\d]", "[z-a]", "(?:a)", "(?=a)a", "a*?", "a++", "a{,2}", "a{2,1}",
            r"\x{41}", r"\p{Greek}", r"\p{Cs}", r"\p{IsGreek_}", r"\Qabc\E", r"\bword\b", r"(a)\1",
            "(", ")", "a}", "a]", "*a", "a{1", "\\", r"\pL", r"\p{}")
        jobs, rows = {}, []
        for index, pattern in enumerate(patterns):
            source = ('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                '<xs:simpleType name="Value"><xs:restriction base="xs:string">'
                + facet("pattern", pattern) + '</xs:restriction></xs:simpleType></xs:schema>').encode()
            name = str(index)
            jobs[name] = SchemaJob(name, f"http://example.invalid/invalid-{index}.xsd", source)
            rows.append({"name": name, "schema": source.decode(), "values": []})
        with tempfile.TemporaryDirectory(prefix="wsdl-regex-grammar-") as temporary:
            manifest = Path(temporary) / "manifest.json"
            manifest.write_text(json.dumps(rows))
            process = subprocess.run(["qore", "-b", "--enable-debug",
                str(Path(__file__).with_name("regex-grammar.qr")), str(manifest)],
                text=True, capture_output=True, timeout=60)
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual("", process.stderr)
        results = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual([row["name"] for row in rows], [row["name"] for row in results])
        oracle = run_independent(list(jobs.values()))
        self.assertEqual(set(jobs), set(oracle["schemas"]))
        self.assertEqual({}, oracle["documents"])
        libxml_acceptances, xerces_acceptances = set(), set()
        for pattern, result in zip(patterns, results):
            with self.subTest(pattern=pattern):
                self.assertFalse(result["schema_ok"], result)
                self.assertEqual("XSD-SIMPLETYPE-ERROR", result["err"])
                assessment = oracle["schemas"][result["name"]]
                self.assertEqual([], assessment["warnings"])
                if assessment["ok"]:
                    xerces_acceptances.add(pattern)
                try:
                    etree.XMLSchema(etree.fromstring(jobs[result["name"]].schema))
                    libxml_acceptances.add(pattern)
                except etree.XMLSchemaParseError:
                    pass
        # Normative grammar and both validator source paths are recorded in regex-classes-evidence.md.
        self.assertLessEqual(libxml_acceptances, {r"[\d-a]", "[a-b-c]", "a{2,1}", "a}", "[]"})
        self.assertEqual({r"\p{Greek}", r"\p{Cs}", r"\Qabc\E"}, xerces_acceptances)


if __name__ == "__main__":
    unittest.main()
