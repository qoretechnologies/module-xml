/* Copyright (C) 2026 Qore Technologies, s.r.o. */
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <libxml/xmlschemastypes.h>
#include <libxml/parser.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static size_t calls, fail_at, live;
static int failed;
static int fail(void) {
    if (fail_at && ++calls == fail_at) {
        failed = 1;
        return 1;
    }
    return 0;
}
static void *allocate(size_t n) {
    void *p;
    if (fail()) {
        return NULL;
    }
    p = malloc(n);
    live += p != NULL;
    return p;
}
static void release(void *p) {
    if (p) {
        assert(live);
        --live;
    }
    free(p);
}
static void *resize(void *p, size_t n) {
    void *result;
    int was_null = p == NULL;
    if (n == 0) {
        release(p);
        return NULL;
    }
    if (fail()) {
        return NULL;
    }
    result = realloc(p, n);
    live += was_null && result != NULL;
    return result;
}
static char *duplicate(const char *s) {
    size_t n = strlen(s) + 1;
    char *p = allocate(n);
    if (p) {
        memcpy(p, s, n);
    }
    return p;
}
static void quiet(void *context, const char *message, ...) {
    (void)context;
    (void)message;
}
int main(void) {
    const char *types[] = {"dateTime", "time", "date", "gYear", "gYearMonth", "gMonth", "gMonthDay", "gDay"};
    const char *texts[] = {"-0001-12-31T24:00:00Z", "00:00:00.123456789012345678901234567890123456789+01:00",
        "9999-12-31-14:00", "-9999-01:00", "9999-12-14:00", "--12+01:00", "--02-29-14:00", "---31+14:00"};
    size_t i, index, tested = 0;
    char extended[2100];
    memset(extended, '9', 1000);
    {
        const char clock[] = "-12-31T23:59:59.";
        size_t fraction_start = 1000 + sizeof(clock) - 1;
        memcpy(extended + 1000, clock, sizeof(clock) - 1);
        memset(extended + fraction_start, '1', 1000);
        strcpy(extended + fraction_start + 1000, "-14:00");
    }
    texts[0] = extended;
    assert(xmlMemSetup(release, allocate, resize, duplicate) == 0);
    xmlInitParser();
    xmlSetGenericErrorFunc(NULL, quiet);
    for (i = 0; i < sizeof(types)/sizeof(types[0]); ++i) {
        xmlSchemaTypePtr type = xmlSchemaGetPredefinedType(BAD_CAST types[i], BAD_CAST "http://www.w3.org/2001/XMLSchema");
        xmlSchemaValPtr initial = NULL;
        const xmlChar *expected = NULL;
        size_t baseline;
        assert(xmlSchemaValidatePredefinedType(type, BAD_CAST texts[i], &initial) == 0);
        assert(xmlSchemaGetCanonValue(initial, &expected) == 0 && expected != NULL);
        xmlSchemaFreeValue(initial);
        baseline = live;
        for (index = 1; index < 200; ++index) {
            xmlSchemaValPtr value = NULL, copy = NULL, unknown = NULL;
            const xmlChar *canonical = NULL;
            int result, propagated = 0;
            calls = 0;
            failed = 0;
            fail_at = index;
            result = xmlSchemaValidatePredefinedType(type, BAD_CAST texts[i], &value);
            if (result != 0) {
                assert(result == -1 && value == NULL);
                propagated = 1;
            } else {
                copy = xmlSchemaCopyValue(value);
                if (copy == NULL) {
                    propagated = 1;
                } else {
                    result = xmlSchemaGetCanonValue(copy, &canonical);
                    if (result != 0) {
                        assert(result == -1 && canonical == NULL);
                        propagated = 1;
                    } else {
                        result = xmlSchemaCompareValues(value, copy);
                        assert(result == 0 || result == -2);
                        propagated = result == -2;
                        if (!propagated && i == 1) {
                            result = xmlSchemaValidatePredefinedType(type, BAD_CAST "09:39:60.22", &unknown);
                            if (result != 0) {
                                assert(result == -1 && unknown == NULL);
                                propagated = 1;
                            } else {
                                result = xmlSchemaCompareValues(value, unknown);
                                assert(result == 2 || result == -2);
                                propagated = result == -2;
                            }
                        }
                    }
                }
            }
            fail_at = 0;
            assert(propagated == failed);
            xmlFree((void *)canonical);
            if (value != NULL) {
                canonical = NULL;
                assert(xmlSchemaGetCanonValue(value, &canonical) == 0 && xmlStrEqual(canonical, expected));
                xmlFree((void *)canonical);
            }
            xmlSchemaFreeValue(unknown);
            xmlSchemaFreeValue(copy);
            xmlSchemaFreeValue(value);
            assert(live == baseline);
            if (!failed) {
                break;
            }
            ++tested;
        }
        assert(index < 200);
        xmlFree((void *)expected);
    }
    xmlCleanupParser();
    assert(live == 0);
    printf("%zu allocation failures propagated with intact ownership and successful recovery\n", tested);
    return 0;
}
