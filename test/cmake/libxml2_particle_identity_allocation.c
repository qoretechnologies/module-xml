/* Copyright (C) 2026 Qore Technologies, s.r.o. */
#ifdef NDEBUG
#undef NDEBUG
#endif
/* This fixture exercises libxml2 internals, including its internal automata API. */
#define IN_LIBXML
#include <assert.h>
#include <libxml/xmlschemas.h>
#include <libxml/xmlschemastypes.h>
#include <libxml/xmlautomata.h>
#include <libxml/xmlmemory.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static size_t live, attempts, fail_at;
static int armed, failed;
static void *allocate(size_t size) {
    void *p;
    if (armed && ++attempts >= fail_at && fail_at != 0) {
        failed = 1;
        return NULL;
    }
    p = malloc(size);
    if (p != NULL) {
        ++live;
    }
    return p;
}
static void release(void *p) {
    if (p != NULL) {
        assert(live != 0);
        --live;
        free(p);
    }
}
static void *resize(void *p, size_t size) {
    if (p == NULL) {
        return allocate(size);
    }
    if (size == 0) {
        release(p);
        return NULL;
    }
    if (armed && ++attempts >= fail_at && fail_at != 0) {
        failed = 1;
        return NULL;
    }
    return realloc(p, size);
}
static char *duplicate(const char *value) {
    size_t length = strlen(value) + 1;
    char *p = allocate(length);
    if (p != NULL) {
        memcpy(p, value, length);
    }
    return p;
}
static void error_handler(void *data, const char *message, ...) {
    (void)data;
    (void)message;
}

/* These private symbols are tested through the static provider only. */
extern int xmlAutomataPushParticle(xmlAutomata*, const void*, size_t*);
extern void xmlAutomataPopParticle(xmlAutomata*, size_t);

static size_t exercise(size_t fault) {
    static int source[80];
    xmlAutomataPtr automaton = xmlNewAutomata();
    size_t parent, inner, count;
    int success = 1;
    assert(automaton != NULL);
    attempts = 0;
    fail_at = fault;
    failed = 0;
    armed = 1;
    for (unsigned i = 0; i < 80; ++i) {
        if (xmlAutomataPushParticle(automaton, &source[i], &parent) < 0) {
            success = 0;
            break;
        }
        assert(parent == 0);
        if (xmlAutomataPushParticle(automaton, &source[0], &inner) < 0) {
            xmlAutomataPopParticle(automaton, parent);
            success = 0;
            break;
        }
        assert(inner != 0);
        xmlAutomataPopParticle(automaton, inner);
        xmlAutomataPopParticle(automaton, parent);
        /* Re-entering the same path reuses the map entry without allocation. */
        count = attempts;
        assert(xmlAutomataPushParticle(automaton, &source[i], &parent) == 0);
        assert(xmlAutomataPushParticle(automaton, &source[0], &inner) == 0);
        assert(attempts == count);
        xmlAutomataPopParticle(automaton, inner);
        xmlAutomataPopParticle(automaton, parent);
    }
    armed = 0;
    assert(success == !failed);
    count = attempts;
    xmlFreeAutomata(automaton);
    xmlResetLastError();
    return count;
}

int main(void) {
    size_t total, baseline;
    assert(xmlMemSetup(release, allocate, resize, duplicate) == 0);
    xmlInitParser();
    xmlSetGenericErrorFunc(NULL, error_handler);
    baseline = live;
    total = exercise(0);
    assert(total > 160);
    assert(live == baseline);
    for (size_t fault = 1; fault <= total; ++fault) {
        exercise(fault);
        assert(live == baseline);
    }
    assert(exercise(0) == total);
    assert(live == baseline);
    xmlCleanupParser();
    assert(live == 0);
    printf("Particle identity allocation cleanup: PASS (%zu fault points)\n", total);
    return 0;
}
