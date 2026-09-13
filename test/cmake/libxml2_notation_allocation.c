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

/* Isolate the new declaration phase from unrelated schema parser allocations. */
static size_t declaration(const char *source, int valid, size_t fault, int permanent) {
    xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(" ", 1);
    xmlSchemaConstructionCtxt constructor;
    xmlSchemaBucket bucket;
    xmlDocPtr document = xmlReadMemory(source, (int)strlen(source), NULL, NULL, XML_PARSE_NONET);
    xmlSchemaPtr schema;
    xmlSchemaNotationPtr notation;
    size_t count;
    int i;
    assert(parser != NULL && document != NULL);
    memset(&constructor, 0, sizeof(constructor));
    memset(&bucket, 0, sizeof(bucket));
    constructor.bucket = &bucket;
    parser->constructor = &constructor;
    schema = xmlSchemaNewSchema(parser);
    assert(schema != NULL);
    parser->schema = schema;
    xmlSchemaSetParserErrors(parser, error_handler, error_handler, NULL);
    attempts = 0;
    fail_at = fault;
    failed = 0;
    persistent = permanent;
    armed = 1;
    notation = xmlSchemaParseNotation(parser, schema, xmlDocGetRootElement(document));
    armed = 0;
    count = attempts;
    assert(failed == (fault != 0));
    if (failed) {
        assert(parser->err != 0);
    } else {
        assert(valid ? notation != NULL && parser->err == 0 : parser->err != 0);
    }
    if (notation != NULL && parser->err == 0) {
        assert(xmlStrEqual(notation->name, BAD_CAST "item"));
    }
    if (bucket.globals != NULL) {
        for (i = 0; i < bucket.globals->nbItems; ++i) {
            xmlSchemaFreeNotation((xmlSchemaNotationPtr) bucket.globals->items[i]);
        }
        xmlSchemaItemListFree(bucket.globals);
    }
    parser->schema = NULL;
    parser->constructor = NULL;
    xmlSchemaFree(schema);
    xmlSchemaFreeParserCtxt(parser);
    xmlFreeDoc(document);
    xmlResetLastError();
    return count;
}

/* Shared and anonymous components exercise both worklist growth and hash growth.
 * Every borrowed type and node must survive a failed checker unchanged. */
static size_t uses(int valid, size_t fault, int permanent) {
    xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(" ", 1);
    xmlSchemaType types[128];
    xmlSchemaElement elements[128];
    xmlSchemaTreeItemPtr items[128];
    xmlSchemaFacet enumeration;
    size_t count;
    int i, result;
    assert(parser != NULL);
    memset(types, 0, sizeof(types));
    memset(elements, 0, sizeof(elements));
    memset(&enumeration, 0, sizeof(enumeration));
    enumeration.type = XML_SCHEMA_FACET_ENUMERATION;
    for (i = 0; i < 128; ++i) {
        types[i].type = XML_SCHEMA_TYPE_SIMPLE;
        types[i].flags = XML_SCHEMAS_TYPE_VARIETY_ATOMIC;
        types[i].baseType = i == 0 ? xmlSchemaGetBuiltInType(XML_SCHEMAS_NOTATION) : &types[i - 1];
        types[i].facets = valid && i == 0 ? &enumeration : NULL;
        elements[i].type = XML_SCHEMA_TYPE_ELEMENT;
        elements[i].subtypes = &types[i];
        items[i] = (xmlSchemaTreeItemPtr) &elements[i];
    }
    xmlSchemaSetParserErrors(parser, error_handler, error_handler, NULL);
    attempts = 0;
    fail_at = fault;
    failed = 0;
    persistent = permanent;
    armed = 1;
    result = qoreXmlCheckNotationUses(parser, items, 128);
    armed = 0;
    count = attempts;
    assert(failed == (fault != 0));
    assert(failed ? result != 0 && parser->err != 0 : (result == 0) == valid);
    for (i = 0; i < 128; ++i) {
        assert(elements[i].subtypes == &types[i]);
        assert(types[i].facets == (valid && i == 0 ? &enumeration : NULL));
    }
    xmlSchemaFreeParserCtxt(parser);
    xmlResetLastError();
    return count;
}

static size_t absent_content(size_t fault, int permanent) {
    xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(" ", 1);
    const xmlChar *value;
    size_t count;
    assert(parser != NULL);
    xmlSchemaSetParserErrors(parser, error_handler, error_handler, NULL);
    attempts = 0;
    fail_at = fault;
    failed = 0;
    persistent = permanent;
    armed = 1;
    value = xmlSchemaGetNodeContent(parser, NULL);
    armed = 0;
    count = attempts;
    assert(failed == (fault != 0));
    assert(failed ? value == NULL && parser->err != 0 : value != NULL && value[0] == 0);
    xmlSchemaFreeParserCtxt(parser);
    xmlResetLastError();
    return count;
}

int main(void) {
    static const struct { const char *source; int valid; } cases[] = {
        {"<xs:notation xmlns:xs='http://www.w3.org/2001/XMLSchema' name='  item  ' public='  a  b '/>", 1},
        {"<xs:notation xmlns:xs='http://www.w3.org/2001/XMLSchema' name='item' system='urn:item' id='  id  '/>", 1},
        {"<xs:notation xmlns:xs='http://www.w3.org/2001/XMLSchema' name='item' public='a'>"
         "<xs:annotation><xs:documentation>format</xs:documentation></xs:annotation></xs:notation>", 1},
        {"<xs:notation xmlns:xs='http://www.w3.org/2001/XMLSchema' name='item'/>", 0},
        {"<xs:notation xmlns:xs='http://www.w3.org/2001/XMLSchema' name='item' public='a' typo='x'/>", 0},
        {"<xs:notation xmlns:xs='http://www.w3.org/2001/XMLSchema' name='bad:name' public='a'/>", 0}
    };
    size_t model, baseline, count, fault, total = 0;
    int permanent, valid;
    assert(xmlMemSetup(release, allocate, resize, duplicate) == 0);
    xmlInitParser();
    xmlSetGenericErrorFunc(NULL, error_handler);
    assert(xmlSchemaInitTypes() == 0);
    baseline = live;
    for (model = 0; model < sizeof(cases) / sizeof(cases[0]); ++model) {
        count = declaration(cases[model].source, cases[model].valid, 0, 0);
        assert(count > 0 && live == baseline);
        for (permanent = 0; permanent < 2; ++permanent) {
            for (fault = 1; fault <= count; ++fault) {
                declaration(cases[model].source, cases[model].valid, fault, permanent);
                assert(live == baseline);
                ++total;
            }
        }
        declaration(cases[model].source, cases[model].valid, 0, 0);
        assert(live == baseline);
    }
    for (valid = 0; valid < 2; ++valid) {
        count = uses(valid, 0, 0);
        assert(count > 0 && live == baseline);
        for (permanent = 0; permanent < 2; ++permanent) {
            for (fault = 1; fault <= count; ++fault) {
                uses(valid, fault, permanent);
                assert(live == baseline);
                ++total;
            }
        }
        uses(valid, 0, 0);
        assert(live == baseline);
    }
    count = absent_content(0, 0);
    assert(count > 0 && live == baseline);
    for (permanent = 0; permanent < 2; ++permanent) {
        for (fault = 1; fault <= count; ++fault) {
            absent_content(fault, permanent);
            assert(live == baseline);
            ++total;
        }
    }
    absent_content(0, 0);
    assert(live == baseline);
    xmlCleanupParser();
    assert(live == 0);
    printf("NOTATION allocation failures propagated with intact ownership and recovery: %zu faults\n", total);
    return 0;
}
