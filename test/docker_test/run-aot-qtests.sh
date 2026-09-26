#!/bin/bash
#
# Runs the Qore tests against the AOT-compiled modules of this build: run-aot-qtests.sh BUILD_DIR [RUNNER...]
#
# The tests load the in-repo modules from their sources (%requires ../qlib/<Module>.qm), which never exercises the
# native modules that the build compiles (QORE_BUILD_AOT_MODULES) and installs. For each test that loads one, this
# writes a copy beside the original (so relative fixture paths still resolve) that loads the modules by name instead,
# including in the sub-programs that tests parse, and runs it with BUILD_DIR/qlib-qmod first in the module path and
# without the source directory. A preflight check requires every module to resolve to its compiled .qmod. RUNNER,
# if given, prefixes each test command (for example "gosu qore:qore"). Exits nonzero if any test fails.
#
# Copyright 2026 Qore Technologies, s.r.o.

set -e

build_dir=$(cd "$1" && pwd)
shift
src_dir=$(cd "$(dirname "$0")/../.." && pwd)
qmod_dir="${build_dir}/qlib-qmod"
cd "${src_dir}"

# the compiled modules and, without the source directory, the rest of the module path
export QORE_MODULE_DIR="${qmod_dir}${QORE_MODULE_DIR:+:${QORE_MODULE_DIR}}"
export QORE_MODULE_DIR=$(echo "${QORE_MODULE_DIR}" | tr ':' '\n' | grep -v -x -F "${src_dir}/qlib" | paste -s -d ':')

# every module compiled from qlib must load from the build
modules=$(cd "${qmod_dir}" && find . -name '*.qmod' | sed -E 's#^\./([^/]+/)?([^/]+)\.qmod$#\2#' | sort)
if [ -z "${modules}" ]; then
    echo "no AOT-compiled modules in ${qmod_dir}; configure with QORE_BUILD_AOT_MODULES=ON" >&2
    exit 1
fi
for module in ${modules}; do
    "$@" qore -e "%requires ${module}
string file = get_module_hash().\"${module}\".filename;
if (!file.equalPartial(\"${qmod_dir}/\")) {
    stderr.printf(\"%s loads from %s, not from ${qmod_dir}\\n\", \"${module}\", file);
    exit(1);
}"
done
echo "AOT modules: $(echo ${modules} | wc -w) load from ${qmod_dir}"

copies=()
cleanup() {
    rm -f "${copies[@]}"
}
trap cleanup EXIT

FAILED=
count=0
for test in test/*.qtest; do
    case "${test}" in
        *.aot.qtest) continue ;;
    esac
    if ! grep -q 'qlib/' "${test}"; then
        continue
    fi
    copy="${test%.qtest}.aot.qtest"
    copies+=("${copy}")
    # load the in-repo modules by name, and drop the source directory from the module path
    sed -E -e '/^[[:space:]]*%prepend-module-path "\$\{SCRIPT_DIR\}\/\.\.\/qlib"[[:space:]]*$/d' \
        -e 's#%requires \.\./qlib/([A-Za-z0-9_]+/)?([A-Za-z0-9_]+)(\.qm)?#%requires \2#g' "${test}" > "${copy}"
    if grep -q '\.\./qlib/' "${copy}"; then
        echo "${test}: unrewritten reference to ../qlib/" >&2
        grep -n '\.\./qlib/' "${copy}" >&2
        FAILED="${FAILED} ${test}"
        continue
    fi
    chmod +x "${copy}"
    count=$((count + 1))
    # run with debugging enabled to catch @debug block parse errors
    "$@" qore -p enable-debug "${copy}" -v && rc=0 || rc=$?
    if [ "${rc}" != "0" ]; then
        FAILED="${FAILED} ${test}"
    fi
done

echo "AOT test files run: ${count}"
if [ -n "${FAILED}" ]; then
    echo "FAILED AOT TEST FILES:"
    for test in ${FAILED}; do
        echo "    ${test}"
    done
    exit 1
fi
