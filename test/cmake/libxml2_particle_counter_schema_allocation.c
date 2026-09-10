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


static size_t exercise(xmlSchemaParticlePtr particle, size_t fault) {
    xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(" ", 1);
    xmlAutomataPtr automaton;
    size_t parent, count;
    int result;
    assert(parser != NULL);
    xmlSchemaSetParserErrors(parser, error_handler, error_handler, NULL);
    automaton = xmlNewAutomata();
    assert(automaton != NULL);
    parser->am = automaton;
    assert(xmlAutomataPushParticle(automaton, particle, &parent) == 0);
    attempts = 0; fail_at = fault; failed = 0; armed = 1;
    result = xmlSchemaNewExactCounter(parser, particle, UNBOUNDED - 1, UNBOUNDED - 1, 1);
    armed = 0;
    assert(failed ? result < 0 : result == 0);
    count = attempts;
    xmlAutomataPopParticle(automaton, parent);
    xmlFreeAutomata(automaton);
    parser->am = NULL;
    xmlSchemaFreeParserCtxt(parser);
    xmlResetLastError();
    return count;
}

int main(void) {
    const char *source = "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
        "<xs:complexType name='Record'><xs:sequence minOccurs='1000000000000000000000000000000000000000000' "
        "maxOccurs='1000000000000000000000000000000000000000000'><xs:element name='a'/>"
        "</xs:sequence></xs:complexType></xs:schema>";
    xmlSchemaParserCtxtPtr parser;
    xmlSchemaPtr schema;
    xmlSchemaTypePtr type;
    xmlSchemaParticlePtr particle;
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
    particle = WXS_TYPE_PARTICLE(type);
    assert(particle != NULL && particle->maxFinite);
    baseline = live;
    total = exercise(particle, 0);
    assert(total > 2);
    assert(live == baseline);
    for (size_t fault = 1; fault <= total; ++fault) {
        exercise(particle, fault);
        assert(live == baseline);
    }
    assert(exercise(particle, 0) == total);
    assert(live == baseline);
    xmlSchemaFree(schema);
    xmlCleanupParser();
    assert(live == 0);
    printf("Exact native schema counter cleanup: PASS (%zu allocation faults)\n", total);
    return 0;
}
