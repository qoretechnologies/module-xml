/* Copyright (C) 2026 Qore Technologies, s.r.o. */
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <libxml/xmlschemas.h>
#include <libxml/xmlschemastypes.h>
#include <libxml/xmlmemory.h>
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
static const char schema_text[] =
    "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
    "<xs:simpleType name='Pair'><xs:restriction base='xs:ENTITIES'>"
    "<xs:length value='2'/><xs:enumeration value='photo other'/>"
    "</xs:restriction></xs:simpleType>"
    "<xs:element name='value' type='Pair'/></xs:schema>";

static void entity_callback(void *data, const xmlChar *name, int type,
        const xmlChar *public_id, const xmlChar *system_id, xmlChar *content) {
    ++((unsigned *)data)[0];
    (void)name;
    (void)type;
    (void)public_id;
    (void)system_id;
    (void)content;
}

static void unparsed_callback(void *data, const xmlChar *name, const xmlChar *public_id,
        const xmlChar *system_id, const xmlChar *notation) {
    ++((unsigned *)data)[1];
    (void)name;
    (void)public_id;
    (void)system_id;
    (void)notation;
}

static void reuse_and_values(void) {
    static const char document[] = "<!DOCTYPE value [<!NOTATION gif SYSTEM 'image/gif'>"
        "<!ENTITY photo SYSTEM 'photo.gif' NDATA gif>]><value/>";
    xmlSchemaParserCtxtPtr parser;
    xmlSchemaPtr schema;
    xmlSchemaValidCtxtPtr context;
    xmlSAXHandler application = {0};
    unsigned callbacks[2] = {0, 0};
    xmlDocPtr doc;
    xmlSchemaValPtr val = NULL, copy;
    xmlSchemaTypePtr entity;
    xmlInitParser();
    parser = xmlSchemaNewMemParserCtxt(schema_text, sizeof(schema_text) - 1);
    assert(parser != NULL);
    schema = xmlSchemaParse(parser);
    assert(schema != NULL);
    xmlSchemaFreeParserCtxt(parser);
    context = xmlSchemaNewValidCtxt(schema);
    assert(context != NULL);
    xmlSchemaSetValidErrors(context, error_handler, error_handler, NULL);
    application.initialized = XML_SAX2_MAGIC;
    application.entityDecl = entity_callback;
    application.unparsedEntityDecl = unparsed_callback;
    for (unsigned iteration = 0; iteration < 6; ++iteration) {
        xmlSAXHandlerPtr sax = &application;
        void *data = callbacks;
        xmlSchemaSAXPlugPtr plug = xmlSchemaSAXPlug(context, &sax, &data);
        assert(plug != NULL);
        if (iteration != 1) {
            if (iteration == 2 || iteration == 4) {
                sax->entityDecl(data, BAD_CAST "photo", iteration == 2 ? XML_INTERNAL_GENERAL_ENTITY
                    : XML_INTERNAL_PARAMETER_ENTITY, NULL, NULL, BAD_CAST "text");
            }
            sax->unparsedEntityDecl(data, BAD_CAST "photo", NULL, BAD_CAST "photo.gif", BAD_CAST "gif");
            sax->unparsedEntityDecl(data, BAD_CAST "other", NULL, BAD_CAST "other.gif", BAD_CAST "gif");
            if (iteration == 3) {
                sax->entityDecl(data, BAD_CAST "photo", XML_INTERNAL_GENERAL_ENTITY, NULL, NULL, BAD_CAST "text");
            }
        }
        sax->startElementNs(data, BAD_CAST "value", NULL, NULL, 0, NULL, 0, 0, NULL);
        sax->characters(data, BAD_CAST "photo other", 11);
        sax->endElementNs(data, BAD_CAST "value", NULL, NULL);
        assert(xmlSchemaIsValid(context) == (iteration != 1 && iteration != 2));
        assert(xmlSchemaSAXUnplug(plug) == 0);
        assert(sax == &application && data == callbacks);
    }
    assert(callbacks[0] == 3 && callbacks[1] == 10);
    xmlSchemaFreeValidCtxt(context);
    xmlSchemaFree(schema);
    doc = xmlReadMemory(document, sizeof(document) - 1, NULL, NULL, XML_PARSE_NONET);
    assert(doc != NULL);
    entity = xmlSchemaGetBuiltInType(XML_SCHEMAS_ENTITY);
    assert(entity != NULL);
    assert(xmlSchemaValPredefTypeNode(entity, BAD_CAST " \tphoto\r\n", &val,
        xmlDocGetRootElement(doc)) == 0);
    assert(val != NULL && xmlSchemaGetValType(val) == XML_SCHEMAS_ENTITY);
    assert(xmlStrEqual(xmlSchemaValueGetAsString(val), BAD_CAST "photo"));
    copy = xmlSchemaCopyValue(val);
    assert(copy != NULL && xmlSchemaCompareValues(val, copy) == 0);
    xmlSchemaFreeValue(val);
    assert(xmlStrEqual(xmlSchemaValueGetAsString(copy), BAD_CAST "photo"));
    xmlSchemaFreeValue(copy);
    val = NULL;
    assert(xmlSchemaValPredefTypeNode(entity, BAD_CAST "missing", &val,
        xmlDocGetRootElement(doc)) != 0 && val == NULL);
    xmlFreeDoc(doc);
    xmlCleanupParser();
    assert(live == 0);
}

static size_t run(int mode, size_t fault, int cancel) {
    xmlSchemaParserCtxtPtr parser;
    xmlSchemaPtr schema;
    xmlSchemaValidCtxtPtr context;
    xmlSchemaSAXPlugPtr plug;
    xmlSAXHandlerPtr sax = NULL;
    void *data = NULL;
    size_t count;
    int valid;
    xmlInitParser();
    xmlSetGenericErrorFunc(NULL, error_handler);
    parser = xmlSchemaNewMemParserCtxt(schema_text, sizeof(schema_text) - 1);
    assert(parser != NULL);
    schema = xmlSchemaParse(parser);
    assert(schema != NULL);
    xmlSchemaFreeParserCtxt(parser);
    context = xmlSchemaNewValidCtxt(schema);
    assert(context != NULL);
    xmlSchemaSetValidErrors(context, error_handler, error_handler, NULL);
    plug = xmlSchemaSAXPlug(context, &sax, &data);
    assert(plug != NULL);
    attempts = 0;
    fail_at = fault;
    failed = 0;
    armed = mode == 0;
    sax->unparsedEntityDecl(data, BAD_CAST "photo", NULL, BAD_CAST "photo.gif", BAD_CAST "gif");
    sax->unparsedEntityDecl(data, BAD_CAST "other", NULL, BAD_CAST "other.gif", BAD_CAST "gif");
    for (unsigned i = 0; i < 64; ++i) {
        char name[24];
        int length = snprintf(name, sizeof(name), "entity%u", i);
        assert(length > 0 && (size_t)length < sizeof(name));
        sax->entityDecl(data, BAD_CAST name, XML_INTERNAL_GENERAL_ENTITY, NULL, NULL, BAD_CAST "text");
    }
    armed = 0;
    sax->startElementNs(data, BAD_CAST "value", NULL, NULL, 0, NULL, 0, 0, NULL);
    sax->characters(data, BAD_CAST "photo other", 11);
    if (mode == 1) {
        attempts = 0;
        armed = 1;
    }
    if (!cancel) {
        sax->endElementNs(data, BAD_CAST "value", NULL, NULL);
    }
    armed = 0;
    valid = xmlSchemaIsValid(context);
    count = attempts;
    assert(valid >= 0);
    if (!cancel && valid != !failed) {
        fprintf(stderr, "mode=%d fault=%zu failed=%d valid=%d\n", mode, fault, failed, valid);
        abort();
    }
    assert(xmlSchemaSAXUnplug(plug) == 0);
    xmlSchemaFreeValidCtxt(context);
    xmlSchemaFree(schema);
    xmlCleanupParser();
    if (live != 0) {
        fprintf(stderr, "mode=%d fault=%zu live=%zu\n", mode, fault, live);
        abort();
    }
    return count;
}
int main(void) {
    size_t total = 0;
    assert(xmlMemSetup(release, allocate, resize, duplicate) == 0);
    reuse_and_values();
    for (int mode = 0; mode < 2; ++mode) {
        size_t count = run(mode, 0, 0);
        assert(count != 0);
        for (size_t i = 1; i <= count; ++i) {
            run(mode, i, 0);
            ++total;
        }
        run(mode, 0, 1);
    }
    printf("ENTITY allocation and cancellation cleanup: PASS (%zu fault sites)\n", total);
    return 0;
}
