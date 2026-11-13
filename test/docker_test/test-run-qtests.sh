#!/bin/bash
#
# Tests run-qtests.sh with stand-in test files: test-run-qtests.sh
#
# Checks that the runner:
# - passes a passing file, fails a failing one, and fails a missing list, an empty list and a list naming no file;
# - runs files whose names contain spaces (also at the end), quotes, "$", backquotes and command substitutions,
#   without running any of it as shell code, and reports and lists them under their exact names;
# - kills a file that times out together with the child that it started and its watchdog, before the next file
#   starts, names it and still prints its output;
# - leaves no process behind: neither the child of a timed-out file, nor the child that a passing file left running,
#   nor a watchdog (its own "sh -c" or its sleep);
# - when it is interrupted, by SIGTERM to the runner alone (as when the CI runner stops the script) or by SIGINT to
#   its whole process group (Ctrl-C), ends with 143 or 130 and leaves no test, child, worker or watchdog running
#   (and does not hang if the runner ignores the signal).
# Takes about 7 s in the CI images. Exits nonzero on the first failed check.
#
# Copyright 2026 Qore Technologies, s.r.o.

set -e

runner=$(cd "$(dirname "$0")" && pwd)/run-qtests.sh
dir=$(mktemp -d)
# a runner started in the background, stopped if a check fails while it runs
bg=
trap 'if [ -n "${bg}" ]; then kill -TERM "${bg}" 2> /dev/null; wait "${bg}" 2> /dev/null; fi; rm -rf "${dir}"' EXIT

fail() {
    echo "test-run-qtests.sh: FAILED: $*" >&2
    if [ -f "${dir}/out.txt" ]; then
        sed 's/^/    | /' "${dir}/out.txt" >&2
    fi
    exit 1
}

# prints the processes whose command line matches one of the glob patterns; the command lines are read from /proc,
# as ps differs between BusyBox and procps, and matched by the shell, so that no process of this scan (such as a grep)
# matches itself
procs_matching() {
    local f cmd pat
    for f in /proc/[0-9]*/cmdline; do
        cmd=$( { tr '\0' ' ' < "${f}"; } 2> /dev/null) || continue
        cmd=${cmd% }
        for pat in "$@"; do
            case "${cmd}" in
                ${pat})
                    echo "${f}: ${cmd}"
                    break
                    ;;
            esac
        done
    done
}

# fails unless the processes matching the patterns are gone; SIGKILL is delivered asynchronously, so a killed process
# may take a moment to disappear: this waits up to SETTLE tenths of a second for that (default 50), and returns at
# once when nothing is left
check_gone() {
    local what=$1 i left
    shift
    for i in $(seq ${SETTLE:-50}); do
        left=$(procs_matching "$@")
        if [ -z "${left}" ]; then
            return 0
        fi
        sleep 0.1
    done
    fail "${what}: processes left behind: ${left}"
}

# fails if the runner left a process: anything whose command line names this test's directory (a test or a worker),
# the stand-ins' children (sleep 4242-4245), and watchdogs (their own "sh -c", matched by its code, or their sleep)
check_none_left() {
    check_gone "$1" "*${dir}/*" "sleep 424[2-5]" "sleep ${watchdog_sleep}" "sleep 2" "*: > \"\$1\"; kill -TERM -*"
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
cat > "${dir}/block.qtest" <<'EOF'
%new-style
# starts a child, tells the test that it runs (opening the FIFO for writing waits for its reader), then hangs
system("sleep 4244 > /dev/null 2>&1 &");
File f();
f.open2(ENV.QTEST_SYNC_FIFO, O_WRONLY);
f.write("started\n");
f.close();
sleep(4245);
EOF
cat > "${dir}/probe.qtest" <<'EOF'
%new-style
# tells the test that it runs, then waits until the test releases it
File f();
f.open2(ENV.QTEST_SYNC_FIFO, O_WRONLY);
f.write("started\n");
f.close();
File r();
r.open2(ENV.QTEST_RELEASE_FIFO);
r.readLine();
EOF
# executed as shell code, either substitution would print INJXTED, which the name itself does not contain
odd="${dir}/odd \"quoted\" \$HOME \`printf INJ%sTED X >&2\` \$(printf INJ%sTED X >&2) 'x'.qtest"
# a name that ends with spaces
spaced="${dir}/trailing spaces.qtest  "
for f in "${odd}" "${spaced}"; do
    printf '%%new-style\nprintf("odd output\\n");\n' > "${f}"
done

# the timeout is short (and the grace before SIGKILL shorter) so that the hang ends quickly
export QTEST_FILE_TIMEOUT=3 QTEST_FILE_KILL_GRACE=2
watchdog_sleep=3

# passing files (one with an unusual name, one ending with spaces), a failing file and a hanging file
printf '%s\n' "${dir}/pass.qtest" "${odd}" "${spaced}" "${dir}/fail.qtest" "${dir}/hang.qtest" > "${dir}/list"
"${runner}" 4 "${dir}/list" > "${dir}/out.txt" 2>&1 && rc=0 || rc=$?
[ "${rc}" = 1 ] || fail "a failing and a hanging file: exit ${rc}, not 1"
grep -q '^ran 5 of 5 test files' "${dir}/out.txt" || fail "not all five files reported a result"
grep -qx "==== ${dir}/pass.qtest: exit 0, [0-9]*s" "${dir}/out.txt" || fail "pass.qtest did not pass"
grep -qx 'pass output' "${dir}/out.txt" || fail "the output of pass.qtest is missing"
for f in "${odd}" "${spaced}"; do
    grep -qF "==== ${f}: exit 0, " "${dir}/out.txt" || fail "\"${f}\" did not pass under its own name"
done
[ "$(grep -cx 'odd output' "${dir}/out.txt")" = 2 ] || fail "the output of the files with unusual names is missing"
! grep -q INJXTED "${dir}/out.txt" || fail "a file name was run as shell code"
grep -qx "==== ${dir}/fail.qtest: FAILED (exit 3)" "${dir}/out.txt" || fail "fail.qtest is not reported as failed"
grep -qx "==== ${dir}/hang.qtest: FAILED (timed out after 3s; its process group was killed)" "${dir}/out.txt" \
    || fail "hang.qtest is not reported as timed out"
grep -qx 'hang output' "${dir}/out.txt" || fail "the output of hang.qtest is missing"
sed -n '/^FAILED TEST FILES:$/,$p' "${dir}/out.txt" > "${dir}/failed.txt"
[ "$(grep -c '^    ' "${dir}/failed.txt")" = 2 ] \
    && grep -qx "    ${dir}/fail.qtest" "${dir}/failed.txt" && grep -qx "    ${dir}/hang.qtest" "${dir}/failed.txt" \
    || fail "the failed files are not listed exactly"
check_none_left "after a run with a timeout"

# a file's child and watchdog are killed when the file ends, not when the run ends: the runner runs the files one at a
# time, the last of them a probe that waits for the test, which checks while the runner still runs (for at most 2 s,
# so that the probe cannot time out first)
export QTEST_SYNC_FIFO="${dir}/sync" QTEST_RELEASE_FIFO="${dir}/release"
mkfifo "${QTEST_SYNC_FIFO}" "${QTEST_RELEASE_FIFO}"
# held open for reading and writing, so that neither the stand-in nor this test waits in open() for the other: a
# stand-in that never starts fails the read below after 30 s instead of blocking this test
exec 4<> "${QTEST_SYNC_FIFO}"
key() {
    printf '%s' "$1" | cksum | cut -d' ' -f1
}
# mid_run WHAT FILE... -- PATTERN...: runs the files and then the probe, and checks that the patterns are gone
mid_run() {
    local what=$1 pid started
    shift
    : > "${dir}/list"
    while [ "$1" != -- ]; do
        printf '%s\n' "$1" >> "${dir}/list"
        shift
    done
    shift
    printf '%s\n' "${dir}/probe.qtest" >> "${dir}/list"
    "${runner}" 1 "${dir}/list" > "${dir}/out.txt" 2>&1 &
    pid=$!
    bg=${pid}
    read -r -t 30 started <&4 || started=
    [ "${started}" = started ] || fail "${what}: probe.qtest did not start within 30 s"
    SETTLE=20 check_gone "${what}, while the next file runs" "$@"
    # opened for reading and writing, the FIFO does not wait for a reader (in case the probe ended meanwhile)
    exec 3<> "${QTEST_RELEASE_FIFO}"
    echo go >&3
    wait "${pid}" || :
    bg=
    exec 3>&-
    check_none_left "${what}, after the run"
}
# a timed-out file: its child (its watchdog sleeps through the SIGKILL grace and ends by itself)
mid_run "a timed-out file" "${dir}/hang.qtest" -- "sleep 4242" "*${dir}/hang.qtest*"
# a passing file: its child and its watchdog (its "sh -c", named by the file's key; the probe has a watchdog too)
QTEST_FILE_TIMEOUT=6007 mid_run "a passing file" "${dir}/pass.qtest" -- "sleep 4243" \
    "*$(key "${dir}/pass.qtest").log.timeout*"

# a missing list, an empty list, and a list of blank lines, are errors
"${runner}" 2 "${dir}/missing" > "${dir}/out.txt" 2>&1 && rc=0 || rc=$?
[ "${rc}" = 1 ] && grep -q 'cannot read the test list' "${dir}/out.txt" || fail "a missing list: exit ${rc}, not 1"
: > "${dir}/empty"
"${runner}" 2 "${dir}/empty" > "${dir}/out.txt" 2>&1 && rc=0 || rc=$?
[ "${rc}" = 1 ] && grep -q 'names no test file' "${dir}/out.txt" || fail "an empty list: exit ${rc}, not 1"
printf '\n\n' > "${dir}/blank"
"${runner}" 2 "${dir}/blank" > "${dir}/out.txt" 2>&1 && rc=0 || rc=$?
[ "${rc}" = 1 ] || fail "a list of blank lines: exit ${rc}, not 1"

# all passing files pass
printf '%s\n' "${dir}/pass.qtest" "${odd}" "${spaced}" > "${dir}/list"
"${runner}" 2 "${dir}/list" > "${dir}/out.txt" 2>&1 || fail "passing files: exit $?, not 0"
check_none_left "after passing files"

# interrupts: the runner runs in its own process group (job control), with a file that blocks until it is
# interrupted, and the test waits on the FIFO until that file runs; the timeout is long, so only the interrupt ends it
export QTEST_FILE_TIMEOUT=6007
watchdog_sleep=6007
printf '%s\n' "${dir}/block.qtest" "${dir}/pass.qtest" > "${dir}/list"
# A non-interactive shell starts a background command with SIGINT ignored, and a signal ignored on entry cannot be
# trapped or reset by a shell; the CI runner starts the job's script that way, so the runner (and everything it
# starts) ignores SIGINT there, as Ctrl-C cannot happen. The SIGINT case therefore starts the runner through Python,
# which restores SIGINT's default disposition first, and is skipped (saying so) without Python.
# (python3 is started directly, not through eval, so that $! is the runner that it becomes)
reset_sigint='import os, signal, sys; signal.signal(signal.SIGINT, signal.SIG_DFL); os.execvp(sys.argv[1], sys.argv[1:])'
set -m
for how in "TERM runner" "INT group"; do
    set -- ${how}
    if [ "$1" = INT ]; then
        if ! command -v python3 > /dev/null 2>&1; then
            echo "test-run-qtests.sh: no python3: the SIGINT case is skipped"
            continue
        fi
        python3 -I -c "${reset_sigint}" "${runner}" 1 "${dir}/list" > "${dir}/out.txt" 2>&1 &
    else
        "${runner}" 1 "${dir}/list" > "${dir}/out.txt" 2>&1 &
    fi
    pid=$!
    bg=${pid}
    read -r -t 30 started <&4 || started=
    [ "${started}" = started ] || fail "SIG$1: the blocking file did not start within 30 s"
    # a runner that ignores the signal would wait for the blocking file for 100 min: it is killed after 30 s instead
    # (in its own process group, the guard and its sleep end together when they are no longer needed)
    ( sleep 30; kill -KILL -"${pid}" 2> /dev/null ) &
    guard=$!
    if [ "$2" = group ]; then
        kill -"$1" -"${pid}"
    else
        kill -"$1" "${pid}"
    fi
    wait "${pid}" && rc=0 || rc=$?
    bg=
    kill -KILL -"${guard}" 2> /dev/null || :
    wait "${guard}" 2> /dev/null || :
    expected=143
    [ "$1" = INT ] && expected=130
    [ "${rc}" = "${expected}" ] || fail "SIG$1 to the ${2}: exit ${rc}, not ${expected} (137: it ignored the signal)"
    grep -q "interrupted (SIG$1)" "${dir}/out.txt" || fail "SIG$1 to the ${2}: the interrupt is not reported"
    check_none_left "after SIG$1 to the ${2}"
done
set +m

rm -f "${dir}/out.txt"
echo "test-run-qtests.sh: all checks passed"
