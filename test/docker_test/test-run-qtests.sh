#!/bin/bash
#
# Tests run-qtests.sh with stand-in test files: test-run-qtests.sh
#
# Checks that the runner:
# - passes a passing file, fails a failing one, and fails an empty list and a list naming no file;
# - runs files whose names contain spaces, quotes, "$", backquotes and command substitutions, without running any of
#   it as shell code, and lists them unsplit;
# - kills a file that times out together with the child that it started, and leaves no process behind: neither the
#   child of a timed-out file, nor the child that a passing file left running, nor a watchdog;
# - names the timed-out file and still prints its output.
# Takes about 10 s. Exits nonzero on the first failed check.
#
# Copyright 2026 Qore Technologies, s.r.o.

set -e

runner=$(cd "$(dirname "$0")" && pwd)/run-qtests.sh
dir=$(mktemp -d)
trap 'rm -rf "${dir}"' EXIT

fail() {
    echo "test-run-qtests.sh: FAILED: $*" >&2
    if [ -f "${dir}/out.txt" ]; then
        sed 's/^/    | /' "${dir}/out.txt" >&2
    fi
    exit 1
}

# the processes whose command line is exactly the arguments, from /proc (ps differs between BusyBox and procps)
procs() {
    want="$*"
    for f in /proc/[0-9]*/cmdline; do
        cmd=$( { tr '\0' ' ' < "${f}"; } 2> /dev/null | sed 's/ $//')
        if [ "${cmd}" = "${want}" ]; then
            echo "${f}"
        fi
    done
}

# stand-ins: the unusual sleep durations identify their processes
cat > "${dir}/pass.qtest" <<'EOF'
%new-style
# leaves a child running in its process group, which the runner must kill when the file ends
system("sleep 4243 > /dev/null 2>&1 &");
printf("pass output\n");
EOF
cat > "${dir}/fail.qtest" <<'EOF'
%new-style
printf("fail output\n");
exit(3);
EOF
cat > "${dir}/hang.qtest" <<'EOF'
%new-style
# starts a child, which the runner must kill with the file, then hangs
system("sleep 4242 > /dev/null 2>&1 &");
printf("hang output\n");
flush();
sleep(4241);
EOF
# executed as shell code, either substitution would print INJXTED, which the name itself does not contain
odd="${dir}/odd \"quoted\" \$HOME \`printf INJ%sTED X >&2\` \$(printf INJ%sTED X >&2) 'x'.qtest"
cat > "${odd}" <<'EOF'
%new-style
printf("odd output\n");
EOF

# the timeout is short (and the grace before SIGKILL shorter) so that the hang ends quickly
export QTEST_FILE_TIMEOUT=3 QTEST_FILE_KILL_GRACE=2

# one passing file, a file with an unusual name, a failing file and a hanging file
printf '%s\n' "${dir}/pass.qtest" "${odd}" "${dir}/fail.qtest" "${dir}/hang.qtest" > "${dir}/list"
"${runner}" 4 "${dir}/list" > "${dir}/out.txt" 2>&1 && rc=0 || rc=$?
[ "${rc}" = 1 ] || fail "a failing and a hanging file: exit ${rc}, not 1"
grep -q '^ran 4 of 4 test files' "${dir}/out.txt" || fail "not all four files reported a result"
grep -qx "==== ${dir}/pass.qtest: exit 0, [0-9]*s" "${dir}/out.txt" || fail "pass.qtest did not pass"
grep -qx 'pass output' "${dir}/out.txt" || fail "the output of pass.qtest is missing"
grep -qF "==== ${odd}: exit 0, " "${dir}/out.txt" || fail "the file with an unusual name did not pass under its own name"
grep -qx 'odd output' "${dir}/out.txt" || fail "the output of the file with an unusual name is missing"
! grep -q INJXTED "${dir}/out.txt" || fail "a file name was run as shell code"
grep -qx "==== ${dir}/fail.qtest: FAILED (exit 3)" "${dir}/out.txt" || fail "fail.qtest is not reported as failed"
grep -qx "==== ${dir}/hang.qtest: FAILED (timed out after 3s; its process group was killed)" "${dir}/out.txt" \
    || fail "hang.qtest is not reported as timed out"
grep -qx 'hang output' "${dir}/out.txt" || fail "the output of hang.qtest is missing"
sed -n '/^FAILED TEST FILES:$/,$p' "${dir}/out.txt" > "${dir}/failed.txt"
[ "$(grep -c '^    ' "${dir}/failed.txt")" = 2 ] \
    && grep -qx "    ${dir}/fail.qtest" "${dir}/failed.txt" && grep -qx "    ${dir}/hang.qtest" "${dir}/failed.txt" \
    || fail "the failed files are not listed exactly"

# no process may be left: the children of the hanging and the passing file, the hanging test, or a watchdog
left=$(procs sleep 4242; procs sleep 4243; procs sleep 3; procs sleep 2)
for f in /proc/[0-9]*/cmdline; do
    if { tr '\0' ' ' < "${f}"; } 2> /dev/null | grep -q 'hang\.qtest'; then
        left="${left} ${f}"
    fi
done
[ -z "$(echo ${left})" ] || fail "processes left behind: ${left}"

# an empty list, and a list of blank lines, are errors
: > "${dir}/empty"
"${runner}" 2 "${dir}/empty" > "${dir}/out.txt" 2>&1 && rc=0 || rc=$?
[ "${rc}" = 1 ] && grep -q 'names no test file' "${dir}/out.txt" || fail "an empty list: exit ${rc}, not 1"
printf '\n\n' > "${dir}/blank"
"${runner}" 2 "${dir}/blank" > "${dir}/out.txt" 2>&1 && rc=0 || rc=$?
[ "${rc}" = 1 ] || fail "a list of blank lines: exit ${rc}, not 1"

# all passing files pass
printf '%s\n' "${dir}/pass.qtest" "${odd}" > "${dir}/list"
"${runner}" 2 "${dir}/list" > "${dir}/out.txt" 2>&1 || fail "passing files: exit $?, not 0"
[ -z "$(echo $(procs sleep 4243))" ] || fail "the child of a passing file was left running"

rm -f "${dir}/out.txt"
echo "test-run-qtests.sh: all checks passed"
