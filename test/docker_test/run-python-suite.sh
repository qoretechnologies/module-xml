#!/bin/bash
#
# Runs one CI shard of the Python WSDL/SOAP suite in test/wsdl-interop, or verifies the combined shard results.
#
#   run-python-suite.sh shard    runs shard $CI_NODE_INDEX of $CI_NODE_TOTAL as the qore user
#   run-python-suite.sh verify   checks that the $PYTHON_SHARDS shard results cover the whole suite and passed
#
# Results are written to test/wsdl-interop/ci-results, which CI archives. See ci_suite.py.
#
# Copyright 2026 Qore Technologies, s.r.o.

set -e
set -x

suite_dir="${MODULE_SRC_DIR}/test/wsdl-interop"
results="${suite_dir}/ci-results"
cd "${suite_dir}"

case "$1" in
    shard)
        : "${CI_NODE_INDEX:?}" "${CI_NODE_TOTAL:?}"
        # the development modules from this checkout, not only the installed ones
        export QORE_MODULE_DIR="${MODULE_SRC_DIR}/build-debug:${MODULE_SRC_DIR}/qlib${QORE_MODULE_DIR:+:${QORE_MODULE_DIR}}"
        mkdir -p "${results}"
        chown qore:qore "${results}"
        # warnings are errors, as in local runs
        exec gosu qore:qore python3 -W error ci_suite.py run --shard "${CI_NODE_INDEX}/${CI_NODE_TOTAL}" \
            --output "${results}"
        ;;
    verify)
        : "${PYTHON_SHARDS:?}"
        exec python3 -W error ci_suite.py verify --shards "${PYTHON_SHARDS}" --output "${results}"
        ;;
    *)
        echo "usage: $0 shard|verify" >&2
        exit 2
        ;;
esac
