#!/usr/bin/env python3
"""Strict Qore coverage, complete accounting, independent values and real binding tests.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from lxml import etree

import corpus
import coverage
import survey
from independent import SchemaJob, run as run_independent


ROOT = Path(__file__).resolve().parent


class CoverageTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="wsdl-coverage-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "w3c/BooleanElement", self.root / "BooleanElement")
        self.source = json.loads((ROOT / "adjudication-report.json").read_text())
        self.source["cases"] = [c for c in self.source["cases"] if c["case"] == "BooleanElement"]
        self.selection = corpus.read_manifest(ROOT / "strict-selection.json")
        self.selection["cases"] = {"BooleanElement": self.selection["cases"]["BooleanElement"]}

    def test_strict_positive_both_directions_and_value_change_detection(self):
        report = coverage.assess(self.root, self.source, self.selection, corpus.Catalog())
        self.assertEqual([], report["selected_failures"])
        self.assertEqual([], report["failures"])
        self.assertEqual({"wsdls": 1, "message_directions": 16}, report["selected_scope"])
        self.assertEqual(16, report["stage_accounting"]["counts"]["values"]["ok"])
        identity = report["cases"][0]["identity"]
        self.assertNotEqual(identity["directions"]["request"]["message"], identity["directions"]["response"]["message"])
        cases, _ = coverage.prepare(self.root, self.source)
        rows = survey.run_worker(cases, {})
        # A changed boolean is still schema-valid. The strict gate must detect its changed value.
        encoded = next(r for r in rows if r["stage"] == "serialize")
        encoded["body"] = encoded["body"].replace(">false<", ">true<")
        with patch.object(survey, "run_worker", return_value=rows):
            report = coverage.assess(self.root, self.source, self.selection, corpus.Catalog())
        self.assertEqual(["value_preservation"], report["selected_failures"][0]["stages"])
        row = report["cases"][0]["messages"][0]
        self.assertTrue(row["output_xerces"]["ok"])
        self.assertTrue(row["output_lxml"]["ok"])
        self.assertFalse(row["values"]["ok"])

    def test_strict_selection_and_source_integrity(self):
        _, records = coverage.prepare(self.root, self.source)
        variants = [{}, {"format": True, "cases": {}}, {"format": 1, "cases": {"absent": {}}}]
        for value in ({}, {"messages": {}}, {"messages": {"absent": []}},
                      {"messages": {next(iter(records["BooleanElement"]["messages"])): []}}):
            variants.append({"format": 1, "cases": {"BooleanElement": value}})
        for selection in variants:
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                coverage.validate_selection(selection, records)
        for key, value in (("wsdl_sha256", "0" * 64), ("messages", {})):
            source = deepcopy(self.source)
            source["cases"][0][key] = value
            with self.assertRaises(ValueError):
                coverage.prepare(self.root, source)
        duplicate = deepcopy(self.source)
        duplicate["cases"] *= 2
        with self.assertRaises(ValueError):
            coverage.prepare(self.root, duplicate)
        source = deepcopy(self.source)
        source["cases"][0]["source_decision"]["valid"] = None
        with self.assertRaisesRegex(ValueError, "provisional"):
            coverage.prepare(self.root, source)

    def test_string_value_assertions_preserve_xml_whitespace_semantics(self):
        for datatype, before, after, valid in (
                ("string", "A\tB", "A B", False),
                ("normalizedString", "A\tB", "A B", True),
                ("normalizedString", "A\tB", "A  B", False),
                ("token", " A\t  B ", "A B", True),
                ("token", "A\u00a0B", "A B", False)):
            with self.subTest(datatype=datatype, before=before, after=after):
                left, right = etree.Element("value"), etree.Element("value")
                left.text, right.text = before, after
                result = coverage.value_checks(left, right, [{"elements": ["value"], "datatype": datatype}])
                self.assertEqual(valid, result["ok"], result)

    def test_missing_worker_stage_cannot_pass(self):
        cases, _ = coverage.prepare(self.root, self.source)
        rows = survey.run_worker(cases, {})
        with patch.object(survey, "run_worker", return_value=rows[:-1]), self.assertRaises(RuntimeError):
            coverage.assess(self.root, self.source, self.selection, corpus.Catalog())

    def test_real_cxf_soap12_binding_distinct_request_response(self):
        ns = "http://apache.org/hello_world_soap12_http/types"
        messages = []
        for direction, body in (("request", f'<sayHi xmlns="{ns}"/>'),
                                ("response", f'<sayHiResponse xmlns="{ns}"><responseType>Hello, world!</responseType>'
                                 '</sayHiResponse>')):
            file = direction + ".xml"
            path = self.root / file
            path.write_text(f'<s:Envelope xmlns:s="{survey.SOAP_NAMESPACES[1]}"><s:Body>{body}</s:Body></s:Envelope>')
            messages.append({"file": file, "path": str(path), "direction": direction})
        wsdl = ROOT / "cxf/hello_world_soap12.wsdl"
        case = {"name": "CxfSoap12", "wsdl": str(wsdl), "base": "http://cxf.invalid/",
                "operation": "sayHi", "binding": "Greeter_SOAPBinding", "messages": messages}
        rows = survey.run_worker([case], {})
        self.assertEqual(2, survey.stage_accounting([case], rows)["counts"]["serialize"]["ok"])
        schema = etree.XMLSchema(etree.parse(str(wsdl)).find(
            "{http://schemas.xmlsoap.org/wsdl/}types/{http://www.w3.org/2001/XMLSchema}schema"))
        for row in rows:
            if row["stage"] == "serialize":
                envelope = etree.fromstring(row["body"].encode())
                self.assertEqual(f"{{{survey.SOAP_NAMESPACES[1]}}}Envelope", envelope.tag)
                body = survey.payload(row["body"].encode(), survey.parser(self.root))
                self.assertTrue(schema.validate(body), str(schema.error_log))
                self.assertEqual(f"{{{ns}}}sayHi" + ("Response" if row["direction"] == "response" else ""), body.tag)
                if row["direction"] == "response":
                    self.assertEqual("Hello, world!", body.find(f"{{{ns}}}responseType").text)

    def test_corrected_attribute_extension_keeps_original_source_and_values(self):
        extracted = corpus.extract(self.root / "derivative-source")
        metadata = corpus.read_manifest(ROOT / "derivatives/manifest.json")
        ns = "{http://www.w3.org/2002/ws/databinding/examples/6/09/}"
        name = "ComplexTypeAttributeExtension"
        wsdl = extracted / name / f"echo{name}.wsdl"
        document = etree.parse(str(wsdl))
        schema_node = document.find(f"{{{coverage.contract.WSDL}}}types/{{{coverage.contract.XSD}}}schema")
        # Materialize inherited WSDL namespace declarations on the standalone schema.
        schema = etree.XMLSchema(etree.fromstring(etree.tostring(schema_node)))
        messages, inputs = [], {}
        self.assertEqual(2, len(metadata["files"]))
        for entry in metadata["files"]:
            original = (extracted / entry["source"]).read_bytes()
            corpus.check_digest(original, entry["source_sha256"], entry["source"])
            corrected = (ROOT / "derivatives" / entry["derivative"]).read_bytes()
            corpus.check_digest(corrected, entry["sha256"], entry["derivative"])
            expected = original
            for change in entry["changes"]:
                self.assertEqual(1, expected.count(change["old"].encode()))
                expected = expected.replace(change["old"].encode(), change["new"].encode())
            self.assertEqual(expected, corrected)
            self.assertFalse(schema.validate(survey.payload(original, survey.parser(extracted))))
            payload = survey.payload(corrected, survey.parser(extracted))
            self.assertTrue(schema.validate(payload), str(schema.error_log))
            inputs[entry["derivative"]] = etree.tostring(payload)
            for direction in ("request", "response"):
                messages.append({"file": entry["derivative"], "direction": direction,
                    "path": str(ROOT / "derivatives" / entry["derivative"])})
        rows = survey.run_worker([{"name": "CorrectedAttributeExtension", "wsdl": str(wsdl),
            "operation": "echo" + name, "binding": "SoapBinding", "base": survey.SOURCE + name + "/",
            "messages": messages}], {})
        outputs = {}
        for row in rows:
            self.assertTrue(row["ok"], row)
            if row["stage"] == "serialize":
                payload = survey.payload(row["body"].encode(), survey.parser(extracted))
                self.assertTrue(schema.validate(payload), str(schema.error_log))
                owner = payload.find(ns + "complexTypeAttributeExtension")
                self.assertEqual("female", owner.get("gender"))
                self.assertEqual("Mary", owner.find(ns + "name").text)
                self.assertIsNone(owner.find(ns + "name").get("gender"))
                outputs[row["file"] + "/" + row["direction"]] = etree.tostring(payload)
        self.assertEqual(4, len(outputs))
        oracle = run_independent([SchemaJob("corrected", survey.SOURCE + name + f"/echo{name}.wsdl",
            etree.tostring(schema_node), inputs | outputs)], {})
        self.assertTrue(all(row["ok"] for row in oracle["documents"].values()), oracle)
        self.assertEqual(6, len(oracle["documents"]))

    def test_simple_content_independent_bindings_and_facets(self):
        fixture = ROOT / "regressions/simple-content"
        manifest = corpus.read_manifest(fixture / "manifest.json")
        for name, digest in manifest["files"].items():
            corpus.check_digest((fixture / name).read_bytes(), digest, name)
        wsdl = fixture / "measurement.wsdl"
        document = etree.parse(str(wsdl))
        schema_xml = etree.tostring(document.find(
            f"{{{coverage.contract.WSDL}}}types/{{{coverage.contract.XSD}}}schema"))
        schema = etree.XMLSchema(etree.fromstring(schema_xml))
        cases, documents, expected = [], {}, {}
        for version in ("11", "12"):
            messages = []
            for direction in ("request", "response"):
                name = f"{direction}-soap{version}.xml"
                path = fixture / name
                node = survey.payload(path.read_bytes(), survey.parser(fixture))
                self.assertTrue(schema.validate(node), str(schema.error_log))
                documents[name] = etree.tostring(node)
                expected[name] = True
                messages.append({"file": name, "path": str(path), "direction": direction})
                for mutation in ("below", "above", "missing", "prohibited", "child"):
                    envelope = etree.parse(str(path))
                    body = envelope.find("{*}Body")[0]
                    if mutation in ("below", "above"):
                        body.text = "0" if mutation == "below" else "4"
                    elif mutation == "missing":
                        del body.attrib["unit"]
                    elif mutation == "prohibited":
                        body.set("note", "forbidden")
                    else:
                        etree.SubElement(body, "unexpected").text = "content"
                    invalid_name = name + "/" + mutation
                    invalid_path = self.root / (name + "-" + mutation)
                    invalid_path.write_bytes(etree.tostring(envelope))
                    self.assertFalse(schema.validate(body), invalid_name)
                    documents[invalid_name] = etree.tostring(body)
                    expected[invalid_name] = False
                    messages.append({"file": invalid_name, "path": str(invalid_path), "direction": direction})
            cases.append({"name": "Measurement" + version, "wsdl": str(wsdl), "base": "http://fixture.invalid/",
                "operation": "submit", "binding": "Soap" + version, "messages": messages})
        rows = survey.run_worker(cases, {})
        self.assertEqual(4, survey.stage_accounting(cases, rows)["counts"]["serialize"]["ok"])
        envelope_versions = []
        for row in rows:
            if row["stage"] == "parse":
                self.assertTrue(row["ok"], row)
            elif not expected[row["file"]]:
                self.assertEqual("deserialize", row["stage"])
                self.assertFalse(row["ok"], row)
                self.assertEqual("SOAP-DESERIALIZATION-ERROR", row["err"])
            else:
                self.assertTrue(row["ok"], row)
                if row["stage"] == "serialize":
                    envelope = etree.fromstring(row["body"].encode())
                    version = row["case"][-2:]
                    envelope_versions.append((row["file"], version, envelope.tag))
                    node = survey.payload(row["body"].encode(), survey.parser(fixture))
                    response = row["direction"] == "response"
                    self.assertEqual("{urn:qore:measurement}" + ("MeasurementReply" if response else "SubmitMeasurement"), node.tag)
                    self.assertEqual("3" if response else "2", node.text)
                    self.assertEqual({"unit": "cm", "flag": "true" if response else "false"}, dict(node.attrib))
                    self.assertTrue(schema.validate(node), str(schema.error_log))
                    name = row["file"] + "/output"
                    documents[name], expected[name] = etree.tostring(node), True
        oracle = run_independent([SchemaJob("measurement", "http://fixture.invalid/measurement.wsdl",
            schema_xml, documents)], {})
        self.assertEqual(28, len(oracle["documents"]))
        for name, valid in expected.items():
            self.assertEqual(valid, oracle["documents"][name]["ok"], name)
        # Check every P2 payload before reporting the separately tracked P6 binding-version defect.
        for file, version, tag in envelope_versions:
            with self.subTest(file=file, requirement="P6-selected-binding-version"):
                self.assertEqual(f"{{{survey.SOAP_NAMESPACES[int(version == '12')]}}}Envelope", tag)

    def test_full_strict_gate_keeps_later_failures_visible(self):
        path = corpus.extract(self.root / "complete")
        output = self.root / "coverage.json"
        process = subprocess.run([sys.executable, str(ROOT / "coverage.py"), str(path), "--strict", "--output",
                                  str(output)], text=True, capture_output=True, timeout=60, check=True)
        self.assertEqual("", process.stderr)
        report = json.loads(output.read_text())
        self.assertEqual([], report["selected_failures"])
        self.assertEqual({"wsdls": 88, "message_directions": 752}, report["selected_scope"])
        self.assertEqual(293, len(report["cases"]))
        self.assertEqual(2272, sum(len(c["messages"]) for c in report["cases"]))
        for stage, counts in report["stage_accounting"]["counts"].items():
            self.assertEqual(293 if stage == "parse" else 2272, sum(counts.values()))
            self.assertEqual(0, counts["missing"])
            self.assertEqual(0, counts["skipped"])
        # Harness assertions verify retained failures, not conformance passes for broken functionality.
        self.assertGreater(len(report["failures"]), 0)
        by_name = {c["case"]: c for c in report["cases"]}
        for name in ("NegativeIntegerElement", "NonNegativeIntegerElement", "DecimalAttribute",
                     "DecimalElement", "DecimalSimpleTypePattern", "IntSimpleTypePattern",
                     "IntegerSimpleTypePattern", "LongSimpleTypePattern", "ShortSimpleTypePattern",
                     "NonNegativeIntegerSimpleTypePattern", "PositiveIntegerSimpleTypePattern",
                     "UnsignedIntSimpleTypePattern", "UnsignedLongSimpleTypePattern", "UnsignedShortSimpleTypePattern"):
            for message in by_name[name]["messages"]:
                self.assertEqual([], message["failures"], message)
                self.assertTrue(message["values"]["ok"], message)
            # IntegerSimpleTypePattern already passed the original corpus and retains its P9 coverage ownership.
            self.assertEqual("P9" if name == "IntegerSimpleTypePattern" else "P3",
                             by_name[name]["implementation_phase"])
        self.assertTrue(by_name["ImportSchema"]["parse_requirement_passed"])
        self.assertEqual("PARSE-XML-EXCEPTION", by_name["ImportSchema"]["expected_parse"])
        self.assertEqual("WSDL-ERROR", by_name["BlockDefault"]["expected_parse"])
        invalid = [m for m in by_name["GlobalAttribute"]["messages"] if m["source_valid"] is False]
        # A global attribute must be qualified; reject the source-invalid unqualified payloads.
        self.assertTrue(invalid)
        for message in invalid:
            self.assertTrue(message["rejection_passed"], message)
            self.assertEqual("SOAP-DESERIALIZATION-ERROR", message["deserialize"]["err"])
            self.assertEqual([], message["failures"])
        disagreements = [m["output_oracle_disagreement"] for c in report["cases"] for m in c["messages"]
                         if "output_oracle_disagreement" in m]
        # Eight formerly rounded/exponential decimal outputs now preserve their exact values;
        # Xerces accepts them while the retained libxml2 precision limitation remains visible.
        self.assertEqual(72, len(disagreements))
        self.assertTrue(all(d["adjudicated"] for d in disagreements))


if __name__ == "__main__":
    unittest.main()
