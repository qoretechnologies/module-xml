/* Copyright (C) 2026 Qore Technologies, s.r.o. */
#ifdef NDEBUG
#undef NDEBUG
#endif
/* Compile the checked native schema source to exercise its private checker. */
#define IN_LIBXML
#include "libxml.h"
#include <libxml/xmlschemastypes.h>
#include QORE_XML_SCHEMA_SOURCE
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
static size_t live, attempts, fail_at;
static int armed, failed, persistent;
static void *allocate(size_t size) {
    void *p;
    if (armed && (++attempts == fail_at || (persistent && attempts > fail_at)) && fail_at != 0) {
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
    if (armed && (++attempts == fail_at || (persistent && attempts > fail_at)) && fail_at != 0) {
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


enum FaultScope { INSTANCE, COMPLEX, VALUE, FORMAT, REJECT };
static enum FaultScope selected;
static int reached;
static void begin(xmlSchemaValidCtxtPtr context, enum FaultScope scope) {
    if (scope == selected && context->depth == 1 && !reached) {
        reached = 1;
        armed = 1;
    }
}
static int qoreFaultInstanceAttributes(xmlSchemaValidCtxtPtr context) {
    int result;
    begin(context, INSTANCE);
    result = xmlSchemaVInstanceAttributes(context);
    armed = 0;
    return result;
}
static int qoreFaultComplexAttributes(xmlSchemaValidCtxtPtr context) {
    int result;
    begin(context, COMPLEX);
    result = xmlSchemaVAttributesComplex(context);
    armed = 0;
    return result;
}
static int qoreFaultNativeValue(xmlSchemaValidCtxtPtr context, xmlSchemaNodeInfoPtr node,
        xmlSchemaTypePtr type, const xmlChar *text) {
    int result;
    begin(context, VALUE);
    result = xmlSchemaVCheckINodeDataType(context, node, type, text);
    armed = 0;
    return result;
}
static const xmlChar *qoreFaultFormat(xmlSchemaValidCtxtPtr context, xmlChar **buffer,
        xmlSchemaPSVIIDCKeyPtr *sequence, int count, int hash) {
    const xmlChar *result;
    begin(context, FORMAT);
    result = xmlSchemaFormatIDCKeySequence_1(context, buffer, sequence, count, hash);
    armed = 0;
    return result;
}
/* libxml2 retains its thread-local error record independently of a validator.
 * Reset that record before comparing validation-owned allocation counts. */
static size_t assess(xmlSchemaPtr schema, xmlDocPtr doc, size_t fault, int permanent) {
    size_t previous = live, count;
    xmlSchemaValidCtxtPtr context = xmlSchemaNewValidCtxt(schema);
    int result;
    assert(context != NULL);
    xmlSchemaSetValidErrors(context, error_handler, error_handler, NULL);
    attempts = 0;
    fail_at = fault;
    persistent = permanent;
    failed = reached = 0;
    result = xmlSchemaValidateDoc(context, doc);
    count = attempts;
    assert(reached || selected == REJECT);
    if (fault != 0) {
        assert(failed);
        if (result == 0) {
            fprintf(stderr, "unreported fault scope %d position %zu/%d\n", selected, fault, permanent);
            abort();
        }
    } else {
        assert(selected == REJECT ? result != 0 : result == 0);
    }
    if (selected == REJECT) {
        assert(xmlSchemaValidateDoc(context, doc) != 0);
    }
    xmlSchemaFreeValidCtxt(context);
    xmlResetLastError();
    if (live != previous) {
        fprintf(stderr, "leak at fault %zu/%d: %zu -> %zu\n", fault, permanent, previous, live);
        abort();
    }
    return count;
}
/* Exercise buffer growth as well as short and unqualified expanded names. */
static size_t format_names(void) {
    char long_uri[256];
    const char *uris[3];
    size_t total = 0;
    int notation, i;
    memset(long_uri, 'u', sizeof(long_uri) - 1);
    long_uri[sizeof(long_uri) - 1] = 0;
    uris[0] = NULL;
    uris[1] = "urn:a";
    uris[2] = long_uri;
    for (notation = 0; notation < 2; ++notation) {
        for (i = 0; i < 3; ++i) {
            xmlChar *uri = uris[i] == NULL ? NULL : xmlStrdup(BAD_CAST uris[i]);
            xmlChar *name = xmlStrdup(BAD_CAST "name");
            xmlSchemaValPtr value = notation ? xmlSchemaNewNOTATIONValue(name, uri)
                : xmlSchemaNewQNameValue(uri, name);
            size_t position, count = 0;
            assert(value != NULL);
            for (position = 0; position <= count; ++position) {
                int mode;
                for (mode = 0; mode < 2; ++mode) {
                    const xmlChar *text = NULL;
                    size_t previous = live;
                    int result;
                    attempts = 0;
                    fail_at = position;
                    persistent = mode;
                    failed = 0;
                    armed = 1;
                    result = xmlSchemaGetCanonValue(value, &text);
                    armed = 0;
                    if (position == 0) {
                        assert(result == 0 && text != NULL);
                        count = attempts;
                    } else {
                        assert(failed && result < 0 && text == NULL);
                    }
                    xmlFree((void *)text);
                    xmlResetLastError();
                    assert(live == previous);
                }
            }
            total += count;
            xmlSchemaFreeValue(value);
        }
    }
    return total;
}

int main(int argc, char **argv) {
    int i;
    size_t total = 0;
    assert(argc > 3 && argc % 3 == 1);
    assert(xmlMemSetup(release, allocate, resize, duplicate) == 0);
    xmlSetGenericErrorFunc(NULL, error_handler);
    xmlInitParser();
    total += format_names();
    for (i = 1; i < argc; i += 3) {
        selected = (enum FaultScope)atoi(argv[i]);
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewParserCtxt(argv[i+1]);
        xmlSchemaPtr schema = xmlSchemaParse(parser);
        xmlDocPtr doc = xmlReadFile(argv[i+2], NULL, XML_PARSE_NONET);
        size_t count, fault;
        assert(schema != NULL && doc != NULL);
        xmlSchemaFreeParserCtxt(parser);
        count = assess(schema, doc, 0, 0);
        total += count;
        for (fault = 1; fault <= count; ++fault) {
            assess(schema, doc, fault, 0);
            assess(schema, doc, 0, 0);
            assess(schema, doc, fault, 1);
            assess(schema, doc, 0, 0);
        }
        xmlFreeDoc(doc);
        xmlSchemaFree(schema);
    }
    xmlCleanupParser();
    assert(live == 0);
    printf("Native instance identity allocation: PASS (%zu positions)\n", total);
    return 0;
}
