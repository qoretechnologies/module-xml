/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Inject permanent allocation failures in datatype APIs and computed fixed values.
 */
#ifdef NDEBUG
#undef NDEBUG
#endif
#include QORE_XML_SCHEMA_SOURCE
#include <libxml/xmlerror.h>
#include <string.h>
#include <assert.h>
#include <stdlib.h>
#include <stdio.h>

static size_t live, attempts, fail_at;
static int armed;
static void *allocate(size_t size) {
    void *result;
    if (armed && ++attempts >= fail_at && fail_at != 0) {
        return NULL;
    }
    result = malloc(size);
    if (result != NULL) {
        ++live;
    }
    return result;
}
static void release(void *value) {
    if (value != NULL) {
        assert(live != 0);
        --live;
        free(value);
    }
}
static void *resize(void *value, size_t size) {
    if (value == NULL) {
        return allocate(size);
    }
    if (size == 0) {
        release(value);
        return NULL;
    }
    if (armed && ++attempts >= fail_at && fail_at != 0) {
        return NULL;
    }
    return realloc(value, size);
}
static char *duplicate(const char *value) {
    size_t size = strlen(value) + 1;
    char *result = allocate(size);
    if (result != NULL) {
        memcpy(result, value, size);
    }
    return result;
}
static void ignore_error(void *data, const char *message, ...) {
    (void)data;
    (void)message;
}
static size_t check(xmlSchemaValType code, const char *lexical, int valid) {
    xmlSchemaTypePtr type = xmlSchemaGetBuiltInType(code);
    size_t baseline, count, fault;
    int with_value;
    assert(type != NULL);
    xmlResetLastError();
    baseline = live;
    count = 0;
    for (with_value = 0; with_value <= 1; ++with_value) {
        size_t allocations = 0;
        for (fault = 0; fault <= allocations; ++fault) {
            xmlSchemaValPtr output = NULL;
            int result;
            attempts = 0;
            fail_at = fault;
            armed = 1;
            result = xmlSchemaValidatePredefinedType(type, BAD_CAST lexical, with_value ? &output : NULL);
            armed = 0;
            if (fault == 0) {
                allocations = attempts;
                assert(valid ? result == 0 : result > 0);
                assert((output != NULL) == (valid && with_value));
            } else {
                if (result != -1) {
                    fprintf(stderr, "datatype %d lexical '%s' computed %d fault %zu/%zu returned %d\n",
                        (int)code, lexical, with_value, fault, allocations, result);
                }
                assert(result == -1);
                assert(output == NULL);
            }
            xmlSchemaFreeValue(output);
            xmlResetLastError();
            if (live != baseline) {
                fprintf(stderr, "datatype %d lexical '%s' computed %d fault %zu/%zu live %zu baseline %zu\n",
                    (int)code, lexical, with_value, fault, allocations, live, baseline);
            }
            assert(live == baseline);
        }
        count += allocations;
        /* A successful call after faults also verifies that no poisoned state remains. */
        assert(xmlSchemaValidatePredefinedType(type, BAD_CAST lexical, NULL) == (valid ? 0 : 1));
    }
    return count;
}
static size_t check_computed(const char *type, const char *fixed, const char *lexical) {
    char source[1024];
    int length = snprintf(source, sizeof(source),
        "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
        "<xs:simpleType name='List'><xs:list itemType='xs:int'/></xs:simpleType>"
        "<xs:element name='root' type='%s' fixed='%s'/></xs:schema>", type, fixed);
    assert(length > 0 && (size_t)length < sizeof(source));
    xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
    xmlSchemaPtr schema;
    xmlSchemaElementPtr element;
    size_t baseline, count = 0, fault;
    assert(parser != NULL);
    xmlSchemaSetParserErrors(parser, ignore_error, ignore_error, NULL);
    schema = xmlSchemaParse(parser);
    assert(schema != NULL);
    element = xmlHashLookup(schema->elemDecl, BAD_CAST "root");
    assert(element != NULL);
    xmlResetLastError();
    baseline = live;
    for (fault = 0; fault <= count; ++fault) {
        xmlSchemaValPtr value = NULL;
        int result;
        attempts = 0;
        fail_at = fault;
        armed = 1;
        result = xmlSchemaVCheckCVCSimpleType(ACTXT_CAST parser, element->node,
            WXS_ELEM_TYPEDEF(element), BAD_CAST lexical, &value, 1, 1, 0);
        armed = 0;
        if (fault == 0) {
            count = attempts;
            assert(result == 0);
            assert(xmlSchemaAreValuesEqual(value, element->defVal) == 1);
        } else {
            if (result >= 0) {
                fprintf(stderr, "%s computed-value fault %zu/%zu returned %d\n", type, fault, count, result);
            }
            assert(result < 0);
            assert(value == NULL);
        }
        xmlSchemaFreeValue(value);
        xmlResetLastError();
        assert(live == baseline);
    }
    assert(xmlSchemaAreValuesEqual(NULL, NULL) == 1);
    assert(xmlSchemaAreValuesEqual(NULL, element->defVal) == 0);
    assert(xmlSchemaAreValuesEqual(element->defVal, NULL) == 0);
    xmlSchemaFree(schema);
    xmlSchemaFreeParserCtxt(parser);
    return count;
}
int main(void) {
    static const xmlSchemaValType positive[] = {
        XML_SCHEMAS_INTEGER, XML_SCHEMAS_NNINTEGER, XML_SCHEMAS_PINTEGER,
        XML_SCHEMAS_INT, XML_SCHEMAS_UINT, XML_SCHEMAS_LONG, XML_SCHEMAS_ULONG,
        XML_SCHEMAS_SHORT, XML_SCHEMAS_USHORT, XML_SCHEMAS_BYTE, XML_SCHEMAS_UBYTE
    };
    size_t index, count = 0;
    assert(xmlMemSetup(release, allocate, resize, duplicate) == 0);
    xmlInitParser();
    xmlSetGenericErrorFunc(NULL, ignore_error);
    for (index = 0; index < sizeof(positive) / sizeof(positive[0]); ++index) {
        count += check(positive[index], "0017", 1);
        count += check(positive[index], "17x", 0);
    }
    count += check(XML_SCHEMAS_NINTEGER, "-0017", 1);
    count += check(XML_SCHEMAS_NPINTEGER, "-0", 1);
    count += check(XML_SCHEMAS_INTEGER, "+000123456789012345678901234567890123456789012345678901234567890", 1);
    count += check(XML_SCHEMAS_UINT, "4294967296", 0);
    count += check(XML_SCHEMAS_INT, "-2147483649", 0);
    /* ID constraints cannot have a fixed declaration; exercise its shared
     * string-value ownership path through the public datatype API instead. */
    count += check(XML_SCHEMAS_ID, "part", 1);
    count += check(XML_SCHEMAS_INT, " \t0017\r\n ", 1);
    count += check(XML_SCHEMAS_INT, " \t17x\n ", 0);
    count += check(XML_SCHEMAS_NORMSTRING, "part\tcode", 1);
    count += check(XML_SCHEMAS_TOKEN, " \tpart  code\n ", 1);
    count += check(XML_SCHEMAS_NCNAME, " \tpart\n ", 1);
    count += check(XML_SCHEMAS_ANYURI, " \turn:part\n ", 1);
    count += check(XML_SCHEMAS_HEXBINARY, "ab00FF", 1);
    count += check(XML_SCHEMAS_HEXBINARY, "", 1);
    count += check(XML_SCHEMAS_HEXBINARY, "0g", 0);
    count += check(XML_SCHEMAS_HEXBINARY, "f", 0);
    count += check(XML_SCHEMAS_BASE64BINARY, " Y W\tJ\nj\r ", 1);
    count += check(XML_SCHEMAS_BASE64BINARY, "YQ==", 1);
    count += check(XML_SCHEMAS_BASE64BINARY, "YWI=", 1);
    count += check(XML_SCHEMAS_BASE64BINARY, "", 1);
    count += check(XML_SCHEMAS_BASE64BINARY, "YW!Jj", 0);
    count += check(XML_SCHEMAS_BASE64BINARY, "YQ==!", 0);
    count += check(XML_SCHEMAS_BASE64BINARY, "YWJj\302\240", 0);
    count += check(XML_SCHEMAS_BASE64BINARY, "YR==", 0);
    count += check_computed("xs:hexBinary", "AB00FF", "ab00ff");
    count += check_computed("xs:base64Binary", "YWJj", "Y W J j");
    count += check_computed("List", "17 0", "+0017 -0");
    count += check_computed("xs:anySimpleType", "part", "part");
    count += check_computed("xs:string", "part", "part");
    count += check_computed("xs:normalizedString", "part", "part");
    count += check_computed("xs:token", "part", "part");
    count += check_computed("xs:language", "en", "en");
    count += check_computed("xs:NMTOKEN", "part", "part");
    count += check_computed("xs:Name", "part", "part");
    count += check_computed("xs:NCName", "part", "part");
    count += check_computed("xs:IDREF", "part", "part");
    count += check_computed("xs:anyURI", "urn:part", "urn:part");
    assert(count > 40);
    xmlCleanupParser();
    assert(live == 0);
    printf("Native datatype allocation cleanup: PASS (%zu injected failures)\n", count);
    return 0;
}
