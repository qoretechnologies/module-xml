#!/usr/bin/env python3
"""Strict Qore coverage, complete accounting, independent values and real binding tests.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

from copy import deepcopy
from collections import Counter
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
        self.assertIs(False, report["scope"]["preserve_types"])
        self.assertEqual([], report["selected_failures"])
        for case in report["cases"]:
            for message in case["messages"]:
                version = "12" if message["file"].endswith("-soap12.xml") else "11"
                self.assertEqual(version, message["binding_version_expected"])
                self.assertEqual(version == "12", message["binding_source"].endswith("-soap12-binding.wsdl"))
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

    def test_worker_timeout_propagates_without_changing_coverage(self):
        with patch.object(survey, "run_worker", wraps=survey.run_worker) as run:
            report = coverage.assess(self.root, self.source, self.selection, corpus.Catalog(), worker_timeout=180)
        self.assertEqual(180, run.call_args.kwargs["worker_timeout"])
        self.assertEqual([], report["selected_failures"])
        self.assertEqual(16, report["stage_accounting"]["counts"]["values"]["ok"])
        for invalid in (0, -1, 3601, True, "180", float("inf")):
            with self.subTest(invalid=invalid), patch.object(coverage, "prepare") as prepare:
                with self.assertRaises(ValueError):
                    coverage.assess(self.root, self.source, self.selection, corpus.Catalog(), worker_timeout=invalid)
                prepare.assert_not_called()

    def test_explicit_type_preservation_report(self):
        legacy = coverage.assess(self.root, self.source, self.selection, corpus.Catalog())
        typed = coverage.assess(self.root, self.source, self.selection, corpus.Catalog(), preserve_types=True)
        self.assertIs(False, legacy["scope"]["preserve_types"])
        self.assertIs(True, typed["scope"]["preserve_types"])
        for key in ("cases", "counts", "stage_accounting", "selected_scope", "source_report_sha256",
                    "selection_sha256", "catalog_sha256", "failures", "selected_failures"):
            self.assertEqual(legacy[key], typed[key], key)

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

    def test_qname_value_assertions_preserve_expanded_names_and_scope(self):
        for left_scope, left_text, right_scope, right_text, valid in (
                ({"p": "urn:catalog"}, " p:Name ", {"q": "urn:catalog"}, "q:Name", True),
                ({"p": "urn:catalog"}, "p:Name", {"p": "urn:other"}, "p:Name", False),
                ({"p": "urn:catalog"}, "p:Name", {"p": "urn:catalog"}, "p:Other", False),
                ({None: "urn:catalog"}, "Name", {"q": "urn:catalog"}, "q:Name", True),
                ({None: "urn:catalog"}, "Name", {}, "Name", False),
                ({None: ""}, "Name", {}, "Name", True),
                ({}, "xml:lang", {"xml": "http://www.w3.org/XML/1998/namespace"}, "xml:lang", True),
                ({"p": "urn:%63atalog"}, "p:Name", {"p": "urn:catalog"}, "p:Name", False),
                ({"p": "URN:catalog"}, "p:Name", {"p": "urn:catalog"}, "p:Name", False),
                ({}, "missing:Name", {}, "missing:Name", False),
                ({}, "a:b:c", {}, "a:b:c", False),
                ({}, "", {}, "", False),
                ({}, "0name", {}, "0name", False),
                ({}, "a\u00a0b", {}, "a\u00a0b", False)):
            for attribute in (False, True):
                with self.subTest(left=left_text, right=right_text, attribute=attribute, valid=valid):
                    left = etree.Element("{urn:record}value", nsmap=left_scope)
                    right = etree.Element("{urn:record}value", nsmap=right_scope)
                    assertion = {"elements": ["{urn:record}value"], "datatype": "QName"}
                    if attribute:
                        assertion["attribute"] = "category"
                        left.set("category", left_text)
                        right.set("category", right_text)
                    else:
                        left.text, right.text = left_text, right_text
                    self.assertEqual(valid, coverage.value_checks(left, right, [assertion])["ok"])
        left = etree.fromstring(b'<outer xmlns:p="urn:wrong"><value xmlns:p="urn:catalog">p:Name</value></outer>')
        right = etree.fromstring(b'<outer xmlns:q="urn:catalog"><value>q:Name</value></outer>')
        assertion = {"elements": ["outer", "value"], "datatype": "QName"}
        self.assertTrue(coverage.value_checks(left, right, [assertion])["ok"])
        right.append(etree.fromstring(b'<value xmlns:q="urn:catalog">q:Name</value>'))
        self.assertFalse(coverage.value_checks(left, right, [assertion])["ok"])
        _, records = coverage.prepare(self.root, self.source)
        name = next(iter(records["BooleanElement"]["messages"]))
        selection = {"format": 1, "cases": {"BooleanElement": {"messages": {name: [assertion]}}}}
        coverage.validate_selection(selection, records)

    def test_list_value_assertions_detect_item_and_order_changes(self):
        for item_type, before, after, valid in (
                ("string", " A\tB ", "A B", True),
                ("string", "A B", "B A", False),
                ("string", "A\u00a0B", "A B", False),
                ("string", "", " \t", True),
                ("string", "A", "A A", False),
                ("boolean", "1 0", "true false", True),
                ("boolean", "yes", "yes", False),
                ("integer", "01 +2", "1 2", True),
                ("integer", "18446744073709551616", "18446744073709551617", False),
                ("decimal", "1.00000000000000000001", "1.00000000000000000002", False),
                ("decimal", "1.0e0", "1", False),
                ("date", "2000-01-01Z 2000-01-02", "2000-01-01-00:00 2000-01-02", True),
                ("date", "2000-01-01Z 2000-01-02", "2000-01-01Z 2000-01-02Z", False),
                ("gDay", "---01 ---02", "---02 ---01", False),
                ("gYear", "0000", "0000", False)):
            with self.subTest(item_type=item_type, before=before, after=after):
                left, right = etree.Element("value"), etree.Element("value")
                left.text, right.text = before, after
                result = coverage.value_checks(left, right, [{"elements": ["value"], "datatype": "list",
                                                              "item_datatype": item_type}])
                self.assertEqual(valid, result["ok"], result)
        _, records = coverage.prepare(self.root, self.source)
        name = next(iter(records["BooleanElement"]["messages"]))
        for item_type in (None, "list", "union", "unknown"):
            selection = {"format": 1, "cases": {"BooleanElement": {"messages": {name: [
                {"elements": ["value"], "datatype": "list", "item_datatype": item_type}]}}}}
            with self.subTest(item_type=item_type), self.assertRaises(ValueError):
                coverage.validate_selection(selection, records)

    def test_duration_value_assertions_detect_precision_and_partial_order_loss(self):
        for before, after, valid in (('P1D', 'PT24H', True), ('P400Y', 'P146097D', True),
                ('-P2000Y', '-P730485D', True), ('P1M', 'P30D', False),
                ('PT1.00000000000000001S', 'PT1.00000000000000002S', False),
                ('PT0.' + '0' * 1000 + '1S', 'PT0S', False), ('PT.1S', 'PT0.1S', False)):
            with self.subTest(before=before, after=after):
                expected = etree.fromstring(('<value>' + before + '</value>').encode())
                actual = etree.fromstring(('<value>' + after + '</value>').encode())
                assertion = {'elements': ['value'], 'datatype': 'duration'}
                self.assertEqual(valid, coverage.value_checks(expected, actual, [assertion])['ok'])
                assertion = {'elements': ['value'], 'datatype': 'list', 'item_datatype': 'duration'}
                expected.text = before + ' P1D'
                actual.text = after + ' PT24H'
                self.assertEqual(valid, coverage.value_checks(expected, actual, [assertion])['ok'])

    def test_binary_value_assertions_detect_changed_octets_and_malformed_text(self):
        for datatype, before, after, valid in (
                ('hexBinary', '00fF', '00FF', True), ('hexBinary', '00ff', '00fe', False),
                ('hexBinary', '', '', True), ('hexBinary', '00', '', False),
                ('hexBinary', '0', '00', False), ('hexBinary', 'ff', 'gg', False),
                ('base64Binary', 'AA==', 'AA==', True), ('base64Binary', 'AA==', 'AQ==', False),
                ('base64Binary', 'AB==', 'AA==', False), ('base64Binary', 'AA==', 'AA===', False),
                ('base64Binary', '', '', True), ('base64Binary', 'AA==', '', False),
                ('base64Binary', 'AA==!', 'AA==', False), ('base64Binary', 'AA==\u00a0', 'AA==', False)):
            with self.subTest(datatype=datatype, before=before, after=after):
                for is_list in (False, True):
                    expected, actual = etree.Element('value'), etree.Element('value')
                    expected.text, actual.text = before, after
                    assertion = {'elements': ['value'], 'datatype': 'list' if is_list else datatype}
                    if is_list:
                        assertion['item_datatype'] = datatype
                    self.assertEqual(valid, coverage.value_checks(expected, actual, [assertion])['ok'])
        expected, actual = etree.Element('value'), etree.Element('value')
        expected.text, actual.text = ' A A = = ', 'AA=='
        self.assertTrue(coverage.value_checks(expected, actual,
                        [{'elements': ['value'], 'datatype': 'base64Binary'}])['ok'])
        _, records = coverage.prepare(self.root, self.source)
        name = next(iter(records['BooleanElement']['messages']))
        for datatype in ('hexBinary', 'base64Binary'):
            for assertion in ({'elements': ['value'], 'datatype': datatype},
                              {'elements': ['value'], 'datatype': 'list', 'item_datatype': datatype}):
                coverage.validate_selection({'format': 1, 'cases': {'BooleanElement': {'messages': {name: [assertion]}}}},
                                            records)

    def test_calendar_value_assertions_detect_timezone_and_year_loss(self):
        huge = '1' + '0' * 1000
        for datatype, before, after, valid in (
                ('date', '2002-10-10+13:00', '2002-10-09-11:00', True),
                ('date', '0001-01-01+14:00', '-0001-12-31-10:00', True),
                ('date', '2000-01-01', '2000-01-01Z', False),
                ('date', huge + '-01-01Z', huge + '-01-02Z', False),
                ('date', '2000-01-01+05:30', '2000-01-01+05:00', False),
                ('gYear', '-0001Z', '-0001-00:00', True),
                ('gYearMonth', '2000-02', '2000-03', False),
                ('gMonthDay', '--01-02+14:00', '--01-01-10:00', True),
                ('gMonth', '--06Z', '--06-00:00', True),
                ('gDay', '---02+14:00', '---01-10:00', True),
                ('gMonth', '--01--', '--01--', False),
                ('date', '-0001-02-29', '-0001-02-29', False)):
            with self.subTest(datatype=datatype, before=before[:30]):
                left, right = etree.Element('value'), etree.Element('value')
                left.text, right.text = before, after
                result = coverage.value_checks(left, right, [{'elements': ['value'], 'datatype': datatype}])
                self.assertEqual(valid, result['ok'], result)

    def test_temporal_value_assertions_detect_precision_timezone_and_leap_loss(self):
        _, records = coverage.prepare(self.root, self.source)
        file = next(iter(records['BooleanElement']['messages']))
        for datatype, before, after, valid in (
                ('dateTime', '2026-12-31T24:00:00Z', '2027-01-01T00:00:00Z', True),
                ('dateTime', '-0001-12-31T24:00:00Z', '0001-01-01T00:00:00Z', True),
                ('dateTime', '1998-12-31T23:59:60Z', '1998-12-31T22:59:60-01:00', True),
                ('dateTime', '1998-12-31T23:59:60Z', '1999-01-01T00:00:00Z', False),
                ('dateTime', '2026-01-01T12:00:00', '2026-01-01T12:00:00Z', False),
                ('time', '23:00:00-02:00', '01:00:00Z', True),
                ('time', '24:00:00', '00:00:00', True),
                ('time', '12:00:00.1234567890123456789Z', '12:00:00.123456789012345678900Z', True),
                ('time', '12:00:00.1234567890123456789Z', '12:00:00.1234567890123456790Z', False),
                ('time', '12:00:00', '12:00:00Z', False),
                ('time', '24:00:00.1Z', '24:00:00.1Z', False)):
            for listed in (False, True):
                with self.subTest(datatype=datatype, listed=listed, before=before):
                    assertion = {'elements': ['value'], 'datatype': 'list' if listed else datatype}
                    if listed:
                        assertion['item_datatype'] = datatype
                    coverage.validate_selection({'format': 1, 'cases': {
                        'BooleanElement': {'messages': {file: [assertion]}}}}, records)
                    left, right = etree.Element('value'), etree.Element('value')
                    left.text, right.text = before, after
                    result = coverage.value_checks(left, right, [assertion])
                    self.assertEqual(valid, result['ok'], result)

    def test_ieee_value_assertions_detect_precision_and_sign_changes(self):
        for datatype, before, after, valid in (
                ("float", "16777217", "16777216", True),
                ("double", "16777217", "16777216", False),
                ("float", "1.00000005960464477539062500000000001", "1.00000011920928955078125", True),
                ("float", "1.00000005960464477539062500000000001", "1", False),
                ("double", "1.00000000000000011102230246251565404236316680908203125001",
                 "1.0000000000000002", True),
                ("double", "1.00000000000000011102230246251565404236316680908203125001", "1", False),
                ("float", "3.5e38", "INF", True),
                ("double", "3.5e38", "INF", False),
                ("float", "-1e-999", "-0", True),
                ("double", "-0", "0", False),
                ("float", "NaN", "NaN", True),
                ("double", "NaN", "INF", False),
                ("double", "1.234567891234567", "1.23456789", False),
                ("float", "1e", "1", False),
                ("double", "+INF", "INF", False),
                ("float", "nan", "NaN", False),
                ("double", "1\u00a0", "1", False)):
            with self.subTest(datatype=datatype, before=before, after=after):
                for is_list in (False, True):
                    left, right = etree.Element("value"), etree.Element("value")
                    left.text, right.text = before, after
                    assertion = {"elements": ["value"], "datatype": "list" if is_list else datatype}
                    if is_list:
                        assertion["item_datatype"] = datatype
                    result = coverage.value_checks(left, right, [assertion])
                    self.assertEqual(valid, result["ok"], result)
        _, records = coverage.prepare(self.root, self.source)
        name = next(iter(records["BooleanElement"]["messages"]))
        for datatype in ("float", "double"):
            for assertion in ({"elements": ["value"], "datatype": datatype},
                              {"elements": ["value"], "datatype": "list", "item_datatype": datatype}):
                coverage.validate_selection({"format": 1, "cases": {"BooleanElement": {"messages": {name: [assertion]}}}},
                                            records)

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
                    "soap_version": "12" if "soap12" in entry["derivative"] else "11",
                    "path": str(ROOT / "derivatives" / entry["derivative"])})
        rows = survey.run_worker([{"name": "CorrectedAttributeExtension", "wsdl": str(wsdl),
            "operation": "echo" + name, "binding": "SoapBinding", "base": survey.SOURCE + name + "/",
            "soap12_binding": survey.soap12_binding_derivative(wsdl), "messages": messages}], {})
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
        # The complete gate also runs independent validators and typed comparisons.
        # Its outer deadline must allow the bounded worker to finish and report failures.
        process = subprocess.run([sys.executable, str(ROOT / "coverage.py"), str(path), "--strict", "--output",
                                  str(output), "--worker-timeout", "180"], text=True, capture_output=True,
                                 timeout=360, check=True)
        self.assertEqual("", process.stderr)
        report = json.loads(output.read_text())
        self.assertEqual([], report["selected_failures"])
        self.assertEqual({"wsdls": 144, "message_directions": 1388}, report["selected_scope"])
        self.assertEqual(293, len(report["cases"]))
        self.assertEqual(2272, sum(len(c["messages"]) for c in report["cases"]))
        for stage, counts in report["stage_accounting"]["counts"].items():
            self.assertEqual(293 if stage == "parse" else 2272, sum(counts.values()))
            self.assertEqual(0, counts["missing"])
            self.assertEqual(0, counts["skipped"])
        # Harness assertions verify retained failures, not conformance passes for broken functionality.
        self.assertGreater(len(report["failures"]), 0)
        by_name = {c["case"]: c for c in report["cases"]}
        substitutions = by_name["SubstitutionGroup"]["messages"]
        self.assertEqual(8, len(substitutions))
        for message in substitutions:
            self.assertTrue(message["source_valid"], message)
            self.assertEqual([], message["failures"], message)
            self.assertTrue(message["values"]["ok"], message)
            self.assertEqual("exact", message["values"]["assertions"][0]["order"])
        from test_particle_corpus import FAMILIES
        particle_messages = [message for name in FAMILIES for message in by_name[name]["messages"]]
        self.assertEqual(120, len(particle_messages))
        self.assertEqual(116, sum(message["source_valid"] for message in particle_messages))
        for message in particle_messages:
            self.assertEqual([], message["failures"], message)
            if message["source_valid"]:
                self.assertTrue(message["values"]["ok"], message)
                self.assertEqual("particle", message["values"]["assertions"][0]["datatype"])
            else:
                self.assertTrue(message["rejection_passed"], message)
                self.assertEqual("SOAP-DESERIALIZATION-ERROR", message["deserialize"]["err"])
        for name, count in (("DateTimeElement", 24), ("DateTimeAttribute", 24),
                            ("TimeElement", 20), ("TimeAttribute", 20)):
            self.assertEqual(count, len(by_name[name]["messages"]))
            for message in by_name[name]["messages"]:
                self.assertEqual([], message["failures"], message)
                self.assertTrue(message["values"]["ok"], message)
        for name in ("ENTITYElement", "ENTITYAttribute", "ENTITIESElement", "ENTITIESAttribute"):
            self.assertEqual(4, len(by_name[name]["messages"]))
            for message in by_name[name]["messages"]:
                self.assertFalse(message["source_valid"])
                self.assertEqual([], message["failures"], message)
                self.assertTrue(message["rejection_passed"], message)
                self.assertEqual("SOAP-DESERIALIZATION-ERROR", message["deserialize"]["err"])
                self.assertIsNone(message["serialize"])
        for name in ("QNameElement", "QNameAttribute"):
            for message in by_name[name]["messages"]:
                self.assertEqual([], message["failures"], message)
                self.assertTrue(message["values"]["ok"], message)
            self.assertEqual("P5", by_name[name]["implementation_phase"])
        for name in ("NegativeIntegerElement", "NonNegativeIntegerElement", "DecimalAttribute",
                     "DecimalElement", "DecimalSimpleTypePattern", "IntSimpleTypePattern",
                     "IntegerSimpleTypePattern", "LongSimpleTypePattern", "ShortSimpleTypePattern",
                     "NonNegativeIntegerSimpleTypePattern", "PositiveIntegerSimpleTypePattern",
                     "UnsignedIntSimpleTypePattern", "UnsignedLongSimpleTypePattern", "UnsignedShortSimpleTypePattern",
                     "FloatElement", "DoubleElement", "FloatAttribute", "DoubleAttribute",
                     "FloatSimpleTypePattern", "DoubleSimpleTypePattern", "FloatEnumerationType",
                     "DoubleEnumerationType"):
            for message in by_name[name]["messages"]:
                self.assertEqual([], message["failures"], message)
                self.assertTrue(message["values"]["ok"], message)
            # These families passed the original corpus and retain their P9 coverage ownership.
            baseline_passes = ("IntegerSimpleTypePattern", "FloatElement", "DoubleElement",
                               "FloatAttribute", "DoubleAttribute")
            self.assertEqual("P9" if name in baseline_passes else "P3",
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
        # Exact numeric outputs retain the adjudicated libxml2 precision limitation.
        # The former 16 IDREF disagreements disappeared when P5-17b began rejecting
        # those invalid inputs; the rejection assertions above cover them explicitly.
        families = Counter(c["case"] for c in report["cases"] for m in c["messages"]
                           if "output_oracle_disagreement" in m)
        self.assertEqual({"IntegerAttribute": 8, "IntegerElement": 8,
                          **{base + position: 4 for base in ("Decimal", "NegativeInteger",
                              "NonNegativeInteger", "NonPositiveInteger", "PositiveInteger")
                             for position in ("Attribute", "Element")}}, families)
        self.assertEqual(56, len(disagreements))
        self.assertTrue(all(d["adjudicated"] for d in disagreements))


if __name__ == "__main__":
    unittest.main()
