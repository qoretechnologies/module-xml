#!/bin/bash
#
# Runs Qore test files in parallel: run-qtests.sh JOBS LIST [RUNNER...]
#
# LIST is a file naming one test file per line, relative to the source directory, which is where the tests run. JOBS
# files run at a time, each as "qore -p enable-debug FILE -v" (debugging enabled to catch @debug block parse errors;
# "-v" reports each test case and every failure in full, while "-vv" would also list every passing assertion and push
# the job log past GitLab's size limit). RUNNER, if given, prefixes each command (for example "gosu qore:qore").
#
# Each file's output goes to its own log, which is printed whole when the file finishes, under a line with its exit
# status and duration, so that the outputs of parallel files never interleave. A file that runs longer than
# QTEST_FILE_TIMEOUT seconds (default 600, about eight times the slowest file seen in CI) is terminated, and killed
# 30 s later if it still runs, and fails, so a hang names its file and prints its output instead of running into the
# job timeout. The slowest files and the failing files are listed at the end. Exits nonzero if any file fails.
#
# The tests share nothing that would keep them from running at the same time: their servers listen on port 0 of a
# loopback address (test/listener-addresses.qtest checks this), and their temporary files and directories have
# unique names (the process ID or a random string).
#
# Copyright 2026 Qore Technologies, s.r.o.

set -e

jobs=$1
list=$2
shift 2
case "${jobs}" in
    ""|*[!0-9]*|0) echo "run-qtests.sh: invalid job count: \"${jobs}\"" >&2; exit 2 ;;
esac
list=$(readlink -f "${list}")
src_dir=$(cd "$(dirname "$0")/../.." && pwd)
cd "${src_dir}"

log_dir=$(mktemp -d)
trap 'rm -rf "${log_dir}"' EXIT

count=$(grep -c . "${list}" || true)
echo "running ${count} test files, ${jobs} in parallel"
start=$(date +%s)

export LOG_DIR="${log_dir}"
export RUNNER="$*"
export QTEST_FILE_TIMEOUT=${QTEST_FILE_TIMEOUT:-600}
# each worker writes one short line when its file finishes: "STATUS SECONDS FILE"; the loop below is the only writer
# of the job log, so the logs print whole
grep . "${list}" | xargs -P "${jobs}" -I{} sh -c '
    log="${LOG_DIR}/$(echo "{}" | tr / _).log"
    t0=$(date +%s)
    timeout -k 30 "${QTEST_FILE_TIMEOUT}" ${RUNNER} qore -p enable-debug "{}" -v > "${log}" 2>&1 && rc=0 || rc=$?
    echo "${rc} $(( $(date +%s) - t0 )) {}"' | while read -r rc secs test; do
    log="${log_dir}/$(echo "${test}" | tr / _).log"
    echo "==== ${test}: exit ${rc}, ${secs}s"
    cat "${log}"
    if [ "${rc}" != "0" ]; then
        # coreutils timeout exits with 124, BusyBox timeout with 143 (SIGTERM), and both with 137 after SIGKILL
        case "${rc}" in
            124|137|143) echo "==== ${test}: FAILED (exit ${rc}; killed after ${QTEST_FILE_TIMEOUT}s if it timed out)" ;;
            *) echo "==== ${test}: FAILED (exit ${rc})" ;;
        esac
    fi
    echo "${rc} ${secs} ${test}" >> "${log_dir}/results.txt"
done

touch "${log_dir}/results.txt"
ran=$(grep -c . "${log_dir}/results.txt" || true)
echo "ran ${ran} of ${count} test files in $(( $(date +%s) - start ))s with ${jobs} in parallel; the slowest:"
sort -k2,2nr "${log_dir}/results.txt" | head -10 | awk '{ printf "    %5ss %s\n", $2, $3 }'
FAILED=$(awk '$1 != "0" { print $3 }' "${log_dir}/results.txt" | sort)
if [ -n "${FAILED}" ]; then
    echo "FAILED TEST FILES:"
    for test in ${FAILED}; do
        echo "    ${test}"
    done
    exit 1
fi
if [ "${ran}" != "${count}" ]; then
    echo "ERROR: ${count} test files were to run, but ${ran} reported a result" >&2
    exit 1
fi
