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

enum action { DEFAULT_VALUE, EXPAND_QNAME, VALIDATE_QNAME, PREDEFINED_QNAME, COPY_QNAME, NOTATION_VALUE };

static size_t exercise(xmlSchemaPtr schema, xmlDocPtr doc, enum action action,
                       size_t fault, int permanent, const char *lexical, int valid) {
    xmlSchemaValidCtxtPtr ctxt = xmlSchemaNewValidCtxt(schema);
    xmlSchemaNodeInfo info;
    xmlSchemaValPtr value = NULL, original = NULL;
    const xmlChar *uri = NULL, *local = NULL;
    xmlSchemaElementPtr declaration = xmlHashLookup(schema->elemDecl, BAD_CAST "value");
    const xmlChar *declared_text;
    xmlSchemaValPtr declared_value;
    size_t count;
    int ret = 0;
    assert(ctxt != NULL && declaration != NULL);
    declared_text = declaration->value;
    declared_value = declaration->defVal;
    memset(&info, 0, sizeof(info));
    info.node = xmlDocGetRootElement(doc);
    info.localName = info.node->name;
    info.decl = declaration;
    info.typeDef = declaration->subtypes;
    info.flags = XML_SCHEMA_NODE_INFO_VALUE_NEEDED;
    if (action == DEFAULT_VALUE) {
        xmlSchemaTypePtr actual = xmlHashLookup(schema->typeDecl, BAD_CAST "Actual");
        if (actual != NULL) {
            info.typeDef = actual;
            info.flags |= XML_SCHEMA_ELEM_INFO_LOCAL_TYPE;
        }
    }
    ctxt->inode = &info;
    ctxt->doc = doc;
    ctxt->defaultNamespaceNode = action == DEFAULT_VALUE ? info.node : NULL;
    xmlSchemaSetValidErrors(ctxt, error_handler, error_handler, NULL);
    if (action == COPY_QNAME) {
        original = qoreXmlQNameValue(BAD_CAST "urn:part", BAD_CAST "item", 0);
        assert(original != NULL);
    }
    attempts = 0;
    fail_at = fault;
    failed = 0;
    persistent = permanent;
    armed = 1;
    switch (action) {
        case DEFAULT_VALUE:
            ret = qoreXmlValidateElementDefault(ctxt);
            value = info.val;
            info.val = NULL;
            break;
        case EXPAND_QNAME:
            ret = xmlSchemaVExpandQName(ctxt, BAD_CAST lexical, &uri, &local);
            if (ret == 0) {
                assert(xmlStrEqual(uri, BAD_CAST "urn:instance"));
                assert(xmlStrEqual(local, BAD_CAST "item"));
            } else {
                assert(uri == NULL && local == NULL);
            }
            break;
        case VALIDATE_QNAME:
            ret = xmlSchemaValidateQName(ctxt, BAD_CAST lexical, &value, 1, 0);
            break;
        case PREDEFINED_QNAME:
            ret = xmlSchemaValPredefTypeNode(xmlSchemaGetBuiltInType(XML_SCHEMAS_QNAME),
                                             BAD_CAST lexical, &value, info.node);
            break;
        case COPY_QNAME:
            value = xmlSchemaCopyValue(original);
            ret = value == NULL ? -1 : 0;
            break;
        case NOTATION_VALUE:
            ret = xmlSchemaValidateNotation(NULL, schema, declaration->node,
                                            BAD_CAST lexical, &value, 1);
            break;
    }
    armed = 0;
    count = attempts;
    assert(ctxt->defaultNamespaceNode == (action == DEFAULT_VALUE ? info.node : NULL));
    assert(declaration->value == declared_text && declaration->defVal == declared_value);
    assert(failed == (fault != 0));
    if (failed && valid) {
        if (ret >= 0) {
            fprintf(stderr, "action=%d fault=%zu permanent=%d ret=%d\n", action, fault, permanent, ret);
        }
        assert(ret < 0 && value == NULL);
    } else if (!failed) {
        assert(valid ? ret == 0 : ret > 0);
        if (valid && action != EXPAND_QNAME) {
            assert(value != NULL);
        }
    } else {
        assert(ret != 0);
    }
    xmlSchemaFreeValue(value);
    if (action == DEFAULT_VALUE) {
        /* Error recovery uses the same context and the declaration's namespace,
         * not the shadowing instance binding. Original metadata stays owned. */
        ret = qoreXmlValidateElementDefault(ctxt);
        assert(valid ? ret == 0 && info.val != NULL : ret > 0);
        if (valid && info.typeDef == declaration->subtypes) {
            assert(xmlSchemaCompareValues(info.val, declaration->defVal) == 0);
        } else if (valid) {
            assert(xmlSchemaGetValType(info.val) == XML_SCHEMAS_STRING);
            assert(xmlStrEqual(xmlSchemaValueGetAsString(info.val), BAD_CAST "true"));
        }
        xmlSchemaFreeValue(info.val);
        info.val = NULL;
    } else if (original != NULL) {
        value = xmlSchemaCopyValue(original);
        assert(value != NULL && xmlSchemaCompareValues(value, original) == 0);
        xmlSchemaFreeValue(value);
    }
    xmlSchemaFreeValue(original);
    ctxt->inode = NULL;
    xmlSchemaFreeValidCtxt(ctxt);
    xmlResetLastError();
    return count;
}

static size_t canonical_defaults(xmlDocPtr doc) {
    const char *definitions[] = {
        "<xs:element name='value' type='xs:int' default='+017'/>",
        "<xs:element name='value' type='xs:decimal' default='+0017.2300'/>",
        "<xs:element name='value' type='xs:hexBinary' default='abcd'/>",
        "<xs:element name='value' type='xs:base64Binary' default='Y W J j'/>",
        "<xs:element name='value' type='xs:dateTime' default='2000-01-01T00:00:00.100+01:00'/>",
        "<xs:simpleType name='Member'><xs:union memberTypes='xs:int xs:QName'/></xs:simpleType>"
        "<xs:simpleType name='Items'><xs:list itemType='Member'/></xs:simpleType>"
        "<xs:element name='value' type='Items' default='+017 p:item'/>",
        "<xs:simpleType name='Base'><xs:union memberTypes='xs:boolean xs:string'/></xs:simpleType>"
        "<xs:simpleType name='Actual'><xs:restriction base='xs:string'/></xs:simpleType>"
        "<xs:element name='value' type='Base' default='1'/>",
        "<xs:simpleType name='Actual'><xs:restriction base='xs:boolean'><xs:pattern value='1'/>"
        "</xs:restriction></xs:simpleType><xs:element name='value' type='xs:boolean' default='1'/>"
    };
    size_t model, total = 0;
    for (model = 0; model < sizeof(definitions)/sizeof(definitions[0]); ++model) {
        char source[2048];
        xmlSchemaParserCtxtPtr parser;
        xmlSchemaPtr schema;
        size_t baseline, count, index;
        int permanent, valid = model != 7;
        int length = snprintf(source, sizeof(source),
            "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema' xmlns:p='urn:part'>%s</xs:schema>",
            definitions[model]);
        assert(length > 0 && (size_t)length < sizeof(source));
        parser = xmlSchemaNewMemParserCtxt(source, length);
        assert(parser != NULL);
        xmlSchemaSetParserErrors(parser, error_handler, error_handler, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        assert(schema != NULL);
        baseline = live;
        count = exercise(schema, doc, DEFAULT_VALUE, 0, 0, NULL, valid);
        assert(live == baseline && count != 0);
        for (permanent = 0; permanent < 2; ++permanent) {
            for (index = 1; index <= count; ++index) {
                exercise(schema, doc, DEFAULT_VALUE, index, permanent, NULL, valid);
                assert(live == baseline);
                ++total;
            }
        }
        xmlSchemaFree(schema);
    }
    return total;
}

static size_t copy_values(xmlDocPtr doc) {
    static const struct { xmlSchemaValType type; const char *text; } inputs[] = {
        {XML_SCHEMAS_STRING, "original string"}, {XML_SCHEMAS_DECIMAL, "+0017.2300"},
        {XML_SCHEMAS_HEXBINARY, "abcd"}, {XML_SCHEMAS_BASE64BINARY, "YWJj"},
        {XML_SCHEMAS_QNAME, "p:item"}
    };
    xmlSchemaValPtr original = NULL, tail = NULL;
    size_t index, fault, count = 0, total = 0, baseline;
    int permanent;
    for (index = 0; index < sizeof(inputs)/sizeof(inputs[0]); ++index) {
        xmlSchemaValPtr value = NULL;
        int result = xmlSchemaValPredefTypeNodeNoNorm(xmlSchemaGetBuiltInType(inputs[index].type),
            BAD_CAST inputs[index].text, &value, xmlDocGetRootElement(doc));
        if (result != 0 || value == NULL) {
            fprintf(stderr, "copy preparation index=%zu ret=%d value=%p\n", index, result, (void *)value);
        }
        assert(result == 0 && value != NULL);
        if (tail != NULL) {
            assert(xmlSchemaValueAppend(tail, value) == 0);
        } else {
            original = value;
        }
        tail = value;
    }
    {
        xmlSchemaValPtr notation = qoreXmlQNameValue(BAD_CAST "urn:part", BAD_CAST "item", 1);
        assert(notation != NULL && xmlSchemaValueAppend(tail, notation) == 0);
    }
    baseline = live;
    for (permanent = 0; permanent < 2; ++permanent) {
        for (fault = 0; fault <= count; ++fault) {
            xmlSchemaValPtr copy, left, right;
            attempts = 0;
            failed = 0;
            fail_at = fault;
            persistent = permanent;
            armed = 1;
            copy = xmlSchemaCopyValue(original);
            armed = 0;
            if (fault == 0) {
                count = attempts;
                assert(!failed && copy != NULL);
            } else {
                assert(failed && copy == NULL);
                ++total;
            }
            xmlSchemaFreeValue(copy);
            assert(live == baseline);
            copy = xmlSchemaCopyValue(original);
            assert(copy != NULL);
            left = original;
            right = copy;
            while (left != NULL) {
                assert(right != NULL && xmlSchemaCompareValues(left, right) == 0);
                left = xmlSchemaValueGetNext(left);
                right = xmlSchemaValueGetNext(right);
            }
            assert(right == NULL);
            xmlSchemaFreeValue(copy);
            assert(live == baseline);
        }
    }
    xmlSchemaFreeValue(original);
    return total;
}

int main(void) {
    const char source[] =
        "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema' xmlns:p='urn:part'>"
        "<xs:notation name='item' public='urn:item'/>"
        "<xs:element name='value' type='xs:QName' default='p:item'/></xs:schema>";
    const char document[] = "<value xmlns:p='urn:instance'/>";
    const char *valid[] = {"p:item", "  p:item \n", "item", "xml:lang"};
    const char *invalid[] = {"unbound:item", "p:item:bad", "1bad", "p: item", ""};
    xmlSchemaParserCtxtPtr parser;
    xmlSchemaPtr schema;
    xmlDocPtr doc;
    size_t baseline, total = 0, index, count, word;
    enum action action;
    int permanent;
    assert(xmlMemSetup(release, allocate, resize, duplicate) == 0);
    xmlInitParser();
    xmlSetGenericErrorFunc(NULL, error_handler);
    parser = xmlSchemaNewMemParserCtxt(source, sizeof(source) - 1);
    assert(parser != NULL);
    xmlSchemaSetParserErrors(parser, error_handler, error_handler, NULL);
    schema = xmlSchemaParse(parser);
    xmlSchemaFreeParserCtxt(parser);
    doc = xmlReadMemory(document, sizeof(document) - 1, NULL, NULL, XML_PARSE_NONET);
    assert(schema != NULL && doc != NULL);
    /* Initialize builtin tables before measuring lifetime ownership. */
    assert(xmlSchemaGetBuiltInType(XML_SCHEMAS_QNAME) != NULL);
    baseline = live;
    for (action = DEFAULT_VALUE; action <= NOTATION_VALUE; ++action) {
        const char *text = action == NOTATION_VALUE ? " item " : "  p:item \n";
        count = exercise(schema, doc, action, 0, 0, text, 1);
        assert(live == baseline && count != 0);
        for (permanent = 0; permanent < 2; ++permanent) {
            for (index = 1; index <= count; ++index) {
                exercise(schema, doc, action, index, permanent, text, 1);
                assert(live == baseline);
                ++total;
            }
        }
    }
    for (action = VALIDATE_QNAME; action <= PREDEFINED_QNAME; ++action) {
        for (word = 0; word < sizeof(valid)/sizeof(valid[0]); ++word) {
            exercise(schema, doc, action, 0, 0, valid[word], 1);
            assert(live == baseline);
        }
        for (word = 0; word < sizeof(invalid)/sizeof(invalid[0]); ++word) {
            exercise(schema, doc, action, 0, 0, invalid[word], 0);
            assert(live == baseline);
        }
    }
    total += canonical_defaults(doc);
    total += copy_values(doc);
    assert(live == baseline);
    xmlFreeDoc(doc);
    xmlSchemaFree(schema);
    xmlCleanupParser();
    assert(live == 0);
    printf("%zu element-default/QName allocation failures propagated with intact scope and recovery\n", total);
    return 0;
}
