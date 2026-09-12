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
    static const char* plain =
        "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
        "<xs:element name='value' type='xs:int'/></xs:schema>";
    static const char* wildcard =
        "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
        "<xs:complexType name='Record'><xs:sequence><xs:element name='code' type='xs:int'/>"
        "</xs:sequence><xs:attribute name='tag' type='xs:string' use='required'/></xs:complexType>"
        "<xs:element name='root'><xs:complexType><xs:sequence>"
        "<xs:any processContents='strict' maxOccurs='unbounded'/></xs:sequence>"
        "</xs:complexType></xs:element></xs:schema>";
    static const char* inputs[] = {
        "<root xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>"
        "<unknown xsi:type='Record' tag='shipment'><code>17</code></unknown></root>",
        "<root xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>"
        "<unknown xsi:type='Record' tag='shipment'><code>bad</code></unknown></root>",
        "<root xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>"
        "<unknown xsi:type='Missing'/></root>",
        "<root xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>"
        "<unknown xsi:type='Record'><code>17</code></unknown></root>"
    };
    static const char* labels[] = {"wildcard-valid", "wildcard-invalid-int", "wildcard-unresolved-type",
        "wildcard-missing-attribute"};
    unsigned int item;
    size_t faults = 0;
    assert(xmlMemSetup(release, allocate, resize, duplicate) == 0);
    xmlInitParser();
    xmlSetGenericErrorFunc(NULL, error_handler);
    faults += sweep("plain-valid", plain, "<value>17</value>", 0);
    faults += sweep("plain-invalid", plain, "<value>bad</value>", 1);
    for (item = 0; item < sizeof(inputs) / sizeof(inputs[0]); ++item) {
        faults += sweep(labels[item], wildcard, inputs[item], item != 0);
    }
    xmlCleanupParser();
    assert(live == 0);
    printf("Native wildcard instance-type phase cleanup: PASS (%zu injected failures per API)\n", faults);
    return 0;
}
