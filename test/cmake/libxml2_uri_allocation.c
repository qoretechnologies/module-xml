/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Fail each allocation in URI/XML Base resolution and verify recovery.
 * This standalone process installs the hooks before initializing libxml2.
 */
#include <libxml/parser.h>
#include <libxml/tree.h>
#include <libxml/uri.h>
#include <libxml/xmlmemory.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned allocations;
static unsigned fail_at;
static int armed;

static int fail_allocation(void) {
    if (!armed) {
        return (0);
    }
    ++allocations;
    return (fail_at != 0 && allocations == fail_at);
}

static void *test_malloc(size_t size) { return (fail_allocation() ? NULL : malloc(size)); }

static void *test_realloc(void *value, size_t size) { return (fail_allocation() ? NULL : realloc(value, size)); }

static char *test_strdup(const char *value) {
    size_t size = strlen(value) + 1;
    char *copy = test_malloc(size);
    if (copy != NULL) {
        memcpy(copy, value, size);
    }
    return (copy);
}

int main(void) {
    static const char source[] = "<r xml:base='http://example.org/wine/'><e xml:base='rosé%2Fwine'/></r>";
    xmlDoc *document;
    xmlNode *node;
    unsigned mode, checks = 0;
    if (xmlMemSetup(free, test_malloc, test_realloc, test_strdup) != 0) {
        return (1);
    }
    xmlInitParser();
    document = xmlReadMemory(source, sizeof(source) - 1, "http://example.org/source.xml", NULL, 0);
    if (document == NULL) {
        return (1);
    }
    node = xmlDocGetRootElement(document)->children;
    for (mode = 0; mode < 2; ++mode) {
        unsigned point, count = 0;
        for (point = 0; point <= count + 1; ++point) {
            xmlChar *result;
            const char *expected = mode ? "http://example.org/wine/rosé%2Fwine" : "http://example.org/base/a%2Fb:c";
            allocations = 0;
            fail_at = point;
            armed = 1;
            result = mode ? xmlNodeGetBase(document, node)
                          : xmlBuildURI(BAD_CAST "./a%2Fb:c", BAD_CAST "http://example.org/base/main.xsd");
            armed = 0;
            if (point == 0) {
                count = allocations;
                if (count == 0) {
                    xmlFree(result);
                    xmlFreeDoc(document);
                    return (1);
                }
            }
            ++checks;
            if ((point > 0 && point <= count) ? result != NULL
                                              : (result == NULL || strcmp((const char *)result, expected) != 0)) {
                fprintf(stderr, "URI allocation mode %u point %u/%u failed\n", mode, point, count);
                xmlFree(result);
                xmlFreeDoc(document);
                xmlCleanupParser();
                return (1);
            }
            xmlFree(result);
        }
    }
    xmlFreeDoc(document);
    xmlCleanupParser();
    printf("%u URI allocation/recovery checks passed\n", checks);
    return (0);
}
