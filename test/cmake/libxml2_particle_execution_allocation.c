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
#include <libxml/xmlregexp.h>
#include <libxml/hash.h>
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


static size_t exercise(xmlRegexpPtr model, size_t fault) {
    static const char *tokens[] = {"a", "a", "a", "a", "b"};
    xmlRegExecCtxtPtr execution;
    size_t count;
    int result = -1;
    attempts = 0; fail_at = fault; failed = 0; armed = 1;
    execution = xmlRegNewExecCtxt(model, NULL, NULL);
    if (execution != NULL) {
        result = 0;
        for (size_t index = 0; index < sizeof(tokens) / sizeof(tokens[0]); ++index) {
            result = xmlRegExecPushString(execution, BAD_CAST tokens[index], NULL);
            if (result < 0) {
                break;
            }
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
int main(void) {
    const char *source = "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
        "<xs:complexType name='Record'><xs:sequence>"
        "<xs:sequence minOccurs='2' maxOccurs='2'><xs:element name='b' minOccurs='0'/>"
        "<xs:element name='a' minOccurs='2' maxOccurs='3'/></xs:sequence><xs:element name='b'/>"
        "</xs:sequence></xs:complexType></xs:schema>";
    xmlSchemaParserCtxtPtr parser;
    xmlSchemaPtr schema;
    xmlSchemaTypePtr type;
    size_t total, baseline;
    assert(xmlMemSetup(release, allocate, resize, duplicate) == 0);
    xmlInitParser();
    xmlSetGenericErrorFunc(NULL, error_handler);
    parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
    assert(parser != NULL);
    xmlSchemaSetParserErrors(parser, error_handler, error_handler, NULL);
    schema = xmlSchemaParse(parser);
    assert(schema != NULL);
    xmlSchemaFreeParserCtxt(parser);
    type = xmlHashLookup(schema->typeDecl, BAD_CAST "Record");
    assert(type != NULL && type->contModel != NULL);
    baseline = live;
    total = exercise(type->contModel, 0);
    assert(total > 10);
    assert(live == baseline);
    for (size_t fault = 1; fault <= total; ++fault) {
        exercise(type->contModel, fault);
        assert(live == baseline);
    }
    assert(exercise(type->contModel, 0) == total);
    assert(live == baseline);
    xmlSchemaFree(schema);
    xmlCleanupParser();
    assert(live == 0);
    printf("Native particle execution cleanup: PASS (%zu fault points)\n", total);
    return 0;
}
