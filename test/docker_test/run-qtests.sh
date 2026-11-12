#!/bin/bash
#
# Runs Qore test files in parallel: run-qtests.sh JOBS LIST [RUNNER...]
#
# LIST is a file naming one test file per line, relative to the source directory, which is where the tests run. JOBS
# files run at a time, each as "qore -p enable-debug FILE -v" (debugging enabled to catch @debug block parse errors;
# "-v" reports each test case and every failure in full, while "-vv" would also list every passing assertion and push
# the job log past GitLab's size limit). RUNNER, if given, prefixes each command (for example "gosu qore:qore").
# An empty LIST is an error.
#
# Each file's output goes to its own log, which is printed whole when the file finishes, under a line with its exit
# status and duration, so that the outputs of parallel files never interleave. Each file runs in its own session
# (setsid), so its process group holds the test and every process it starts. A file that runs longer than
# QTEST_FILE_TIMEOUT seconds (default 600, about eight times the slowest file seen in CI) fails: its process group is
# sent SIGTERM, and SIGKILL QTEST_FILE_KILL_GRACE seconds later (default 30), so a hang names its file and prints its
# output instead of running into the job timeout, and no child of a killed test outlives it. When a file ends,
# whatever is left in its process group is killed, and so is the group of its watchdog. The slowest files and the
# failing files are listed at the end. Exits nonzero if any file fails.
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

count=$(grep -c . "${list}" || true)
if [ "${count}" = "0" ]; then
    echo "ERROR: ${list} names no test file" >&2
    exit 1
fi

log_dir=$(mktemp -d)
trap 'rm -rf "${log_dir}"' EXIT

echo "running ${count} test files, ${jobs} in parallel"
start=$(date +%s)

export LOG_DIR="${log_dir}"
export RUNNER="$*"
export QTEST_FILE_TIMEOUT=${QTEST_FILE_TIMEOUT:-600}
export QTEST_FILE_KILL_GRACE=${QTEST_FILE_KILL_GRACE:-30}
# The file name is the worker's argument ("$1"), never part of its code. A background job of a non-interactive shell
# is not a process group leader, so setsid runs the command in a new session without forking, and $! is the ID of
# its process group. The watchdog writes LOG.timeout before it kills the group. Each worker writes one short line
# when its file finishes, "STATUS SECONDS FILE"; the loop below is the only writer of the job log, so the logs print
# whole.
grep . "${list}" | tr '\n' '\0' | xargs -0 -n 1 -P "${jobs}" sh -c '
    f=$1
    log="${LOG_DIR}/$(printf "%s" "${f}" | cksum | cut -d" " -f1).log"
    t0=$(date +%s)
    setsid ${RUNNER} qore -p enable-debug "${f}" -v > "${log}" 2>&1 < /dev/null &
    pid=$!
    setsid sh -c "sleep ${QTEST_FILE_TIMEOUT}; : > \"\$1\"; kill -TERM -${pid}; sleep ${QTEST_FILE_KILL_GRACE}; kill -KILL -${pid}" \
        sh "${log}.timeout" > /dev/null 2>&1 < /dev/null &
    watchdog=$!
    wait "${pid}" && rc=0 || rc=$?
    kill -KILL -"${watchdog}" 2> /dev/null || :
    kill -KILL -"${pid}" 2> /dev/null || :
    if [ -e "${log}.timeout" ]; then
        rc=timeout
    fi
    printf "%s %s %s\n" "${rc}" "$(( $(date +%s) - t0 ))" "${f}"' sh | while read -r rc secs test; do
    log="${log_dir}/$(printf "%s" "${test}" | cksum | cut -d" " -f1).log"
    echo "==== ${test}: exit ${rc}, ${secs}s"
    cat "${log}"
    case "${rc}" in
        0) ;;
        timeout) echo "==== ${test}: FAILED (timed out after ${QTEST_FILE_TIMEOUT}s; its process group was killed)" ;;
        *) echo "==== ${test}: FAILED (exit ${rc})" ;;
    esac
    printf "%s %s %s\n" "${rc}" "${secs}" "${test}" >> "${log_dir}/results.txt"
done

touch "${log_dir}/results.txt"
ran=$(grep -c . "${log_dir}/results.txt" || true)
echo "ran ${ran} of ${count} test files in $(( $(date +%s) - start ))s with ${jobs} in parallel; the slowest:"
sort -k2,2nr "${log_dir}/results.txt" | head -10 | while read -r rc secs test; do
    printf "    %5ss %s\n" "${secs}" "${test}"
done
rc=0
grep -v '^0 ' "${log_dir}/results.txt" | sort -k3 > "${log_dir}/failed.txt" || true
if [ -s "${log_dir}/failed.txt" ]; then
    echo "FAILED TEST FILES:"
    while read -r status secs test; do
        echo "    ${test}"
    done < "${log_dir}/failed.txt"
    rc=1
fi
if [ "${ran}" != "${count}" ]; then
    echo "ERROR: ${count} test files were to run, but ${ran} reported a result" >&2
    rc=1
fi
exit ${rc}
