#!/bin/bash
#
# Runs the native module's Qore tests under valgrind: run-valgrind-qtests.sh JOBS [RUNNER...]
#
# The native tests are those that load no in-repo Qore module (no ../qlib/ reference): they exercise the C++ module
# and its bundled libxml2 directly. Valgrind is about 50 times slower than a normal run, so the WSDL/SOAP tests,
# which exercise Qore code of the qlib modules, are left to the other jobs. Every test must report no valgrind error
# and no definitely or indirectly lost memory. QORE_PCRE2_NO_JIT=1 makes PCRE2 use its interpreter: its JIT
# matcher reads past a subject's length in SIMD blocks, which valgrind reports as an uninitialised read. JOBS tests
# run in parallel; RUNNER, if given, prefixes each command (for example "gosu qore:qore"). Exits nonzero if any test
# fails or reports a valgrind error.
#
# Copyright 2026 Qore Technologies, s.r.o.

set -e

jobs=$1
shift
src_dir=$(cd "$(dirname "$0")/../.." && pwd)
cd "${src_dir}"
log_dir=$(mktemp -d)
trap 'rm -rf "${log_dir}"' EXIT

tests=$(grep -L 'qlib/' test/*.qtest | grep -v '\.aot\.qtest$')
echo "valgrind: $(echo ${tests} | wc -w) native test files, ${jobs} in parallel"

export QORE_PCRE2_NO_JIT=1
export LOG_DIR="${log_dir}"
export RUNNER="$*"
# prints "PASS test" or "FAIL test"; a nonzero valgrind exit is an error report or a test failure
echo "${tests}" | xargs -P "${jobs}" -I{} sh -c '
    log="${LOG_DIR}/$(basename {}).log"
    if ${RUNNER} env -u DEBUGINFOD_URLS valgrind --error-exitcode=99 --leak-check=full \
            --errors-for-leak-kinds=definite,indirect --show-leak-kinds=definite,indirect \
            qore -b -p enable-debug {} > "${log}" 2>&1; then
        echo "PASS {}"
    else
        echo "FAIL {}"
    fi' | sort > "${log_dir}/results.txt"

cat "${log_dir}/results.txt"
FAILED=$(grep '^FAIL ' "${log_dir}/results.txt" | cut -d' ' -f2)
if [ -n "${FAILED}" ]; then
    for test in ${FAILED}; do
        echo "==== ${test}"
        # the valgrind error and leak reports, and the test's own failures
        grep -E '^==[0-9]+== |FAILURE|Exception|Ran ' "${log_dir}/$(basename ${test}).log" | head -200
    done
    echo "FAILED VALGRIND TEST FILES:"
    for test in ${FAILED}; do
        echo "    ${test}"
    done
    exit 1
fi
