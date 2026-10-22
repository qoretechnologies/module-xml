/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Runs checks through the libxml2 probe's isolation (cmake/libxml2-probe-isolation.h): a check that crashes fails
 * without ending the probe and without a core dump, the checks after it still run, and the output buffered before a
 * check is written once.  Exits with 0 if every expectation holds.
 */
#include <signal.h>
#include <stdio.h>
#include "libxml2-probe-isolation.h"

static int check_passes(void) {
    printf("check_passes ran\n");
    return 0;
}

static int check_fails(void) {
    return 1;
}

static int check_crashes(void) {
    /* as libxml2 2.13.9 does when an allocation fails in xmlSchemaParseUInt() */
    volatile char* volatile target = NULL;
    *target = 'x';
    return 0;
}

static int check_aborts(void) {
    raise(SIGABRT);
    return 0;
}

#if !defined(_WIN32)
/* passes only in a process that cannot dump core */
static int check_dumps_no_core(void) {
    struct rlimit limit;
    if (getrlimit(RLIMIT_CORE, &limit) != 0 || limit.rlim_cur != 0) {
        fprintf(stderr, "a check's process may dump core: RLIMIT_CORE is %llu\n",
            (unsigned long long)limit.rlim_cur);
        return 1;
    }
#if defined(__linux__)
    if (prctl(PR_GET_DUMPABLE, 0, 0, 0, 0) != 0) {
        fprintf(stderr, "a check's process is dumpable\n");
        return 1;
    }
#endif
    return 0;
}
#endif

static int expect(int actual, int expected, const char* what) {
    if (actual != expected) {
        fprintf(stderr, "FAIL: %s: %d, expected %d\n", what, actual, expected);
        return 1;
    }
    printf("ok: %s\n", what);
    return 0;
}

int main(void) {
    int failed = 0;
    /* buffered when stdout is a pipe: the processes of the checks must not write it again */
    printf("probe output before the checks\n");
    failed |= expect(QORE_XML_PROBE_CHECK(check_passes), 0, "a passing check passes");
    failed |= expect(QORE_XML_PROBE_CHECK(check_fails), 1, "a failing check fails");
    failed |= expect(QORE_XML_PROBE_CHECK(check_crashes), 1, "a check that crashes fails");
    failed |= expect(QORE_XML_PROBE_CHECK(check_aborts), 1, "a check that aborts fails");
    failed |= expect(QORE_XML_PROBE_CHECK(check_passes), 0, "a check after a crashed one runs");
#if !defined(_WIN32)
    failed |= expect(QORE_XML_PROBE_CHECK(check_dumps_no_core), 0, "the process of a check dumps no core");
#endif
    return failed;
}
