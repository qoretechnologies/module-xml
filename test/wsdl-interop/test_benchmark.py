#!/usr/bin/env python3
"""P9b benchmark gate: pinned workloads, byte-identical outputs and the comparison rules.

Copyright (C) 2026 Qore Technologies, s.r.o.

Performance itself is measured with benchmark/benchmark.py on a Release build; this gate makes no timing assertions.
It checks that the workloads are the pinned ones, that the current code produces the reference outputs for every
binding style and for one list-values item per value model, SOAP version and provider kind, and that the benchmark
reports regressions and output changes as it should.
"""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import unittest.mock

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
sys.path.insert(0, str(ROOT / "benchmark"))
import benchmark  # noqa: E402

# one item for each value model (atomic, record, repeated), SOAP version and element or message provider
ITEMS = [f"float-minInclusive/{model}/{version}/{kind}" for model in ("atomic", "record", "repeated")
         for version in ("11", "12") for kind in ("element", "message")]


class BenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads(benchmark.REFERENCE.read_text())
        cls.build = REPO / "build-debug"

    def test_pinned_workloads(self):
        for name, path in benchmark.WORKLOADS.items():
            self.assertEqual(self.reference["workloads"][name]["input_sha256"], benchmark.sha256(path), name)
        with tempfile.TemporaryDirectory(prefix="xml-benchmark-test-") as temp:
            directory = benchmark.unpack(benchmark.WORKLOADS["list-values"], temp)
            manifest = json.loads((directory / "manifest.json").read_text())
            self.assertEqual(384, len(manifest))
            self.assertEqual(len(manifest), len({row["name"] for row in manifest}))
            for row in manifest:
                self.assertTrue((directory / row["wsdl"]).is_file(), row["wsdl"])
            self.assertEqual(set(self.reference["workloads"]["list-values"]["items"]),
                             {row["name"] for row in manifest})

    def test_binding_style_outputs_match_the_reference(self):
        result = benchmark.run_driver("binding-styles", benchmark.WORKLOADS["binding-styles"], self.build, (1,))
        expected = self.reference["workloads"]["binding-styles"]
        self.assertEqual(expected["items"], result["items"])
        self.assertEqual(expected["digest"], result["digest"])
        self.assertEqual(expected["rows"], result["rows"])
        self.assertEqual(sorted(expected["phases"]), sorted(result["phases"]))

    def test_selects_the_requested_wsdl_source(self):
        # the driver loads the WSDL source beside it by an explicit path, which QORE_MODULE_DIR cannot change; a
        # comparison must load the requested source, and every run reports and checks the one it loaded
        workload = benchmark.WORKLOADS["binding-styles"]
        result = benchmark.run_driver("binding-styles", workload, self.build, (1,))
        self.assertEqual((REPO / "qlib" / "WSDL.qm").resolve(), Path(result["wsdl_module"]).resolve())
        with tempfile.TemporaryDirectory(prefix="xml-benchmark-source-") as temp:
            # a distinct copy of the source, so that the loaded file is identified by its location
            source = Path(temp) / "WSDL.qm"
            source.write_text((REPO / "qlib" / "WSDL.qm").read_text() + "\n# benchmark source selection test\n")
            result = benchmark.run_driver("binding-styles", workload, self.build, (1,), wsdl_dir=temp)
            self.assertEqual(source.resolve(), Path(result["wsdl_module"]).resolve())
            self.assertEqual(self.reference["workloads"]["binding-styles"]["digest"], result["digest"])
        with tempfile.TemporaryDirectory(prefix="xml-benchmark-source-") as temp:
            with self.assertRaisesRegex(RuntimeError, "no WSDL.qm"):
                benchmark.run_driver("binding-styles", workload, self.build, (1,), wsdl_dir=temp)
        # a reference always measures the checkout's own source
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            self.assertEqual(2, benchmark.main(["--build", str(self.build), "--allow-debug", "--record", "--wsdl-dir",
                                                str(REPO / "qlib")]))
        self.assertIn("--wsdl-dir is for comparisons only", errors.getvalue())

    def test_list_value_outputs_match_the_reference(self):
        expected = self.reference["workloads"]["list-values"]["items"]
        with tempfile.TemporaryDirectory(prefix="xml-benchmark-test-") as temp:
            directory = benchmark.unpack(benchmark.WORKLOADS["list-values"], temp)
            result = benchmark.run_driver("list-values", directory, self.build, ITEMS)
        self.assertEqual({name: expected[name] for name in ITEMS}, result["items"])
        self.assertEqual(sorted(self.reference["workloads"]["list-values"]["phases"]), sorted(result["phases"]))

    def test_comparison(self):
        reference = {"digest": "d", "items": {"a": "1", "b": "2"},
                     "phases": {"construction": 1000, "serialization": 2000, "sample": 100}}
        # within the tolerance
        failures, findings, improvements = benchmark.compare(reference, dict(reference, phases={
            "construction": 1200, "serialization": 1900, "sample": 100}), 0.25)
        self.assertEqual(([], [], []), (failures, findings, improvements))
        # a slower phase is a finding, a much faster one an improvement
        failures, findings, improvements = benchmark.compare(reference, dict(reference, phases={
            "construction": 1300, "serialization": 1000, "sample": 100}), 0.25)
        self.assertEqual([], failures)
        self.assertEqual([("construction", 1000, 1300, 1.3)], findings)
        self.assertEqual([("serialization", 2000, 1000, 0.5)], improvements)
        # changed output is a failure naming the items, whatever the times
        failures, _, _ = benchmark.compare(reference, dict(reference, digest="x", items={"a": "1", "b": "3"}), 0.25)
        self.assertEqual(1, len(failures))
        self.assertIn("1 item(s): b", failures[0])
        # a phase missing on either side is a failure
        failures, _, _ = benchmark.compare(reference, dict(reference, phases={"construction": 1000}), 0.25)
        self.assertEqual(2, len(failures))

    def test_busy_recording(self):
        # the load of each workload is taken when it finishes; a recording needs every one on a quiet machine
        quiet, loaded = (os.cpu_count() or 1) / 4, (os.cpu_count() or 1) / 4 + 0.01
        self.assertIsNone(benchmark.busy(quiet))
        self.assertEqual(loaded, benchmark.busy(loaded))
        self.assertEqual([], benchmark.busy_workloads({"a": {"load_average": quiet}, "b": {}}))
        self.assertEqual(["a", "c"], benchmark.busy_workloads({"c": {"load_average": loaded}, "b": {"load_average": 0},
                                                               "a": {"load_average": loaded + 10}}))
        # a busy period during a run shows in the 5-minute average after the 1-minute one has fallen
        with unittest.mock.patch("os.getloadavg", return_value=(quiet, loaded, quiet)):
            self.assertEqual(loaded, benchmark.current_load())
            self.assertEqual(loaded, benchmark.busy())
        with unittest.mock.patch("os.getloadavg", return_value=(loaded, quiet, quiet)):
            self.assertEqual(loaded, benchmark.busy())
        with unittest.mock.patch("os.getloadavg", return_value=(quiet, quiet, loaded + 10)):
            self.assertIsNone(benchmark.busy())

    def test_requires_a_release_build(self):
        self.assertEqual("Debug", benchmark.build_type(REPO / "build-debug"))
        self.assertEqual(2, benchmark.main(["--build", str(REPO / "build-debug")]))
        self.assertEqual(2, benchmark.main(["--build", str(REPO / "build-debug"), "--allow-debug", "--record"]))


if __name__ == "__main__":
    unittest.main()
