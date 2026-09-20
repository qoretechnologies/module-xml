#!/usr/bin/env python3
"""Tests for the offline survey and fixture provenance.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""

import hashlib
import json
import os
from copy import deepcopy
from pathlib import Path
import subprocess
import selectors
import sys
import tempfile
import unittest
from unittest.mock import patch

from lxml import etree

import survey
from test_attribute_values import description, NS
from test_compositor_context import schema


ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "w3c"


class SurveyTest(unittest.TestCase):
    def test_inventory_and_provenance(self):
        cases = survey.inventory(FIXTURES, "both")
        self.assertEqual(8, len(cases))
        self.assertEqual(64, sum(len(c["messages"]) for c in cases))
        cases11 = survey.inventory(FIXTURES, "11")
        cases12 = survey.inventory(FIXTURES, "12")
        self.assertEqual(32, sum(len(c["messages"]) for c in cases11))
        self.assertEqual(32, sum(len(c["messages"]) for c in cases12))
        for item in json.loads((FIXTURES / "manifest.json").read_text()):
            self.assertEqual(item["sha256"], hashlib.sha256((FIXTURES / item["path"]).read_bytes()).hexdigest())

    def test_explicit_soap12_derivative(self):
        case = survey.inventory(FIXTURES, "both")[0]
        derived = case["soap12_binding"]
        original = Path(case["wsdl"]).read_bytes()
        old = 'xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"'
        new = 'xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap12/"'
        self.assertEqual(original.decode().replace(old, new), derived["xml"])
        self.assertEqual(hashlib.sha256(original).hexdigest(), derived["source_sha256"])
        self.assertEqual(hashlib.sha256(derived["xml"].encode()).hexdigest(), derived["sha256"])
        self.assertTrue(derived["name"].endswith("-soap12-binding.wsdl"))
        self.assertNotIn("xml", survey.binding_derivatives([case])[case["name"]])
        rows = survey.run_worker([case], {})
        for row in rows:
            if row["stage"] == "serialize":
                uri = "http://www.w3.org/2003/05/soap-envelope" if row["file"].endswith("-soap12.xml") else "http://schemas.xmlsoap.org/soap/envelope/"
                self.assertEqual("{" + uri + "}Envelope", etree.fromstring(row["body"].encode()).tag)
        for key in ("name", "xml", "source_sha256", "sha256", "transform"):
            for value in (None, "", " ", False):
                broken = deepcopy(case)
                broken["soap12_binding"][key] = value
                with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, "binding derivative"):
                    survey.validate_cases([broken])
        for digest in ("a" * 63, "z" * 64):
            broken = deepcopy(case)
            broken["soap12_binding"]["source_sha256"] = digest
            with self.assertRaisesRegex(ValueError, "binding derivative"):
                survey.validate_cases([broken])
        derived["xml"] += "modified"
        with self.assertRaisesRegex(ValueError, "binding derivative"):
            survey.run_worker([case], {})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.wsdl"
            path.write_text("<definitions/>")
            with self.assertRaisesRegex(ValueError, "pinned W3C"):
                survey.soap12_binding_derivative(path)

    def test_empty_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "no echo WSDL"):
                survey.inventory(Path(directory), "11")

    def test_payload_preserves_qname_context(self):
        schema = etree.XMLSchema(etree.fromstring(b'''
            <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
              <xs:element name="q" type="xs:QName"/>
            </xs:schema>'''))
        xml_parser = survey.parser(FIXTURES)
        for ns in survey.SOAP_NAMESPACES:
            wire = f'<s:Envelope xmlns:s="{ns}" xmlns:t="urn:example"><s:Body><q>t:value</q></s:Body></s:Envelope>'
            element = survey.payload(wire.encode(), xml_parser)
            self.assertEqual("urn:example", element.nsmap["t"])
            self.assertTrue(schema.validate(element))
            invalid = wire.replace(' xmlns:t="urn:example"', "")
            self.assertFalse(survey.validate(schema, invalid.encode(), xml_parser)["ok"])

    def test_invalid_envelopes(self):
        for wire in (b"<not-soap/>", b"<broken", b'''<s:Envelope
                     xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><a/><b/></s:Body></s:Envelope>'''):
            with self.assertRaises((ValueError, etree.XMLSyntaxError)):
                survey.payload(wire, survey.parser(FIXTURES))

    def test_offline_resolution(self):
        resolver = survey.CorpusResolver(FIXTURES)
        for url in ("https://example.invalid/schema.xsd", "file:///etc/passwd",
                    survey.SOURCE + "../outside.xsd", survey.SOURCE + "missing.xsd"):
            with self.assertRaises(OSError):
                resolver.resolve(url, None, None)
        self.assertIsNotNone(resolver.resolve(survey.SOURCE + "BooleanElement/echoBooleanElement.xsd", None, None))

    def test_oracle_disagreement_is_separate(self):
        cases = [c for c in survey.inventory(FIXTURES, "11") if c["name"] == "UnsignedShortElement"]
        original = FIXTURES / "UnsignedShortElement/echoUnsignedShortElement-UnsignedShortElement04-soap11.xml"
        wire = original.read_text().replace(">65535<", ">65536<")
        rows = [{"case": "UnsignedShortElement", "stage": "serialize", "ok": True,
                 "file": original.relative_to(FIXTURES).as_posix(), "body": wire}]
        report = survey.examine(FIXTURES, cases, rows)
        self.assertEqual(1, report["counts"]["valid_input_invalid_output"])
        self.assertTrue(report["rows"][0]["input_validation"]["ok"])
        self.assertFalse(report["rows"][0]["output_validation"]["ok"])
        self.assertIn("body", report["rows"][0])
        # A rejected source is still recorded separately, regardless of the validator's exact reason.
        self.assertEqual(4, len(report["inputs"]))

    def test_cli_with_real_qore(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            run = subprocess.run([sys.executable, str(ROOT / "survey.py"), str(FIXTURES),
                                  "--output", str(output), "--soap-version", "both"],
                                 text=True, capture_output=True, timeout=30, check=True)
            self.assertEqual("", run.stderr)
            result = json.loads(output.read_text())
            self.assertEqual(8, result["counts"]["parse_ok"])
            self.assertEqual(48, result["counts"]["serialize_ok"])
            self.assertEqual(0, result["counts"].get("valid_input_invalid_output", 0))
            self.assertEqual(16, result["counts"]["deserialize_failed"])
            rejected = [row for row in result["rows"] if row["stage"] == "deserialize" and not row["ok"]]
            expected = {f"Unsigned{size}{kind}/echoUnsigned{size}{kind}-Unsigned{size}{kind}{case}-soap{version}.xml"
                        for size in ("Short", "Int") for kind in ("Element", "Attribute")
                        for case in ("02", "03") for version in ("11", "12")}
            self.assertEqual(expected, {row["file"] for row in rejected})
            for row in rejected:
                self.assertEqual("SOAP-DESERIALIZATION-ERROR", row["err"], row)
                self.assertFalse(row["input_validation"]["ok"], row)
            self.assertEqual(80, len(result["source_sha256"]))
            self.assertEqual(False, result["scope"]["network"])
            self.assertIs(False, result["scope"]["preserve_types"])
            lossless = subprocess.run([sys.executable, str(ROOT / "survey.py"), str(FIXTURES),
                                      "--output", str(output), "--soap-version", "both", "--preserve-types"],
                                     text=True, capture_output=True, timeout=30, check=True)
            self.assertEqual("", lossless.stderr)
            typed = json.loads(output.read_text())
            self.assertIs(True, typed["scope"]["preserve_types"])
            self.assertEqual(result["rows"], typed["rows"])
            self.assertEqual(result["source_sha256"], typed["source_sha256"])

    def test_worker_type_projection_modes(self):
        source = f'''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:t="{NS}"
            targetNamespace="{NS}">
          <xs:simpleType name="Code"><xs:restriction base="xs:string">
            <xs:pattern value="[A-Z]+"/></xs:restriction></xs:simpleType>
          <xs:element name="Submit" type="xs:string"/><xs:element name="Reply" type="xs:string"/>
        </xs:schema>'''
        compiled = etree.XMLSchema(etree.fromstring(source.encode()))
        xsi = "http://www.w3.org/2001/XMLSchema-instance"
        cases = []
        with tempfile.TemporaryDirectory(prefix="wsdl-worker-types-") as temporary:
            root = Path(temporary)
            for version, namespace in zip(("11", "12"), survey.SOAP_NAMESPACES):
                wsdl = root / (version + ".wsdl")
                wsdl.write_text(description(version, source))
                messages = []
                for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                    for name, selected, text in (("valid", "Code", "ABC"),
                                                  ("facet", "Code", "123"),
                                                  ("unknown", "Missing", "ABC")):
                        key = version + "/" + direction + "/" + name
                        path = root / key.replace("/", "-")
                        wire = (f'<s:Envelope xmlns:s="{namespace}" xmlns:t="{NS}" xmlns:i="{xsi}">'
                                f'<s:Body><t:{wrapper} i:type="t:{selected}">{text}</t:{wrapper}>'
                                '</s:Body></s:Envelope>')
                        path.write_text(wire)
                        self.assertEqual(name == "valid", compiled.validate(
                            survey.payload(wire.encode(), survey.parser(root))))
                        messages.append({"file": key, "path": str(path), "direction": direction})
                cases.append({"name": "Types" + version, "wsdl": str(wsdl), "base": "http://example.invalid/",
                              "operation": "submit", "binding": "Soap" + version, "messages": messages})
            legacy = survey.run_worker(cases, {})
            self.assertEqual(legacy, survey.run_worker(cases, {}, preserve_types=False))
            for preserve, rows in ((False, legacy), (True, survey.run_worker(cases, {}, preserve_types=True))):
                counts = survey.stage_accounting(cases, rows)["counts"]
                self.assertEqual(4, counts["serialize"]["ok"])
                self.assertEqual(8, counts["deserialize"]["failed"])
                self.assertEqual(8, counts["serialize"]["unreachable"])
                for row in rows:
                    if row["stage"] == "parse":
                        self.assertTrue(row["ok"], row)
                    elif not row["file"].endswith("/valid"):
                        self.assertEqual("SOAP-DESERIALIZATION-ERROR", row["err"], row)
                    else:
                        self.assertTrue(row["ok"], row)
                        if row["stage"] == "serialize":
                            node = survey.payload(row["body"].encode(), survey.parser(root))
                            self.assertTrue(compiled.validate(node), str(compiled.error_log))
                            self.assertEqual("ABC", node.text)
                            selected = node.get(f"{{{xsi}}}type")
                            if preserve:
                                self.assertIsNotNone(selected)
                                prefix, local = selected.split(":")
                                self.assertEqual((NS, "Code"), (node.nsmap[prefix], local))
                            else:
                                self.assertIsNone(selected)
            for invalid in (None, 0, 1, "true", [], {}):
                with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, "preserve_types"):
                    survey.run_worker(cases, {}, preserve_types=invalid)
            manifest = root / "bad.json"
            manifest.write_text(json.dumps({"cases": [], "cache": {}, "preserve_types": "true"}))
            bad = subprocess.run(["qore", "-b", "--enable-debug", str(ROOT / "probe.qr"), str(manifest)],
                                 text=True, capture_output=True, timeout=30)
            self.assertNotEqual(0, bad.returncode)
            self.assertIn("INVALID-MANIFEST", bad.stderr)

    def test_worker_output_completeness(self):
        cases = [{"name": "A", "messages": [{"file": "A/one.xml"}, {"file": "A/two.xml"}]},
                 {"name": "B", "messages": [{"file": "B/one.xml"}]}]
        rows = [{"case": "A", "stage": "parse", "ok": True},
                {"case": "A", "file": "A/one.xml", "stage": "deserialize", "ok": True},
                {"case": "A", "file": "A/one.xml", "stage": "serialize", "ok": True, "body": "<a/>"},
                {"case": "A", "file": "A/two.xml", "stage": "deserialize", "ok": False,
                 "err": "SOAP-DESERIALIZATION-ERROR", "desc": "rejected input"},
                {"case": "B", "stage": "parse", "ok": False, "err": "WSDL-ERROR", "desc": "bad schema"}]
        survey.check_rows(cases, rows)
        variants = [rows[:-1], rows[:2] + rows[3:], rows + [rows[0]], rows[:1] + rows[2:], rows + [None]]
        for index, key, value in ((0, "case", "unknown"), (1, "file", "A/wrong.xml"), (0, "ok", 1),
                                  (2, "body", None), (3, "err", None), (0, "stage", "serialize")):
            invalid = deepcopy(rows)
            invalid[index][key] = value
            variants.append(invalid)
        for variant in variants:
            with self.subTest(rows=variant), self.assertRaises(RuntimeError):
                survey.check_rows(cases, variant)

    def test_worker_serialization_failure(self):
        cases = [{"name": "A", "messages": [{"file": "A/one.xml"}]}]
        rows = [{"case": "A", "stage": "parse", "ok": True},
                {"case": "A", "file": "A/one.xml", "stage": "deserialize", "ok": True},
                {"case": "A", "file": "A/one.xml", "stage": "serialize", "ok": False,
                 "err": "SOAP-SERIALIZATION-ERROR", "desc": "rejected value"}]
        survey.check_rows(cases, rows)
        with self.assertRaises(RuntimeError):
            survey.check_rows(cases, rows[:-1])

    def test_complete_stage_accounting(self):
        cases = [{"name": "A", "messages": [{"file": "a", "direction": "request"},
                   {"file": "a", "direction": "response"}]},
                 {"name": "B", "messages": [{"file": "b"}]}]
        rows = [{"case": "A", "stage": "parse", "ok": True},
                {"case": "A", "file": "a", "direction": "request", "stage": "deserialize", "ok": True},
                {"case": "A", "file": "a", "direction": "request", "stage": "serialize", "ok": False,
                 "err": "SOAP-SERIALIZATION-ERROR", "desc": "failure"},
                {"case": "A", "file": "a", "direction": "response", "stage": "deserialize", "ok": False,
                 "err": "SOAP-DESERIALIZATION-ERROR", "desc": "failure"},
                {"case": "B", "stage": "parse", "ok": False, "err": "WSDL-ERROR", "desc": "failure"}]
        result = survey.stage_accounting(cases, rows)
        self.assertEqual({"ok": 1, "failed": 1, "unreachable": 1, "missing": 0, "skipped": 0},
                         result["counts"]["deserialize"])
        self.assertEqual({"ok": 0, "failed": 1, "unreachable": 2, "missing": 0, "skipped": 0},
                         result["counts"]["serialize"])
        self.assertEqual(6, len(result["stages"]))
        for variant in (rows[:-1], rows + rows[:1], rows[:2] + rows[3:]):
            with self.assertRaises(RuntimeError):
                survey.stage_accounting(cases, variant)

    def test_worker_rejects_malformed_manifests(self):
        cases = survey.inventory(FIXTURES, "11")
        for key, value in (("name", ""), ("binding", None), ("operation", 42), ("messages", {}),
                           ("parse_only", True), ("schema_only", "true")):
            invalid = deepcopy(cases)
            invalid[0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                survey.validate_cases(invalid)
        invalid = deepcopy(cases)
        invalid[0]["messages"][0]["direction"] = "typo"
        for variant in ([], cases * 2, invalid):
            with self.assertRaises(ValueError):
                survey.validate_cases(variant)
        duplicate = deepcopy(cases)
        duplicate[0]["messages"].append(duplicate[0]["messages"][0])
        with self.assertRaisesRegex(ValueError, "duplicate worker message"):
            survey.validate_cases(duplicate)

    def test_worker_failure_cancellation_and_cleanup(self):
        cases = survey.inventory(FIXTURES, "11")
        for error in (KeyboardInterrupt(), subprocess.TimeoutExpired("qore", 60),
                      subprocess.CalledProcessError(1, "qore", "", "failure")):
            manifests = []

            def run(command, **kwargs):
                manifests.append(Path(command[-1]))
                self.assertTrue(manifests[0].is_file())
                self.assertTrue(kwargs["check"])
                self.assertEqual(60, kwargs["timeout"])
                raise error

            with patch.object(survey.subprocess, "run", side_effect=run), self.assertRaises(type(error)):
                survey.run_worker(cases, {})
            self.assertEqual(1, len(manifests))
            self.assertFalse(manifests[0].parent.exists())

    def test_worker_timeout_bounds_and_cleanup(self):
        cases = survey.inventory(FIXTURES, "11")
        for invalid in (0, -1, 3601, True, False, None, "180", 1.0, float("inf"), float("nan")):
            with self.subTest(invalid=invalid), patch.object(survey.subprocess, "run") as run:
                with self.assertRaises(ValueError):
                    survey.run_worker(cases, {}, worker_timeout=invalid)
                run.assert_not_called()
        for seconds in (1, 180, 3600):
            for error in (subprocess.TimeoutExpired("qore", seconds), KeyboardInterrupt()):
                manifests = []

                def run(command, **kwargs):
                    manifests.append(Path(command[-1]))
                    self.assertTrue(manifests[-1].is_file())
                    self.assertEqual(seconds, kwargs["timeout"])
                    self.assertTrue(kwargs["check"])
                    raise error

                with self.subTest(seconds=seconds, error=type(error).__name__):
                    with patch.object(survey.subprocess, "run", side_effect=run), self.assertRaises(type(error)):
                        survey.run_worker(cases, {}, worker_timeout=seconds)
                    self.assertEqual(1, len(manifests))
                    self.assertFalse(manifests[0].parent.exists())

    def test_worker_timeout_cli_validation(self):
        for script in ("survey.py", "coverage.py"):
            for value in ("0", "-1", "3601", "nan", "inf", "1.5", "invalid"):
                with self.subTest(script=script, value=value):
                    result = subprocess.run([sys.executable, "-B", str(ROOT / script), "absent-corpus",
                                             "--output", "unused.json", "--worker-timeout", value],
                                            text=True, capture_output=True, timeout=10)
                    self.assertEqual(2, result.returncode)
                    self.assertIn("--worker-timeout", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)

    def test_failed_worker_retains_diagnostics_and_cleanup(self):
        cases = survey.inventory(FIXTURES, "11")
        with tempfile.TemporaryDirectory(prefix="wsdl-failed-worker-") as directory:
            worker = Path(directory) / "worker"
            worker.write_text("#!/usr/bin/env python3\nimport sys\nprint(sys.argv[-1])\n"
                              "print('PARSE-ERROR: controlled worker failure', file=sys.stderr)\n"
                              "sys.exit(2)\n")
            worker.chmod(0o755)
            with self.assertRaises(subprocess.CalledProcessError) as caught:
                survey.run_worker(cases, {}, str(worker))
        self.assertEqual(2, caught.exception.returncode)
        self.assertIn("PARSE-ERROR: controlled worker failure", str(caught.exception))
        self.assertEqual("PARSE-ERROR: controlled worker failure\n", caught.exception.stderr)
        self.assertFalse(Path(caught.exception.output.strip()).parent.exists())
        long_error = survey.WorkerProcessError(2, "qore", "retained output", "X" * 5000)
        self.assertIn("truncated", str(long_error))
        self.assertLess(len(str(long_error)), 4300)
        self.assertEqual(5000, len(long_error.stderr))
        self.assertEqual("retained output", long_error.output)
        self.assertEqual(str(subprocess.CalledProcessError(2, "qore")),
                         str(survey.WorkerProcessError(2, "qore")))

    def test_cancelled_worker_is_terminated_and_reaped(self):
        cases = survey.inventory(FIXTURES, "11")
        processes, manifests = [], []
        base_process = subprocess.Popen
        test = self

        class InterruptedProcess(base_process):
            def __init__(self, command, **kwargs):
                manifests.append(Path(command[-1]))
                super().__init__(command, **kwargs)
                processes.append(self)

            def communicate(self, *args, **kwargs):
                # One readiness event with a bounded deadline; no polling or sleeps.
                with selectors.DefaultSelector() as ready:
                    ready.register(self.stdout, selectors.EVENT_READ)
                    test.assertTrue(ready.select(timeout=5), "child did not signal readiness")
                    test.assertEqual("ready\n", self.stdout.readline())
                raise KeyboardInterrupt()

        with tempfile.TemporaryDirectory(prefix="wsdl-cancel-child-") as directory:
            worker = Path(directory) / "worker"
            worker.write_text("#!/usr/bin/env python3\nimport signal\nprint('ready', flush=True)\nsignal.pause()\n")
            worker.chmod(0o755)
            with patch.object(survey.subprocess, "Popen", InterruptedProcess), self.assertRaises(KeyboardInterrupt):
                survey.run_worker(cases, {}, str(worker))
        self.assertEqual(1, len(processes))
        self.assertIsNotNone(processes[0].returncode)
        with self.assertRaises(ProcessLookupError):
            os.kill(processes[0].pid, 0)
        self.assertFalse(manifests[0].parent.exists())

    def test_explicit_binding_and_independent_directions(self):
        case = next(c for c in survey.inventory(FIXTURES, "both") if c["name"] == "BooleanElement")
        case["binding"] = "SoapBinding"
        case["messages"] = [dict(m, direction=d) for m in case["messages"] for d in ("request", "response")]
        rows = survey.run_worker([case], {})
        self.assertEqual(16, survey.stage_accounting([case], rows)["counts"]["serialize"]["ok"])
        report = survey.examine(FIXTURES, [case], rows, retain_bodies=True)
        self.assertEqual(16, report["counts"]["output_valid"])
        self.assertEqual(8, len(report["inputs"]))
        for row in report["rows"]:
            if row["stage"] == "serialize":
                self.assertIn("body", row)
                self.assertIn(row["direction"], ("request", "response"))
        case["binding"] = "not-a-binding"
        rows = survey.run_worker([case], {})
        self.assertEqual(1, len(rows))
        self.assertEqual("WSDL-BINDING-ERROR", rows[0]["err"])

    def test_worker_preserves_complete_repeated_sequence_order(self):
        source = schema('<xs:sequence minOccurs="2" maxOccurs="2">'
                        '<xs:element name="a" type="xs:string"/>'
                        '<xs:element name="b" type="xs:string"/></xs:sequence>')
        compiled = etree.XMLSchema(etree.fromstring(source.encode()))
        cases, expected = [], {}
        with tempfile.TemporaryDirectory(prefix="wsdl-worker-particles-") as directory:
            root = Path(directory)
            for version, namespace in zip(("11", "12"), survey.SOAP_NAMESPACES):
                path = root / (version + '.wsdl')
                path.write_text(description(version, source))
                messages = []
                for direction, wrapper in (("request", "Submit"), ("response", "Reply")):
                    for valid, word in ((True, 'abab'), (False, 'aabb'), (False, 'abba'), (False, 'aba')):
                        name = version + '/' + direction + '/' + word
                        content = ''.join(f'<{letter}>{index}</{letter}>' for index, letter in enumerate(word))
                        wire = (f'<s:Envelope xmlns:s="{namespace}" xmlns:t="{NS}"><s:Body>'
                                f'<t:{wrapper}>{content}</t:{wrapper}></s:Body></s:Envelope>')
                        payload = survey.payload(wire.encode(), survey.parser(root))
                        self.assertEqual(valid, compiled.validate(payload), name)
                        target = root / name.replace('/', '-')
                        target.write_text(wire)
                        messages.append({'file': name, 'path': str(target), 'direction': direction})
                        expected[name] = valid
                cases.append({'name': 'Pairs' + version, 'wsdl': str(path), 'base': 'http://example.invalid/',
                              'operation': 'submit', 'binding': 'Soap' + version, 'messages': messages})
            rows = survey.run_worker(cases, {})
        counts = survey.stage_accounting(cases, rows)['counts']
        self.assertEqual(4, counts['serialize']['ok'])
        self.assertEqual(12, counts['deserialize']['failed'])
        self.assertEqual(12, counts['serialize']['unreachable'])
        for row in rows:
            if row['stage'] == 'parse':
                self.assertTrue(row['ok'], row)
            elif not expected[row['file']]:
                self.assertFalse(row['ok'], row)
                self.assertEqual('SOAP-DESERIALIZATION-ERROR', row['err'])
            else:
                self.assertTrue(row['ok'], row)
                if row['stage'] == 'serialize':
                    payload = etree.fromstring(row['body'].encode()).find('{*}Body')[0]
                    self.assertTrue(compiled.validate(payload), str(compiled.error_log))
                    self.assertEqual(list('abab'), [child.tag for child in payload])
                    self.assertEqual(['0', '1', '2', '3'], [child.text for child in payload])


if __name__ == "__main__":
    unittest.main()
