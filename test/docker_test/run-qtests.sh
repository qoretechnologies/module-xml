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
# Because the tests and watchdogs run in their own sessions, an interrupt of the runner (Ctrl-C, or SIGTERM when the
# CI runner stops the job's script at RUNNER_SCRIPT_TIMEOUT) does not reach them. Every worker therefore records the
# process groups that it starts, and kills them itself when it is interrupted; the runner stops starting files and
# kills every recorded group on SIGINT, SIGTERM and SIGHUP and on exit, so nothing outlives an interrupted run.
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
if [ ! -f "${list}" ] || [ ! -r "${list}" ]; then
    echo "ERROR: cannot read the test list \"${list}\"" >&2
    exit 1
fi
list=$(readlink -f "${list}")
src_dir=$(cd "$(dirname "$0")/../.." && pwd)
cd "${src_dir}"

count=$(grep -c . "${list}" || true)
if [ "${count}" = "0" ]; then
    echo "ERROR: ${list} names no test file" >&2
    exit 1
fi

log_dir=$(mktemp -d)
mkdir "${log_dir}/groups"
xargs_pid=

# kills every process group that a worker recorded (a file per test file, one group ID per line)
kill_groups() {
    local f g
    for f in "${log_dir}"/groups/*; do
        [ -f "${f}" ] || continue
        while read -r g; do
            kill -KILL -"${g}" 2> /dev/null || :
        done < "${f}"
    done
}

# on an interrupt: no new files (the stop file, and xargs ends), and no test, child or watchdog left running
interrupted() {
    trap - INT TERM HUP
    echo "run-qtests.sh: interrupted (SIG$1): killing the running test files" >&2
    : > "${log_dir}/stop"
    if [ -n "${xargs_pid}" ]; then
        kill -TERM "${xargs_pid}" 2> /dev/null || :
    fi
    kill_groups
    exit "$2"
}
trap 'interrupted INT 130' INT
trap 'interrupted TERM 143' TERM
trap 'interrupted HUP 129' HUP
trap 'kill_groups; rm -rf "${log_dir}"' EXIT

echo "running ${count} test files, ${jobs} in parallel"
start=$(date +%s)

export LOG_DIR="${log_dir}"
export RUNNER="$*"
export QTEST_FILE_TIMEOUT=${QTEST_FILE_TIMEOUT:-600}
export QTEST_FILE_KILL_GRACE=${QTEST_FILE_KILL_GRACE:-30}
# The worker runs one file, its argument ("$1"), which is never part of its code. A background job of a
# non-interactive shell is not a process group leader, so setsid runs the command in a new session without forking,
# and $! is the ID of its process group. The worker records each group in groups/KEY before it waits; if it is
# interrupted (its trap sets "stop"; a caught signal is reset to the default in the commands it starts), or the runner
# has stopped (the stop file, or the log directory is gone), it kills its groups and keeps waiting until the test has
# ended. The watchdog writes KEY.timeout before it kills the test's group. The worker ends with one line, "STATUS
# SECONDS KEY FILE", where KEY (the cksum of the name) names its log; the loop below is the only writer of the job log,
# so the logs print whole.
grep . "${list}" | tr '\n' '\0' > "${log_dir}/list0"
mkfifo "${log_dir}/results.fifo"
xargs -0 -n 1 -P "${jobs}" sh -c '
    stop=
    trap "stop=1" INT TERM HUP
    f=$1
    key=$(printf "%s" "${f}" | cksum | cut -d" " -f1)
    log="${LOG_DIR}/${key}.log"
    t0=$(date +%s)
    setsid ${RUNNER} qore -p enable-debug "${f}" -v > "${log}" 2>&1 < /dev/null &
    pid=$!
    echo "${pid}" >> "${LOG_DIR}/groups/${key}" 2> /dev/null || :
    setsid sh -c "sleep ${QTEST_FILE_TIMEOUT}; : > \"\$1\"; kill -TERM -${pid}; sleep ${QTEST_FILE_KILL_GRACE}; kill -KILL -${pid}" \
        sh "${log}.timeout" > /dev/null 2>&1 < /dev/null &
    watchdog=$!
    echo "${watchdog}" >> "${LOG_DIR}/groups/${key}" 2> /dev/null || :
    rc=
    while :; do
        if [ -n "${stop}" ] || [ -e "${LOG_DIR}/stop" ] || [ ! -d "${LOG_DIR}/groups" ]; then
            kill -KILL -"${pid}" -"${watchdog}" 2> /dev/null || :
        fi
        wait "${pid}" && rc=0 || rc=$?
        # a trapped signal interrupts wait; the test has ended only when it is gone
        if ! kill -0 "${pid}" 2> /dev/null; then
            break
        fi
    done
    kill -KILL -"${watchdog}" 2> /dev/null || :
    kill -KILL -"${pid}" 2> /dev/null || :
    if [ -n "${stop}" ] || [ ! -d "${LOG_DIR}/groups" ]; then
        exit 1
    fi
    if [ -e "${log}.timeout" ]; then
        rc=timeout
    fi
    printf "%s %s %s %s\n" "${rc}" "$(( $(date +%s) - t0 ))" "${key}" "${f}"' sh \
    < "${log_dir}/list0" > "${log_dir}/results.fifo" &
xargs_pid=$!

# splits a result line, "STATUS SECONDS KEY FILE", without changing the file name
parse() {
    local rest
    rc=${1%% *}
    rest=${1#* }
    secs=${rest%% *}
    rest=${rest#* }
    key=${rest%% *}
    test=${rest#* }
}

while IFS= read -r line; do
    parse "${line}"
    echo "==== ${test}: exit ${rc}, ${secs}s"
    cat "${log_dir}/${key}.log"
    case "${rc}" in
        0) ;;
        timeout) echo "==== ${test}: FAILED (timed out after ${QTEST_FILE_TIMEOUT}s; its process group was killed)" ;;
        *) echo "==== ${test}: FAILED (exit ${rc})" ;;
    esac
    printf "%s\n" "${line}" >> "${log_dir}/results.txt"
done < "${log_dir}/results.fifo"
wait "${xargs_pid}" || :
xargs_pid=

touch "${log_dir}/results.txt"
ran=$(grep -c . "${log_dir}/results.txt" || true)
echo "ran ${ran} of ${count} test files in $(( $(date +%s) - start ))s with ${jobs} in parallel; the slowest:"
sort -k2,2nr "${log_dir}/results.txt" | head -10 | while IFS= read -r line; do
    parse "${line}"
    printf "    %5ss %s\n" "${secs}" "${test}"
done
rc=0
grep -v '^0 ' "${log_dir}/results.txt" | sort -k4 > "${log_dir}/failed.txt" || true
if [ -s "${log_dir}/failed.txt" ]; then
    echo "FAILED TEST FILES:"
    while IFS= read -r line; do
        parse "${line}"
        echo "    ${test}"
    done < "${log_dir}/failed.txt"
    rc=1
fi
if [ "${ran}" != "${count}" ]; then
    echo "ERROR: ${count} test files were to run, but ${ran} reported a result" >&2
    rc=1
fi
exit ${rc}
