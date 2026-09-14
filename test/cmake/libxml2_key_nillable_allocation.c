/* Copyright (C) 2026 Qore Technologies, s.r.o. */
#ifdef NDEBUG
#undef NDEBUG
#endif
/* Compile the checked native schema source to exercise its private checker. */
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

/* Isolate the new rejection branch after XPath matching and value assessment.
 * Schema construction and tuple allocation have separate fault-injection suites. */
static size_t reject(size_t fault, int permanent) {
    xmlSchemaValidCtxtPtr context = xmlSchemaNewValidCtxt(NULL);
    xmlPatternPtr pattern = xmlPatterncompile(BAD_CAST ".", NULL, XML_PATTERN_XSFIELD, NULL);
    xmlStreamCtxtPtr stream;
    xmlSchemaIDCStateObj state = {0};
    xmlSchemaIDCMatcher matcher = {0};
    xmlSchemaIDCAug augmented = {0};
    xmlSchemaIDC definition = {0};
    xmlSchemaNodeInfo node = {0};
    xmlSchemaElement declaration = {0};
    int history = 0;
    size_t count;
    assert(context != NULL && pattern != NULL);
    stream = xmlPatternGetStreamCtxt(pattern);
    assert(stream != NULL);
    assert(xmlStreamPush(stream, NULL, NULL) >= 0);
    assert(xmlStreamPush(stream, BAD_CAST "row", NULL) >= 0);
    definition.type = XML_SCHEMA_TYPE_IDC_KEY;
    definition.name = BAD_CAST "K";
    augmented.def = &definition;
    matcher.aidc = &augmented;
    state.type = XPATH_STATE_OBJ_TYPE_IDC_FIELD;
    state.matcher = &matcher;
    state.history = &history;
    state.nbHistory = state.sizeHistory = 1;
    state.xpathCtxt = stream;
    declaration.flags = XML_SCHEMAS_ELEM_NILLABLE;
    node.nodeType = XML_ELEMENT_NODE;
    node.localName = BAD_CAST "row";
    node.decl = &declaration;
    node.typeDef = xmlSchemaGetBuiltInType(XML_SCHEMAS_INT);
    context->inode = &node;
    context->xpathStates = &state;
    xmlSchemaSetValidErrors(context, error_handler, error_handler, NULL);
    attempts = 0;
    fail_at = fault;
    failed = 0;
    persistent = permanent;
    armed = 1;
    assert(xmlSchemaXPathProcessHistory(context, 0) == 0);
    armed = 0;
    count = attempts;
    assert(failed == (fault != 0));
    assert(context->err != 0);
    if (!failed) {
        assert(context->err == XML_SCHEMAV_CVC_IDC);
    }
    assert(state.nbHistory == 0);
    assert(context->xpathStates == NULL && context->xpathStatePool == &state);
    /* Detach the stack-owned test state before normal context cleanup. */
    context->xpathStatePool = NULL;
    context->inode = NULL;
    xmlFreeStreamCtxt(stream);
    xmlFreePattern(pattern);
    xmlSchemaFreeValidCtxt(context);
    xmlResetLastError();
    return count;
}

int main(void) {
    size_t baseline, count, fault;
    int permanent;
    assert(xmlMemSetup(release, allocate, resize, duplicate) == 0);
    xmlInitParser();
    assert(xmlSchemaInitTypes() == 0);
    baseline = live;
    count = reject(0, 0);
    assert(count > 0 && live == baseline);
    for (permanent = 0; permanent < 2; ++permanent) {
        for (fault = 1; fault <= count; ++fault) {
            reject(fault, permanent);
            assert(live == baseline);
            reject(0, 0);
            assert(live == baseline);
        }
    }
    xmlCleanupParser();
    assert(live == 0);
    printf("Native key nillable allocation: PASS (%zu fault positions)\n", count);
    return 0;
}
