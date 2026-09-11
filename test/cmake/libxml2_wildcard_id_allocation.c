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


static size_t exercise(xmlSchemaTypePtr type, const char* lexical, size_t fault, int invalid) {
    xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(" ", 1);
    xmlSchemaAttribute declaration;
    xmlSchemaAttributeUse use;
    size_t count;
    int result;
    assert(parser != NULL);
    memset(&declaration, 0, sizeof(declaration));
    memset(&use, 0, sizeof(use));
    declaration.type = XML_SCHEMA_TYPE_ATTRIBUTE;
    declaration.name = BAD_CAST "identifier";
    declaration.subtypes = type;
    use.type = XML_SCHEMA_TYPE_ATTRIBUTE_USE;
    use.attrDecl = &declaration;
    use.defValue = BAD_CAST lexical;
    xmlSchemaSetParserErrors(parser, error_handler, error_handler, NULL);
    attempts = 0; fail_at = fault; failed = 0; armed = 1;
    result = xmlSchemaCheckAttrUsePropsCorrect(parser, &use);
    armed = 0;
    assert(failed ? result != 0 : (result != 0) == invalid);
    if (!failed && !invalid) {
        assert(use.defVal != NULL);
    }
    count = attempts;
    xmlSchemaFreeValue(use.defVal);
    xmlSchemaFreeParserCtxt(parser);
    xmlResetLastError();
    return count;
}

int main(void) {
    const int types[] = {XML_SCHEMAS_INT, XML_SCHEMAS_INT, XML_SCHEMAS_ID};
    const char* values[] = {"17", "not-an-integer", "identifier"};
    size_t faults = 0;
    assert(xmlMemSetup(release, allocate, resize, duplicate) == 0);
    xmlInitParser();
    xmlSetGenericErrorFunc(NULL, error_handler);
    assert(xmlSchemaInitTypes() == 0);
    for (unsigned int item = 0; item < sizeof(types) / sizeof(types[0]); ++item) {
        xmlSchemaTypePtr type = xmlSchemaGetBuiltInType(types[item]);
        size_t baseline = live;
        size_t total = exercise(type, values[item], 0, item != 0);
        assert(total > 0 && live == baseline);
        for (size_t fault = 1; fault <= total; ++fault) {
            exercise(type, values[item], fault, item != 0);
            assert(live == baseline);
        }
        assert(exercise(type, values[item], 0, item != 0) == total);
        assert(live == baseline);
        faults += total;
    }
    xmlCleanupParser();
    assert(live == 0);
    printf("Native attribute use constraints: PASS (%zu allocation faults)\n", faults);
    return 0;
}
