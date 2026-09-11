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


static size_t exercise(xmlSchemaTypePtr type, xmlSchemaElementPtr head,
                       xmlSchemaElementPtr member, size_t fault, int invalid) {
    xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(" ", 1);
    size_t count;
    int result;
    assert(parser != NULL);
    parser->constructor = xmlSchemaConstructionCtxtCreate(parser->dict);
    parser->ownsConstructor = 1;
    assert(parser->constructor != NULL);
    assert(xmlSchemaAddElementSubstitutionMember(parser, head, member) == 0);
    xmlSchemaSetParserErrors(parser, error_handler, error_handler, NULL);
    attempts = 0; fail_at = fault; failed = 0; armed = 1;
    result = xmlSchemaCheckElementConsistency(parser, (xmlSchemaTreeItemPtr)WXS_TYPE_PARTICLE(type));
    armed = 0;
    assert(failed ? result != 0 : result == invalid);
    count = attempts;
    xmlSchemaFreeParserCtxt(parser);
    xmlResetLastError();
    return count;
}

int main(void) {
    const char *source = "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema' xmlns:t='urn:edc' targetNamespace='urn:edc'>"
        "<xs:element name='head' type='xs:decimal' abstract='true'/>"
        "<xs:element name='member' type='xs:int' substitutionGroup='t:head'/>"
        "<xs:group name='G'><xs:sequence><xs:element ref='t:head'/>"
        "<xs:element name='member' type='xs:int' form='qualified'/></xs:sequence></xs:group>"
        "<xs:complexType name='Record'><xs:sequence><xs:group ref='t:G'/><xs:group ref='t:G'/>"
        "</xs:sequence></xs:complexType></xs:schema>";
    xmlSchemaParserCtxtPtr parser;
    xmlSchemaPtr schema;
    xmlSchemaTypePtr type, original;
    xmlSchemaElementPtr head, member;
    size_t total, baseline, faults = 0;
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
    head = xmlHashLookup(schema->elemDecl, BAD_CAST "head");
    member = xmlHashLookup(schema->elemDecl, BAD_CAST "member");
    assert(type != NULL && head != NULL && member != NULL);
    assert(head->flags & XML_SCHEMAS_ELEM_SUBST_GROUP_HEAD);
    original = member->subtypes;
    for (int invalid = 0; invalid < 2; ++invalid) {
        if (invalid) {
            member->subtypes = xmlSchemaGetBuiltInType(XML_SCHEMAS_STRING);
        }
        baseline = live;
        total = exercise(type, head, member, 0, invalid);
        assert(total > 10 && live == baseline);
        for (size_t fault = 1; fault <= total; ++fault) {
            exercise(type, head, member, fault, invalid);
            assert(live == baseline);
        }
        assert(exercise(type, head, member, 0, invalid) == total);
        assert(live == baseline);
        faults += total;
    }
    member->subtypes = original;
    xmlSchemaFree(schema);
    xmlCleanupParser();
    assert(live == 0);
    printf("Native element consistency cleanup: PASS (%zu allocation faults)\n", faults);
    return 0;
}
