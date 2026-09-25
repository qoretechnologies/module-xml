#!/usr/bin/env python3
"""Sharded CI runner and completeness check for the Python WSDL/SOAP suite.

Copyright (C) 2026 Qore Technologies, s.r.o.

The suite takes longer than one CI job allows, so CI splits it by test module into shards that run as parallel
jobs, and a final job checks the combined result:

- ``run --shard I/N`` runs the test modules assigned to shard I of N and writes ``shard-I-of-N.json``, which
  records every test with its outcome and duration, the shard's modules and the environment;
- ``verify --shards N`` discovers the suite independently and fails unless every discovered test ran exactly
  once, in the shard it is assigned to, and passed. A missing shard, a missing, duplicate, unknown, skipped or
  failed test, or a module that cannot be imported fails the check, so none of them can improve the counts;
- ``timings`` writes the measured module durations to ``ci-timings.json``, which only balances the shards.

The assignment is deterministic: modules are placed longest first, by their recorded durations, on the shard
with the least total time. A module with no recorded duration counts as the median duration.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
import unittest

HERE = Path(__file__).resolve().parent
TIMINGS = HERE / "ci-timings.json"
PATTERN = "test_*.py"
# outcomes a passing test may have; anything else fails the shard and the verification
PASSED = "passed"


def modules():
    """Returns the names of all test modules, sorted."""
    return sorted(path.stem for path in HERE.glob(PATTERN))


def read_timings(path=TIMINGS):
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    timings = data.get("modules")
    if not isinstance(timings, dict) or not all(isinstance(value, (int, float)) and value >= 0
                                                for value in timings.values()):
        raise ValueError(f"{path}: malformed module timings")
    return timings


def assign(names, count, timings):
    """Returns a list of ``count`` sorted module lists, balanced by the recorded durations."""
    if count < 1:
        raise ValueError("the shard count must be positive")
    known = [timings[name] for name in names if name in timings]
    default = statistics.median(known) if known else 1.0
    cost = {name: timings.get(name, default) for name in names}
    shards = [[] for _ in range(count)]
    totals = [0.0] * count
    # longest first; ties by name, so the assignment does not depend on dictionary or file system order
    for name in sorted(names, key=lambda name: (-cost[name], name)):
        index = min(range(count), key=lambda index: (totals[index], index))
        shards[index].append(name)
        totals[index] += cost[name]
    return [sorted(shard) for shard in shards]


def parse_shard(text):
    try:
        index, count = (int(part) for part in text.split("/"))
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected I/N, got {text!r}") from None
    if count < 1 or not 1 <= index <= count:
        raise argparse.ArgumentTypeError(f"shard {text!r} is out of range")
    return index, count


def test_ids(suite):
    """Yields (id, test) for every test in a suite, including placeholders for modules that failed to load."""
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from test_ids(item)
        else:
            yield item.id(), item


def load(names):
    """Loads the named modules; returns (suite, load errors)."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for name in names:
        suite.addTests(loader.loadTestsFromName(name))
    # a module that cannot be imported becomes a failing placeholder test; its error is reported as such
    return suite, list(loader.errors)


def discover():
    """Returns the ids of all tests in the suite; fails if any module cannot be loaded."""
    suite, errors = load(modules())
    ids = [test_id for test_id, _ in test_ids(suite)]
    failed = [test_id for test_id in ids if test_id.startswith("unittest.loader._FailedTest.")]
    if errors or failed:
        raise RuntimeError("test modules failed to load: " + ", ".join(failed) + "\n" + "\n".join(errors))
    return ids


class RecordingResult(unittest.TextTestResult):
    """Records the outcome and duration of every test."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = {}
        self.started = {}

    def startTest(self, test):
        self.started[test.id()] = time.monotonic()
        super().startTest(test)

    def record(self, test, outcome, detail=None):
        test_id = test.id()
        entry = self.records.setdefault(test_id, {"outcome": PASSED, "seconds": 0.0})
        # a failing subtest or a cleanup error fails the whole test; the first failure is kept
        if outcome != PASSED and entry["outcome"] == PASSED:
            entry["outcome"] = outcome
            if detail:
                entry["detail"] = detail

    def stopTest(self, test):
        super().stopTest(test)
        test_id = test.id()
        self.record(test, PASSED)
        if test_id in self.started:
            self.records[test_id]["seconds"] = round(time.monotonic() - self.started.pop(test_id), 3)

    def addError(self, test, err):
        super().addError(test, err)
        self.record(test, "error", self._exc_info_to_string(err, test))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.record(test, "failure", self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.record(test, "skipped", reason)

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.record(test, "expected failure", self._exc_info_to_string(err, test))

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.record(test, "unexpected success")

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            outcome = "failure" if issubclass(err[0], test.failureException) else "error"
            self.record(test, outcome, f"{subtest.id()}: {self._exc_info_to_string(err, test)}")


def environment():
    def output(command):
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return (result.stdout + result.stderr).strip()
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "qore": output([os.environ.get("QORE", "qore"), "--version"]),
        "java": output(["java", "-version"]),
        "qore_module_dir": os.environ.get("QORE_MODULE_DIR"),
        "exec_mode": os.environ.get("QORE_EXEC_MODE", "jit"),
        "warnings": list(sys.warnoptions),
    }


def run_shard(index, count, output, timings):
    names = assign(modules(), count, timings)[index - 1]
    suite, errors = load(names)
    ids = [test_id for test_id, _ in test_ids(suite)]
    started = time.monotonic()
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2, resultclass=RecordingResult)
    result = runner.run(suite)
    seconds = time.monotonic() - started
    # module durations come from the tests in them, so balancing does not depend on the shard's other modules
    durations = {name: 0.0 for name in names}
    for test_id, entry in result.records.items():
        module = test_id.split(".", 1)[0]
        if module in durations:
            durations[module] = round(durations[module] + entry["seconds"], 3)
    report = {
        "shard": index,
        "shards": count,
        "modules": names,
        "discovered": ids,
        "load_errors": errors,
        "tests": result.records,
        "module_seconds": durations,
        "seconds": round(seconds, 3),
        "environment": environment(),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / f"shard-{index}-of-{count}.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    problems = shard_problems(report)
    for problem in problems:
        print(f"FAILED: {problem}")
    print(f"shard {index}/{count}: {len(names)} modules, {len(result.records)} tests, {seconds:.0f} s, "
          f"{'FAILED' if problems else 'OK'}")
    return 1 if problems else 0


def shard_problems(report):
    problems = [f"load error: {error}" for error in report["load_errors"]]
    discovered = report["discovered"]
    duplicates = sorted({test_id for test_id in discovered if discovered.count(test_id) > 1})
    problems += [f"{test_id}: discovered more than once" for test_id in duplicates]
    for test_id in discovered:
        entry = report["tests"].get(test_id)
        if entry is None:
            problems.append(f"{test_id}: did not run")
        elif entry["outcome"] != PASSED:
            problems.append(f"{test_id}: {entry['outcome']}")
    problems += [f"{test_id}: ran without being discovered" for test_id in sorted(set(report["tests"])
                                                                                    - set(discovered))]
    return problems


def verify(directory, count, timings, expected_ids=None, names=None):
    """Returns (problems, summary) for the shard reports in a directory.

    The expected test ids and module names default to those discovered in the suite.
    """
    problems = []
    names = modules() if names is None else names
    expected_ids = discover() if expected_ids is None else expected_ids
    duplicates = sorted({test_id for test_id in expected_ids if expected_ids.count(test_id) > 1})
    problems += [f"{test_id}: discovered more than once" for test_id in duplicates]
    tested = {test_id.split(".", 1)[0] for test_id in expected_ids}
    if tested != set(names):
        problems.append("modules without tests: " + ", ".join(sorted(set(names) - tested)))
    assignment = assign(names, count, timings)
    owner = {name: index for index, shard in enumerate(assignment, 1) for name in shard}
    seen = {}
    summary = {"shards": count, "tests": len(expected_ids), "modules": len(names), "seconds": {},
               "module_seconds": {}}
    for index in range(1, count + 1):
        path = directory / f"shard-{index}-of-{count}.json"
        if not path.exists():
            problems.append(f"shard {index}/{count}: no result")
            continue
        report = json.loads(path.read_text())
        if (report.get("shard"), report.get("shards")) != (index, count):
            problems.append(f"{path.name}: records shard {report.get('shard')}/{report.get('shards')}")
            continue
        if report["modules"] != assignment[index - 1]:
            problems.append(f"shard {index}/{count}: ran modules {report['modules']}, "
                            f"expected {assignment[index - 1]}")
        problems += [f"shard {index}/{count}: {problem}" for problem in shard_problems(report)]
        for test_id, entry in report["tests"].items():
            if test_id in seen:
                problems.append(f"{test_id}: ran in shards {seen[test_id]} and {index}")
                continue
            seen[test_id] = index
            module = test_id.split(".", 1)[0]
            if owner.get(module) != index:
                problems.append(f"{test_id}: ran in shard {index}, assigned to {owner.get(module)}")
        summary["seconds"][str(index)] = report["seconds"]
        summary["module_seconds"].update(report["module_seconds"])
    problems += [f"{test_id}: no result" for test_id in expected_ids if test_id not in seen]
    problems += [f"{test_id}: not in the suite" for test_id in sorted(set(seen) - set(expected_ids))]
    summary["passed"] = not problems
    return problems, summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="run one shard")
    run.add_argument("--shard", type=parse_shard, required=True, help="I/N")
    run.add_argument("--output", type=Path, required=True, help="the result directory")
    check = commands.add_parser("verify", help="check the combined shard results")
    check.add_argument("--shards", type=int, required=True)
    check.add_argument("--output", type=Path, required=True, help="the result directory")
    record = commands.add_parser("timings", help="record module durations from shard results")
    record.add_argument("--output", type=Path, required=True, help="the result directory")
    commands.add_parser("list", help="print the shard assignment").add_argument("--shards", type=int, required=True)
    args = parser.parse_args(argv)
    timings = read_timings()
    if args.command == "run":
        return run_shard(*args.shard, args.output, timings)
    if args.command == "list":
        for index, shard in enumerate(assign(modules(), args.shards, timings), 1):
            total = sum(timings.get(name, 0) for name in shard)
            print(f"shard {index}/{args.shards}: {len(shard)} modules, ~{total:.0f} s: {' '.join(shard)}")
        return 0
    if args.command == "verify":
        problems, summary = verify(args.output, args.shards, timings)
        # every shard can fail before archiving a result; the summary still records why
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "summary.json").write_text(json.dumps({"problems": problems, **summary}, indent=1,
                                                             sort_keys=True) + "\n")
        for problem in problems:
            print(f"FAILED: {problem}")
        print(f"{summary['tests']} tests in {summary['modules']} modules and {args.shards} shards: "
              f"{'FAILED' if problems else 'all passed'}")
        return 1 if problems else 0
    durations = {}
    for path in sorted(args.output.glob("shard-*-of-*.json")):
        durations.update(json.loads(path.read_text())["module_seconds"])
    if sorted(durations) != modules():
        print("the results do not cover every module", file=sys.stderr)
        return 1
    TIMINGS.write_text(json.dumps({
        "copyright": "2026 Qore Technologies, s.r.o.",
        "note": "Measured seconds per test module; only balances the CI shards (see ci_suite.py).",
        "modules": durations,
    }, indent=1, sort_keys=True) + "\n")
    print(f"recorded {TIMINGS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
