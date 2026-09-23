#!/bin/bash

set -e
set -x

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

# build module and install
echo && echo "-- building module-xml --"
mkdir -p ${MODULE_SRC_DIR}/build
cd ${MODULE_SRC_DIR}/build
cmake .. -DCMAKE_BUILD_TYPE=debug -DCMAKE_INSTALL_PREFIX=${INSTALL_PREFIX}
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
