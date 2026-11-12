#!/usr/bin/env python3
"""The CI runner: deterministic balanced assignment, parallel module processes, recorded outcomes and the
completeness check.

Copyright (C) 2026 Qore Technologies, s.r.o.
"""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import textwrap
import threading
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


# sample test modules for the parallel runner, written to a temporary directory; FIFO and PIDS name files there
SAMPLE_MODULES = {
    "test_good": """
        import unittest
        class T(unittest.TestCase):
            def test_one(self):
                print("output of test_good")
                self.assertTrue(isinstance(1, int))
            def test_two(self):
                self.assertEqual(4, 2 + 2)
        """,
    "test_bad": """
        import unittest
        class T(unittest.TestCase):
            def test_fails(self):
                self.assertEqual(5, 2 + 2)
            def test_passes(self):
                self.assertEqual(4, 2 + 2)
        """,
    # the second test kills its own process, as a crash in a native module would
    "test_crash": """
        import os, signal, unittest
        class T(unittest.TestCase):
            def test_a_first(self):
                self.assertEqual(4, 2 + 2)
            def test_b_crashes(self):
                os.kill(os.getpid(), signal.SIGSEGV)
            def test_c_never_runs(self):
                self.assertEqual(4, 2 + 2)
        """,
    # starts a child process, records its PID and never finishes
    "test_hang": """
        import os, subprocess, threading, unittest
        class T(unittest.TestCase):
            def test_hangs(self):
                child = subprocess.Popen(["sleep", "3600"])
                with open(os.environ["CI_SUITE_TEST_DIR"] + "/hang.pid", "w") as f:
                    f.write(str(child.pid))
                # tells a test that reads the FIFO that the module is running; blocks without a reader
                with open(os.environ["CI_SUITE_TEST_DIR"] + "/fifo", "w") as f:
                    f.write("started")
                threading.Event().wait()
        """,
    # passes, but leaves a process running
    "test_leftover": """
        import os, subprocess, unittest
        class T(unittest.TestCase):
            def test_leaves_a_process(self):
                child = subprocess.Popen(["sleep", "3600"])
                with open(os.environ["CI_SUITE_TEST_DIR"] + "/leftover.pid", "w") as f:
                    f.write(str(child.pid))
        """,
    "test_import_error": """
        raise ImportError("missing dependency")
        """,
    # each needs the other running at the same time: opening a FIFO blocks until both ends are open
    "test_writer": """
        import os, unittest
        class T(unittest.TestCase):
            def test_write(self):
                with open(os.environ["CI_SUITE_TEST_DIR"] + "/fifo", "w") as f:
                    f.write("ping")
        """,
    "test_reader": """
        import os, unittest
        class T(unittest.TestCase):
            def test_read(self):
                with open(os.environ["CI_SUITE_TEST_DIR"] + "/fifo") as f:
                    self.assertEqual("ping", f.read())
        """,
}


def gone(pid):
    """True if a process does not exist or is a zombie."""
    try:
        with open(f"/proc/{pid}/stat") as stat:
            return stat.read().rsplit(")", 1)[1].split()[0] == "Z"
    except FileNotFoundError:
        return True


@unittest.skipUnless(sys.platform.startswith("linux"), "the process checks read /proc")
class ParallelRunnerTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="ci-suite-parallel-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.modules = self.directory / "modules"
        self.modules.mkdir()
        for name, source in SAMPLE_MODULES.items():
            (self.modules / f"{name}.py").write_text(textwrap.dedent(source))
        self.output = self.directory / "output"
        os.mkfifo(self.directory / "fifo")
        os.environ["CI_SUITE_TEST_DIR"] = str(self.directory)
        self.addCleanup(os.environ.pop, "CI_SUITE_TEST_DIR", None)
        self.addCleanup(self.kill_recorded)

    def kill_recorded(self):
        for name in ("hang.pid", "leftover.pid"):
            path = self.directory / name
            if path.exists():
                try:
                    os.kill(int(path.read_text()), signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def runner(self, jobs, timeout=60):
        # runs ci_suite's module command with the sample modules first on the path
        code = ("import sys; sys.path[:0] = [sys.argv.pop(1), sys.argv.pop(1)]; import ci_suite; "
                "sys.exit(ci_suite.run_module(sys.argv[1], ci_suite.Path(sys.argv[2])))")
        command = [sys.executable, "-u", "-W", "error", "-c", code, str(self.modules), str(ci_suite.HERE)]
        self.stream = io.StringIO()
        return ci_suite.ModuleRunner(jobs, timeout, self.output / "logs", command, self.stream)

    def run_modules(self, names, jobs=4, timeout=60, runner=None):
        """Runs sample modules through run_shard; returns (status, report)."""
        sys.path.insert(0, str(self.modules))
        self.addCleanup(sys.path.remove, str(self.modules))
        runner = runner or self.runner(jobs, timeout)
        with contextlib.redirect_stdout(io.StringIO()):
            status = ci_suite.run_shard(1, 1, self.output, {}, runner=runner, names=sorted(names))
        report = json.loads((self.output / "shard-1-of-1.json").read_text())
        return status, report

    def outcomes(self, report):
        return {test_id: entry["outcome"] for test_id, entry in report["tests"].items()}

    def test_passing_modules(self):
        status, report = self.run_modules(["test_good", "test_reader", "test_writer"], jobs=3)
        self.assertEqual(0, status)
        self.assertEqual({"test_good.T.test_one": "passed", "test_good.T.test_two": "passed",
                          "test_reader.T.test_read": "passed", "test_writer.T.test_write": "passed"},
                         self.outcomes(report))
        self.assertEqual({"test_good": "ok", "test_reader": "ok", "test_writer": "ok"}, report["module_status"])
        self.assertEqual([], ci_suite.shard_problems(report))
        self.assertEqual(3, report["jobs"])
        self.assertEqual(["test_good", "test_reader", "test_writer"], sorted(report["module_wall_seconds"]))
        self.assertIn("output of test_good", (self.output / "logs" / "test_good.log").read_text())

    def test_modules_run_concurrently(self):
        # the reader and the writer block until both run, so they pass only when run at the same time
        status, report = self.run_modules(["test_reader", "test_writer"], jobs=2)
        self.assertEqual(0, status, report["module_status"])

    def test_one_job_runs_one_module_at_a_time(self):
        # with one job, the first of the FIFO pair blocks until its timeout, and both fail
        status, report = self.run_modules(["test_reader", "test_writer"], jobs=1, timeout=3)
        self.assertEqual(1, status)
        timed_out = [name for name, value in report["module_status"].items() if "timed out after 3 s" in value]
        self.assertTrue(timed_out, report["module_status"])

    def test_output_kept_together(self):
        self.run_modules(["test_good", "test_bad", "test_reader", "test_writer"], jobs=4)
        lines = self.stream.getvalue().splitlines()
        begins = [line for line in lines if line.startswith("===== begin ")]
        self.assertEqual(4, len(begins))
        # every module's output is between its own markers, with no other module's in between
        current = None
        for line in lines:
            if line.startswith("===== begin "):
                self.assertIsNone(current, line)
                current = line.removeprefix("===== begin ")
            elif line.startswith("===== end "):
                self.assertTrue(line.removeprefix("===== end ").startswith(current + ":"), line)
                current = None
        self.assertIsNone(current)
        good = self.stream.getvalue().index("===== begin test_good")
        self.assertLess(good, self.stream.getvalue().index("output of test_good"))

    def test_failing_test(self):
        status, report = self.run_modules(["test_bad", "test_good"])
        self.assertEqual(1, status)
        self.assertEqual("failure", report["tests"]["test_bad.T.test_fails"]["outcome"])
        self.assertIn("AssertionError", report["tests"]["test_bad.T.test_fails"]["detail"])
        self.assertEqual("passed", report["tests"]["test_bad.T.test_passes"]["outcome"])
        # a failing test is not a failed process
        self.assertEqual("ok", report["module_status"]["test_bad"])
        self.assertEqual(["test_bad.T.test_fails: failure"], ci_suite.shard_problems(report))

    def test_crashing_module(self):
        status, report = self.run_modules(["test_crash", "test_good"])
        self.assertEqual(1, status)
        self.assertEqual("was killed by SIGSEGV", report["module_status"]["test_crash"])
        tests = report["tests"]
        # the test that finished keeps its result; the one that ran and the one after fail with the reason
        self.assertEqual("passed", tests["test_crash.T.test_a_first"]["outcome"])
        self.assertEqual("error", tests["test_crash.T.test_b_crashes"]["outcome"])
        self.assertEqual("the process of module test_crash was killed by SIGSEGV while it ran",
                         tests["test_crash.T.test_b_crashes"]["detail"])
        self.assertEqual("the process of module test_crash was killed by SIGSEGV before it ran",
                         tests["test_crash.T.test_c_never_runs"]["detail"])
        self.assertEqual("ok", report["module_status"]["test_good"])
        problems = ci_suite.shard_problems(report)
        self.assertIn("test_crash: was killed by SIGSEGV", problems)
        self.assertIn("test_crash.T.test_b_crashes: error", problems)
        self.assertNotIn("test_crash.T.test_a_first: passed", problems)

    def test_hung_module_times_out(self):
        status, report = self.run_modules(["test_hang", "test_good"], timeout=3)
        self.assertEqual(1, status)
        self.assertEqual("timed out after 3 s and was killed", report["module_status"]["test_hang"])
        self.assertEqual("the process of module test_hang timed out after 3 s and was killed while it ran",
                         report["tests"]["test_hang.T.test_hangs"]["detail"])
        self.assertEqual("ok", report["module_status"]["test_good"])
        # the process the hung test started was killed with it
        self.assertTrue(gone(int((self.directory / "hang.pid").read_text())))

    def test_leftover_process_killed(self):
        status, report = self.run_modules(["test_leftover"])
        self.assertEqual(0, status)
        self.assertTrue(gone(int((self.directory / "leftover.pid").read_text())))
        self.assertIn("processes it left running were killed", self.stream.getvalue())

    def test_import_error(self):
        status, report = self.run_modules(["test_import_error", "test_good"])
        self.assertEqual(1, status)
        problems = ci_suite.shard_problems(report)
        self.assertTrue(any("missing dependency" in problem for problem in problems), problems)
        self.assertEqual("error", report["tests"]["unittest.loader._FailedTest.test_import_error"]["outcome"])

    def test_interrupt_stops_every_module(self):
        runner = self.runner(2, timeout=3600)
        def interrupt():
            # opening the FIFO returns once the hung module runs
            with open(self.directory / "fifo") as fifo:
                fifo.read()
            runner.interrupt()
        thread = threading.Thread(target=interrupt)
        thread.start()
        try:
            status, report = self.run_modules(["test_hang"], runner=runner)
        finally:
            thread.join()
        self.assertEqual(130, status)
        self.assertEqual("was killed by SIGTERM", report["module_status"]["test_hang"])
        self.assertEqual("the process of module test_hang was killed by SIGTERM while it ran",
                         report["tests"]["test_hang.T.test_hangs"]["detail"])
        self.assertTrue(gone(int((self.directory / "hang.pid").read_text())))
        # nothing starts after an interruption
        self.assertIsNone(runner.run_one("test_good", ["test_good.T.test_one"]))

    def test_sigterm_stops_the_command(self):
        # "ci_suite.py run" with the hung sample module as the whole suite; SIGTERM once the module runs
        code = textwrap.dedent("""
            import sys, types
            sys.path[:0] = [sys.argv[1], sys.argv[2]]
            sys.modules["oracle_versions"] = types.SimpleNamespace(check=lambda: None)
            import ci_suite
            ci_suite.modules = lambda: ["test_hang"]
            ci_suite.modules = lambda: ["test_hang", "test_good"]
            # test_good is shorter and starts after test_hang, which holds the only job
            open(sys.argv[3] + ".timings", "w").write('{"modules": {"test_hang": 2, "test_good": 1}}')
            ci_suite.TIMINGS = ci_suite.Path(sys.argv[3] + ".timings")
            sys.exit(ci_suite.main(["run", "--jobs", "1", "--output", sys.argv[3]]))
            """)
        environment = dict(os.environ, PYTHONPATH=str(self.modules))
        process = subprocess.Popen([sys.executable, "-W", "error", "-c", code, str(self.modules), str(ci_suite.HERE),
                                    str(self.output)], env=environment, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.PIPE, text=True)
        try:
            # opening the FIFO returns once the hung module runs
            with open(self.directory / "fifo") as fifo:
                fifo.read()
            # a repeated signal neither stops the stopping nor loses the report
            process.send_signal(signal.SIGTERM)
            process.send_signal(signal.SIGTERM)
            _, stderr = process.communicate(timeout=60)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
        self.assertEqual(130, process.returncode, stderr)
        self.assertIn("interrupted: the module processes were stopped", stderr)
        self.assertTrue(gone(int((self.directory / "hang.pid").read_text())))
        # the report is still written, and names the test that was running and the module that never started
        report = json.loads((self.output / "shard-1-of-1.json").read_text())
        self.assertEqual("the process of module test_hang was killed by SIGTERM while it ran",
                         report["tests"]["test_hang.T.test_hangs"]["detail"])
        self.assertEqual("did not run: the run was interrupted", report["module_status"]["test_good"])
        self.assertIn("test_good.T.test_one: did not run", ci_suite.shard_problems(report))

    def test_module_that_cannot_start(self):
        # a command that cannot be executed fails the module's tests with the reason, and the run goes on
        runner = ci_suite.ModuleRunner(2, 60, self.output / "logs", [str(self.directory / "missing-python")],
                                       io.StringIO())
        status, report = self.run_modules(["test_good"], runner=runner)
        self.assertEqual(1, status)
        self.assertTrue(report["module_status"]["test_good"].startswith("could not be run: FileNotFoundError"),
                        report["module_status"])
        self.assertEqual("error", report["tests"]["test_good.T.test_one"]["outcome"])
        self.assertIn("could not be run", report["tests"]["test_good.T.test_one"]["detail"])

    def test_unexpected_tests_fail(self):
        # a module process that reports other tests than the runner discovered fails the run
        result = ci_suite.module_result("test_x", ["test_x.T.test_1"],
                                        [{"event": "final", "discovered": ["test_x.T.test_2"], "load_errors": [],
                                          "records": {"test_x.T.test_2": {"outcome": "passed", "seconds": 1}}}],
                                        0, False, 60)
        self.assertEqual("ok", result["status"])
        self.assertEqual(["test_x.T.test_2"], result["discovered"])

        class Fixed:
            jobs = 1
            interrupted = False

            def run(self, names, expected, timings):
                return {"test_good": dict(result, seconds=1.0, returncode=0)}
        status, report = self.run_modules(["test_good"], runner=Fixed())
        self.assertEqual(1, status)
        problems = ci_suite.shard_problems(report)
        self.assertIn("test_good: its process discovered 1 tests, expected 2", problems)
        self.assertIn("test_good.T.test_one: did not run", problems)

    def test_module_result(self):
        events = [{"event": "discovered", "ids": ["m.T.a", "m.T.b"], "load_errors": []},
                  {"event": "start", "id": "m.T.a"}, {"event": "stop", "id": "m.T.a", "outcome": "passed",
                                                      "seconds": 2.0}]
        # an exit without the final event fails the tests that were not reported
        result = ci_suite.module_result("m", ["m.T.a", "m.T.b"], events, 3, False, 60)
        self.assertEqual("exited with status 3 without a result", result["status"])
        self.assertEqual("passed", result["records"]["m.T.a"]["outcome"])
        self.assertEqual("the process of module m exited with status 3 without a result before it ran",
                         result["records"]["m.T.b"]["detail"])
        final = {"event": "final", "discovered": ["m.T.a"], "load_errors": [],
                 "records": {"m.T.a": {"outcome": "passed", "seconds": 2.0}}}
        self.assertEqual("ok", ci_suite.module_result("m", ["m.T.a"], [final], 1, False, 60)["status"])
        self.assertEqual("exited with status 2",
                         ci_suite.module_result("m", ["m.T.a"], [final], 2, False, 60)["status"])
        # a partly written last line is ignored
        path = self.directory / "events"
        path.write_text(json.dumps(events[0]) + "\n" + '{"event": "sta')
        self.assertEqual([events[0]], ci_suite.read_events(path))
        self.assertEqual([], ci_suite.read_events(self.directory / "missing"))

    def test_invalid_runner_arguments(self):
        with self.assertRaises(ValueError):
            ci_suite.ModuleRunner(0, 60, self.output)
        with self.assertRaises(ValueError):
            ci_suite.ModuleRunner(1, 0, self.output)
        for text in ("0", "-1", "a", ""):
            with self.assertRaises(argparse.ArgumentTypeError, msg=text):
                ci_suite.positive(text)
        self.assertEqual(3, ci_suite.positive("3"))
        self.assertEqual("test_x", ci_suite.module_of("unittest.loader._FailedTest.test_x"))
        self.assertEqual("test_x", ci_suite.module_of("test_x.T.test_1"))


class ChangeRulesTest(unittest.TestCase):
    """The files the suite reads outside test/wsdl-interop are among the paths whose changes run it in a partial
    pipeline (.python-paths in .gitlab/ci/module-xml.yml)."""

    def paths(self):
        text = (ci_suite.HERE.parents[1] / ".gitlab" / "ci" / "module-xml.yml").read_text()
        block = re.search(r"(?m)^  python: &python-paths\n((?:    - .*\n)+)", text)
        self.assertIsNotNone(block, "no python-paths list in module-xml.yml")
        return [line.strip()[2:] for line in block.group(1).splitlines()]

    @staticmethod
    def pattern(glob):
        """The regular expression of a glob as GitLab matches it: File.fnmatch with FNM_PATHNAME, where "*" matches
        within a directory and "**/" any number of directories."""
        parts = re.split(r"(\*\*/|\*|\?)", glob)
        return re.compile("".join({"**/": "(?:[^/]+/)*", "*": "[^/]*", "?": "[^/]"}.get(part, re.escape(part))
                                  for part in parts))

    def covered(self, path):
        return any(self.pattern(glob).fullmatch(path) for glob in self.paths())

    def test_glob_matching(self):
        self.assertTrue(self.covered("qlib/SoapClientIo/SoapClientIo.qm"))
        self.assertTrue(self.covered("qlib/SoapClient.qm"))
        self.assertTrue(self.covered("test/wsdl-interop/ci_suite.py"))
        self.assertTrue(self.covered("src/xml-module.cpp"))
        self.assertTrue(self.covered("test/cmake/libxml2_uri_allocation.c"))
        self.assertFalse(self.covered("test/wsdl-interop"))
        self.assertFalse(self.covered("qlib/WebDavHandler/WebDavHandler.qm"))
        self.assertFalse(self.covered("test/webdav_FsWebDavHandler_litmus.qtest"))
        self.assertFalse(self.covered("README"))

    def test_ledger_test_files(self):
        named = set(re.findall(r"test/[A-Za-z0-9_.-]+\.qtest", (ci_suite.HERE / "assertion-ledger.json").read_text()))
        self.assertTrue(named)
        self.assertEqual([], sorted(path for path in named if not self.covered(path)))

    def test_named_test_files(self):
        # every file at the top of test/ that a Python file of the suite names, such as a qtest it runs
        test = ci_suite.HERE.parent
        named = set()
        for path in ci_suite.HERE.glob("*.py"):
            if path.name == "test_ci_suite.py":
                continue
            for literal in re.findall(r"""["']([A-Za-z0-9_.-]+\.[A-Za-z0-9]+)["']""", path.read_text()):
                if (test / literal).is_file():
                    named.add(f"test/{literal}")
        self.assertIn("test/xml-id-bindings.qtest", named)
        self.assertEqual([], sorted(path for path in named if not self.covered(path)))

    def test_files_read_outside_the_suite(self):
        repository = ci_suite.HERE.parents[1]
        for path in ("test/test.wsdl", "test/cmake/ieee_reference_cases.py", "docs/xml-serialization.doxygen.tmpl",
                     "qlib/WSDL.qm", "qlib/SoapHandler.qm", "qlib/XmlRpcHandler.qm"):
            self.assertTrue((repository / path).exists(), path)
            self.assertTrue(self.covered(path), path)


if __name__ == "__main__":
    unittest.main()
