#!/usr/bin/env python3
"""Parallel CI runner and completeness check for the Python WSDL/SOAP suite.

Copyright (C) 2026 Qore Technologies, s.r.o.

Most tests start one ``qore`` or ``java`` process at a time and wait for it, so a single test runner uses about one
CPU. The runner therefore runs several test modules at a time, each in a process and session of its own, and can
also split the suite by module into shards for separate CI jobs:

- ``run [--shard I/N] --jobs J`` runs the test modules of shard I of N (default: all of them, 1/1), J at a time,
  and writes ``shard-I-of-N.json``, which records every test with its outcome and duration, the shard's modules,
  each module process's status and the environment, and ``logs/<module>.log`` with each module's output, which
  is also printed whole when the module finishes. The tests expected in each module are discovered by the runner
  itself: a module process that crashes, hangs (``--module-timeout``) or exits early fails the tests it did not
  report, naming the test that was running, and a process that reports other tests than expected fails the run.
  A run interrupted by SIGINT or SIGTERM (as a CI job timeout may send) stops its module processes and still
  writes its report, which names the tests that were running, and exits with 130;
- ``verify --shards N`` discovers the suite independently and fails unless every discovered test ran exactly
  once, in the shard it is assigned to, and passed. A missing shard, a missing, duplicate, unknown, skipped or
  failed test, a module that cannot be imported or a module process that failed fails the check, so none of them
  can improve the counts;
- ``timings`` writes the measured module durations to ``ci-timings.json``, which only balances the shards and
  orders the modules within a run.

The assignment is deterministic: modules are placed longest first, by their recorded durations, on the shard
with the least total time. A module with no recorded duration counts as the median duration. Within a run the
modules start longest first, so that the longest do not start last.
"""
import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import platform
import select
import signal
import statistics
import subprocess
import sys
import threading
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


def read_timings(path=None):
    path = TIMINGS if path is None else path
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


def positive(text):
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {text!r}") from None
    if value < 1:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {text!r}")
    return value


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


# the outcome recorded for the tests of a module whose process failed before reporting them
PROCESS_ERROR = "error"
# a module process that has not finished after this many seconds is killed and its unreported tests fail
DEFAULT_MODULE_TIMEOUT = 3600
# seconds a timed-out or interrupted module process group has to exit after SIGTERM before it is killed
TERM_GRACE = 10


class EventResult(RecordingResult):
    """Records like RecordingResult and also writes each test's start and result as a JSON line, so that the
    parent process knows which tests finished, and which one was running, if the module's process dies."""

    events = None

    def emit(self, event):
        self.events.write(json.dumps(event, sort_keys=True) + "\n")
        self.events.flush()

    def startTest(self, test):
        self.emit({"event": "start", "id": test.id()})
        super().startTest(test)

    def stopTest(self, test):
        super().stopTest(test)
        self.emit({"event": "stop", "id": test.id(), **self.records[test.id()]})


def run_module(name, events_path):
    """Runs one test module in this process and writes its events to ``events_path``; returns the exit status.

    The last event, "final", holds the discovered tests, the load errors and every record, including those of
    class and module fixtures that failed outside a test. A process that dies before writing it leaves the
    tests it started and finished in the earlier events.
    """
    with open(events_path, "w", encoding="utf-8") as events:
        EventResult.events = events
        suite, errors = load([name])
        ids = [test_id for test_id, _ in test_ids(suite)]
        events.write(json.dumps({"event": "discovered", "ids": ids, "load_errors": errors}) + "\n")
        events.flush()
        runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2, resultclass=EventResult)
        result = runner.run(suite)
        events.write(json.dumps({"event": "final", "discovered": ids, "load_errors": errors,
                                 "records": result.records}, sort_keys=True) + "\n")
    passed = not errors and all(entry["outcome"] == PASSED for entry in result.records.values())
    return 0 if passed else 1


def read_events(path):
    """Returns the events written by a module process; a partly written last line is ignored."""
    events = []
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return events
    for line in text.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            break
    return events


def module_result(name, expected, events, returncode, timed_out, timeout):
    """Combines a module process's events and exit with the tests expected in it.

    Returns a dict with "status" ("ok" or why the process failed), "records", "discovered" (as the process
    found them, or None) and "load_errors". When the process failed, every expected test without a record
    gets an error naming the failure, and the test that was running when it happened is named.
    """
    final = next((event for event in events if event.get("event") == "final"), None)
    found = next((event for event in events if event.get("event") == "discovered"), None)
    if timed_out:
        status = f"timed out after {timeout} s and was killed"
    elif returncode < 0:
        try:
            signal_name = signal.Signals(-returncode).name
        except ValueError:
            signal_name = f"signal {-returncode}"
        status = f"was killed by {signal_name}"
    elif final is None:
        status = f"exited with status {returncode} without a result"
    elif returncode not in (0, 1):
        status = f"exited with status {returncode}"
    else:
        status = "ok"
    if final is not None:
        records = dict(final["records"])
    else:
        records = {}
        for event in events:
            if event.get("event") == "stop":
                records[event["id"]] = {key: value for key, value in event.items() if key not in ("event", "id")}
    if status != "ok":
        started = [event["id"] for event in events if event.get("event") == "start"]
        running = started[-1] if started and started[-1] not in records else None
        for test_id in expected:
            if test_id not in records:
                when = "while it ran" if test_id == running else "before it ran"
                records[test_id] = {"outcome": PROCESS_ERROR, "seconds": 0.0,
                                    "detail": f"the process of module {name} {status} {when}"}
    return {
        "status": status,
        "records": records,
        "discovered": final["discovered"] if final else (found["ids"] if found else None),
        "load_errors": final["load_errors"] if final else (found["load_errors"] if found else []),
    }


def signal_group(pid, signum):
    """Sends a signal to a process group; returns False if the group no longer exists."""
    try:
        os.killpg(pid, signum)
    except ProcessLookupError:
        return False
    except PermissionError:
        # a member changed its user; the members that can still be signalled were
        return True
    return True


def live_members(pgid):
    """Returns the PIDs of the processes in a process group that have not exited (Linux: read from /proc), or
    None where that cannot be read."""
    members = []
    try:
        entries = os.listdir("/proc")
    except OSError:
        return None
    for entry in entries:
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/stat") as stat:
                fields = stat.read().rsplit(")", 1)[1].split()
        except OSError:
            continue
        # fields: state, ppid, pgrp, ...
        if int(fields[2]) == pgid and fields[0] != "Z":
            members.append(int(entry))
    return members


# the runner that a signal interrupts (see main())
RUNNERS = []


class ModuleRunner:
    """Runs test modules concurrently, each in its own process and session.

    A module process, and everything it started, is a process group of its own. The worker thread of a module
    waits for it without reaping it (with a pidfd), so that the group's ID, its PID, cannot be reused while the
    group is signalled: when the module finishes, any process it left running is killed; when it runs longer than
    the timeout, or the runner is interrupted, the group gets SIGTERM and, after TERM_GRACE seconds, SIGKILL; then
    the worker reaps it. interrupt() only sets a flag and wakes the workers, so a signal handler can call it. Each
    module's output goes to its own log file and is printed whole when the module finishes.
    """

    def __init__(self, jobs, timeout, logs, command=None, stream=None):
        if jobs < 1:
            raise ValueError("the job count must be positive")
        if timeout <= 0:
            raise ValueError("the module timeout must be positive")
        if not hasattr(os, "pidfd_open"):
            raise RuntimeError("the parallel runner needs pidfd_open (Linux 5.3 or later)")
        self.jobs = jobs
        self.timeout = timeout
        self.logs = logs
        # the command that runs one module: the module name and the events file are appended; unbuffered, so
        # that a process that dies leaves all its output in the log
        self.command = command or [sys.executable, "-u", *(f"-W{option}" for option in sys.warnoptions),
                                   *(f"-X{key}" if value is True else f"-X{key}={value}"
                                     for key, value in sys._xoptions.items()),
                                   str(Path(__file__).resolve()), "module"]
        self.stream = stream or sys.stdout
        self.lock = threading.Lock()
        self.interrupted = False
        # readable once interrupted: it is never drained, so every later wait ends at once too
        self.wake_read, self.wake_write = os.pipe()

    def close(self):
        for fd in (self.wake_read, self.wake_write):
            try:
                os.close(fd)
            except OSError:
                pass
        self.wake_read = self.wake_write = -1

    def interrupt(self):
        """Stops every running module and starts no more; safe to call from a signal handler, and again."""
        self.interrupted = True
        if self.wake_write >= 0:
            try:
                os.write(self.wake_write, b"x")
            except OSError:
                # closed: the run is over
                pass

    @staticmethod
    def wait_exit(process, timeout, wake=None):
        """Waits up to ``timeout`` seconds for a process to exit, without reaping it; returns "exited",
        "timeout" or, when the ``wake`` file descriptor became readable first, "interrupted"."""
        pidfd = os.pidfd_open(process.pid)
        try:
            poller = select.poll()
            poller.register(pidfd, select.POLLIN)
            if wake is not None and wake >= 0:
                poller.register(wake, select.POLLIN)
            ready = {fd for fd, _ in poller.poll(int(timeout * 1000))}
        finally:
            os.close(pidfd)
        if pidfd in ready:
            return "exited"
        return "interrupted" if ready else "timeout"

    def run_one(self, name, expected):
        """Runs one module; returns its result (see module_result()), or None when the run was interrupted
        before the module started."""
        log_path = self.logs / f"{name}.log"
        events_path = self.logs / f"{name}.events"
        started = time.monotonic()
        state = None
        leftover = False
        try:
            with open(log_path, "wb") as log:
                with self.lock:
                    if self.interrupted:
                        return None
                    process = subprocess.Popen([*self.command, name, str(events_path)], cwd=HERE,
                                               stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                               start_new_session=True)
                try:
                    state = self.wait_exit(process, self.timeout, self.wake_read)
                    if state != "exited":
                        signal_group(process.pid, signal.SIGTERM)
                        self.wait_exit(process, TERM_GRACE)
                    # the leader is not reaped yet, so its group ID is still this group's
                    members = live_members(process.pid)
                    leftover = state == "exited" and bool(members)
                    signal_group(process.pid, signal.SIGKILL)
                    try:
                        # in case the leader left its group
                        os.kill(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                finally:
                    if process.returncode is None:
                        process.kill()
                    process.wait()
        except Exception as error:
            # the module could not be run or waited for: its tests fail with the reason
            result = module_result(name, expected, [], 2, False, self.timeout)
            result["status"] = f"could not be run: {error!r}"
            for entry in result["records"].values():
                entry["detail"] = f"module {name} could not be run: {error!r}"
            result["seconds"] = round(time.monotonic() - started, 3)
            result["returncode"] = None
            self.report(name, log_path, f"{name}: could not be run: {error!r}")
            return result
        seconds = time.monotonic() - started
        result = module_result(name, expected, read_events(events_path), process.returncode, state == "timeout",
                               self.timeout)
        result["seconds"] = round(seconds, 3)
        result["returncode"] = process.returncode
        if leftover:
            result["leftover"] = True
        failed = [test_id for test_id, entry in result["records"].items() if entry["outcome"] != PASSED]
        self.report(name, log_path,
                    f"{name}: {len(result['records'])} tests, {len(failed)} not passed, {seconds:.0f} s"
                    + ("" if result["status"] == "ok" else f"; the process {result['status']}")
                    + ("; processes it left running were killed" if leftover else ""))
        return result

    def report(self, name, log_path, summary):
        """Prints a module's whole output between its markers."""
        try:
            output = log_path.read_text(encoding="utf-8", errors="replace")
        except OSError as error:
            output = f"(no output: {error})\n"
        with self.lock:
            self.stream.write(f"===== begin {name}\n")
            self.stream.write(output)
            self.stream.write(f"===== end {summary}\n")
            self.stream.flush()

    def run(self, names, expected, timings):
        """Runs the modules, longest first by the recorded durations; returns {name: result}.

        After interrupt() it returns once the running modules are stopped; their results name the tests that
        were running, and the modules that had not started have none.
        """
        self.logs.mkdir(parents=True, exist_ok=True)
        known = [timings[name] for name in names if name in timings]
        default = statistics.median(known) if known else 1.0
        order = sorted(names, key=lambda name: (-timings.get(name, default), name))
        results = {}
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.jobs) as pool:
                futures = {pool.submit(self.run_one, name, expected.get(name, [])): name for name in order}
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result is not None:
                        results[futures[future]] = result
        finally:
            self.close()
        return results


def module_of(test_id):
    """The module of a test id; a module that failed to import has the id unittest.loader._FailedTest.<module>."""
    if test_id.startswith("unittest.loader._FailedTest."):
        return test_id.rsplit(".", 1)[1]
    return test_id.split(".", 1)[0]


def run_shard(index, count, output, timings, jobs=1, timeout=DEFAULT_MODULE_TIMEOUT, runner=None, names=None):
    """Runs shard ``index`` of ``count``, ``jobs`` modules at a time, and writes its report; returns the status.

    The tests expected in each module are discovered here, in this process, so a module process that loses or
    adds tests is found out, and one that dies leaves its tests failed, not missing.
    """
    names = assign(modules(), count, timings)[index - 1] if names is None else names
    suite, errors = load(names)
    ids = [test_id for test_id, _ in test_ids(suite)]
    expected = {name: [] for name in names}
    for test_id in ids:
        expected.setdefault(module_of(test_id), []).append(test_id)
    output.mkdir(parents=True, exist_ok=True)
    runner = runner or ModuleRunner(jobs, timeout, output / "logs")
    started = time.monotonic()
    results = runner.run(names, expected, timings)
    seconds = time.monotonic() - started
    records = {}
    module_status = {}
    for name in names:
        result = results.get(name)
        if result is None:
            module_status[name] = "did not run: the run was interrupted" if runner.interrupted else "did not run"
            continue
        module_status[name] = result["status"]
        if result["discovered"] is not None and result["discovered"] != expected.get(name, []):
            module_status[name] = (f"its process discovered {len(result['discovered'])} tests, "
                                   f"expected {len(expected.get(name, []))}")
        for test_id, entry in result["records"].items():
            if test_id in records:
                # two modules cannot report one test; keep the failure visible
                module_status[name] = f"reported {test_id}, which another module also reported"
                continue
            records[test_id] = entry
    # module durations come from the tests in them, so balancing does not depend on the shard's other modules
    durations = {name: 0.0 for name in names}
    for test_id, entry in records.items():
        module = module_of(test_id)
        if module in durations:
            durations[module] = round(durations[module] + entry["seconds"], 3)
    report = {
        "shard": index,
        "shards": count,
        "jobs": runner.jobs,
        "modules": names,
        "discovered": ids,
        "load_errors": errors,
        "tests": records,
        "module_seconds": durations,
        "module_wall_seconds": {name: result["seconds"] for name, result in sorted(results.items())},
        "module_status": module_status,
        "seconds": round(seconds, 3),
        "environment": environment(),
    }
    # written whole or not at all, so that verify never reads a partial report
    path = output / f"shard-{index}-of-{count}.json"
    partial = path.with_name(path.name + ".partial")
    partial.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    os.replace(partial, path)
    problems = shard_problems(report)
    for problem in problems:
        print(f"FAILED: {problem}")
    print(f"shard {index}/{count}: {len(names)} modules, {len(records)} tests, {runner.jobs} at a time, "
          f"{seconds:.0f} s, {'INTERRUPTED' if runner.interrupted else 'FAILED' if problems else 'OK'}")
    if runner.interrupted:
        return 130
    return 1 if problems else 0


def shard_problems(report):
    problems = [f"load error: {error}" for error in report["load_errors"]]
    problems += [f"{name}: {status}" for name, status in sorted(report.get("module_status", {}).items())
                 if status != "ok"]
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
    run = commands.add_parser("run", help="run the suite or one shard of it")
    run.add_argument("--shard", type=parse_shard, default=(1, 1), help="I/N (default: 1/1, the whole suite)")
    run.add_argument("--jobs", type=positive, default=1, help="the number of modules to run at a time")
    run.add_argument("--module-timeout", type=positive, default=DEFAULT_MODULE_TIMEOUT,
                     help=f"seconds after which a module's process is killed (default: {DEFAULT_MODULE_TIMEOUT})")
    run.add_argument("--output", type=Path, required=True, help="the result directory")
    one = commands.add_parser("module", help="run one test module (used by run)")
    one.add_argument("name")
    one.add_argument("events", type=Path, help="the file to write the test events to")
    check = commands.add_parser("verify", help="check the combined shard results")
    check.add_argument("--shards", type=int, required=True)
    check.add_argument("--output", type=Path, required=True, help="the result directory")
    record = commands.add_parser("timings", help="record module durations from shard results")
    record.add_argument("--output", type=Path, required=True, help="the result directory")
    commands.add_parser("list", help="print the shard assignment").add_argument("--shards", type=int, required=True)
    args = parser.parse_args(argv)
    if args.command == "module":
        return run_module(args.name, args.events)
    if args.command in ("run", "verify"):
        # expected validator results belong to the pinned lxml and libxml2 (oracle_versions.py)
        import oracle_versions
        oracle_versions.check()
    timings = read_timings()
    if args.command == "run":
        # a SIGTERM (a job timeout or cancellation) or SIGINT stops the module processes, which run in sessions of
        # their own and would not get it: the handler only interrupts the runner (also one started after the
        # signal), which then still writes its report; a repeated signal changes nothing
        signalled = []

        def terminate(signum, frame):
            signalled.append(signum)
            for runner in list(RUNNERS):
                runner.interrupt()
        signal.signal(signal.SIGTERM, terminate)
        signal.signal(signal.SIGINT, terminate)
        runner = ModuleRunner(args.jobs, args.module_timeout, args.output / "logs")
        RUNNERS.append(runner)
        if signalled:
            runner.interrupt()
        try:
            status = run_shard(*args.shard, args.output, timings, runner=runner)
        finally:
            RUNNERS.remove(runner)
        if status == 130:
            print("interrupted: the module processes were stopped; the report names the tests that were running",
                  file=sys.stderr)
        return status
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
        "note": "Measured seconds per test module; only balances the CI shards and orders the modules of a run "
                "(see ci_suite.py).",
        "modules": durations,
    }, indent=1, sort_keys=True) + "\n")
    print(f"recorded {TIMINGS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
