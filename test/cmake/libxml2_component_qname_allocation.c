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

/* Isolate component QName extraction and lookup from unrelated parser phases. */
static size_t resolve(const char *text, const char *expected_uri, const char *expected_local,
                      int valid, size_t fault, int permanent) {
    xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(" ", 1);
    const char *source = "<value xmlns:p='urn:partner' xmlns='urn:default'/>";
    xmlDocPtr document = xmlReadMemory(source, (int) strlen(source), NULL, NULL, XML_PARSE_NONET);
    xmlSchemaPtr schema;
    xmlAttrPtr attribute;
    const xmlChar *uri = NULL, *local = NULL;
    int status;
    size_t count;
    assert(parser != NULL && document != NULL);
    schema = xmlSchemaNewSchema(parser);
    assert(schema != NULL);
    attribute = xmlNewProp(xmlDocGetRootElement(document), BAD_CAST "refer", BAD_CAST text);
    assert(attribute != NULL);
    xmlSchemaSetParserErrors(parser, error_handler, error_handler, NULL);
    attempts = 0;
    fail_at = fault;
    failed = 0;
    persistent = permanent;
    armed = 1;
    status = xmlSchemaPValAttrNodeQName(parser, schema, NULL, attribute, &uri, &local);
    armed = 0;
    count = attempts;
    assert(failed == (fault != 0));
    if (failed) {
        /* Valid input must report allocation failure, never an unbound prefix.
         * Invalid input may retain its primary syntax error if formatting fails. */
        if (status == 0 || parser->err == 0 || (valid && parser->err != XML_ERR_NO_MEMORY)) {
            fprintf(stderr, "QName %s fault %zu permanent %d: status %d error %d\n", text, fault, permanent, status, parser->err);
            abort();
        }
    } else if (valid) {
        assert(status == 0 && parser->err == 0);
        assert(xmlStrEqual(uri, BAD_CAST expected_uri));
        assert(xmlStrEqual(local, BAD_CAST expected_local));
    } else {
        assert(status > 0 && parser->err != 0);
    }
    xmlSchemaFree(schema);
    xmlFreeDoc(document);
    xmlSchemaFreeParserCtxt(parser);
    xmlResetLastError();
    return count;
}

int main(void) {
    static const struct {
        const char *text, *uri, *local;
        int valid;
    } cases[] = {
        {"plain", "urn:default", "plain", 1},
        {"  plain \t\n", "urn:default", "plain", 1},
        {" p:local\r\n", "urn:partner", "local", 1},
        {"xml:lang", "http://www.w3.org/XML/1998/namespace", "lang", 1},
        {"", NULL, NULL, 0}, {" ", NULL, NULL, 0},
        {"a:b:c", NULL, NULL, 0}, {"p: local", NULL, NULL, 0},
        {"missing:local", NULL, NULL, 0}
    };
    unsigned int i;
    size_t baseline, count, fault;
    int permanent;
    assert(xmlMemSetup(release, allocate, resize, duplicate) == 0);
    xmlInitParser();
    assert(xmlSchemaInitTypes() == 0);
    baseline = live;
    for (i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        count = resolve(cases[i].text, cases[i].uri, cases[i].local, cases[i].valid, 0, 0);
        assert(live == baseline);
        for (permanent = 0; permanent < 2; ++permanent) {
            for (fault = 1; fault <= count; ++fault) {
                resolve(cases[i].text, cases[i].uri, cases[i].local, cases[i].valid, fault, permanent);
                assert(live == baseline);
                resolve(cases[i].text, cases[i].uri, cases[i].local, cases[i].valid, 0, 0);
                assert(live == baseline);
            }
        }
    }
    xmlCleanupParser();
    assert(live == 0);
    puts("Native component QName allocation: PASS");
    return 0;
}
