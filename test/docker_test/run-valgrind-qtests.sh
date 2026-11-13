#!/bin/bash
#
# Runs the native module's Qore tests under valgrind: run-valgrind-qtests.sh JOBS [RUNNER...]
# Prints the selected test files, one per line: run-valgrind-qtests.sh --list
#
# The selected tests are the test files without a "qlib/" reference: they exercise the C++ module and its bundled
# libxml2. The WSDL/SOAP tests, which load the in-repo modules by path (%requires ../qlib/WSDL.qm) and mostly exercise
# their Qore code, are left out, as valgrind is about 50 times slower than a normal run. Tests that load in-repo
# modules by name are selected: they find them through the module path, which the CI job sets to the checkout's qlib
# first (QORE_MODULE_DIR) and most tests prepend themselves (%prepend-module-path "${SCRIPT_DIR}/../qlib", without
# "qlib/"). Seven of them load in-repo modules (WSDL, WebDavHandler, SaxDataProvider, XmlRpcClientIo), among them
# xml.qtest, the main test of the native API; they are kept under valgrind, and the path rules of
# .gitlab/ci/module-xml.yml cover those modules (test-change-rules.py checks it). Every test must report no valgrind error
# and no definitely or indirectly lost memory. QORE_PCRE2_NO_JIT=1 makes PCRE2 use its interpreter: its JIT
# matcher reads past a subject's length in SIMD blocks, which valgrind reports as an uninitialised read. JOBS tests
# run in parallel; RUNNER, if given, prefixes each command (for example "gosu qore:qore"). Exits nonzero if any test
# fails or reports a valgrind error.
#
# Copyright 2026 Qore Technologies, s.r.o.

set -e

src_dir=$(cd "$(dirname "$0")/../.." && pwd)
cd "${src_dir}"

tests=$(grep -L 'qlib/' test/*.qtest | grep -v '\.aot\.qtest$')
if [ "$1" = "--list" ]; then
    echo "${tests}"
    exit 0
fi

jobs=$1
shift
log_dir=$(mktemp -d)
trap 'rm -rf "${log_dir}"' EXIT

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
