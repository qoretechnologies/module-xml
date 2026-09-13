/* Copyright (C) 2026 Qore Technologies, s.r.o. */
#ifdef NDEBUG
#undef NDEBUG
#endif
/* Reach the private validation phases in the checked native schema source. */
#include QORE_XML_SCHEMA_SOURCE
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

enum phase { PHASE_NONE, PHASE_PREPARE, PHASE_WALK, PHASE_RESET };
static size_t live, attempts, fail_at;
static int armed, failed;
static enum phase active_phase, failed_phase;

static int fail_allocation(void) {
    if (armed && ++attempts >= fail_at && fail_at != 0) {
        /* Permanent failure may recur in cleanup; retain the first phase. */
        if (!failed) {
            failed_phase = active_phase;
        }
        failed = 1;
        return 1;
    }
    return 0;
}

static void* allocate(size_t size) {
    void* p;
    if (fail_allocation()) {
        return NULL;
    }
    p = malloc(size);
    if (p != NULL) {
        ++live;
    }
    return p;
}

static void release(void* p) {
    if (p != NULL) {
        assert(live != 0);
        --live;
        free(p);
    }
}

static void* resize(void* p, size_t size) {
    if (p == NULL) {
        return allocate(size);
    }
    if (size == 0) {
        release(p);
        return NULL;
    }
    if (fail_allocation()) {
        return NULL;
    }
    return realloc(p, size);
}

static char* duplicate(const char* value) {
    size_t length = strlen(value) + 1;
    char* p = allocate(length);
    if (p != NULL) {
        memcpy(p, value, length);
    }
    return p;
}

static void error_handler(void* data, const char* message, ...) {
    (void)data;
    (void)message;
}

/* Follow the DOM path of xmlSchemaValidateDoc/xmlSchemaVStart, recording phase
 * boundaries. Every run below is also repeated through the public API. */
static int validate_marked(xmlSchemaValidCtxtPtr context, xmlDocPtr doc, int* verdict) {
    int result;
    context->doc = doc;
    context->node = xmlDocGetRootElement(doc);
    assert(context->node != NULL);
    context->validationRoot = context->node;
    active_phase = PHASE_PREPARE;
    if (xmlSchemaPreRun(context) < 0) {
        *verdict = -1;
        return -1;
    }
    active_phase = PHASE_WALK;
    result = xmlSchemaVDocWalk(context);
    *verdict = result == 0 ? context->err : result;
    active_phase = PHASE_RESET;
    xmlSchemaPostRun(context);
    if (result == 0) {
        result = context->err;
    }
    return result;
}

struct outcome {
    size_t count;
    int result;
    enum phase phase;
};

static struct outcome exercise(xmlSchemaPtr schema, const char* input, size_t fault, int invalid,
        const struct outcome* marked) {
    xmlDocPtr doc = xmlReadMemory(input, (int)strlen(input), NULL, NULL, XML_PARSE_NONET);
    xmlSchemaValidCtxtPtr context = xmlSchemaNewValidCtxt(schema);
    struct outcome output;
    int verdict = -1;
    assert(doc != NULL && context != NULL);
    xmlSchemaSetValidErrors(context, error_handler, error_handler, NULL);
    attempts = 0;
    fail_at = fault;
    failed = 0;
    failed_phase = PHASE_NONE;
    active_phase = PHASE_NONE;
    armed = 1;
    output.result = marked ? xmlSchemaValidateDoc(context, doc) : validate_marked(context, doc, &verdict);
    armed = 0;
    output.count = attempts;
    output.phase = marked ? marked->phase : failed_phase;
    assert(failed == (fault != 0));
    if (!failed) {
        assert((output.result != 0) == invalid);
        assert(context->dict != NULL);
    } else if (output.phase == PHASE_RESET) {
        /* The document verdict precedes this optional context-reset allocation. */
        assert((output.result != 0) == invalid);
        assert(context->dict == NULL);
        if (!marked) {
            assert(output.result == verdict);
        }
    } else {
        assert(output.phase == PHASE_PREPARE || output.phase == PHASE_WALK);
        assert(output.result != 0);
    }
    if (marked) {
        assert(output.result == marked->result);
        assert(output.count == marked->count);
    }
    xmlSchemaFreeValidCtxt(context);
    xmlFreeDoc(doc);
    xmlResetLastError();
    return output;
}

static size_t sweep(const char* label, const char* source, const char* input, int invalid) {
    xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
    xmlSchemaPtr schema;
    struct outcome normal;
    size_t fault, baseline, required = 0, resets = 0;
    assert(parser != NULL);
    xmlSchemaSetParserErrors(parser, error_handler, error_handler, NULL);
    schema = xmlSchemaParse(parser);
    xmlSchemaFreeParserCtxt(parser);
    assert(schema != NULL);
    normal = exercise(schema, input, 0, invalid, NULL);
    assert(normal.count != 0);
    baseline = live;
    exercise(schema, input, 0, invalid, &normal);
    assert(live == baseline);
    for (fault = 1; fault <= normal.count; ++fault) {
        struct outcome marked = exercise(schema, input, fault, invalid, NULL);
        assert(live == baseline);
        if (marked.phase == PHASE_RESET) {
            ++resets;
        } else {
            ++required;
        }
        exercise(schema, input, fault, invalid, &marked);
        assert(live == baseline);
    }
    /* Recovery uses a fresh per-document context, as module-xml does. */
    exercise(schema, input, 0, invalid, &normal);
    assert(live == baseline);
    assert(required != 0 && resets == 1);
    xmlSchemaFree(schema);
    printf("%s: %zu required failures, %zu optional reset failure; private/public verdicts match\n",
        label, required, resets);
    return normal.count;
}

int main(void) {
    size_t faults = 0;
    assert(xmlMemSetup(release, allocate, resize, duplicate) == 0);
    xmlInitParser();
    xmlSetGenericErrorFunc(NULL, error_handler);
    assert(xmlSchemaInitTypes() == 0);
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"ref\" type=\"xs:IDREF\" minOccurs=\"0\" maxOccurs=\"unbounded\"/><xs:element name=\"id\" type=\"xs:ID\" minOccurs=\"0\" maxOccurs=\"unbounded\"/></xs:sequence></xs:complexType></xs:element></xs:schema>";
        faults += sweep("IDREF/elements/empty", source, "<value></value>", 0);
        faults += sweep("IDREF/elements/forward", source, "<value><ref>a</ref><id>a</id></value>", 0);
        faults += sweep("IDREF/elements/missing", source, "<value><ref>a</ref></value>", 1);
        faults += sweep("IDREF/elements/duplicate", source, "<value><id>a</id><id>a</id></value>", 0);
        faults += sweep("IDREF/elements/repeated-ref", source, "<value><ref>a</ref><ref>a</ref><id>a</id></value>", 0);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"item\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:attribute name=\"id\" type=\"xs:ID\"/><xs:attribute name=\"ref\" type=\"xs:IDREF\"/></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>";
        faults += sweep("IDREF/attributes/empty", source, "<value></value>", 0);
        faults += sweep("IDREF/attributes/forward", source, "<value><item ref=\"a\"/><item id=\"a\"/></value>", 0);
        faults += sweep("IDREF/attributes/missing", source, "<value><item ref=\"a\"/></value>", 1);
        faults += sweep("IDREF/attributes/duplicate", source, "<value><item id=\"a\"/><item id=\"a\"/></value>", 1);
        faults += sweep("IDREF/attributes/repeated-ref", source, "<value><item ref=\"a\"/><item ref=\"a\"/><item id=\"a\"/></value>", 0);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"ref\" type=\"xs:IDREFS\" minOccurs=\"0\" maxOccurs=\"unbounded\"/><xs:element name=\"id\" type=\"xs:ID\" minOccurs=\"0\" maxOccurs=\"unbounded\"/></xs:sequence></xs:complexType></xs:element></xs:schema>";
        faults += sweep("IDREFS/elements/empty", source, "<value></value>", 0);
        faults += sweep("IDREFS/elements/forward", source, "<value><ref>a</ref><id>a</id></value>", 0);
        faults += sweep("IDREFS/elements/missing", source, "<value><ref>a</ref></value>", 1);
        faults += sweep("IDREFS/elements/duplicate", source, "<value><id>a</id><id>a</id></value>", 0);
        faults += sweep("IDREFS/elements/repeated-ref", source, "<value><ref>a</ref><ref>a</ref><id>a</id></value>", 0);
        faults += sweep("IDREFS/elements/list", source, "<value><ref>a b</ref><id>a</id><id>b</id></value>", 0);
        faults += sweep("IDREFS/elements/missing-list-item", source, "<value><ref>a b</ref><id>a</id></value>", 1);
        faults += sweep("IDREFS/elements/duplicate-list-ref", source, "<value><ref>a a</ref><id>a</id></value>", 0);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"item\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:attribute name=\"id\" type=\"xs:ID\"/><xs:attribute name=\"ref\" type=\"xs:IDREFS\"/></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>";
        faults += sweep("IDREFS/attributes/empty", source, "<value></value>", 0);
        faults += sweep("IDREFS/attributes/forward", source, "<value><item ref=\"a\"/><item id=\"a\"/></value>", 0);
        faults += sweep("IDREFS/attributes/missing", source, "<value><item ref=\"a\"/></value>", 1);
        faults += sweep("IDREFS/attributes/duplicate", source, "<value><item id=\"a\"/><item id=\"a\"/></value>", 1);
        faults += sweep("IDREFS/attributes/repeated-ref", source, "<value><item ref=\"a\"/><item ref=\"a\"/><item id=\"a\"/></value>", 0);
        faults += sweep("IDREFS/attributes/list", source, "<value><item ref=\"a b\"/><item id=\"a\"/><item id=\"b\"/></value>", 0);
        faults += sweep("IDREFS/attributes/missing-list-item", source, "<value><item ref=\"a b\"/><item id=\"a\"/></value>", 1);
        faults += sweep("IDREFS/attributes/duplicate-list-ref", source, "<value><item ref=\"a a\"/><item id=\"a\"/></value>", 0);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"id\" type=\"xs:ID\" minOccurs=\"0\" maxOccurs=\"unbounded\"/><xs:element name=\"ref\" type=\"xs:IDREF\" minOccurs=\"0\"/></xs:sequence><xs:attribute name=\"id\" type=\"xs:ID\"/></xs:complexType></xs:element></xs:schema>";
        faults += sweep("siblings/same-parent", source, "<value><id>a</id><id>a</id><ref>a</ref></value>", 0);
        faults += sweep("siblings/attribute-and-child", source, "<value id=\"a\"><id>a</id><ref>a</ref></value>", 0);
        faults += sweep("siblings/missing", source, "<value><id>a</id><ref>b</ref></value>", 1);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"item\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:sequence><xs:element name=\"id\" type=\"xs:ID\" minOccurs=\"0\"/></xs:sequence><xs:attribute name=\"id\" type=\"xs:ID\"/><xs:attribute name=\"ref\" type=\"xs:IDREF\"/></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>";
        faults += sweep("cousins/unique", source, "<value><item><id>a</id></item><item><id>b</id></item></value>", 0);
        faults += sweep("cousins/distinct-parent", source, "<value><item><id>a</id></item><item><id>a</id></item></value>", 1);
        faults += sweep("cousins/attribute-duplicate", source, "<value><item id=\"a\"/><item id=\"a\"/></value>", 1);
        faults += sweep("cousins/forward", source, "<value><item ref=\"a\"/><item id=\"a\"/></value>", 0);
        faults += sweep("cousins/missing", source, "<value><item ref=\"a\"/></value>", 1);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:simpleType><xs:restriction base=\"xs:ID\"/></xs:simpleType></xs:element></xs:schema>";
        faults += sweep("root-id/unbound", source, "<value>a</value>", 1);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:complexType><xs:simpleContent><xs:extension base=\"xs:ID\"><xs:attribute name=\"id\" type=\"xs:ID\"/><xs:attribute name=\"ref\" type=\"xs:IDREF\"/></xs:extension></xs:simpleContent></xs:complexType></xs:element></xs:schema>";
        faults += sweep("root-id-with-attribute/unbound", source, "<value>a</value>", 1);
        faults += sweep("root-id-with-attribute/bound", source, "<value id=\"a\">a</value>", 0);
        faults += sweep("root-id-with-attribute/unbound-reference", source, "<value ref=\"a\">a</value>", 1);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"item\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:attribute name=\"id\" type=\"xs:ID\"/><xs:attribute name=\"ref\" type=\"xs:IDREF\" default=\"a\"/></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>";
        faults += sweep("default-IDREF/missing", source, "<value><item/></value>", 1);
        faults += sweep("default-IDREF/bound", source, "<value><item id=\"a\"/></value>", 0);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"item\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:attribute name=\"id\" type=\"xs:ID\"/><xs:attribute name=\"ref\" type=\"xs:IDREFS\" default=\"a\"/></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>";
        faults += sweep("default-IDREFS/missing", source, "<value><item/></value>", 1);
        faults += sweep("default-IDREFS/bound", source, "<value><item id=\"a\"/></value>", 0);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:simpleType name=\"Choice\"><xs:union memberTypes=\"xs:IDREF xs:string\"/></xs:simpleType><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"item\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:attribute name=\"id\" type=\"xs:ID\"/><xs:attribute name=\"ref\" type=\"Choice\"/></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>";
        faults += sweep("union-IDREF/missing", source, "<value><item ref=\"a\"/></value>", 1);
        faults += sweep("union-IDREF/bound", source, "<value><item ref=\"a\"/><item id=\"a\"/></value>", 0);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:simpleType name=\"Choice\"><xs:union memberTypes=\"xs:string xs:IDREF\"/></xs:simpleType><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"item\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:attribute name=\"id\" type=\"xs:ID\"/><xs:attribute name=\"ref\" type=\"Choice\"/></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>";
        faults += sweep("union-string/missing", source, "<value><item ref=\"a\"/></value>", 0);
        faults += sweep("union-string/bound", source, "<value><item ref=\"a\"/><item id=\"a\"/></value>", 0);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:simpleType name=\"Identifier\"><xs:restriction base=\"xs:ID\"><xs:pattern value=\"a\"/></xs:restriction></xs:simpleType><xs:simpleType name=\"Choice\"><xs:union memberTypes=\"Identifier xs:string\"/></xs:simpleType><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"item\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:attribute name=\"id\" type=\"Choice\"/><xs:attribute name=\"ref\" type=\"xs:IDREF\"/></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>";
        faults += sweep("union-id-trials/different-selected-types", source, "<value><item id=\"b\"/><item id=\"b\"/></value>", 0);
        faults += sweep("union-id-trials/missing-selected-string", source, "<value><item id=\"b\"/><item ref=\"b\"/></value>", 1);
        faults += sweep("union-id-trials/selected-id", source, "<value><item id=\"a\"/><item ref=\"a\"/></value>", 0);
        faults += sweep("union-id-trials/selected-id-duplicate", source, "<value><item id=\"a\"/><item id=\"a\"/></value>", 1);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:simpleType name=\"Choice\"><xs:union memberTypes=\"xs:IDREF xs:int\"/></xs:simpleType><xs:simpleType name=\"References\"><xs:list itemType=\"Choice\"/></xs:simpleType><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"ref\" type=\"References\"/><xs:element name=\"id\" type=\"xs:ID\" minOccurs=\"0\" maxOccurs=\"unbounded\"/></xs:sequence></xs:complexType></xs:element></xs:schema>";
        faults += sweep("list-union/missing", source, "<value><ref>a 17</ref></value>", 1);
        faults += sweep("list-union/bound", source, "<value><ref>a 17</ref><id>a</id></value>", 0);
        faults += sweep("list-union/numeric", source, "<value><ref>17 23</ref></value>", 0);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:attribute name=\"ref\" type=\"xs:IDREF\"/><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"id\" type=\"xs:ID\" minOccurs=\"0\"/></xs:sequence><xs:anyAttribute processContents=\"strict\"/></xs:complexType></xs:element></xs:schema>";
        faults += sweep("wildcard-attribute-strict/missing", source, "<value ref=\"a\"/>", 1);
        faults += sweep("wildcard-attribute-strict/bound", source, "<value ref=\"a\"><id>a</id></value>", 0);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"id\" type=\"xs:ID\"/><xs:element name=\"ref\" type=\"xs:IDREF\"/><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:any minOccurs=\"0\" maxOccurs=\"unbounded\" processContents=\"strict\"/></xs:sequence></xs:complexType></xs:element></xs:schema>";
        faults += sweep("wildcard-element-strict/missing", source, "<value><ref>a</ref></value>", 1);
        faults += sweep("wildcard-element-strict/bound", source, "<value><ref>a</ref><id>a</id></value>", 0);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:attribute name=\"ref\" type=\"xs:IDREF\"/><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"id\" type=\"xs:ID\" minOccurs=\"0\"/></xs:sequence><xs:anyAttribute processContents=\"lax\"/></xs:complexType></xs:element></xs:schema>";
        faults += sweep("wildcard-attribute-lax/missing", source, "<value ref=\"a\"/>", 1);
        faults += sweep("wildcard-attribute-lax/bound", source, "<value ref=\"a\"><id>a</id></value>", 0);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"id\" type=\"xs:ID\"/><xs:element name=\"ref\" type=\"xs:IDREF\"/><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:any minOccurs=\"0\" maxOccurs=\"unbounded\" processContents=\"lax\"/></xs:sequence></xs:complexType></xs:element></xs:schema>";
        faults += sweep("wildcard-element-lax/missing", source, "<value><ref>a</ref></value>", 1);
        faults += sweep("wildcard-element-lax/bound", source, "<value><ref>a</ref><id>a</id></value>", 0);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:attribute name=\"ref\" type=\"xs:IDREF\"/><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"id\" type=\"xs:ID\" minOccurs=\"0\"/></xs:sequence><xs:anyAttribute processContents=\"skip\"/></xs:complexType></xs:element></xs:schema>";
        faults += sweep("wildcard-attribute-skip/missing", source, "<value ref=\"a\"/>", 0);
        faults += sweep("wildcard-attribute-skip/bound", source, "<value ref=\"a\"><id>a</id></value>", 0);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"id\" type=\"xs:ID\"/><xs:element name=\"ref\" type=\"xs:IDREF\"/><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:any minOccurs=\"0\" maxOccurs=\"unbounded\" processContents=\"skip\"/></xs:sequence></xs:complexType></xs:element></xs:schema>";
        faults += sweep("wildcard-element-skip/missing", source, "<value><ref>a</ref></value>", 0);
        faults += sweep("wildcard-element-skip/bound", source, "<value><ref>a</ref><id>a</id></value>", 0);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"ref\" type=\"xs:token\"/><xs:element name=\"id\" type=\"xs:token\" minOccurs=\"0\"/></xs:sequence></xs:complexType></xs:element></xs:schema>";
        faults += sweep("dynamic-types/missing", source, "<value xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><ref xsi:type=\"xs:IDREF\">a</ref></value>", 1);
        faults += sweep("dynamic-types/bound", source, "<value xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><ref xsi:type=\"xs:IDREF\">a</ref><id xsi:type=\"xs:ID\">a</id></value>", 0);
        faults += sweep("dynamic-types/untyped", source, "<value><ref>a</ref></value>", 0);
    }
    xmlCleanupParser();
    assert(live == 0);
    printf("Native ID binding allocation: PASS (%zu faults)\n", faults);
    return 0;
}
