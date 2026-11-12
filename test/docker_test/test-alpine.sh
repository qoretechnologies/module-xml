#!/bin/bash

set -e
set -x

# qtest (default): build the module and run the Qore test files against the module sources
# qtest-aot: build the module and run the Qore test files against the AOT-compiled modules of the build
# (both run QTEST_JOBS test files at a time, by default as many as the container's CPUs: see cpu-jobs.sh)
# python-shard: build the module and run shard $CI_NODE_INDEX of $CI_NODE_TOTAL of the Python WSDL/SOAP suite
# python-verify: check the combined results of all Python suite shards
MODE=${1:-qtest}
case "${MODE}" in
    qtest|qtest-aot|python-shard|python-verify) ;;
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

echo "export QORE_UID=1000" >> ${ENV_FILE}
echo "export QORE_GID=1000" >> ${ENV_FILE}

. ${ENV_FILE}

export MAKE_JOBS=4

if [ "${MODE}" != "qtest" ] && [ "${MODE}" != "qtest-aot" ]; then
    # lxml is the Python suite's only package outside the standard library: the pinned, hash-checked wheel
    # (test/wsdl-interop/requirements.txt), whose bundled libxml2 is the suite's second independent validator
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
if ! grep -q "^qore:x:${QORE_GID}" /etc/group; then
    addgroup -g ${QORE_GID} qore
fi
if ! grep -q "^qore:x:${QORE_UID}" /etc/passwd; then
    adduser -u ${QORE_UID} -D -G qore -h /home/qore -s /bin/bash qore
fi

# own everything by the qore user
chown -R qore:qore ${MODULE_SRC_DIR}

export QORE_MODULE_DIR=${MODULE_SRC_DIR}/qlib:${MODULE_BUILD_DIR}:${QORE_MODULE_DIR}
# the tests must load the modules that this job built, not the copies that the image already has
${MODULE_SRC_DIR}/test/docker_test/check-loaded-modules.sh ${MODULE_BUILD_DIR} gosu qore:qore

if [ "${MODE}" = "python-shard" ]; then
    exec ${MODULE_SRC_DIR}/test/docker_test/run-python-suite.sh shard
fi

# the parallel test runner itself (about 7 s)
${MODULE_SRC_DIR}/test/docker_test/test-run-qtests.sh

# the number of test files to run at a time
QTEST_JOBS=${QTEST_JOBS:-$(${MODULE_SRC_DIR}/test/docker_test/cpu-jobs.sh)}

if [ "${MODE}" = "qtest-aot" ]; then
    # run the tests against the AOT-compiled modules of this build
    exec ${MODULE_SRC_DIR}/test/docker_test/run-aot-qtests.sh ${MODULE_BUILD_DIR} ${QTEST_JOBS} gosu qore:qore
fi

# run the tests against the module sources
cd ${MODULE_SRC_DIR}
ls test/*.qtest | grep -v '\.aot\.qtest$' > /tmp/qtests.txt
rc=0
${MODULE_SRC_DIR}/test/docker_test/run-qtests.sh ${QTEST_JOBS} /tmp/qtests.txt gosu qore:qore || rc=1

# ... and they still load the modules that this job built once the tests have run
${MODULE_SRC_DIR}/test/docker_test/check-loaded-modules.sh ${MODULE_BUILD_DIR} gosu qore:qore || rc=1
exit ${rc}
