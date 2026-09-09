/* Copyright (C) 2026 Qore Technologies, s.r.o. */
#include <libxml/xmlschemas.h>

static void qname_schema_error(void* context, const char* message, ...) {
    if (context) {
        ++*(int*)context;
    }
    (void)message;
}

static void qname_reader_error(void* context, const char* message, xmlParserSeverities severity,
        xmlTextReaderLocatorPtr locator) {
    if (context) {
        ++*(int*)context;
    }
    (void)message;
    (void)severity;
    (void)locator;
}

static int check_qname_document(xmlSchemaPtr schema, const char* document, int expected) {
    xmlDocPtr tree = xmlReadMemory(document, (int)strlen(document), NULL, "UTF-8", XML_PARSE_NONET);
    const char* rejected = "<undeclared/>";
    xmlDocPtr invalid = xmlReadMemory(rejected, (int)strlen(rejected), NULL, "UTF-8", XML_PARSE_NONET);
    xmlSchemaValidCtxtPtr context = xmlSchemaNewValidCtxt(schema);
    xmlTextReaderPtr reader = NULL;
    int result = 1;
    int status;
    int diagnostics = 0;
    if (!tree || !invalid || !context) {
        goto cleanup;
    }
    xmlSchemaSetValidErrors(context, qname_schema_error, qname_schema_error, &diagnostics);
    status = xmlSchemaValidateDoc(context, tree);
    if (status < 0 || (status == 0) != expected || (diagnostics == 0) != expected) {
        goto cleanup;
    }
    /* A rejected document must not poison subsequent validation on this context. */
    diagnostics = 0;
    status = xmlSchemaValidateDoc(context, invalid);
    if (status <= 0 || !diagnostics) {
        goto cleanup;
    }
    diagnostics = 0;
    status = xmlSchemaValidateDoc(context, tree);
    if (status < 0 || (status == 0) != expected || (diagnostics == 0) != expected) {
        goto cleanup;
    }
    xmlSchemaFreeValidCtxt(context);
    context = xmlSchemaNewValidCtxt(schema);
    diagnostics = 0;
    reader = xmlReaderForMemory(document, (int)strlen(document), NULL, "UTF-8", XML_PARSE_NONET);
    if (!context || !reader) {
        goto cleanup;
    }
    xmlSchemaSetValidErrors(context, qname_schema_error, qname_schema_error, &diagnostics);
    xmlTextReaderSetErrorHandler(reader, qname_reader_error, &diagnostics);
    if (xmlTextReaderSchemaValidateCtxt(reader, context, 0) != 0) {
        goto cleanup;
    }
    while ((status = xmlTextReaderRead(reader)) == 1) {
    }
    if (status < 0 || xmlTextReaderIsValid(reader) != expected || (diagnostics == 0) != expected) {
        goto cleanup;
    }
    result = 0;
cleanup:
    if (reader) {
        xmlFreeTextReader(reader);
    }
    if (context) {
        xmlSchemaFreeValidCtxt(context);
    }
    if (tree) {
        xmlFreeDoc(tree);
    }
    if (invalid) {
        xmlFreeDoc(invalid);
    }
    return result;
}

static int check_qname_values(void) {
    static const char* facets[] = {
        "", "<xs:enumeration value='Product'/>",
        "<xs:enumeration xmlns='' value='Product'/>",
        "<xs:enumeration xmlns:p='urn:catalog' value='p:Product'/>",
        "<xs:enumeration value='Product'/>", "<xs:enumeration xmlns='' value='Product'/>"
    };
    static const char* documents[] = {
        "<value category='Product'>Product</value>",
        "<value xmlns='' category='Product'>Product</value>",
        "<value xmlns:q='urn:catalog' category='q:Product'>q:Product</value>",
        "<value xmlns:p='urn:other' category='p:Product'>p:Product</value>",
        "<value category='xml:lang'>xml:lang</value>",
        "<value xmlns:xml='http://www.w3.org/XML/1998/namespace' category='xml:lang'>xml:lang</value>",
        "<value category='unbound:Product'>unbound:Product</value>",
        "<value category='p:Product:Bad'>p:Product:Bad</value>"
    };
    static const int expected[6][8] = {
        {1, 1, 1, 1, 1, 1, 0, 0},
        {1, 1, 0, 0, 0, 0, 0, 0},
        {1, 1, 0, 0, 0, 0, 0, 0},
        {0, 0, 1, 0, 0, 0, 0, 0},
        {1, 1, 0, 0, 0, 0, 0, 0},
        {1, 1, 0, 0, 0, 0, 0, 0}
    };
    int result = 0;
    unsigned int i, j;
    for (i = 0; i < sizeof(facets) / sizeof(facets[0]); ++i) {
        char source[1024];
        xmlSchemaParserCtxtPtr parser;
        xmlSchemaPtr schema;
        int size = snprintf(source, sizeof(source),
            "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
            "<xs:notation name='Product' public='urn:catalog'/>"
            "<xs:simpleType name='Name'><xs:restriction base='xs:%s'>%s</xs:restriction></xs:simpleType>"
            "<xs:element name='value'><xs:complexType><xs:simpleContent><xs:extension base='Name'>"
            "<xs:attribute name='category' type='Name' use='required'/>"
            "</xs:extension></xs:simpleContent></xs:complexType></xs:element></xs:schema>",
            i < 4 ? "QName" : "NOTATION", facets[i]);
        if (size < 0 || (size_t)size >= sizeof(source)) {
            return 1;
        }
        parser = xmlSchemaNewMemParserCtxt(source, size);
        if (!parser) {
            return 1;
        }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (!schema) {
            return 1;
        }
        for (j = 0; j < sizeof(documents) / sizeof(documents[0]); ++j) {
            result |= check_qname_document(schema, documents[j], expected[i][j]);
        }
        xmlSchemaFree(schema);
    }
    return result;
}

/* Ordered union matching must keep trial QName errors local to the candidate. */
static int check_qname_unions(void) {
    static const char* types[] = {
        "xs:QName", "QNameString", "StringQName", "QNameInt", "StringChoice", "QNameChoice",
        "Nested", "ListOrString", "IntItems", "StringItems"
    };
    static const char* documents[] = {
        "<value category='p:Name'>p:Name</value>",
        "<value xmlns:p='urn:catalog' category='p:Name'>p:Name</value>",
        "<value xmlns:p='urn:other' category='p:Name'>p:Name</value>",
        "<value category='xml:lang'>xml:lang</value>",
        "<value category='Name'>Name</value>",
        "<value category=''></value>",
        "<value category='p:Name:Bad'>p:Name:Bad</value>",
        "<value category='17'>17</value>",
        "<value category='p:Name 17'>p:Name 17</value>",
        "<value xmlns:p='urn:catalog' category='p:Name 17'>p:Name 17</value>"
    };
    static const int expected[10][10] = {
        {0, 1, 1, 1, 1, 0, 0, 0, 0, 0},
        {1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
        {1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
        {0, 1, 1, 1, 1, 0, 0, 1, 0, 0},
        {1, 0, 0, 0, 0, 0, 0, 0, 0, 0},
        {0, 1, 0, 0, 0, 0, 0, 0, 0, 0},
        {1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
        {1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
        {0, 1, 1, 1, 1, 1, 0, 1, 0, 1},
        {1, 1, 1, 1, 1, 1, 1, 1, 1, 1}
    };
    unsigned int i, j;
    int result = 0;
    for (i = 0; i < sizeof(types) / sizeof(types[0]); ++i) {
        char source[3072];
        xmlSchemaParserCtxtPtr parser;
        xmlSchemaPtr schema;
        int diagnostics = 0;
        int size = snprintf(source, sizeof(source),
            "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
            "<xs:simpleType name='QNameString'><xs:union memberTypes='xs:QName xs:string'/></xs:simpleType>"
            "<xs:simpleType name='StringQName'><xs:union memberTypes='xs:string xs:QName'/></xs:simpleType>"
            "<xs:simpleType name='QNameInt'><xs:union memberTypes='xs:QName xs:int'/></xs:simpleType>"
            "<xs:simpleType name='StringChoice'><xs:restriction base='QNameString'>"
            "<xs:enumeration value='p:Name'/></xs:restriction></xs:simpleType>"
            "<xs:simpleType name='QNameChoice'><xs:restriction base='QNameString'>"
            "<xs:enumeration xmlns:c='urn:catalog' value='c:Name'/></xs:restriction></xs:simpleType>"
            "<xs:simpleType name='Nested'><xs:union memberTypes='QNameInt xs:string'/></xs:simpleType>"
            "<xs:simpleType name='QNameList'><xs:list itemType='xs:QName'/></xs:simpleType>"
            "<xs:simpleType name='ListOrString'><xs:union memberTypes='QNameList xs:string'/></xs:simpleType>"
            "<xs:simpleType name='IntItems'><xs:list itemType='QNameInt'/></xs:simpleType>"
            "<xs:simpleType name='StringItems'><xs:list itemType='QNameString'/></xs:simpleType>"
            "<xs:element name='value'><xs:complexType><xs:simpleContent><xs:extension base='%s'>"
            "<xs:attribute name='category' type='%s' use='required'/>"
            "</xs:extension></xs:simpleContent></xs:complexType></xs:element></xs:schema>", types[i], types[i]);
        if (size < 0 || (size_t)size >= sizeof(source)) {
            return 1;
        }
        parser = xmlSchemaNewMemParserCtxt(source, size);
        if (!parser) {
            return 1;
        }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, &diagnostics);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (!schema || diagnostics) {
            if (schema) {
                xmlSchemaFree(schema);
            }
            return 1;
        }
        for (j = 0; j < sizeof(documents) / sizeof(documents[0]); ++j) {
            int failed = check_qname_document(schema, documents[j], expected[i][j]);
            if (failed) {
                fprintf(stderr, "QName union validation failed: type=%s document=%u expected=%d\n",
                    types[i], j, expected[i][j]);
            }
            result |= failed;
        }
        xmlSchemaFree(schema);
    }
    return result;
}
