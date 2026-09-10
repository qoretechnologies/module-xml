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


static size_t exercise(xmlSchemaTypePtr type, size_t fault) {
    xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(" ", 1);
    xmlSchemaTreeItemPtr item = (xmlSchemaTreeItemPtr)type;
    size_t count;
    int result;
    assert(parser != NULL);
    xmlSchemaSetParserErrors(parser, error_handler, error_handler, NULL);
    attempts = 0; fail_at = fault; failed = 0; armed = 1;
    result = xmlSchemaCheckParticleAttributions(parser, &item, 1);
    armed = 0;
    assert(result == (failed ? -1 : 0));
    count = attempts;
    xmlSchemaFreeParserCtxt(parser);
    xmlResetLastError();
    return count;
}

static void check_all_summary(int optional) {
    char source[512];
    xmlSchemaParserCtxtPtr parser;
    xmlSchemaPtr schema;
    xmlSchemaTypePtr type;
    xmlSchemaUpaSchema analysis = {0};
    xmlSchemaUpaNode *node;
    int length = snprintf(source, sizeof(source),
        "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
        "<xs:element name='h' abstract='true'/>"
        "<xs:complexType name='Record'><xs:all><xs:element ref='h' minOccurs='%d'/>"
        "<xs:element name='a'/></xs:all></xs:complexType></xs:schema>", optional ? 0 : 1);
    assert(length > 0 && (size_t)length < sizeof(source));
    parser = xmlSchemaNewMemParserCtxt(source, length);
    assert(parser != NULL);
    schema = xmlSchemaParse(parser);
    assert(schema != NULL);
    type = xmlHashLookup(schema->typeDecl, BAD_CAST "Record");
    assert(type != NULL);
    analysis.parser = parser;
    analysis.context.overlap = xmlSchemaUpaSchemaOverlap;
    assert(xmlSchemaUpaInit(&analysis.context) == 0);
    analysis.nodes = xmlSchemaUpaNewTable(&analysis.context);
    analysis.names = xmlSchemaUpaNewTable(&analysis.context);
    analysis.wildcards = xmlSchemaUpaNewTable(&analysis.context);
    assert(!analysis.context.memory.failed);
    assert(xmlSchemaUpaVisit(&analysis, (xmlSchemaTreeItemPtr)WXS_TYPE_PARTICLE(type)) == 0);
    node = xmlSchemaUpaGetNode(&analysis, (xmlSchemaTreeItemPtr)WXS_TYPE_PARTICLE(type));
    assert(node != NULL && node->status == 2);
    assert(node->info.empty == !optional);
    assert(node->info.nullable == 0);
    xmlSchemaUpaCleanup(&analysis.context);
    xmlSchemaFree(schema);
    xmlSchemaFreeParserCtxt(parser);
    xmlResetLastError();
}
int main(void) {
    const char *source = "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
        "<xs:group name='G'><xs:choice><xs:element name='x'/><xs:any namespace='urn:a' processContents='skip'/></xs:choice></xs:group>"
        "<xs:complexType name='Record'><xs:sequence>"
        "<xs:sequence minOccurs='2' maxOccurs='2'><xs:element name='b' minOccurs='0'/>"
        "<xs:element name='a' minOccurs='2' maxOccurs='3'/></xs:sequence><xs:element name='b'/>"
        "<xs:group ref='G'/><xs:group ref='G'/>"
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
    assert(type != NULL);
    baseline = live;
    total = exercise(type, 0);
    assert(total > 200);
    assert(live == baseline);
    for (size_t fault = 1; fault <= total; ++fault) {
        exercise(type, fault);
        assert(live == baseline);
    }
    assert(exercise(type, 0) == total);
    assert(live == baseline);
    xmlSchemaFree(schema);
    check_all_summary(0);
    check_all_summary(1);
    xmlCleanupParser();
    assert(live == 0);
    printf("Native particle attribution cleanup: PASS (%zu fault points)\n", total);
    return 0;
}
