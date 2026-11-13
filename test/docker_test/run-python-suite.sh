#!/bin/bash
#
# Runs one CI shard of the Python WSDL/SOAP suite in test/wsdl-interop, or verifies the combined shard results:
#
#   run-python-suite.sh shard    runs shard $CI_NODE_INDEX of $CI_NODE_TOTAL as the qore user
#   run-python-suite.sh verify   checks that the $PYTHON_SHARDS shard results cover the whole suite and passed
#
# A shard runs PYTHON_JOBS test modules at a time, each in its own process, by default half as many as the container's
# CPUs (cpu-jobs.sh), rounded up: a test waits for one qore or java process at a time, which runs more than one
# thread, so a module process keeps more than one CPU busy. Measured in podman with 4 CPUs and the develop images:
# the serial suite ran at 1.59 (Ubuntu) and 1.68 (Alpine) CPUs on average; four modules at a time kept the CPUs
# saturated (3.87-3.93 on average) and made each test about twice as slow as in the serial run (Ubuntu
# test_calendar_values: 946 s, serially 471 s), beyond the fixed timeouts that some tests set for their subprocesses
# (test_wsdl_ieee_constraints timed out at 180 s). With two at a time the tests took about as long as in the serial
# run (Alpine test_calendar_values: 387 s, serially 383 s), and the two shards together (1965 s) took no longer than
# the whole suite with four at a time (2135 s; the host was busier then). PYTHON_MODULE_TIMEOUT (default 3600) is the
# number of seconds after which a module's process is killed and its unfinished tests fail.
#
# Copyright 2026 Qore Technologies, s.r.o.

set -e
set -x

suite_dir="${MODULE_SRC_DIR}/test/wsdl-interop"
# the environment with the pinned lxml validator, created by the distribution script
python="${suite_dir}/.venv/bin/python"
results="${suite_dir}/ci-results"
cd "${suite_dir}"

case "$1" in
    shard)
        : "${CI_NODE_INDEX:?}" "${CI_NODE_TOTAL:?}"
        cpus=$("${MODULE_SRC_DIR}/test/docker_test/cpu-jobs.sh")
        jobs="${PYTHON_JOBS:-$(( (cpus + 1) / 2 ))}"
        # the development modules from this checkout, not only the installed ones
        export QORE_MODULE_DIR="${MODULE_SRC_DIR}/build-debug:${MODULE_SRC_DIR}/qlib${QORE_MODULE_DIR:+:${QORE_MODULE_DIR}}"
        mkdir -p "${results}"
        chown qore:qore "${results}"
        # warnings are errors, as in local runs; exec, so that a SIGTERM sent to this script reaches the runner,
        # which then stops the module processes and still writes its report
        exec gosu qore:qore "${python}" -W error ci_suite.py run --shard "${CI_NODE_INDEX}/${CI_NODE_TOTAL}" \
            --jobs "${jobs}" --module-timeout "${PYTHON_MODULE_TIMEOUT:-3600}" --output "${results}"
        ;;
    verify)
        : "${PYTHON_SHARDS:?}"
        exec "${python}" -W error ci_suite.py verify --shards "${PYTHON_SHARDS}" --output "${results}"
        ;;
    *)
        echo "usage: $0 shard|verify" >&2
        exit 2
        ;;
esac
