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


#include "../../cmake/libxml2-particle-attribution-math.inc"
#include "../../cmake/libxml2-particle-attribution-sets.inc"
static int overlaps(void *data, const xmlSchemaUpaTerm *left, const xmlSchemaUpaTerm *right) {
    (void)data;
    return left->wildcard != NULL || right->wildcard != NULL || strcmp((const char *)left->key, (const char *)right->key) == 0;
}
static size_t exercise(size_t fault) {
    xmlSchemaUpaContext context = {0};
    xmlSchemaUpaInt *three, *two, *difference;
    const xmlSchemaUpaRatio *ratio, *threshold;
    xmlSchemaUpaTerm a = {.name = BAD_CAST "a", .key = "a"};
    xmlSchemaUpaTerm b = {.name = BAD_CAST "b", .key = "b"};
    xmlSchemaUpaTerm any = {.wildcard = &context, .key = "wild"};
    xmlSchemaUpaMap *first = NULL, *follow = NULL, *copy, *wild = NULL;
    attempts = 0; fail_at = fault; failed = 0; armed = 1;
    if (xmlSchemaUpaInit(&context) < 0) {
        goto done;
    }
    context.overlap = overlaps;
    three = xmlSchemaUpaDecimalInt(&context.memory, "3", 1);
    two = xmlSchemaUpaDecimalInt(&context.memory, "2", 1);
    if (context.memory.failed) {
        goto done;
    }
    difference = xmlSchemaUpaSubtractInt(&context.memory, three, two);
    ratio = xmlSchemaUpaNewRatio(&context.memory, three, two);
    threshold = xmlSchemaUpaThreshold(&context, three, two);
    if (context.memory.failed) {
        goto done;
    }
    assert(xmlSchemaUpaCompareInt(difference, context.oneInt) == 0);
    assert(!xmlSchemaUpaApplies(threshold));
    assert(xmlSchemaUpaWithContext(&context, threshold, 0) == NULL);
    assert(xmlSchemaUpaWithContext(&context, threshold, 1) == threshold);
    assert(xmlSchemaUpaScale(&context, threshold, NULL) == context.zero);
    assert(xmlSchemaUpaScale(&context, NULL, two) == NULL);
    assert(xmlSchemaUpaMinimum(&context, NULL, ratio) == ratio);
    assert(xmlSchemaUpaMaximum(&context, NULL, ratio) == NULL);
    (void)xmlSchemaUpaMaximum(&context, context.one, ratio);
    if (context.memory.failed) {
        goto done;
    }
    assert(xmlSchemaUpaScale(&context, threshold, two) == context.zero || context.memory.failed);
    if (context.memory.failed) {
        goto done;
    }
    xmlSchemaUpaPut(&context, &first, &a, context.zero);
    xmlSchemaUpaPut(&context, &follow, &a, threshold);
    xmlSchemaUpaPut(&context, &follow, &b, context.zero);
    if (context.memory.failed) {
        goto done;
    }
    assert(xmlSchemaUpaIntersection(&context, follow, first) == threshold);
    copy = xmlSchemaUpaContexts(&context, follow, 0);
    if (context.memory.failed) {
        goto done;
    }
    assert(xmlSchemaUpaLookup(copy, &a) == NULL);
    assert(xmlSchemaUpaLookup(copy, &b)->threshold == context.zero);
    xmlSchemaUpaMerge(&context, &copy, first);
    if (context.memory.failed) {
        goto done;
    }
    assert(xmlSchemaUpaApplies(xmlSchemaUpaLookup(copy, &a)->threshold));
    xmlSchemaUpaPut(&context, &wild, &any, context.zero);
    context.hasWildcards = 1;
    if (context.memory.failed) {
        goto done;
    }
    threshold = xmlSchemaUpaIntersection(&context, follow, wild);
    if (!context.memory.failed) {
        assert(xmlSchemaUpaApplies(threshold));
    }
    if (context.memory.failed) {
        goto done;
    }
    {
        xmlSchemaUpaInfo aInfo = {.ratio = context.one};
        xmlSchemaUpaInfo bInfo = {.ratio = context.one};
        xmlSchemaUpaInfo optional, range, inner, outer;
        xmlSchemaUpaPut(&context, &aInfo.first, &a, context.zero);
        xmlSchemaUpaPut(&context, &bInfo.first, &b, context.zero);
        if (context.memory.failed) {
            goto done;
        }
        optional = xmlSchemaUpaRepeat(&context, &bInfo, context.zeroInt, context.oneInt);
        range = xmlSchemaUpaRepeat(&context, &aInfo, two, three);
        inner = xmlSchemaUpaCopyInfo(&context, &optional);
        xmlSchemaUpaCombine(&context, &inner, &range, 0);
        outer = xmlSchemaUpaRepeat(&context, &inner, two, two);
        xmlSchemaUpaCombine(&context, &outer, &bInfo, 0);
        if (context.memory.failed) {
            goto done;
        }
        assert(!xmlSchemaUpaApplies(outer.plain));
        outer = xmlSchemaUpaRepeat(&context, &inner, three, three);
        xmlSchemaUpaCombine(&context, &outer, &bInfo, 0);
        if (context.memory.failed) {
            goto done;
        }
        assert(xmlSchemaUpaApplies(outer.plain));
        outer = xmlSchemaUpaCopyInfo(&context, &aInfo);
        xmlSchemaUpaCombine(&context, &outer, &aInfo, 1);
        if (!context.memory.failed) {
            assert(xmlSchemaUpaApplies(outer.plain));
        }
    }
done:
    armed = 0;
    assert(context.memory.failed == failed);
    xmlSchemaUpaCleanup(&context);
    xmlResetLastError();
    return attempts;
}
int main(void) {
    size_t total, baseline;
    assert(xmlMemSetup(release, allocate, resize, duplicate) == 0);
    xmlInitParser(); xmlSetGenericErrorFunc(NULL, error_handler);
    baseline = live;
    total = exercise(0);
    assert(total > 30);
    assert(live == baseline);
    for (size_t fault = 1; fault <= total; ++fault) {
        exercise(fault);
        assert(live == baseline);
    }
    assert(exercise(0) == total);
    assert(live == baseline);
    xmlCleanupParser(); assert(live == 0);
    printf("Native UPA arithmetic/sets: PASS (%zu allocation faults)\n", total);
    return 0;
}
