#!/usr/bin/env python3
"""The sharded CI runner: deterministic balanced assignment, recorded outcomes and the completeness check.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import argparse
import io
import json
from pathlib import Path
import tempfile
import unittest

import ci_suite

NAMES = ["test_a", "test_b", "test_c", "test_d", "test_e"]
TIMINGS = {"test_a": 100.0, "test_b": 60.0, "test_c": 50.0, "test_d": 10.0}


class Samples:
    """Sample cases for the recording result; nested so that discovery does not run them."""

    class Sample(unittest.TestCase):
        def test_pass(self):
            self.assertEqual(2, 1 + 1)

        def test_fail(self):
            self.assertEqual(3, 1 + 1)

        def test_error(self):
            raise RuntimeError("broken")

        def test_skip(self):
            self.skipTest("not here")

        def test_subtest(self):
            for value in (1, 2):
                with self.subTest(value=value):
                    self.assertEqual(1, value)

        @unittest.expectedFailure
        def test_expected(self):
            self.assertEqual(3, 1 + 1)

        @unittest.expectedFailure
        def test_unexpected(self):
            self.assertEqual(2, 1 + 1)

        def test_cleanup(self):
            self.addCleanup(lambda: 1 / 0)

    class BrokenClass(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            raise RuntimeError("no fixture")

        def test_never_runs(self):
            self.fail("setUpClass failed")


def report(index, count, names, tests, discovered=None):
    return {"shard": index, "shards": count, "modules": names, "load_errors": [],
            "discovered": list(tests) if discovered is None else discovered,
            "tests": {test_id: {"outcome": outcome, "seconds": 1.0} for test_id, outcome in tests.items()},
            "module_seconds": {name: 1.0 for name in names}, "seconds": 1.0}


class AssignmentTest(unittest.TestCase):
    def test_balanced_and_deterministic(self):
        shards = ci_suite.assign(NAMES, 2, TIMINGS)
        # longest first on the least loaded shard: a (100) | b (60), e (the median, 55) on b's, c (50) on a's,
        # then d (10) on b's
        self.assertEqual([["test_a", "test_c"], ["test_b", "test_d", "test_e"]], shards)
        self.assertEqual(shards, ci_suite.assign(list(reversed(NAMES)), 2, dict(reversed(TIMINGS.items()))))
        self.assertEqual(sorted(NAMES), sorted(name for shard in shards for name in shard))

    def test_every_module_exactly_once(self):
        for count in range(1, 8):
            shards = ci_suite.assign(NAMES, count, TIMINGS)
            self.assertEqual(count, len(shards))
            self.assertEqual(sorted(NAMES), sorted(name for shard in shards for name in shard), count)

    def test_without_timings(self):
        # equal costs: placed by name, round robin
        self.assertEqual([["test_a", "test_c", "test_e"], ["test_b", "test_d"]], ci_suite.assign(NAMES, 2, {}))

    def test_invalid_counts(self):
        with self.assertRaises(ValueError):
            ci_suite.assign(NAMES, 0, TIMINGS)
        for text in ("0/2", "3/2", "1/0", "1", "a/b", "1/2/3", "-1/2"):
            with self.assertRaises(argparse.ArgumentTypeError, msg=text):
                ci_suite.parse_shard(text)
        self.assertEqual((2, 4), ci_suite.parse_shard("2/4"))

    def test_real_suite_assignment(self):
        names = ci_suite.modules()
        self.assertIn("test_ci_suite", names)
        timings = ci_suite.read_timings()
        shards = ci_suite.assign(names, 4, timings)
        self.assertEqual(sorted(names), sorted(name for shard in shards for name in shard))

    def test_timings_file(self):
        with tempfile.TemporaryDirectory(prefix="ci-suite-test-") as temp:
            path = Path(temp) / "timings.json"
            self.assertEqual({}, ci_suite.read_timings(path))
            path.write_text(json.dumps({"modules": {"test_a": 1.5}}))
            self.assertEqual({"test_a": 1.5}, ci_suite.read_timings(path))
            for bad in ({"modules": {"test_a": -1}}, {"modules": {"test_a": "1"}}, {"modules": [1]}, {}):
                path.write_text(json.dumps(bad))
                with self.assertRaises(ValueError, msg=bad):
                    ci_suite.read_timings(path)


class RecordingTest(unittest.TestCase):
    def test_outcomes(self):
        suite = unittest.TestSuite()
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(Samples.Sample))
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(Samples.BrokenClass))
        result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0,
                                         resultclass=ci_suite.RecordingResult).run(suite)
        prefix = f"{__name__}.Samples.Sample."
        outcomes = {test_id.removeprefix(prefix): entry["outcome"] for test_id, entry in result.records.items()}
        self.assertEqual({
            "test_pass": "passed",
            "test_fail": "failure",
            "test_error": "error",
            "test_skip": "skipped",
            "test_subtest": "failure",
            "test_expected": "expected failure",
            "test_unexpected": "unexpected success",
            "test_cleanup": "error",
            f"setUpClass ({__name__}.Samples.BrokenClass)": "error",
        }, outcomes)
        self.assertIn("value=2", result.records[prefix + "test_subtest"]["detail"])
        self.assertIn("ZeroDivisionError", result.records[prefix + "test_cleanup"]["detail"])
        self.assertGreaterEqual(result.records[prefix + "test_pass"]["seconds"], 0)

    def test_shard_problems(self):
        good = report(1, 1, ["test_a"], {"test_a.T.test_x": "passed"})
        self.assertEqual([], ci_suite.shard_problems(good))
        self.assertEqual(["test_a.T.test_x: skipped"],
                         ci_suite.shard_problems(report(1, 1, ["test_a"], {"test_a.T.test_x": "skipped"})))
        missing = report(1, 1, ["test_a"], {}, ["test_a.T.test_x"])
        self.assertEqual(["test_a.T.test_x: did not run"], ci_suite.shard_problems(missing))
        extra = report(1, 1, ["test_a"], {"test_a.T.test_x": "passed", "setUpClass (test_a.T)": "error"},
                       ["test_a.T.test_x"])
        self.assertEqual(["setUpClass (test_a.T): ran without being discovered"], ci_suite.shard_problems(extra))
        twice = report(1, 1, ["test_a"], {"test_a.T.test_x": "passed"}, ["test_a.T.test_x"] * 2)
        self.assertEqual(["test_a.T.test_x: discovered more than once"], ci_suite.shard_problems(twice))
        broken = dict(good, load_errors=["ImportError: lxml"])
        self.assertEqual(["load error: ImportError: lxml"], ci_suite.shard_problems(broken))


class VerifyTest(unittest.TestCase):
    NAMES = ["test_a", "test_b", "test_c"]
    IDS = ["test_a.T.test_1", "test_a.T.test_2", "test_b.T.test_1", "test_c.T.test_1"]
    TIMINGS = {"test_a": 30.0, "test_b": 20.0, "test_c": 15.0}

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="ci-suite-test-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        # test_a | test_b, test_c
        self.assertEqual([["test_a"], ["test_b", "test_c"]], ci_suite.assign(self.NAMES, 2, self.TIMINGS))

    def write(self, index, names, tests, **changes):
        data = dict(report(index, 2, names, tests), **changes)
        (self.directory / f"shard-{index}-of-2.json").write_text(json.dumps(data))

    def verify(self):
        return ci_suite.verify(self.directory, 2, self.TIMINGS, self.IDS, self.NAMES)

    def write_good(self):
        self.write(1, ["test_a"], {"test_a.T.test_1": "passed", "test_a.T.test_2": "passed"})
        self.write(2, ["test_b", "test_c"], {"test_b.T.test_1": "passed", "test_c.T.test_1": "passed"})

    def test_complete(self):
        self.write_good()
        problems, summary = self.verify()
        self.assertEqual([], problems)
        self.assertTrue(summary["passed"])
        self.assertEqual({"shards": 2, "tests": 4, "modules": 3}, {key: summary[key] for key in
                                                                   ("shards", "tests", "modules")})
        self.assertEqual({"test_a", "test_b", "test_c"}, set(summary["module_seconds"]))

    def test_missing_shard(self):
        self.write_good()
        (self.directory / "shard-2-of-2.json").unlink()
        problems, summary = self.verify()
        self.assertFalse(summary["passed"])
        self.assertEqual(["shard 2/2: no result", "test_b.T.test_1: no result", "test_c.T.test_1: no result"],
                         problems)

    def test_missing_test(self):
        # a test left out of both the discovery and the results of its shard is still expected
        self.write(1, ["test_a"], {"test_a.T.test_1": "passed"})
        self.write(2, ["test_b", "test_c"], {"test_b.T.test_1": "passed", "test_c.T.test_1": "passed"})
        self.assertEqual(["test_a.T.test_2: no result"], self.verify()[0])

    def test_failed_and_skipped(self):
        self.write(1, ["test_a"], {"test_a.T.test_1": "failure", "test_a.T.test_2": "skipped"})
        self.write(2, ["test_b", "test_c"], {"test_b.T.test_1": "passed", "test_c.T.test_1": "passed"})
        self.assertEqual(["shard 1/2: test_a.T.test_1: failure", "shard 1/2: test_a.T.test_2: skipped"],
                         self.verify()[0])

    def test_duplicate_and_unknown(self):
        self.write(1, ["test_a"], {"test_a.T.test_1": "passed", "test_a.T.test_2": "passed"})
        self.write(2, ["test_b", "test_c"], {"test_b.T.test_1": "passed", "test_c.T.test_1": "passed",
                                             "test_a.T.test_1": "passed", "test_c.T.test_9": "passed"})
        problems = self.verify()[0]
        self.assertIn("test_a.T.test_1: ran in shards 1 and 2", problems)
        self.assertIn("test_c.T.test_9: not in the suite", problems)

    def test_wrong_assignment(self):
        self.write(1, ["test_a", "test_b"], {"test_a.T.test_1": "passed", "test_a.T.test_2": "passed",
                                             "test_b.T.test_1": "passed"})
        self.write(2, ["test_c"], {"test_c.T.test_1": "passed"})
        problems = self.verify()[0]
        self.assertIn("shard 1/2: ran modules ['test_a', 'test_b'], expected ['test_a']", problems)
        self.assertIn("test_b.T.test_1: ran in shard 1, assigned to 2", problems)

    def test_mislabelled_shard(self):
        self.write_good()
        self.write(2, ["test_b", "test_c"], {"test_b.T.test_1": "passed", "test_c.T.test_1": "passed"},
                   shard=1)
        problems = self.verify()[0]
        self.assertIn("shard-2-of-2.json: records shard 1/2", problems)
        self.assertIn("test_b.T.test_1: no result", problems)

    def test_module_without_tests(self):
        self.write_good()
        problems = ci_suite.verify(self.directory, 2, self.TIMINGS, self.IDS, self.NAMES + ["test_d"])[0]
        self.assertIn("modules without tests: test_d", problems)

    def test_duplicate_discovery(self):
        self.write_good()
        problems = ci_suite.verify(self.directory, 2, self.TIMINGS, self.IDS + ["test_c.T.test_1"],
                                   self.NAMES)[0]
        self.assertEqual(["test_c.T.test_1: discovered more than once"], problems)


if __name__ == "__main__":
    unittest.main()
