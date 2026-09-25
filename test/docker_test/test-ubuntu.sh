#!/bin/bash

set -e
set -x

# qtest (default): build the module and run the Qore test files
# python-shard: build the module and run shard $CI_NODE_INDEX of $CI_NODE_TOTAL of the Python WSDL/SOAP suite
# python-verify: check the combined results of all Python suite shards
MODE=${1:-qtest}
case "${MODE}" in
    qtest|python-shard|python-verify) ;;
    *) echo "unknown mode: ${MODE}" >&2; exit 2 ;;
esac

ENV_FILE=/tmp/env.sh

. ${ENV_FILE}

# setup MODULE_SRC_DIR env var
cwd=`pwd`
if [ -z "${MODULE_SRC_DIR}" ]; then
    if [ -e "$cwd/qlib/WSDL.qm" ] || [ -e "$cwd/src/xml-module.cpp" ]; then
        MODULE_SRC_DIR=$cwd
    else
        MODULE_SRC_DIR=$WORKDIR/module-xml
    fi
fi
echo "export MODULE_SRC_DIR=${MODULE_SRC_DIR}" >> ${ENV_FILE}

echo "export QORE_UID=999" >> ${ENV_FILE}
echo "export QORE_GID=999" >> ${ENV_FILE}

. ${ENV_FILE}

export MAKE_JOBS=4

if [ "${MODE}" != "qtest" ]; then
    # lxml is the Python suite's only package outside the standard library: the pinned, hash-checked wheel
    # (test/wsdl-interop/requirements.txt), whose bundled libxml2 is the suite's second independent validator
    apt-get update && DEBIAN_FRONTEND=noninteractive apt-get -y install --no-install-recommends python3-venv
    python3 -m venv ${MODULE_SRC_DIR}/test/wsdl-interop/.venv
    ${MODULE_SRC_DIR}/test/wsdl-interop/.venv/bin/pip install --disable-pip-version-check --only-binary=:all: --require-hashes \
        -r ${MODULE_SRC_DIR}/test/wsdl-interop/requirements.txt
fi

if [ "${MODE}" = "python-verify" ]; then
    exec ${MODULE_SRC_DIR}/test/docker_test/run-python-suite.sh verify
fi

# build module and install
echo && echo "-- building module-xml --"
export MODULE_BUILD_DIR=${MODULE_SRC_DIR}/build-debug
mkdir -p ${MODULE_BUILD_DIR}
cd ${MODULE_BUILD_DIR}
cmake .. -DCMAKE_BUILD_TYPE=Debug -DCMAKE_INSTALL_PREFIX=${INSTALL_PREFIX}
make -j${MAKE_JOBS}
make install

# Verify that source-owned provider presentation catalogs match this checkout.
${MODULE_SRC_DIR}/test/docker_test/check-i18n.sh

# add Qore user and group
groupadd -o -g ${QORE_GID} qore
useradd -o -m -d /home/qore -u ${QORE_UID} -g ${QORE_GID} qore

# own everything by the qore user
chown -R qore:qore ${MODULE_SRC_DIR}

if [ "${MODE}" = "python-shard" ]; then
    exec ${MODULE_SRC_DIR}/test/docker_test/run-python-suite.sh shard
fi

# run the tests
export QORE_MODULE_DIR=${MODULE_SRC_DIR}/qlib:${QORE_MODULE_DIR}
cd ${MODULE_SRC_DIR}
FAILED=
for test in test/*.qtest; do
    # run with debugging enabled to catch @debug block parse errors
    # capture the status instead of letting it propagate: under "set -e" a failing
    # test aborts the job immediately, which skips every later test file
    # "-v" reports each test case and every failure in full; "-vv" also lists each passing
    # assertion, which pushes the job log past GitLab's size limit and hides later failures
    gosu qore:qore qore -p enable-debug $test -v && rc=0 || rc=$?
    if [ "$rc" != "0" ]; then
        FAILED="$FAILED $test"
    fi
done

# name the failing test files at the end of the log
if [ -n "$FAILED" ]; then
    echo "FAILED TEST FILES:"
    for test in $FAILED; do
        echo "    $test"
    done
    exit 1 # fail
fi
