#!/usr/bin/env python3
"""Independent XSD 1.0 string whitespace and character/octet/item length checks.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from dataclasses import dataclass
from pathlib import Path
import base64
import json
import subprocess
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS, XSD
from test_facet_declarations import facet
import survey


@dataclass(frozen=True)
class SizedCase:
    name: str
    facets: str
    values: tuple[tuple[str, str | None], ...] = ()
    base: str = "string"
    parent: str = ""
    valid: bool = True
    list_type: bool = False


def definitions():
    yield SizedCase("token-enum", facet("enumeration", " A&#x9; B "),
                    (("  A\t B ", "A B"), ("A C", None)), "token")
    yield SizedCase("replace-enum", facet("enumeration", "A&#x9;B"),
                    (("A\nB", "A B"), ("A  B", None)), "normalizedString")
    yield SizedCase("own-whitespace-empty-intersection", facet("whiteSpace", "collapse")
                    + facet("enumeration", " A B "), (("A B", None), (" A B ", None)))
    for inherited in (facet("pattern", "A B"), facet("enumeration", "A B"), facet("length", 3)):
        name = inherited.split(":", 1)[1].split(" ", 1)[0]
        yield SizedCase("derived-collapse-" + name, facet("whiteSpace", "collapse"),
                        ((" A\t  B ", "A B"),), parent=inherited)
    yield SizedCase("xml-whitespace-only", facet("whiteSpace", "collapse") + facet("pattern", "A B"),
                    (("A\u00a0B", None), (" A\rB ", "A B")))
    yield SizedCase("pattern-final-newline", facet("pattern", "A"), (("A\n", None), ("A", "A")))
    yield SizedCase("unicode-codepoints", facet("length", 1), (("😀", "😀"), ("é", None)))
    yield SizedCase("unicode-combining", facet("length", 2), (("é", "é"), ("é", None)))
    yield SizedCase("empty", facet("maxLength", 0), (("", ""), ("a", None)))
    yield SizedCase("normalized-length", facet("minLength", 3) + facet("maxLength", 3),
                    ((" A  B ", "A B"), ("AB", None), ("ABCD", None)), "token")
    yield SizedCase("base-min-own-length", facet("length", 3), (("abc", "abc"), ("ab", None)),
                    parent=facet("minLength", 2))
    yield SizedCase("base-min-repeat-own-length", facet("length", 3) + facet("minLength", 2),
                    (("abc", "abc"),), parent=facet("minLength", 2))
    yield SizedCase("own-length-min", facet("length", 3) + facet("minLength", 2), valid=False)
    yield SizedCase("base-length-own-min", facet("minLength", 2), parent=facet("length", 3), valid=False)
    yield SizedCase("changed-length", facet("length", 2), parent=facet("length", 3), valid=False)
    yield SizedCase("weakened-min", facet("minLength", 1), parent=facet("minLength", 2), valid=False)
    yield SizedCase("weakened-max", facet("maxLength", 3), parent=facet("maxLength", 2), valid=False)
    yield SizedCase("fixed-max", facet("maxLength", 2), parent=facet("maxLength", 3, ' fixed="true"'), valid=False)
    yield SizedCase("contradictory-length", facet("minLength", 3) + facet("maxLength", 2), valid=False)
    yield SizedCase("weakened-whitespace", facet("whiteSpace", "replace"), base="token", valid=False)
    yield SizedCase("fixed-whitespace", facet("whiteSpace", "collapse"),
                    parent=facet("whiteSpace", "replace", ' fixed="true"'), valid=False)
    yield SizedCase("inapplicable-bound", facet("minInclusive", 1), valid=False)
    yield SizedCase("inapplicable-length", facet("length", 1), base="boolean", valid=False)
    for name in ("length", "minLength", "maxLength"):
        for value in ("-1", "1x", "1.0", "", "١"):
            yield SizedCase("invalid-" + name + "-" + (value or "empty"), facet(name, value), valid=False)
    for count in (2147483648, 9223372036854775808):
        yield SizedCase(f"large-count-{count}", facet("maxLength", count), (("abc", "abc"),))
    yield SizedCase("large-count-narrowed", facet("maxLength", 9223372036854775808), (("abc", "abc"),),
                    parent=facet("maxLength", 9223372036854775809))
    yield SizedCase("large-count-widened", facet("maxLength", 9223372036854775809),
                    parent=facet("maxLength", 9223372036854775808), valid=False)
    yield SizedCase("list-items", facet("length", 2), (("01\t+2", "1 2"), ("1", None), ("1 2 3", None)),
                    "integer", list_type=True)
    yield SizedCase("empty-list", facet("length", 0), ((" \t ", ""), ("a", None)), list_type=True)
    yield SizedCase("builtin-list-items", facet("length", 2), ((" A\t B ", "A B"), ("A", None)), "NMTOKENS")
    yield SizedCase("builtin-list-empty", "", ((" \t ", None),), "NMTOKENS")
    for name in ("length", "minLength", "maxLength"):
        yield SizedCase("builtin-list-zero-" + name, facet(name, 0), base="NMTOKENS", valid=False)
    yield SizedCase("list-whitespace", facet("whiteSpace", "preserve"), base="integer", valid=False, list_type=True)
    yield SizedCase("list-bounds", facet("minInclusive", 1), base="integer", valid=False, list_type=True)
    yield SizedCase("hex-octets", facet("length", 1), (("00", "00"), ("0000", None)), "hexBinary")
    yield SizedCase("base64-octets", facet("length", 1), (("AA==", "AA=="), ("AAA=", None)), "base64Binary")
    yield SizedCase("qname-length", facet("length", 0), (("longLocalName", "longLocalName"),), "QName")


def schema(case, model):
    base = f'<xs:list itemType="xs:{case.base}"/>' if case.list_type else (
        f'<xs:restriction base="xs:{case.base}">{case.parent}</xs:restriction>')
    types = f'<xs:simpleType name="Base">{base}</xs:simpleType>'
    if model == "atomic":
        types += f'<xs:simpleType name="Value"><xs:restriction base="t:Base">{case.facets}</xs:restriction></xs:simpleType>'
    else:
        types += f'''<xs:complexType name="BaseRecord"><xs:simpleContent><xs:extension base="t:Base"/>
            </xs:simpleContent></xs:complexType><xs:complexType name="Value"><xs:simpleContent>
            <xs:restriction base="t:BaseRecord">{case.facets}</xs:restriction></xs:simpleContent></xs:complexType>'''
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">{types}
        <xs:element name="Submit" type="t:Value"/><xs:element name="Reply" type="t:Value"/></xs:schema>'''.encode()


# Exact compiler disagreements adjudicated in sized-facets-adjudication.md; Qore verdicts stay mandatory.
ORACLE_DEFECTS = {
    "libxml2": {"base-length-own-min", "base-min-repeat-own-length", "contradictory-length",
                "list-whitespace", "weakened-whitespace", "builtin-list-zero-length",
                "builtin-list-zero-minLength", "builtin-list-zero-maxLength"},
    "Xerces": {"invalid-length-١", "invalid-minLength-١", "invalid-maxLength-١",
               "large-count-2147483648", "large-count-9223372036854775808", "large-count-narrowed"},
}


class SizedFacetsTest(unittest.TestCase):
    def test_providers_reconstruction_and_generated_examples(self):
        cases = [case for case in definitions() if case.name in {
            "token-enum", "replace-enum", "own-whitespace-empty-intersection", "derived-collapse-pattern",
            "pattern-final-newline",
            "unicode-codepoints", "unicode-combining", "empty", "normalized-length", "list-items", "empty-list",
            "builtin-list-items", "hex-octets", "base64-octets"}]
        cases += [SizedCase("enum-pattern", facet("enumeration", "BAD") + facet("enumeration", "GOOD")
                            + facet("pattern", "GOOD"), (("GOOD", "GOOD"), ("BAD", None))),
                  SizedCase("unconstrained-list", "", (("1 2", "1 2"),), "integer", list_type=True),
                  SizedCase("builtin-list-example", "", (("A B", "A B"),), "NMTOKENS")]
        jobs, validators, expectations, manifest_rows = {}, {}, {}, []
        with tempfile.TemporaryDirectory(prefix="wsdl-sized-consumers-") as temporary:
            root = Path(temporary)
            for case in cases:
                for model in ("atomic", "record", "repeated"):
                    key = case.name + "-" + model
                    source = schema(case, "atomic")
                    if model == "record":
                        source = source.replace(b'<xs:element name="Submit"', b'''<xs:complexType name="Record">
                            <xs:simpleContent><xs:extension base="t:Value"><xs:attribute name="choice"
                            type="t:Value" use="required"/></xs:extension></xs:simpleContent></xs:complexType>
                            <xs:element name="Submit"''').replace(b'type="t:Value"/>', b'type="t:Record"/>')
                    elif model == "repeated":
                        source = source.replace(b'<xs:element name="Submit"', b'''<xs:complexType name="Record">
                            <xs:sequence><xs:element name="item" type="t:Value" maxOccurs="3"/></xs:sequence>
                            </xs:complexType><xs:element name="Submit"''').replace(
                                b'type="t:Value"/>', b'type="t:Record"/>')
                    jobs[key] = SchemaJob(key, f"http://example.invalid/{key}.xsd", source)
                    validators[key] = etree.XMLSchema(etree.fromstring(source))
                    variants = []
                    for lexical, expected in case.values:
                        value = lexical.split() if case.list_type else lexical
                        native = ""
                        if case.base == "hexBinary":
                            native = "hex"
                        elif case.base == "base64Binary":
                            value, native = base64.b64decode(lexical).hex(), "hex"
                        for count in ((1, 2) if model == "repeated" else (1,)):
                            variants.append({"value": value, "native": native, "expected": expected, "count": count})
                    for version in ("11", "12"):
                        name = key + "/" + version
                        path = root / (name.replace("/", "-") + ".wsdl")
                        path.write_text(description(version, source.decode()))
                        manifest_rows.append({"name": name, "wsdl": str(path), "binding": "Soap" + version,
                                              "model": model, "values": variants})
                        expectations[name] = case, model, variants
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(manifest_rows))
            process = subprocess.run(["qore", "--enable-debug",
                                      str(Path(__file__).with_name("sized-facet-consumers.qr")), str(manifest)],
                                     text=True, capture_output=True, timeout=60)
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual("", process.stderr)
        rows = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(sum(4 * (len(item[2]) + 1) for item in expectations.values()), len(rows))
        seen = set()
        for row in rows:
            name = f"{row['name']}/{row['copy']}/{row['direction']}/{row['index']}"
            self.assertNotIn(name, seen)
            seen.add(name)
            self.assertIn(row["copy"], (0, 1))
            self.assertIn(row["direction"], ("request", "response"))
            case, model, variants = expectations[row["name"]]
            with self.subTest(consumer=name):
                if row["index"] == "example" and case.name == "own-whitespace-empty-intersection":
                    self.assertEqual("XSD-SAMPLE-ERROR", row.get("err"), row)
                    self.assertNotIn("body", row)
                    continue
                if row["index"] != "example" and variants[row["index"]]["expected"] is None:
                    self.assertEqual("RUNTIME-TYPE-ERROR", row.get("err"), row)
                    self.assertNotIn("body", row)
                    continue
                self.assertNotIn("err", row)
                key, version = row["name"].split("/")
                envelope = etree.fromstring(row["body"].encode())
                self.assertEqual(f"{{{survey.SOAP_NAMESPACES[int(version == '12')]}}}Envelope", envelope.tag)
                element = envelope.find("{*}Body")[0]
                self.assertEqual(f"{{{NS}}}" + ("Submit" if row["direction"] == "request" else "Reply"), element.tag)
                self.assertTrue(validators[key].validate(element), (name, str(validators[key].error_log)))
                if row["index"] != "example":
                    expected = variants[row["index"]]["expected"]
                    if model == "repeated":
                        self.assertEqual(variants[row["index"]]["count"], len(element))
                        elements = list(element)
                        self.assertTrue(all(child.tag == "item" for child in elements))
                    else:
                        elements = [element]
                    normalize = lambda text: text
                    if case.list_type and case.base == "integer":
                        normalize = lambda text: tuple(map(int, text.split()))
                    elif case.base == "hexBinary":
                        normalize = bytes.fromhex
                    elif case.base == "base64Binary":
                        normalize = base64.b64decode
                    for child in elements:
                        self.assertEqual(normalize(expected), normalize(child.text or ""), name)
                    if model == "record":
                        self.assertEqual(normalize(expected), normalize(element.get("choice")), name)
                jobs[key].documents[name] = etree.tostring(element)
        oracle = run_independent(list(jobs.values()))
        self.assertTrue(all(result["ok"] for result in oracle["schemas"].values()), oracle["schemas"])
        self.assertEqual({name for job in jobs.values() for name in job.documents}, set(oracle["documents"]))
        for name, result in oracle["documents"].items():
            self.assertTrue(result["ok"], (name, result))

    def test_sized_facets_in_both_directions(self):
        jobs, cases, expected, expected_documents, validators, libxml_results = [], [], {}, {}, {}, {}
        with tempfile.TemporaryDirectory(prefix="wsdl-sized-facets-") as temporary:
            root = Path(temporary)
            for case in definitions():
                for model in ("atomic", "simple-content"):
                    key = case.name + "/" + model
                    expected[key] = case
                    source = schema(case, model)
                    job = SchemaJob(key, f"http://example.invalid/{key}.xsd", source)
                    jobs.append(job)
                    try:
                        validators[key] = etree.XMLSchema(etree.fromstring(source))
                        libxml_results[key] = True
                    except etree.XMLSchemaParseError:
                        libxml_results[key] = False
                    for version, envelope_ns in zip(("11", "12"), survey.SOAP_NAMESPACES):
                        wsdl = root / (key.replace("/", "-") + version + ".wsdl")
                        wsdl.write_text(description(version, source.decode()))
                        messages = []
                        for index, (lexical, value) in enumerate(case.values):
                            for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                                name = key + f"/{version}/{index}/{direction}"
                                expected_documents[name] = value
                                envelope = etree.Element(f"{{{envelope_ns}}}Envelope", nsmap={"s": envelope_ns})
                                body = etree.SubElement(envelope, f"{{{envelope_ns}}}Body")
                                element = etree.SubElement(body, f"{{{NS}}}{wrapper}")
                                element.text = lexical
                                job.documents[name] = etree.tostring(element)
                                path = root / name.replace("/", "-")
                                path.write_bytes(etree.tostring(envelope))
                                messages.append({"file": name, "path": str(path), "direction": direction})
                        cases.append({"name": key + "/" + version, "wsdl": str(wsdl), "base": "http://example.invalid/",
                                      "operation": "submit", "binding": "Soap" + version, "messages": messages})
            rows = survey.run_worker(cases, {})
        accounting = survey.stage_accounting(cases, rows)["counts"]
        self.assertEqual(len(expected) * 2, accounting["parse"]["ok"] + accounting["parse"]["failed"])
        for stages in accounting.values():
            self.assertEqual(0, stages["missing"])
            self.assertEqual(0, stages["skipped"])
        by_key = {job.name: job for job in jobs}
        outputs = 0
        for row in rows:
            key = "/".join(row["case"].split("/")[:2])
            case = expected[key]
            with self.subTest(row=row.get("file", row["case"]), stage=row["stage"]):
                if row["stage"] == "parse":
                    self.assertEqual(case.valid, row["ok"], row)
                    if not case.valid:
                        self.assertEqual("XSD-SIMPLETYPE-ERROR", row["err"], row)
                    continue
                value = expected_documents[row["file"]]
                if row["stage"] == "deserialize":
                    self.assertEqual(value is not None, row["ok"], row)
                    if value is None:
                        self.assertEqual("SOAP-DESERIALIZATION-ERROR", row["err"], row)
                elif row["stage"] == "serialize":
                    self.assertTrue(row["ok"], row)
                    self.assertIsNotNone(value)
                    envelope = etree.fromstring(row["body"].encode())
                    version, _, direction = row["file"].split("/")[-3:]
                    self.assertEqual(f"{{{survey.SOAP_NAMESPACES[int(version == '12')]}}}Envelope", envelope.tag)
                    element = envelope.find("{*}Body")[0]
                    self.assertEqual(f"{{{NS}}}" + ("Submit" if direction == "request" else "Reply"), element.tag)
                    text = element.text or ""
                    if case.list_type and case.base == "integer":
                        self.assertEqual([int(part) for part in value.split()], [int(part) for part in text.split()])
                    elif case.base == "hexBinary":
                        self.assertEqual(bytes.fromhex(value), bytes.fromhex(text))
                    elif case.base == "base64Binary":
                        self.assertEqual(base64.b64decode(value, validate=True), base64.b64decode(text, validate=True))
                    else:
                        self.assertEqual(value, text)
                    outputs += 1
                    output_name = row["file"] + "/output"
                    expected_documents[output_name] = value
                    by_key[key].documents[output_name] = etree.tostring(element)
        self.assertEqual(sum(value is not None for name, value in expected_documents.items()
                             if not name.endswith("/output")), outputs)
        oracle = run_independent(jobs)
        disagreements = {"libxml2": set(), "Xerces": set()}
        document_disagreements = set()
        for key, case in expected.items():
            for name, actual in (("libxml2", libxml_results[key]), ("Xerces", oracle["schemas"][key]["ok"])):
                with self.subTest(schema=key, oracle=name):
                    if actual != case.valid:
                        disagreements[name].add(case.name)
                        self.assertIn(case.name, ORACLE_DEFECTS[name], (key, actual, case.valid))
            for name, document in by_key[key].documents.items():
                valid = expected_documents[name] is not None
                with self.subTest(document=name):
                    if key in validators:
                        actual = validators[key].validate(etree.fromstring(document))
                        if actual != valid:
                            self.assertEqual("builtin-list-empty", case.name, str(validators[key].error_log))
                            self.assertFalse(valid)
                            self.assertTrue(actual)
                            document_disagreements.add(case.name)
                    if oracle["schemas"][key]["ok"]:
                        self.assertEqual(valid, oracle["documents"][name]["ok"], oracle["documents"][name])
                    else:
                        self.assertEqual("unreachable", oracle["documents"][name]["status"])
        self.assertEqual(ORACLE_DEFECTS["Xerces"], disagreements["Xerces"])
        if etree.LIBXML_VERSION == (2, 12, 10):
            self.assertEqual(ORACLE_DEFECTS["libxml2"], disagreements["libxml2"])
            self.assertEqual({"builtin-list-empty"}, document_disagreements)


if __name__ == "__main__":
    unittest.main()
