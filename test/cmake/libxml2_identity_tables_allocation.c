/* Copyright (C) 2026 Qore Technologies, s.r.o. */
#ifdef NDEBUG
#undef NDEBUG
#endif
/* Compile the checked native schema source to exercise its private checker. */
#define IN_LIBXML
#include "libxml.h"
#include <libxml/xmlschemastypes.h>
static int counted_equal(xmlSchemaValPtr a, xmlSchemaWhitespaceValueType aws,
                         xmlSchemaValPtr b, xmlSchemaWhitespaceValueType bws);
#define xmlSchemaCompareValuesWhtsp counted_equal
#include QORE_XML_SCHEMA_SOURCE
#undef xmlSchemaCompareValuesWhtsp
static size_t comparisons;
static int counted_equal(xmlSchemaValPtr a, xmlSchemaWhitespaceValueType aws,
                         xmlSchemaValPtr b, xmlSchemaWhitespaceValueType bws) {
    ++comparisons;
    return xmlSchemaCompareValuesWhtsp(a, aws, b, bws);
}
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


/* Exercise each allocating merge branch independently, including persistent
 * allocation failure. Keys and nodes are borrowed; bindings own only arrays. */
enum Scenario {
    BUBBLE_NEW, BUBBLE_EMPTY, BUBBLE_CONFLICT, BUBBLE_GROW,
    FILL_NEW, FILL_GROW, FILL_OVERRIDE, FILL_REPLACE,
    BUBBLE_IGNORED_CONFLICT, BUBBLE_EXISTING_CONFLICT, BUBBLE_UNUSED,
    FILL_UNUSED, BUBBLE_NEW_THEN_CONFLICT, BUBBLE_CONFLICT_THEN_NEW, SCENARIOS
};
static xmlSchemaPSVIIDCBindingPtr binding(xmlSchemaIDCPtr definition,
        xmlSchemaPSVIIDCNodePtr node) {
    xmlSchemaPSVIIDCBindingPtr result = xmlSchemaIDCNewBinding(definition);
    assert(result != NULL);
    if (node != NULL) {
        result->nodeTable = xmlMalloc(sizeof(*result->nodeTable));
        assert(result->nodeTable != NULL);
        result->nodeTable[0] = node;
        result->nbNodes = result->sizeNodes = 1;
    }
    return result;
}
static void conflict(xmlSchemaPSVIIDCBindingPtr bind, xmlSchemaPSVIIDCNodePtr node) {
    bind->dupls = xmlSchemaItemListCreate();
    assert(bind->dupls != NULL);
    assert(xmlSchemaItemListAdd(bind->dupls, node) == 0);
}
static size_t assess(enum Scenario scenario, size_t fault, int permanent) {
    xmlSchemaValidCtxtPtr context = xmlSchemaNewValidCtxt(NULL);
    xmlSchemaIDC definition = {0};
    xmlSchemaIDCAug augmented = {0};
    xmlSchemaIDCMatcher matcher = {0};
    xmlSchemaNodeInfo parent = {0}, child = {0};
    xmlSchemaNodeInfoPtr elements[] = {&parent, &child};
    xmlSchemaPSVIIDCKey keys[3] = {{0}};
    xmlSchemaPSVIIDCKeyPtr fields[3][1] = {{&keys[0]}, {&keys[1]}, {&keys[2]}};
    xmlSchemaPSVIIDCNode nodes[3] = {{0}};
    xmlSchemaPSVIIDCBindingPtr result;
    int i, status, filling = scenario == FILL_NEW || scenario == FILL_GROW
        || scenario == FILL_OVERRIDE || scenario == FILL_REPLACE || scenario == FILL_UNUSED;
    size_t count;
    assert(context != NULL);
    definition.type = XML_SCHEMA_TYPE_IDC_KEY;
    definition.nbFields = 1;
    augmented.def = &definition;
    augmented.keyrefDepth = 0;
    context->aidcs = &augmented;
    context->createIDCNodeTables = 1;
    context->depth = 1;
    context->elemInfos = elements;
    context->inode = &child;
    xmlSchemaSetValidErrors(context, error_handler, error_handler, NULL);
    for (i = 0; i < 3; i++) {
        keys[i].type = xmlSchemaGetBuiltInType(XML_SCHEMAS_INT);
        assert(xmlSchemaValidatePredefinedType(keys[i].type,
            BAD_CAST (i == 2 ? "2" : "1"), &keys[i].val) == 0);
        nodes[i].keys = fields[i];
    }
    if (filling) {
        matcher.aidc = &augmented;
        matcher.depth = 1;
        matcher.targets = xmlSchemaItemListCreate();
        assert(matcher.targets != NULL);
        assert(xmlSchemaItemListAdd(matcher.targets,
            scenario == FILL_GROW ? &nodes[2] : &nodes[1]) == 0);
        child.idcMatchers = &matcher;
        if (scenario == FILL_GROW || scenario == FILL_REPLACE) {
            child.idcTable = binding(&definition, &nodes[0]);
        } else if (scenario == FILL_OVERRIDE) {
            child.idcTable = binding(&definition, &nodes[2]);
            conflict(child.idcTable, &nodes[0]);
        }
        if (scenario == FILL_UNUSED) {
            context->createIDCNodeTables = 0;
            augmented.keyrefDepth = -1;
        }
    } else {
        child.idcTable = binding(&definition,
            scenario == BUBBLE_EMPTY || scenario == BUBBLE_GROW
                || scenario == BUBBLE_NEW_THEN_CONFLICT ? &nodes[2] : &nodes[1]);
        if (scenario == BUBBLE_CONFLICT || scenario == BUBBLE_GROW
                || scenario == BUBBLE_NEW_THEN_CONFLICT || scenario == BUBBLE_CONFLICT_THEN_NEW) {
            parent.idcTable = binding(&definition, &nodes[0]);
        } else if (scenario == BUBBLE_EMPTY || scenario == BUBBLE_EXISTING_CONFLICT) {
            parent.idcTable = binding(&definition, NULL);
            conflict(parent.idcTable, &nodes[0]);
        } else if (scenario == BUBBLE_IGNORED_CONFLICT) {
            child.idcTable->nbNodes = 0;
            conflict(child.idcTable, &nodes[0]);
        } else if (scenario == BUBBLE_UNUSED) {
            context->createIDCNodeTables = 0;
            augmented.keyrefDepth = -1;
        }
    }
    if (scenario == BUBBLE_NEW_THEN_CONFLICT || scenario == BUBBLE_CONFLICT_THEN_NEW) {
        assert(xmlSchemaIDCAppendNodeTableItem(context, child.idcTable,
            scenario == BUBBLE_NEW_THEN_CONFLICT ? &nodes[1] : &nodes[2]) == 0);
    }
    attempts = 0;
    fail_at = fault;
    failed = 0;
    persistent = permanent;
    armed = 1;
    status = filling ? xmlSchemaIDCFillNodeTables(context, &child)
                     : xmlSchemaBubbleIDCNodeTables(context);
    armed = 0;
    count = attempts;
    assert(failed == (fault != 0));
    if (failed) {
        assert(status == -1 && context->err == XML_ERR_NO_MEMORY);
    } else {
        assert(status == 0 && context->err == 0);
        result = filling ? child.idcTable : parent.idcTable;
        switch (scenario) {
            case BUBBLE_NEW:
            case FILL_NEW:
            case FILL_REPLACE:
                assert(result != NULL && result->nbNodes == 1 && result->nodeTable[0] == &nodes[1]);
                break;
            case BUBBLE_NEW_THEN_CONFLICT:
            case BUBBLE_CONFLICT_THEN_NEW:
            case BUBBLE_EMPTY:
                assert(result->nbNodes == 1 && result->nodeTable[0] == &nodes[2]);
                assert(result->dupls->nbItems == 1);
                break;
            case BUBBLE_CONFLICT:
            case BUBBLE_EXISTING_CONFLICT:
                assert(result->nbNodes == 0 && result->dupls->nbItems == 1);
                break;
            case BUBBLE_GROW:
            case FILL_GROW:
                assert(result->nbNodes == 2 && result->nodeTable[0] == &nodes[0]
                    && result->nodeTable[1] == &nodes[2]);
                break;
            case FILL_OVERRIDE:
                assert(result->nbNodes == 2 && result->nodeTable[0] == &nodes[2]
                    && result->nodeTable[1] == &nodes[1] && result->dupls->nbItems == 0);
                break;
            case BUBBLE_IGNORED_CONFLICT:
            case BUBBLE_UNUSED:
            case FILL_UNUSED:
                assert(result == NULL);
                break;
            default:
                assert(0);
        }
    }
    /* Stack-owned nodes, matchers, and schema components are detached before
     * freeing the context; every partially published binding is still owned. */
    context->elemInfos = NULL;
    context->inode = NULL;
    context->aidcs = NULL;
    xmlSchemaIDCFreeIDCTable(parent.idcTable);
    xmlSchemaIDCFreeIDCTable(child.idcTable);
    xmlSchemaItemListFree(matcher.targets);
    for (i = 0; i < 3; i++) {
        xmlSchemaFreeValue(keys[i].val);
    }
    xmlSchemaFreeValidCtxt(context);
    xmlResetLastError();
    return count;
}

/* Deterministic complexity checks, independent of machine load or build mode.
 * A single child table and a local table are already unique: never compare
 * entries newly added from either table with one another. */
static void linear_merge(int count, int filling) {
    xmlSchemaValidCtxtPtr context = xmlSchemaNewValidCtxt(NULL);
    xmlSchemaIDC definition = {0};
    xmlSchemaIDCAug augmented = {0};
    xmlSchemaIDCMatcher matcher = {0};
    xmlSchemaNodeInfo parent = {0}, child = {0};
    xmlSchemaNodeInfoPtr elements[] = {&parent, &child};
    xmlSchemaPSVIIDCKey *keys = calloc(count + 1, sizeof(*keys));
    xmlSchemaPSVIIDCKeyPtr *fields = calloc(count + 1, sizeof(*fields));
    xmlSchemaPSVIIDCNode *nodes = calloc(count + 1, sizeof(*nodes));
    xmlSchemaPSVIIDCBindingPtr table;
    int i;
    assert(context != NULL && keys != NULL && fields != NULL && nodes != NULL);
    definition.type = XML_SCHEMA_TYPE_IDC_KEY;
    definition.nbFields = 1;
    augmented.def = &definition;
    context->createIDCNodeTables = 1;
    context->depth = 1;
    context->elemInfos = elements;
    context->inode = &child;
    for (i = 0; i <= count; i++) {
        char value[32];
        int length = snprintf(value, sizeof(value), "%d", i);
        assert(length > 0 && (size_t)length < sizeof(value));
        keys[i].type = xmlSchemaGetBuiltInType(XML_SCHEMAS_INT);
        assert(xmlSchemaValidatePredefinedType(keys[i].type, BAD_CAST value, &keys[i].val) == 0);
        fields[i] = &keys[i];
        nodes[i].keys = &fields[i];
    }
    if (filling) {
        matcher.aidc = &augmented;
        matcher.depth = 1;
        matcher.targets = xmlSchemaItemListCreate();
        assert(matcher.targets != NULL);
        for (i = 1; i <= count; i++) {
            assert(xmlSchemaItemListAdd(matcher.targets, &nodes[i]) == 0);
        }
        child.idcTable = binding(&definition, &nodes[0]);
        child.idcMatchers = &matcher;
        comparisons = 0;
        assert(xmlSchemaIDCFillNodeTables(context, &child) == 0);
        assert(comparisons == (size_t)count);
        table = child.idcTable;
        assert(table->nbNodes == count + 1 && table->nodeTable[0] == &nodes[0]);
        for (i = 1; i <= count; i++) {
            assert(table->nodeTable[i] == &nodes[i]);
        }
    } else {
        child.idcTable = binding(&definition, NULL);
        for (i = 1; i <= count; i++) {
            assert(xmlSchemaIDCAppendNodeTableItem(context, child.idcTable, &nodes[i]) == 0);
        }
        comparisons = 0;
        assert(xmlSchemaBubbleIDCNodeTables(context) == 0);
        assert(comparisons == 0);
        table = parent.idcTable;
        assert(table->nbNodes == count);
        for (i = 1; i <= count; i++) {
            assert(table->nodeTable[i - 1] == &nodes[i]);
        }
    }
    context->elemInfos = NULL;
    context->inode = NULL;
    xmlSchemaIDCFreeIDCTable(parent.idcTable);
    xmlSchemaIDCFreeIDCTable(child.idcTable);
    xmlSchemaItemListFree(matcher.targets);
    xmlSchemaFreeValidCtxt(context);
    for (i = 0; i <= count; i++) {
        xmlSchemaFreeValue(keys[i].val);
    }
    free(nodes);
    free(fields);
    free(keys);
}
int main(void) {
    size_t baseline, count, fault, total = 0;
    int permanent;
    enum Scenario scenario;
    assert(xmlMemSetup(release, allocate, resize, duplicate) == 0);
    xmlSetGenericErrorFunc(NULL, error_handler);
    xmlInitParser();
    assert(xmlSchemaInitTypes() == 0);
    baseline = live;
    for (scenario = 0; scenario < SCENARIOS; scenario++) {
        count = assess(scenario, 0, 0);
        assert(live == baseline);
        total += count;
        for (permanent = 0; permanent < 2; permanent++) {
            for (fault = 1; fault <= count; fault++) {
                assess(scenario, fault, permanent);
                assert(live == baseline);
                assess(scenario, 0, 0);
                assert(live == baseline);
            }
        }
    }
    linear_merge(128, 0);
    assert(live == baseline);
    linear_merge(1024, 0);
    assert(live == baseline);
    linear_merge(128, 1);
    assert(live == baseline);
    linear_merge(1024, 1);
    assert(live == baseline);
    xmlCleanupParser();
    assert(live == 0);
    printf("Native identity table allocation: PASS (%d scenarios, %zu fault positions)\n", SCENARIOS, total);
    return 0;
}
