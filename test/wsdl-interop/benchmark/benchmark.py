#!/usr/bin/env python3
"""P9b deterministic performance benchmark for the WSDL/SOAP modules.

Copyright (C) 2026 Qore Technologies, s.r.o.

Runs the pinned workloads with bench.qr against an optimized (Release) build, takes the median of each phase over
several repetitions, and compares it with the recorded reference in reference.json:

- a phase slower than the reference by more than the tolerance is reported as a regression finding (exit 1);
- output that differs from the reference digests is a failure (exit 2): a performance change must not change
  results, and an intended output change needs a new reference recorded with --record.

Timing depends on the machine; the reference records the environment it was measured in. Compare only on the same
machine class, or record a new reference first.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
REFERENCE = HERE / "reference.json"
DRIVER = HERE / "bench.qr"
WORKLOADS = {
    "list-values": HERE / "workloads" / "list-values.tar.xz",
    "binding-styles": HERE / "workloads" / "binding-styles.wsdl",
}
# binding-style iterations per run: enough for stable per-phase times
BINDING_ITERATIONS = 20
DEFAULT_TOLERANCE = 0.25
DEFAULT_REPETITIONS = 5


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_type(build):
    cache = Path(build) / "CMakeCache.txt"
    if not cache.exists():
        return None
    for line in cache.read_text().splitlines():
        if line.startswith("CMAKE_BUILD_TYPE:"):
            return line.split("=", 1)[1]
    return None


def unpack(archive, destination):
    """Unpacks the list-values archive safely; returns the workload directory."""
    with tarfile.open(archive, "r:xz") as tar:
        tar.extractall(destination, filter="data")
    return Path(destination) / "list-values"


def run_driver(workload, target, build, extra=(), timeout=1800):
    """Runs bench.qr once; returns its parsed JSON result."""
    env = os.environ.copy()
    env["QORE_MODULE_DIR"] = os.pathsep.join((str(Path(build).resolve()), str(REPO / "qlib")))
    command = [os.environ.get("QORE", "qore"), "-b", str(DRIVER), workload, str(target), *map(str, extra)]
    result = subprocess.run(command, capture_output=True, text=True, env=env, timeout=timeout)
    if result.returncode or result.stderr:
        raise RuntimeError(f"{command}: exit {result.returncode}\n{result.stdout}\n{result.stderr}")
    return json.loads(result.stdout)


def measure(workload, target, build, repetitions, extra=()):
    """Runs a workload repeatedly; returns the median phase times and the (identical) output digests."""
    runs = [run_driver(workload, target, build, extra) for _ in range(repetitions)]
    digests = {run["digest"] for run in runs}
    if len(digests) != 1:
        raise RuntimeError(f"{workload}: output differs between repetitions")
    phases = {phase: int(statistics.median(run["phases"].get(phase, 0) for run in runs))
              for phase in sorted(runs[0]["phases"])}
    return {"digest": runs[0]["digest"], "items": runs[0]["items"], "rows": runs[0]["rows"], "phases": phases,
            "total": int(statistics.median(run["total"] for run in runs)), "repetitions": repetitions}


def compare(reference, measured, tolerance):
    """Returns (failures, findings, improvements) for one workload."""
    failures, findings, improvements = [], [], []
    if measured["digest"] != reference["digest"]:
        changed = sorted(name for name in set(reference["items"]) | set(measured["items"])
                         if reference["items"].get(name) != measured["items"].get(name))
        failures.append(f"output differs from the reference for {len(changed)} item(s): {', '.join(changed[:10])}")
    for phase in sorted(set(reference["phases"]) | set(measured["phases"])):
        base, now = reference["phases"].get(phase), measured["phases"].get(phase)
        if base is None or now is None:
            failures.append(f"phase {phase!r} is not in both the reference and the measurement")
            continue
        if base <= 0:
            continue
        ratio = now / base
        if ratio > 1 + tolerance:
            findings.append((phase, base, now, ratio))
        elif ratio < 1 - tolerance:
            improvements.append((phase, base, now, ratio))
    return failures, findings, improvements


def environment(build):
    def run(command):
        try:
            return subprocess.run(command, capture_output=True, text=True, timeout=60).stdout.strip()
        except OSError:
            return None
    cpu = next((line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines()
                if line.startswith("model name")), platform.processor()) if Path("/proc/cpuinfo").exists() \
        else platform.processor()
    qore = run([os.environ.get("QORE", "qore"), "--version"]) or ""
    libqore = next((str(path) for path in (Path("/usr/lib64/libqore.so"), Path("/usr/lib/libqore.so"))
                    if path.exists()), None)
    return {
        "cpu": cpu,
        "cpus": os.cpu_count(),
        "system": platform.platform(),
        "qore": qore.splitlines()[1].strip() if len(qore.splitlines()) > 1 else qore,
        "libqore_sha256": sha256(Path(libqore).resolve()) if libqore else None,
        "module_xml_commit": run(["git", "-C", str(REPO), "rev-parse", "HEAD"]),
        "module_xml_dirty": bool(run(["git", "-C", str(REPO), "status", "--porcelain", "--untracked-files=no"])),
        "build_type": build_type(build),
        "binding_iterations": BINDING_ITERATIONS,
    }


def busy():
    """Returns the 1-minute load average when other work competes for the CPUs, else None."""
    load = os.getloadavg()[0]
    return load if load > (os.cpu_count() or 1) / 4 else None


def run_workloads(build, repetitions, names):
    results = {}
    with tempfile.TemporaryDirectory(prefix="xml-benchmark-") as temp:
        for name in names:
            if name == "list-values":
                target = unpack(WORKLOADS[name], temp)
                results[name] = measure(name, target, build, repetitions)
            else:
                results[name] = measure(name, WORKLOADS[name], build, repetitions, (BINDING_ITERATIONS,))
            results[name]["input_sha256"] = sha256(WORKLOADS[name])
            # other work on the machine distorts the timings
            results[name]["load_average"] = round(os.getloadavg()[0], 2)
    return results


def report(name, reference, measured, failures, findings, improvements, tolerance, out):
    out.write(f"\n{name}: {measured['rows']} outputs, total {measured['total'] / 1e9:.2f} s "
              f"(reference {reference['total'] / 1e9:.2f} s), median of {measured['repetitions']}, load "
              f"{measured.get('load_average')} (reference {reference.get('load_average')})\n")
    out.write(f"  {'phase':<16} {'reference':>12} {'measured':>12} {'ratio':>7}\n")
    for phase in sorted(measured["phases"]):
        base, now = reference["phases"].get(phase, 0), measured["phases"][phase]
        ratio = now / base if base else float("nan")
        out.write(f"  {phase:<16} {base / 1e6:>10.1f}ms {now / 1e6:>10.1f}ms {ratio:>7.2f}\n")
    for failure in failures:
        out.write(f"  FAILURE: {failure}\n")
    for phase, base, now, ratio in findings:
        out.write(f"  FINDING: {phase} is {ratio:.2f}x the reference ({base / 1e6:.1f} ms -> {now / 1e6:.1f} ms), "
                  f"beyond the {tolerance:.0%} tolerance\n")
    for phase, base, now, ratio in improvements:
        out.write(f"  improved: {phase} is {ratio:.2f}x the reference\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--build", default=str(REPO / "build"), help="the build directory (default: build)")
    parser.add_argument("--repetitions", type=int, default=DEFAULT_REPETITIONS)
    parser.add_argument("--tolerance", type=float, help="allowed slowdown as a fraction (default: the reference's)")
    parser.add_argument("--workload", action="append", choices=sorted(WORKLOADS), help="run only these workloads")
    parser.add_argument("--record", action="store_true", help="record the measurement as the new reference")
    parser.add_argument("--allow-debug", action="store_true",
                        help="accept a non-Release build (output checks only; timings are not comparable)")
    parser.add_argument("--json", help="also write the measurement to this file")
    parser.add_argument("--force", action="store_true", help="record a reference even on a busy machine")
    args = parser.parse_args(argv)

    kind = build_type(args.build)
    if kind != "Release" and not args.allow_debug:
        print(f"{args.build}: CMAKE_BUILD_TYPE is {kind!r}; the benchmark needs an optimized Release build",
              file=sys.stderr)
        return 2
    if args.record and kind != "Release":
        print("a reference can only be recorded with a Release build", file=sys.stderr)
        return 2
    reference = json.loads(REFERENCE.read_text()) if REFERENCE.exists() else None
    names = args.workload or sorted(WORKLOADS)
    for name in names:
        if reference and not args.record and sha256(WORKLOADS[name]) != \
                reference["workloads"][name]["input_sha256"]:
            print(f"{name}: the pinned workload differs from the reference's input", file=sys.stderr)
            return 2
    load = busy()
    if load is not None:
        print(f"warning: the 1-minute load average is {load:.1f} on {os.cpu_count()} CPUs; other work distorts the "
              f"timings", file=sys.stderr)
        if args.record and not args.force:
            print("refusing to record a reference on a busy machine; use --force to record anyway",
                  file=sys.stderr)
            return 2
    measured = run_workloads(args.build, args.repetitions, names)
    if args.json:
        Path(args.json).write_text(json.dumps(measured, indent=1, sort_keys=True) + "\n")
    if args.record:
        tolerance = args.tolerance if args.tolerance is not None else DEFAULT_TOLERANCE
        REFERENCE.write_text(json.dumps({
            "copyright": "2026 Qore Technologies, s.r.o.",
            "note": "P9b benchmark reference; see README.md. Phase and total times are medians in nanoseconds.",
            "tolerance": tolerance,
            "environment": environment(args.build),
            "workloads": measured,
        }, indent=1, sort_keys=True) + "\n")
        print(f"recorded {REFERENCE}")
        return 0
    if not reference:
        print("no reference; record one with --record", file=sys.stderr)
        return 2
    tolerance = args.tolerance if args.tolerance is not None else reference["tolerance"]
    status = 0
    for name in names:
        failures, findings, improvements = compare(reference["workloads"][name], measured[name], tolerance)
        report(name, reference["workloads"][name], measured[name], failures, findings, improvements, tolerance,
               sys.stdout)
        if failures:
            status = 2
        elif findings and status == 0:
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
