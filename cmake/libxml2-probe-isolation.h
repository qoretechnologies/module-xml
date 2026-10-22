/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Runs each check of the libxml2 probe in its own process.
 *
 * The probe exercises a libxml2 that may be defective, and a defect can crash a check: libxml2 2.13.9 (Alpine 3.23)
 * writes through the NULL that xmlMalloc() returns in xmlSchemaParseUInt() when check_value_allocation() injects an
 * allocation failure.  A check that ends with a signal fails like any other failed check: the remaining checks still
 * run, and the probe exits normally with its failed result, which CMake's try_run() reports as a failed probe, so the
 * module builds its private libxml2.  The process of a check dumps no core: a library crash there is a probe result,
 * not a fault of the build to debug.
 */
#if defined(_WIN32)
static int qore_xml_probe_run(int (*check)(void), const char* name) {
    (void)name;
    return check();
}
#else
#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#if defined(__linux__)
#include <sys/prctl.h>
#endif

/* Prevents core dumps of the calling process, also where the kernel pipes cores to a helper that does not apply
 * RLIMIT_CORE (Linux: the process is made non-dumpable) */
static void qore_xml_probe_disable_core_dumps(void) {
    struct rlimit no_core = {0, 0};
    setrlimit(RLIMIT_CORE, &no_core);
#if defined(__linux__)
    prctl(PR_SET_DUMPABLE, 0, 0, 0, 0);
#endif
}

/* Returns 0 if the check passed, and 1 if it failed, ended with a signal or could not be run */
static int qore_xml_probe_run(int (*check)(void), const char* name) {
    pid_t pid;
    int status;
    /* the check's process must not repeat output buffered before it started */
    fflush(stdout);
    fflush(stderr);
    pid = fork();
    if (pid < 0) {
        fprintf(stderr, "%s: cannot start the check: %s\n", name, strerror(errno));
        return 1;
    }
    if (pid == 0) {
        int failed;
        qore_xml_probe_disable_core_dumps();
        failed = check();
        fflush(stdout);
        fflush(stderr);
        _exit(failed ? 1 : 0);
    }
    while (waitpid(pid, &status, 0) < 0) {
        if (errno != EINTR) {
            fprintf(stderr, "%s: cannot wait for the check: %s\n", name, strerror(errno));
            return 1;
        }
    }
    if (WIFSIGNALED(status)) {
        fprintf(stderr, "%s: the check ended with signal %d (%s), so the library fails it\n", name,
            WTERMSIG(status), strsignal(WTERMSIG(status)));
        return 1;
    }
    return !WIFEXITED(status) || WEXITSTATUS(status) != 0;
}
#endif

#define QORE_XML_PROBE_CHECK(check) qore_xml_probe_run(check, #check)
