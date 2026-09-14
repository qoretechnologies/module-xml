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

/* Isolate nil field capture after XPath matching. Inject every sequence/key
 * allocation failure, checking context error identity and retained ownership. */
static size_t assess(size_t fault, int permanent) {
    xmlSchemaValidCtxtPtr context = xmlSchemaNewValidCtxt(NULL);
    xmlPatternPtr pattern = xmlPatterncompile(BAD_CAST ".", NULL, XML_PATTERN_XSFIELD, NULL);
    xmlStreamCtxtPtr stream;
    xmlSchemaIDCStateObj state = {0};
    xmlSchemaIDCMatcher matcher = {0};
    xmlSchemaIDCAug augmented = {0};
    xmlSchemaIDC definition = {0};
    xmlSchemaIDCSelect field = {0};
    int status;
    xmlSchemaNodeInfo node = {0};
    xmlSchemaElement declaration = {0};
    int history = 0;
    size_t count;
    assert(context != NULL && pattern != NULL);
    stream = xmlPatternGetStreamCtxt(pattern);
    assert(stream != NULL);
    assert(xmlStreamPush(stream, NULL, NULL) >= 0);
    assert(xmlStreamPush(stream, BAD_CAST "row", NULL) >= 0);
    definition.type = XML_SCHEMA_TYPE_IDC_UNIQUE;
    definition.nbFields = 1;
    field.xpath = BAD_CAST ".";
    state.sel = &field;
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
    node.flags = XML_SCHEMA_ELEM_INFO_NILLED;
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
    status = xmlSchemaXPathProcessHistory(context, 0);
    armed = 0;
    count = attempts;
    assert(failed == (fault != 0));
    if (failed) {
        assert(status == -1 && context->err == XML_ERR_NO_MEMORY);
    } else {
        assert(status == 0 && context->err == 0);
        assert(state.nbHistory == 0);
        assert(context->xpathStates == NULL && context->xpathStatePool == &state);
        assert(matcher.keySeqs != NULL && matcher.keySeqs[0] != NULL);
        assert(matcher.keySeqs[0][0] != NULL && matcher.keySeqs[0][0]->val == NULL);
        assert(context->nbIdcKeys == 1 && context->idcKeys[0] == matcher.keySeqs[0][0]);
    }
    /* Detach stack-owned state and free the test-owned matcher sequence.
     * The context owns every successfully stored nil key. */
    context->xpathStatePool = context->xpathStates = NULL;
    context->inode = NULL;
    if (matcher.keySeqs != NULL) {
        xmlFree(matcher.keySeqs[0]);
        xmlFree(matcher.keySeqs);
    }
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
    count = assess(0, 0);
    assert(count > 0 && live == baseline);
    for (permanent = 0; permanent < 2; ++permanent) {
        for (fault = 1; fault <= count; ++fault) {
            assess(fault, permanent);
            assert(live == baseline);
            assess(0, 0);
            assert(live == baseline);
        }
    }
    xmlCleanupParser();
    assert(live == 0);
    printf("Native nil identity allocation: PASS (%zu fault positions)\n", count);
    return 0;
}
