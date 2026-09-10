/* Copyright (C) 2026 Qore Technologies, s.r.o. */
#ifdef NDEBUG
#undef NDEBUG
#endif
/* The fixture uses private counter state to reach numeric boundaries directly. */
#include QORE_REGEXP_SOURCE
#include <assert.h>
#include <stdlib.h>
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


static xmlRegexpPtr model(const char *low, const char *high) {
    xmlAutomataPtr am = xmlNewAutomata();
    xmlAutomataStatePtr start, hop, end;
    int index;
    size_t parent;
    assert(am != NULL);
    assert(xmlAutomataPushParticle(am, low, &parent) == 0);
    start = xmlAutomataGetInitState(am);
    index = xmlAutomataNewCounter(am, 0, 1073741824);
    assert(index == 0);
    assert(xmlAutomataSetExactCounter(am, index, low, high, 1, 0) == 0);
    hop = xmlAutomataNewTransition(am, start, NULL, BAD_CAST "a", NULL);
    assert(hop != NULL);
    assert(xmlAutomataNewCountedTrans(am, hop, start, index) != NULL);
    end = xmlAutomataNewCounterTrans(am, hop, NULL, index);
    assert(end != NULL);
    assert(xmlAutomataSetFinalState(am, end) == 0);
    xmlAutomataPopParticle(am, parent);
    xmlRegexpPtr compiled = xmlAutomataCompile(am);
    assert(compiled != NULL && compiled->counters[0].exact != NULL);
    xmlFreeAutomata(am);
    return compiled;
}
static void seed(xmlRegExecCtxtPtr e, const char *value) {
    xmlRegCountLexical lexical;
    assert(xmlRegCountParse(value, 0, &lexical) == 0);
    xmlRegCountRead(e->wideCounts, &lexical);
}
static size_t exercise(xmlRegexpPtr compiled, size_t fault) {
    xmlRegExecCtxtPtr execution;
    size_t count;
    int result = -1;
    attempts = 0; fail_at = fault; failed = 0; armed = 1;
    execution = xmlRegNewExecCtxt(compiled, NULL, NULL);
    if (execution != NULL) {
        seed(execution, "99999999999999999999999999999999999999999999999999999999999999999999999999999998");
        result = xmlRegExecPushString(execution, BAD_CAST "a", NULL);
        if (result >= 0) {
            result = xmlRegExecPushString(execution, BAD_CAST "a", NULL);
        }
        if (result >= 0) {
            result = xmlRegExecPushString(execution, NULL, NULL);
        }
    }
    armed = 0;
    assert(failed ? result < 0 : result == 1);
    count = attempts;
    xmlRegFreeExecCtxt(execution);
    xmlResetLastError();
    return count;
}

/* Distinct widths share one executor allocation without aliasing. The ordinary
 * INT_MAX case must stay finite, while an unbounded value saturates at its minimum. */
static void counter_slots(void) {
    xmlAutomataPtr am = xmlNewAutomata();
    xmlAutomataStatePtr start, end;
    xmlRegexpPtr compiled;
    xmlRegExecCtxtPtr execution;
    const char *minimum[] = {"2147483646", "99999999999999999999", "2"};
    const char *maximum[] = {"2147483647", "100000000000000000000", "unbounded"};
    size_t parent;
    assert(am != NULL);
    assert(xmlAutomataPushParticle(am, minimum, &parent) == 0);
    for (int index = 0; index < 3; ++index) {
        assert(xmlAutomataNewCounter(am, 0, 1073741824) == index);
        assert(xmlAutomataSetExactCounter(am, index, minimum[index], maximum[index], 0, 0) == 0);
    }
    start = xmlAutomataGetInitState(am);
    end = xmlAutomataNewCountedTrans(am, start, NULL, 0);
    assert(end != NULL);
    end = xmlAutomataNewTransition(am, end, NULL, BAD_CAST "a", NULL);
    assert(end != NULL && xmlAutomataSetFinalState(am, end) == 0);
    xmlAutomataPopParticle(am, parent);
    compiled = xmlAutomataCompile(am);
    assert(compiled != NULL);
    xmlFreeAutomata(am);
    assert(compiled->nbCounters == 3 && compiled->counters[0].exact == NULL);
    assert(compiled->counters[0].max == INT_MAX);
    assert(compiled->counters[1].exact->offset == 0);
    assert(compiled->counters[2].exact->offset == compiled->counters[1].exact->size);
    execution = xmlRegNewExecCtxt(compiled, NULL, NULL);
    assert(execution != NULL);
    execution->counts[0] = INT_MAX - 1;
    assert(xmlRegCounterInRange(execution, 0) && xmlRegCounterCanIncrement(execution, 0, 0));
    assert(xmlRegCounterIncrement(execution, 0) == 0);
    assert(xmlRegCounterInRange(execution, 0) && !xmlRegCounterCanIncrement(execution, 0, 0));
    assert(!xmlRegCounterInRange(execution, 2));
    assert(xmlRegCounterIncrement(execution, 2) == 0 && !xmlRegCounterInRange(execution, 2));
    assert(xmlRegCounterIncrement(execution, 2) == 0 && xmlRegCounterInRange(execution, 2));
    for (int count = 0; count < 10; ++count) {
        assert(xmlRegCounterIncrement(execution, 2) == 0 && xmlRegCounterInRange(execution, 2));
    }
    assert(execution->wideCounts[compiled->counters[2].exact->offset] == 2);
    seed(execution, "99999999999999999999");
    assert(xmlRegCounterInRange(execution, 1));
    xmlFARegExecSave(execution);
    assert(execution->nbRollbacks == 1);
    for (int index = 0; index < 3; ++index) {
        xmlRegCounterReset(execution, index);
        assert(!xmlRegCounterInRange(execution, index));
    }
    xmlFARegExecRollBack(execution);
    for (int index = 0; index < 3; ++index) {
        assert(xmlRegCounterInRange(execution, index));
    }
    assert(execution->counts[0] == INT_MAX);
    assert(execution->wideCounts[compiled->counters[2].exact->offset] == 2);
    xmlRegCounterReset(execution, 1);
    assert(xmlRegCounterInRange(execution, 0) && xmlRegCounterInRange(execution, 2));
    xmlRegFreeExecCtxt(execution);
    xmlRegFreeRegexp(compiled);
}

int main(void) {
    size_t total, baseline;
    assert(xmlMemSetup(release, allocate, resize, duplicate) == 0);
    xmlInitParser();
    xmlSetGenericErrorFunc(NULL, error_handler);
    xmlRegexpPtr c = model("99999999999999999999999999999999999999999999999999999999999999999999999999999999", "100000000000000000000000000000000000000000000000000000000000000000000000000000000");
    xmlRegExecCtxtPtr e = xmlRegNewExecCtxt(c, NULL, NULL);
    assert(e != NULL);
    seed(e, "99999999999999999999999999999999999999999999999999999999999999999999999999999998");
    assert(xmlRegExecPushString(e, BAD_CAST "a", NULL) >= 0);
    assert(xmlRegExecPushString(e, NULL, NULL) == 1);
    xmlRegFreeExecCtxt(e);
    e = xmlRegNewExecCtxt(c, NULL, NULL);
    seed(e, "99999999999999999999999999999999999999999999999999999999999999999999999999999997");
    assert(xmlRegExecPushString(e, BAD_CAST "a", NULL) >= 0);
    assert(xmlRegExecPushString(e, NULL, NULL) != 1);
    xmlRegFreeExecCtxt(e);
    e = xmlRegNewExecCtxt(c, NULL, NULL);
    seed(e, "99999999999999999999999999999999999999999999999999999999999999999999999999999999");
    assert(xmlRegExecPushString(e, BAD_CAST "a", NULL) >= 0);
    assert(xmlRegExecPushString(e, BAD_CAST "a", NULL) < 0);
    xmlRegFreeExecCtxt(e);
    e = xmlRegNewExecCtxt(c, NULL, NULL);
    seed(e, "99999999999999999999999999999999999999999999999999999999999999999999999999999998");
    xmlFARegExecSave(e);
    assert(e->nbRollbacks == 1);
    assert(xmlRegCounterIncrement(e, 0) == 0);
    e->schemaEmptySeen[0] = 1;
    xmlFARegExecRollBack(e);
    assert(e->nbRollbacks == 0 && e->schemaEmptySeen[0] == 0);
    assert(xmlRegCountCompare(e->wideCounts, c->counters[0].exact->digits, c->counters[0].exact->size) == 0);
    xmlRegFreeExecCtxt(e);
    e = xmlRegNewExecCtxt(c, NULL, NULL);
    assert(e != NULL);
    seed(e, "99999999999999999999999999999999999999999999999999999999999999999999999999999998");
    assert(xmlRegExecPushString(e, BAD_CAST "b", NULL) < 0);
    assert(xmlRegCountCompare(e->errWideCounts, c->counters[0].exact->digits,
                             c->counters[0].exact->size) == 0);
    xmlRegCounterReset(e, 0);
    assert(xmlRegCounterCanIncrement(e, 0, 1));
    assert(xmlRegCountCompare(e->errWideCounts, c->counters[0].exact->digits,
                             c->counters[0].exact->size) == 0);
    xmlRegFreeExecCtxt(e);
    counter_slots();
    xmlRegexpPtr unbounded = model("99999999999999999999999999999999999999999999999999999999999999999999999999999999", "unbounded");
    e = xmlRegNewExecCtxt(unbounded, NULL, NULL);
    assert(e != NULL);
    seed(e, "99999999999999999999999999999999999999999999999999999999999999999999999999999998");
    for (int index = 0; index < 4; ++index) {
        assert(xmlRegExecPushString(e, BAD_CAST "a", NULL) >= 0);
    }
    assert(xmlRegExecPushString(e, NULL, NULL) == 1);
    xmlRegFreeExecCtxt(e);
    xmlRegFreeRegexp(unbounded);
    xmlResetLastError();
    baseline = live;
    total = exercise(c, 0);
    assert(total > 5);
    assert(live == baseline);
    for (size_t fault = 1; fault <= total; ++fault) {
        exercise(c, fault);
        assert(live == baseline);
    }
    assert(exercise(c, 0) == total);
    assert(live == baseline);
    xmlRegFreeRegexp(c);
    xmlCleanupParser();
    assert(live == 0);
    printf("Exact native counter execution and rollback: PASS (%zu allocation faults)\n", total);
    return 0;
}
