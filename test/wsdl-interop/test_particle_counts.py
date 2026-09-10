#!/usr/bin/env python3
"""Native particle occurrence semantics against the pinned Xerces implementation.

Copyright (C) 2026 Qore Technologies, s.r.o.
Original schemas and explicitly identified lexical derivatives remain separate.
"""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from lxml import etree

from independent import SchemaJob, run as run_independent


def schema(kind, minimum, maximum):
    attributes = f'minOccurs="{minimum}" maxOccurs="{maximum}"'
    declarations = ""
    if kind == "element":
        particle = f'<xs:sequence><xs:element name="v" type="xs:string" {attributes}/></xs:sequence>'
    elif kind == "group":
        declarations = '<xs:group name="Fields"><xs:sequence><xs:element name="v" type="xs:string"/></xs:sequence></xs:group>'
        particle = f'<xs:group ref="Fields" {attributes}/>'
    else:
        particle = f'<xs:{kind} {attributes}><xs:element name="v" type="xs:string"/></xs:{kind}>'
    return f'''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">{declarations}
      <xs:element name="r"><xs:complexType>{particle}</xs:complexType></xs:element></xs:schema>'''


class ParticleCountsTest(unittest.TestCase):
    def test_occurrence_values_preserve_validity_in_both_native_apis(self):
        cases, expected = [], {}
        for kind in ("sequence", "choice", "element", "group", "all"):
            ranges = [("-000", "+1"), (" +1 ", " 1 ")] if kind == "all" else [
                ("+0", "+1"), ("-000", "  unbounded  "), (" +001 ", " +002 "),
                ("-0", "-0"), (" +002 ", " 0003 "), ("0", "\t unbounded\r\n")]
            for index, (minimum, maximum) in enumerate(ranges):
                lower = int(minimum)
                upper = None if maximum.strip() == "unbounded" else int(maximum)
                for derivative in (False, True):
                    name = f'{kind}-{index}-' + ('canonical-derivative' if derivative else 'original')
                    source = schema(kind, str(lower) if derivative else minimum,
                                    ('unbounded' if upper is None else str(upper)) if derivative else maximum)
                    documents = {}
                    verdicts = {}
                    for count in range(5):
                        doc = f'{name}/{count}'
                        documents[doc] = '<r>' + '<v>text</v>' * count + '</r>'
                        verdicts[doc] = count >= lower and (upper is None or count <= upper)
                    doc = f'{name}/unknown'
                    documents[doc] = '<r><unknown/></r>'
                    verdicts[doc] = False
                    case = {"name": name, "schema": source, "documents": documents}
                    if kind == "all" and not derivative:
                        case["xerces_defect"] = "all-count-lexical-enumeration"
                    cases.append(case)
                    expected[name] = True, verdicts
                    try:
                        compiled = etree.XMLSchema(etree.fromstring(source.encode()))
                    except etree.XMLSchemaParseError as error:
                        # libxml2 reads digits without the nonNegativeInteger sign;
                        # its 'unbounded' check also precedes whitespace collapsing.
                        self.assertFalse(derivative, (name, str(error)))
                        self.assertTrue('attribute \'minOccurs\'' in str(error)
                                        or 'attribute \'maxOccurs\'' in str(error), str(error))
                        self.assertIn("is not valid", str(error))
                        continue
                    for doc, text in documents.items():
                        actual = compiled.validate(etree.fromstring(text.encode()))
                        if actual != verdicts[doc]:
                            # A second libxml2 defect compiles a consuming transition
                            # for a zero-occurrence local element. Xerces and both
                            # fixed native APIs must reject these same documents.
                            self.assertEqual("element", kind, (doc, str(compiled.error_log)))
                            self.assertEqual((0, 0), (lower, upper))
                            self.assertTrue(actual)
                            self.assertFalse(verdicts[doc])
                            self.assertNotIn("unknown", doc)
        self.assertEqual(52, len(cases))
        self.assertEqual(312, sum(len(case["documents"]) for case in cases))
        self.check(cases, expected)

    def test_invalid_counts_preserve_schema_errors(self):
        cases, expected = [], {}
        for kind in ("sequence", "choice", "element", "group"):
            for property in ("min", "max"):
                for index, invalid in enumerate(("", " ", "+", "-", "+ 1", "1.0", "0x1", "1e0", "1 0",
                        "-1", "-0001", "--0", "+-0", "unbounded extra", "Unbounded", "\u00a00")):
                    name = f"{kind}-{property}-{index}"
                    source = schema(kind, invalid if property == "min" else "0",
                                    invalid if property == "max" else "unbounded")
                    with self.assertRaises(etree.XMLSchemaParseError, msg=name):
                        etree.XMLSchema(etree.fromstring(source.encode()))
                    case = {"name": name, "schema": source, "documents": {name + "/empty": "<r/>"}}
                    if invalid == "+-0":
                        case["xerces_defect"] = "two-signs"
                    cases.append(case)
                    expected[name] = False, {name + "/empty": None}
        self.assertEqual(128, len(cases))
        self.check(cases, expected)

    def check(self, cases, expected):
        self.assertEqual(len(cases), len(expected), "duplicate schema identity")
        jobs = [SchemaJob(case["name"], f'http://example.invalid/{case["name"]}.xsd', case["schema"].encode(),
                          {name: xml.encode() for name, xml in case["documents"].items()}) for case in cases]
        oracle = run_independent(jobs)
        defects = {case["name"]: case["xerces_defect"] for case in cases if "xerces_defect" in case}
        self.assertEqual(set(expected), set(oracle["schemas"]))
        all_documents = {name: verdict for _, documents in expected.values() for name, verdict in documents.items()}
        self.assertEqual(set(all_documents), set(oracle["documents"]))
        for name, result in oracle["schemas"].items():
            if defects.get(name) == "all-count-lexical-enumeration":
                # XSAttributeChecker compares the all count enumeration to the
                # literal strings "0" and "1", instead of their integer values.
                self.assertFalse(result["ok"], (name, result))
                self.assertIn("cvc-enumeration-valid", result["desc"])
            elif defects.get(name) == "two-signs":
                # XSAttributeChecker strips '+' before Integer.parseInt(), which
                # then accepts the second '-' sign in the invalid spelling '+-0'.
                self.assertTrue(result["ok"], (name, result))
            else:
                self.assertEqual(expected[name][0], result["ok"], (name, result))
            self.assertEqual([], result["warnings"])
        for name, result in oracle["documents"].items():
            defect = defects.get(name.rsplit("/", 1)[0])
            oracle_verdict = None if defect == "all-count-lexical-enumeration" else True if defect == "two-signs" \
                else all_documents[name]
            self.assertEqual(oracle_verdict, result["ok"], (name, result))
            self.assertEqual([], result["warnings"])
        mode = os.environ.get("QORE_EXEC_MODE", "jit")
        self.assertIn(mode, ("ast", "ir", "jit", "tiered"))
        with tempfile.TemporaryDirectory(prefix="wsdl-native-particles-") as temporary:
            path = Path(temporary) / "cases.json"
            path.write_text(json.dumps(cases), encoding="utf-8")
            process = subprocess.run(["qore", "-b", "--enable-debug", "--exec-mode=" + mode,
                                      str(Path(__file__).with_name("particle-counts.qr")), str(path)],
                                     text=True, capture_output=True, timeout=60)
        self.assertEqual(0, process.returncode, process.stderr + process.stdout[-2000:])
        self.assertEqual("", process.stderr)
        rows = iter(json.loads(line) for line in process.stdout.splitlines())
        for case in cases:
            schema_ok, documents = expected[case["name"]]
            for api in ("reader", "data"):
                for name, verdict in documents.items():
                    row = next(rows)
                    self.assertEqual(case["name"], row["schema"])
                    self.assertEqual(api, row["api"])
                    self.assertEqual(name, row["document"])
                    self.assertEqual(bool(verdict), row["ok"], row)
                    if not verdict:
                        self.assertEqual("PARSE-XML-EXCEPTION" if schema_ok else "XSD-SYNTAX-ERROR", row["err"])
                        self.assertTrue(row["desc"])
        self.assertIsNone(next(rows, None), "unexpected extra native worker result")


if __name__ == "__main__":
    unittest.main()
