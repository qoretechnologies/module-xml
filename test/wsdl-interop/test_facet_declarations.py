#!/usr/bin/env python3
"""XSD 1.0 numeric restriction declarations, independent of instance validation.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent
from test_attribute_values import description, NS, XSD
import survey


@dataclass(frozen=True)
class Declaration:
    name: str
    facets: str
    valid: bool
    value: str | None = None
    parent: str = ""
    base: str = "decimal"


def facet(name, value, extra=""):
    return f'<xs:{name} value="{value}"{extra}/>'


def declarations():
    # XSD 1.0 Part 2 4.3.7-10: valid derivation at values below/equal/above 1.
    # Rows are inherited bounds; columns are newly declared bounds.
    names = ("minInclusive", "minExclusive", "maxInclusive", "maxExclusive")
    valid_offsets = (
        ((1, 2), (1, 2), (1, 2), (2,)),
        ((2,), (1, 2), (2,), (2,)),
        ((0, 1), (0,), (0, 1), (0, 1)),
        ((0,), (0,), (0,), (0, 1)),
    )
    comparisons = {
        "minInclusive": lambda value, bound: value >= bound,
        "minExclusive": lambda value, bound: value > bound,
        "maxInclusive": lambda value, bound: value <= bound,
        "maxExclusive": lambda value, bound: value < bound,
    }
    for row, inherited in enumerate(names):
        for column, own in enumerate(names):
            for offset in (0, 1, 2):
                valid = offset in valid_offsets[row][column]
                candidates = ("-1", "0", "0.5", "1", "1.5", "2", "3")
                value = next((text for text in candidates if comparisons[inherited](Decimal(text), 1)
                              and comparisons[own](Decimal(text), offset)), None) if valid else None
                yield Declaration(f"bounds-{inherited}-{own}-{offset}", facet(own, offset), valid, value,
                                  facet(inherited, 1))
    yield Declaration("equal-exclusive-empty", facet("minExclusive", 1) + facet("maxExclusive", 1), True)
    yield Declaration("exclusive-enum", facet("minExclusive", 1), True, "2",
                      facet("minExclusive", 1) + facet("enumeration", 2))
    yield Declaration("exclusive-digits", facet("minExclusive", "1.234"), True, "2",
                      facet("minExclusive", "1.234") + facet("fractionDigits", 0))
    yield Declaration("exclusive-pattern-invalid", facet("minExclusive", 1), False,
                      parent=facet("minExclusive", 1) + facet("pattern", "0[0-9]"))
    yield Declaration("exclusive-pattern-valid", facet("minExclusive", "01"), True, "02",
                      facet("minExclusive", 1) + facet("pattern", "0[0-9]"))
    yield Declaration("same-fixed", facet("minInclusive", "1", ' fixed="false"'), True, "1",
                      facet("minInclusive", "+01.00", ' fixed="true"'))
    yield Declaration("changed-fixed", facet("minInclusive", "2"), False, parent=facet("minInclusive", 1, ' fixed="true"'))
    yield Declaration("different-fixed-kind", facet("minExclusive", 1), True, "2",
                      facet("minInclusive", 1, ' fixed="true"'))
    yield Declaration("integer-fraction", facet("fractionDigits", 1), False, base="integer")
    yield Declaration("builtin-upper-empty", facet("minExclusive", 127), False, base="byte")
    yield Declaration("builtin-lower-empty", facet("maxExclusive", -128), False, base="byte")
    yield Declaration("builtin-upper-singleton", facet("minInclusive", 127), True, "127", base="byte")
    yield Declaration("builtin-lower-singleton", facet("maxInclusive", -128), True, "-128", base="byte")
    yield Declaration("duplicate-bound", facet("minInclusive", 1) * 2, False)
    yield Declaration("whitespace-weakened", facet("whiteSpace", "replace"), False)
    yield Declaration("whitespace-token", facet("whiteSpace", "  collapse &#x9;"), True, "1.23")
    yield Declaration("inherited-digits", facet("totalDigits", 2), False, parent=facet("fractionDigits", 4))
    yield Declaration("widened-digits", facet("totalDigits", 3), False, parent=facet("totalDigits", 2))
    yield Declaration("base-digits-bound", facet("minInclusive", 123), False, parent=facet("totalDigits", 2))
    yield Declaration("base-pattern-enum", facet("enumeration", "+0009"), False,
                      parent=facet("pattern", "00[0-9]"), base="integer")
    yield Declaration("own-pattern-enum", facet("enumeration", "+0009") + facet("pattern", "00[0-9]"),
                      True, "009", base="integer")
    yield Declaration("own-enum-digits-empty", facet("enumeration", 123) + facet("totalDigits", 2), True)
    for count in (2147483648, 9223372036854775808):
        yield Declaration(f"large-count-{count}", facet("totalDigits", count) + facet("fractionDigits", count),
                          True, "1.00000000000000000001")
    yield Declaration("large-count-narrowed", facet("totalDigits", 9223372036854775808), True, "1.23",
                      facet("totalDigits", 9223372036854775809))
    yield Declaration("large-count-widened", facet("totalDigits", 9223372036854775809), False,
                      parent=facet("totalDigits", 9223372036854775808))
    for name, source in {
        "missing-value": '<xs:minInclusive/>',
        "unknown-attribute": '<xs:minInclusive value="1" extra="x"/>',
        "schema-attribute": '<xs:minInclusive value="1" xs:extra="x"/>',
        "no-namespace": '<minInclusive value="1"/>',
        "wrong-namespace": '<x:minInclusive xmlns:x="urn:other" value="1"/>',
        "late-annotation": '<xs:minInclusive value="1"/><xs:annotation/>',
        "facet-text": '<xs:minInclusive value="1">text</xs:minInclusive>',
        "invalid-fixed": '<xs:minInclusive value="1" fixed="yes"/>',
        "pattern-fixed": '<xs:pattern value=".*" fixed="false"/>',
        "invalid-pattern": '<xs:pattern value="["/>',
    }.items():
        yield Declaration(name, source, False)
    yield Declaration("foreign-attribute", '<xs:minInclusive value="1" xmlns:m="urn:metadata" m:note="x"/>', True, "2")
    yield Declaration("default-namespace", '<minInclusive xmlns="http://www.w3.org/2001/XMLSchema" value="1"/>', True, "2")


# The independent implementations' known schema-compiler defects are documented in
# facet-declarations-adjudication.md. These are oracle disagreements, never production passes.
ORACLE_DEFECTS = {
    "libxml2": {
        "bounds-minExclusive-minExclusive-1", "bounds-maxExclusive-maxExclusive-1",
        "exclusive-enum", "exclusive-digits", "exclusive-pattern-valid",
        "bounds-maxInclusive-minExclusive-1", "builtin-upper-empty", "builtin-lower-empty",
        "integer-fraction", "duplicate-bound", "whitespace-weakened", "whitespace-token",
        "unknown-attribute", "schema-attribute", "invalid-fixed", "pattern-fixed",
    },
    "Xerces": {
        "bounds-minInclusive-maxExclusive-1", "bounds-maxInclusive-minExclusive-1",
        "builtin-upper-empty", "builtin-lower-empty", "inherited-digits",
        "large-count-2147483648", "large-count-9223372036854775808", "large-count-narrowed",
    },
}


def schema(case, model):
    types = f'<xs:simpleType name="Base"><xs:restriction base="xs:{case.base}">{case.parent}</xs:restriction></xs:simpleType>'
    if model == "atomic":
        types += f'<xs:simpleType name="Amount"><xs:restriction base="t:Base">{case.facets}</xs:restriction></xs:simpleType>'
    else:
        types += f'''<xs:complexType name="BaseRecord"><xs:simpleContent><xs:extension base="t:Base"/>
            </xs:simpleContent></xs:complexType><xs:complexType name="Amount"><xs:simpleContent>
            <xs:restriction base="t:BaseRecord">{case.facets}</xs:restriction></xs:simpleContent></xs:complexType>'''
    return f'''<xs:schema xmlns:xs="{XSD}" xmlns:t="{NS}" targetNamespace="{NS}">{types}
        <xs:element name="Submit" type="t:Amount"/><xs:element name="Reply" type="t:Amount"/></xs:schema>'''.encode()


class FacetDeclarationsTest(unittest.TestCase):
    def test_declarations_and_bound_values(self):
        jobs, cases, expected, validators = [], [], {}, {}
        libxml_results = {}
        with tempfile.TemporaryDirectory(prefix="wsdl-facet-declarations-") as temporary:
            root = Path(temporary)
            for case in declarations():
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
                        if case.value is not None:
                            for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                                name = key + "/" + version + "/" + direction
                                envelope = etree.Element(f"{{{envelope_ns}}}Envelope", nsmap={"s": envelope_ns})
                                body = etree.SubElement(envelope, f"{{{envelope_ns}}}Body")
                                element = etree.SubElement(body, f"{{{NS}}}{wrapper}")
                                element.text = case.value
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
        output_count = 0
        for row in rows:
            key = "/".join(row["case"].split("/")[:2])
            case = expected[key]
            with self.subTest(row=row.get("file", row["case"]), stage=row["stage"]):
                if row["stage"] == "parse":
                    self.assertEqual(case.valid, row["ok"], row)
                    if not case.valid:
                        self.assertEqual("XSD-SIMPLETYPE-ERROR", row["err"], row)
                else:
                    self.assertTrue(row["ok"], row)
                    if row["stage"] == "serialize":
                        envelope = etree.fromstring(row["body"].encode())
                        version, direction = row["file"].split("/")[-2:]
                        self.assertEqual(f"{{{survey.SOAP_NAMESPACES[int(version == '12')]}}}Envelope", envelope.tag)
                        element = envelope.find("{*}Body")[0]
                        self.assertEqual(f"{{{NS}}}" + ("Submit" if direction == "request" else "Reply"), element.tag)
                        self.assertEqual(Decimal(case.value), Decimal(element.text))
                        output_count += 1
                        by_key[key].documents[row["file"] + "/output"] = etree.tostring(element)
                        if key in validators:
                            self.assertTrue(validators[key].validate(element), str(validators[key].error_log))
        self.assertEqual(sum(case.value is not None for case in expected.values()) * 4, output_count)
        oracle = run_independent(jobs)
        disagreements = {"libxml2": set(), "Xerces": set()}
        for key, case in expected.items():
            for name, actual in (("libxml2", libxml_results[key]), ("Xerces", oracle["schemas"][key]["ok"])):
                with self.subTest(schema=key, oracle=name):
                    if actual != case.valid:
                        self.assertIn(case.name, ORACLE_DEFECTS[name], (key, actual, case.valid))
                        disagreements[name].add(case.name)
            for name in by_key[key].documents:
                if oracle["schemas"][key]["ok"]:
                    self.assertTrue(oracle["documents"][name]["ok"], (name, oracle["documents"][name]))
                else:
                    self.assertEqual("unreachable", oracle["documents"][name]["status"])
                    self.assertIn(case.name, ORACLE_DEFECTS["Xerces"])
                    # Exact Decimal checks above remain mandatory for the count-overflow cases.
        self.assertEqual(set(ORACLE_DEFECTS["Xerces"]), disagreements["Xerces"])
        if etree.LIBXML_VERSION == (2, 12, 10):
            self.assertEqual(set(ORACLE_DEFECTS["libxml2"]), disagreements["libxml2"])


if __name__ == "__main__":
    unittest.main()
