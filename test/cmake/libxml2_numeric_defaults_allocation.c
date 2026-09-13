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

enum constraint_path { ELEMENT, ATTRIBUTE, ATTRIBUTE_USE };

static size_t exercise(xmlSchemaTypePtr type, const char *lexical, enum constraint_path path,
        size_t fault, int valid) {
    xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(" ", 1);
    xmlSchemaAttribute declaration;
    xmlSchemaAttributeUse use;
    xmlSchemaValPtr value = NULL;
    size_t count;
    int result;
    assert(parser != NULL);
    memset(&declaration, 0, sizeof(declaration));
    memset(&use, 0, sizeof(use));
    declaration.type = XML_SCHEMA_TYPE_ATTRIBUTE;
    declaration.name = BAD_CAST "value";
    declaration.node = type->node;
    declaration.subtypes = type;
    use.type = XML_SCHEMA_TYPE_ATTRIBUTE_USE;
    use.attrDecl = &declaration;
    use.node = type->node;
    xmlSchemaSetParserErrors(parser, error_handler, error_handler, NULL);
    attempts = 0;
    fail_at = fault;
    failed = 0;
    armed = 1;
    if (path == ELEMENT) {
        result = xmlSchemaParseCheckCOSValidDefault(parser, type->node, type, BAD_CAST lexical, &value);
    } else if (path == ATTRIBUTE) {
        declaration.defValue = BAD_CAST lexical;
        result = xmlSchemaCheckAttrPropsCorrect(parser, &declaration);
        value = declaration.defVal;
    } else {
        use.defValue = BAD_CAST lexical;
        result = xmlSchemaCheckAttrUsePropsCorrect(parser, &use);
        value = use.defVal;
    }
    armed = 0;
    count = attempts;
    assert(failed == (fault != 0));
    if (failed) {
        /* A rejected canonical pattern can exhaust memory while formatting its
         * diagnostic. Its positive rejection code is retained with NO_MEMORY
         * in the context; an otherwise valid constraint must fail internally. */
        assert(valid ? result < 0 : result != 0);
        assert(valid || result < 0 || parser->err == XML_ERR_NO_MEMORY);
    } else {
        assert(valid ? result == 0 : result > 0);
        assert(*lexical == 0 || value != NULL);
    }
    xmlSchemaFreeValue(value);
    xmlSchemaFreeParserCtxt(parser);
    xmlResetLastError();
    return count;
}

static size_t sweep(const char *definition, const char *lexical, const char *canonical, int valid) {
    char source[4096];
    int length = snprintf(source, sizeof(source),
        "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema' xmlns:p='urn:part'>%s</xs:schema>",
        definition);
    xmlSchemaParserCtxtPtr parser;
    xmlSchemaPtr schema;
    xmlSchemaTypePtr type;
    size_t baseline, faults = 0;
    enum constraint_path path;
    assert(length > 0 && (size_t)length < sizeof(source));
    parser = xmlSchemaNewMemParserCtxt(source, length);
    assert(parser != NULL);
    xmlSchemaSetParserErrors(parser, error_handler, error_handler, NULL);
    schema = xmlSchemaParse(parser);
    assert(schema != NULL);
    type = xmlHashLookup(schema->typeDecl, BAD_CAST "Value");
    assert(type != NULL);
    /* Check the exact temporary lexical and preserve the original computed value.
     * A NULL output explicitly means no numeric/boolean member needed rewriting. */
    {
        xmlSchemaValPtr value = NULL;
        xmlChar *text = NULL;
        assert(xmlSchemaVCheckCVCSimpleType(ACTXT_CAST parser, type->node, type,
            BAD_CAST lexical, &value, 1, 1, 0) == 0);
        assert(qoreXmlNumericDefaultLexical(value, BAD_CAST lexical, &text) == 0);
        assert(canonical ? xmlStrEqual(text, BAD_CAST canonical) : text == NULL);
        xmlFree(text);
        xmlSchemaFreeValue(value);
    }
    xmlResetLastError();
    baseline = live;
    for (path = ELEMENT; path <= ATTRIBUTE_USE; ++path) {
        size_t count = exercise(type, lexical, path, 0, valid);
        size_t fault;
        assert(live == baseline);
        for (fault = 1; fault <= count; ++fault) {
            exercise(type, lexical, path, fault, valid);
            assert(live == baseline);
        }
        assert(exercise(type, lexical, path, 0, valid) == count);
        assert(live == baseline);
        faults += count;
    }
    xmlSchemaFree(schema);
    xmlSchemaFreeParserCtxt(parser);
    return faults;
}

int main(void) {
    size_t faults = 0;
    assert(xmlMemSetup(release, allocate, resize, duplicate) == 0);
    xmlInitParser();
    xmlSetGenericErrorFunc(NULL, error_handler);
    assert(xmlSchemaInitTypes() == 0);
    faults += sweep("<xs:simpleType name='Value'><xs:restriction base='xs:int'/></xs:simpleType>",
        "+017", "17", 1);
    faults += sweep("<xs:simpleType name='Value'><xs:restriction base='xs:decimal'/></xs:simpleType>",
        "-0.000", "0.0", 1);
    faults += sweep("<xs:simpleType name='Value'><xs:restriction base='xs:integer'/></xs:simpleType>",
        "+00123456789012345678901234567890123456789012345678901234567890",
        "123456789012345678901234567890123456789012345678901234567890", 1);
    faults += sweep("<xs:simpleType name='Value'><xs:restriction base='xs:boolean'>"
        "<xs:pattern value='1'/></xs:restriction></xs:simpleType>", "1", "true", 0);
    faults += sweep("<xs:simpleType name='Value'><xs:list itemType='xs:boolean'/></xs:simpleType>",
        "1", "true", 1);
    faults += sweep("<xs:simpleType name='Value'><xs:list itemType='xs:int'/></xs:simpleType>",
        "", NULL, 1);
    faults += sweep("<xs:simpleType name='Value'><xs:union memberTypes='xs:string xs:int'/></xs:simpleType>",
        "+017", NULL, 1);
    faults += sweep("<xs:simpleType name='Item'><xs:union memberTypes='xs:boolean xs:QName'/></xs:simpleType>"
        "<xs:simpleType name='Value'><xs:list itemType='Item'/></xs:simpleType>",
        "1 p:Part 0", "true p:Part false", 1);
    {
        char lexical[2048] = "", canonical[2048] = "";
        unsigned int index;
        for (index = 0; index < 180; ++index) {
            strcat(lexical, index ? " 1" : "1");
            strcat(canonical, index ? " true" : "true");
        }
        faults += sweep("<xs:simpleType name='Value'><xs:list itemType='xs:boolean'/></xs:simpleType>",
            lexical, canonical, 1);
    }
    xmlCleanupParser();
    assert(live == 0);
    assert(faults > 500);
    printf("Native numeric constraint allocation: PASS (%zu allocation faults)\n", faults);
    return 0;
}
