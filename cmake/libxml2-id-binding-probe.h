/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 cvc-id and ID/IDREF table; includes parent identity and root scope.
 * Included after libxml2-entity-probe.h for DOM/reader/SAX validation and reuse.
 */
#include <libxml/valid.h>

static int check_id_binding_scope(void) {
    static const char* source =
        "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
        "<xs:element name='value'><xs:complexType><xs:attribute name='id' type='xs:ID'/>"
        "<xs:attribute name='ref' type='xs:IDREF'/></xs:complexType></xs:element></xs:schema>";
    static const char* documents[] = {
        "<outside id='a'><value ref='a'/></outside>",
        "<outside id='a'><value id='a' ref='a'/></outside>",
        "<outside id='a'><value id='b' ref='a'/></outside>",
        "<outside id='a'><value id='b' ref='b'/></outside>"
    };
    static const int expected[] = {0, 1, 0, 1};
    xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
    xmlSchemaPtr schema;
    unsigned int i;
    int failed = 0;
    if (parser == NULL) { return 1; }
    schema = xmlSchemaParse(parser);
    xmlSchemaFreeParserCtxt(parser);
    if (schema == NULL) { return 1; }
    for (i = 0; i < sizeof(documents) / sizeof(documents[0]); ++i) {
        xmlDocPtr doc = xmlReadMemory(documents[i], (int)strlen(documents[i]), NULL, "UTF-8", XML_PARSE_NONET);
        xmlSchemaValidCtxtPtr context = xmlSchemaNewValidCtxt(schema);
        int diagnostics = 0;
        if (doc != NULL && context != NULL) {
            xmlNodePtr parent = xmlDocGetRootElement(doc);
            xmlAttrPtr outside_id = xmlHasProp(parent, BAD_CAST "id");
            int status;
            if (xmlAddIDSafe(outside_id, BAD_CAST "a") != 1) {
                failed = 1;
            }
            xmlSchemaSetValidErrors(context, qname_schema_error, qname_schema_error, &diagnostics);
            status = xmlSchemaValidateOneElement(context, parent->children);
            if (status < 0 || (status == 0) != expected[i] || (diagnostics == 0) != expected[i]
                    || xmlGetID(doc, BAD_CAST "a") != outside_id) {
                failed = 1;
            }
        } else {
            failed = 1;
        }
        xmlSchemaFreeValidCtxt(context);
        xmlFreeDoc(doc);
    }
    xmlSchemaFree(schema);
    {
        const char* nil_source =
            "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
            "<xs:element name='value'><xs:complexType><xs:sequence>"
            "<xs:element name='id' type='xs:ID' nillable='true'/>"
            "<xs:element name='ref' type='xs:IDREF' minOccurs='0'/>"
            "</xs:sequence></xs:complexType></xs:element></xs:schema>";
        parser = xmlSchemaNewMemParserCtxt(nil_source, (int)strlen(nil_source));
        if (parser == NULL) { return 1; }
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema,
            "<value xmlns:i='http://www.w3.org/2001/XMLSchema-instance'><id i:nil='true'/></value>", 1);
        failed |= check_entity_document(schema,
            "<value xmlns:i='http://www.w3.org/2001/XMLSchema-instance'><id i:nil='true'/><ref>a</ref></value>", 0);
        failed |= check_entity_document(schema, "<value><id>a</id><ref>a</ref></value>", 1);
        failed |= check_entity_document(schema,
            "<value xmlns:i='http://www.w3.org/2001/XMLSchema-instance'><id i:nil='true'>a</id></value>", 0);
        xmlSchemaFree(schema);
    }
    return failed;
}

/* Schema list validation historically marks each selected IDREF item, even
 * for an IDREFS declaration. Keep that DOM metadata independent of list size. */
static int check_id_binding_dom_markers(void) {
    static const char* source =
        "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
        "<xs:element name='value'><xs:complexType>"
        "<xs:attribute name='id' type='xs:ID'/><xs:attribute name='ref' type='xs:IDREF'/>"
        "<xs:attribute name='refs' type='xs:IDREFS'/></xs:complexType></xs:element></xs:schema>";
    static const char* documents[] = {
        "<value id='a' ref='a' refs='a'/>",
        "<value id='a' ref='a' refs='a a'/>"
    };
    xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
    xmlSchemaPtr schema;
    unsigned int i;
    int failed = 0;
    if (parser == NULL) { return 1; }
    schema = xmlSchemaParse(parser);
    xmlSchemaFreeParserCtxt(parser);
    if (schema == NULL) { return 1; }
    for (i = 0; i < sizeof(documents) / sizeof(documents[0]); ++i) {
        xmlDocPtr doc = xmlReadMemory(documents[i], (int)strlen(documents[i]), NULL, "UTF-8", XML_PARSE_NONET);
        xmlSchemaValidCtxtPtr context = xmlSchemaNewValidCtxt(schema);
        if (doc != NULL && context != NULL) {
            xmlNodePtr root = xmlDocGetRootElement(doc);
            xmlAttrPtr id = xmlHasProp(root, BAD_CAST "id");
            xmlAttrPtr ref = xmlHasProp(root, BAD_CAST "ref");
            xmlAttrPtr refs = xmlHasProp(root, BAD_CAST "refs");
            if (xmlSchemaValidateDoc(context, doc) != 0 || id == NULL || ref == NULL || refs == NULL
                    || id->atype != XML_ATTRIBUTE_ID || ref->atype != XML_ATTRIBUTE_IDREF
                    || refs->atype != XML_ATTRIBUTE_IDREF || xmlGetID(doc, BAD_CAST "a") != id) {
                failed = 1;
            }
        } else {
            failed = 1;
        }
        xmlSchemaFreeValidCtxt(context);
        xmlFreeDoc(doc);
    }
    xmlSchemaFree(schema);
    return failed;
}

static int check_id_bindings(void) {
    int failed = check_id_binding_scope() | check_id_binding_dom_markers();
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"ref\" type=\"xs:IDREF\" minOccurs=\"0\" maxOccurs=\"unbounded\"/><xs:element name=\"id\" type=\"xs:ID\" minOccurs=\"0\" maxOccurs=\"unbounded\"/></xs:sequence></xs:complexType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value></value>", 1);
        failed |= check_entity_document(schema, "<value><ref>a</ref><id>a</id></value>", 1);
        failed |= check_entity_document(schema, "<value><ref>a</ref></value>", 0);
        failed |= check_entity_document(schema, "<value><id>a</id><id>a</id></value>", 1);
        failed |= check_entity_document(schema, "<value><ref>a</ref><ref>a</ref><id>a</id></value>", 1);
        xmlSchemaFree(schema);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"item\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:attribute name=\"id\" type=\"xs:ID\"/><xs:attribute name=\"ref\" type=\"xs:IDREF\"/></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value></value>", 1);
        failed |= check_entity_document(schema, "<value><item ref=\"a\"/><item id=\"a\"/></value>", 1);
        failed |= check_entity_document(schema, "<value><item ref=\"a\"/></value>", 0);
        failed |= check_entity_document(schema, "<value><item id=\"a\"/><item id=\"a\"/></value>", 0);
        failed |= check_entity_document(schema, "<value><item ref=\"a\"/><item ref=\"a\"/><item id=\"a\"/></value>", 1);
        xmlSchemaFree(schema);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"ref\" type=\"xs:IDREFS\" minOccurs=\"0\" maxOccurs=\"unbounded\"/><xs:element name=\"id\" type=\"xs:ID\" minOccurs=\"0\" maxOccurs=\"unbounded\"/></xs:sequence></xs:complexType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value></value>", 1);
        failed |= check_entity_document(schema, "<value><ref>a</ref><id>a</id></value>", 1);
        failed |= check_entity_document(schema, "<value><ref>a</ref></value>", 0);
        failed |= check_entity_document(schema, "<value><id>a</id><id>a</id></value>", 1);
        failed |= check_entity_document(schema, "<value><ref>a</ref><ref>a</ref><id>a</id></value>", 1);
        failed |= check_entity_document(schema, "<value><ref>a b</ref><id>a</id><id>b</id></value>", 1);
        failed |= check_entity_document(schema, "<value><ref>a b</ref><id>a</id></value>", 0);
        failed |= check_entity_document(schema, "<value><ref>a a</ref><id>a</id></value>", 1);
        xmlSchemaFree(schema);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"item\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:attribute name=\"id\" type=\"xs:ID\"/><xs:attribute name=\"ref\" type=\"xs:IDREFS\"/></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value></value>", 1);
        failed |= check_entity_document(schema, "<value><item ref=\"a\"/><item id=\"a\"/></value>", 1);
        failed |= check_entity_document(schema, "<value><item ref=\"a\"/></value>", 0);
        failed |= check_entity_document(schema, "<value><item id=\"a\"/><item id=\"a\"/></value>", 0);
        failed |= check_entity_document(schema, "<value><item ref=\"a\"/><item ref=\"a\"/><item id=\"a\"/></value>", 1);
        failed |= check_entity_document(schema, "<value><item ref=\"a b\"/><item id=\"a\"/><item id=\"b\"/></value>", 1);
        failed |= check_entity_document(schema, "<value><item ref=\"a b\"/><item id=\"a\"/></value>", 0);
        failed |= check_entity_document(schema, "<value><item ref=\"a a\"/><item id=\"a\"/></value>", 1);
        xmlSchemaFree(schema);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"id\" type=\"xs:ID\" minOccurs=\"0\" maxOccurs=\"unbounded\"/><xs:element name=\"ref\" type=\"xs:IDREF\" minOccurs=\"0\"/></xs:sequence><xs:attribute name=\"id\" type=\"xs:ID\"/></xs:complexType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value><id>a</id><id>a</id><ref>a</ref></value>", 1);
        failed |= check_entity_document(schema, "<value id=\"a\"><id>a</id><ref>a</ref></value>", 1);
        failed |= check_entity_document(schema, "<value><id>a</id><ref>b</ref></value>", 0);
        xmlSchemaFree(schema);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"item\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:sequence><xs:element name=\"id\" type=\"xs:ID\" minOccurs=\"0\"/></xs:sequence><xs:attribute name=\"id\" type=\"xs:ID\"/><xs:attribute name=\"ref\" type=\"xs:IDREF\"/></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value><item><id>a</id></item><item><id>b</id></item></value>", 1);
        failed |= check_entity_document(schema, "<value><item><id>a</id></item><item><id>a</id></item></value>", 0);
        failed |= check_entity_document(schema, "<value><item id=\"a\"/><item id=\"a\"/></value>", 0);
        failed |= check_entity_document(schema, "<value><item ref=\"a\"/><item id=\"a\"/></value>", 1);
        failed |= check_entity_document(schema, "<value><item ref=\"a\"/></value>", 0);
        xmlSchemaFree(schema);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:simpleType><xs:restriction base=\"xs:ID\"/></xs:simpleType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value>a</value>", 0);
        xmlSchemaFree(schema);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:complexType><xs:simpleContent><xs:extension base=\"xs:ID\"><xs:attribute name=\"id\" type=\"xs:ID\"/><xs:attribute name=\"ref\" type=\"xs:IDREF\"/></xs:extension></xs:simpleContent></xs:complexType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value>a</value>", 0);
        failed |= check_entity_document(schema, "<value id=\"a\">a</value>", 1);
        failed |= check_entity_document(schema, "<value ref=\"a\">a</value>", 0);
        xmlSchemaFree(schema);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"item\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:attribute name=\"id\" type=\"xs:ID\"/><xs:attribute name=\"ref\" type=\"xs:IDREF\" default=\"a\"/></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value><item/></value>", 0);
        failed |= check_entity_document(schema, "<value><item id=\"a\"/></value>", 1);
        xmlSchemaFree(schema);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"item\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:attribute name=\"id\" type=\"xs:ID\"/><xs:attribute name=\"ref\" type=\"xs:IDREFS\" default=\"a\"/></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value><item/></value>", 0);
        failed |= check_entity_document(schema, "<value><item id=\"a\"/></value>", 1);
        xmlSchemaFree(schema);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:simpleType name=\"Choice\"><xs:union memberTypes=\"xs:IDREF xs:string\"/></xs:simpleType><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"item\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:attribute name=\"id\" type=\"xs:ID\"/><xs:attribute name=\"ref\" type=\"Choice\"/></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value><item ref=\"a\"/></value>", 0);
        failed |= check_entity_document(schema, "<value><item ref=\"a\"/><item id=\"a\"/></value>", 1);
        xmlSchemaFree(schema);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:simpleType name=\"Choice\"><xs:union memberTypes=\"xs:string xs:IDREF\"/></xs:simpleType><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"item\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:attribute name=\"id\" type=\"xs:ID\"/><xs:attribute name=\"ref\" type=\"Choice\"/></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value><item ref=\"a\"/></value>", 1);
        failed |= check_entity_document(schema, "<value><item ref=\"a\"/><item id=\"a\"/></value>", 1);
        xmlSchemaFree(schema);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:simpleType name=\"Identifier\"><xs:restriction base=\"xs:ID\"><xs:pattern value=\"a\"/></xs:restriction></xs:simpleType><xs:simpleType name=\"Choice\"><xs:union memberTypes=\"Identifier xs:string\"/></xs:simpleType><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"item\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:attribute name=\"id\" type=\"Choice\"/><xs:attribute name=\"ref\" type=\"xs:IDREF\"/></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value><item id=\"b\"/><item id=\"b\"/></value>", 1);
        failed |= check_entity_document(schema, "<value><item id=\"b\"/><item ref=\"b\"/></value>", 0);
        failed |= check_entity_document(schema, "<value><item id=\"a\"/><item ref=\"a\"/></value>", 1);
        failed |= check_entity_document(schema, "<value><item id=\"a\"/><item id=\"a\"/></value>", 0);
        xmlSchemaFree(schema);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:simpleType name=\"Choice\"><xs:union memberTypes=\"xs:IDREF xs:int\"/></xs:simpleType><xs:simpleType name=\"References\"><xs:list itemType=\"Choice\"/></xs:simpleType><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"ref\" type=\"References\"/><xs:element name=\"id\" type=\"xs:ID\" minOccurs=\"0\" maxOccurs=\"unbounded\"/></xs:sequence></xs:complexType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value><ref>a 17</ref></value>", 0);
        failed |= check_entity_document(schema, "<value><ref>a 17</ref><id>a</id></value>", 1);
        failed |= check_entity_document(schema, "<value><ref>17 23</ref></value>", 1);
        xmlSchemaFree(schema);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:attribute name=\"ref\" type=\"xs:IDREF\"/><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"id\" type=\"xs:ID\" minOccurs=\"0\"/></xs:sequence><xs:anyAttribute processContents=\"strict\"/></xs:complexType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value ref=\"a\"/>", 0);
        failed |= check_entity_document(schema, "<value ref=\"a\"><id>a</id></value>", 1);
        xmlSchemaFree(schema);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"id\" type=\"xs:ID\"/><xs:element name=\"ref\" type=\"xs:IDREF\"/><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:any minOccurs=\"0\" maxOccurs=\"unbounded\" processContents=\"strict\"/></xs:sequence></xs:complexType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value><ref>a</ref></value>", 0);
        failed |= check_entity_document(schema, "<value><ref>a</ref><id>a</id></value>", 1);
        xmlSchemaFree(schema);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:attribute name=\"ref\" type=\"xs:IDREF\"/><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"id\" type=\"xs:ID\" minOccurs=\"0\"/></xs:sequence><xs:anyAttribute processContents=\"lax\"/></xs:complexType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value ref=\"a\"/>", 0);
        failed |= check_entity_document(schema, "<value ref=\"a\"><id>a</id></value>", 1);
        xmlSchemaFree(schema);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"id\" type=\"xs:ID\"/><xs:element name=\"ref\" type=\"xs:IDREF\"/><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:any minOccurs=\"0\" maxOccurs=\"unbounded\" processContents=\"lax\"/></xs:sequence></xs:complexType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value><ref>a</ref></value>", 0);
        failed |= check_entity_document(schema, "<value><ref>a</ref><id>a</id></value>", 1);
        xmlSchemaFree(schema);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:attribute name=\"ref\" type=\"xs:IDREF\"/><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"id\" type=\"xs:ID\" minOccurs=\"0\"/></xs:sequence><xs:anyAttribute processContents=\"skip\"/></xs:complexType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value ref=\"a\"/>", 1);
        failed |= check_entity_document(schema, "<value ref=\"a\"><id>a</id></value>", 1);
        xmlSchemaFree(schema);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"id\" type=\"xs:ID\"/><xs:element name=\"ref\" type=\"xs:IDREF\"/><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:any minOccurs=\"0\" maxOccurs=\"unbounded\" processContents=\"skip\"/></xs:sequence></xs:complexType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value><ref>a</ref></value>", 1);
        failed |= check_entity_document(schema, "<value><ref>a</ref><id>a</id></value>", 1);
        xmlSchemaFree(schema);
    }
    {
        const char* source = "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"value\"><xs:complexType><xs:sequence><xs:element name=\"ref\" type=\"xs:token\"/><xs:element name=\"id\" type=\"xs:token\" minOccurs=\"0\"/></xs:sequence></xs:complexType></xs:element></xs:schema>";
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        xmlSchemaPtr schema;
        if (parser == NULL) { return 1; }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL) { return 1; }
        failed |= check_entity_document(schema, "<value xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><ref xsi:type=\"xs:IDREF\">a</ref></value>", 0);
        failed |= check_entity_document(schema, "<value xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><ref xsi:type=\"xs:IDREF\">a</ref><id xsi:type=\"xs:ID\">a</id></value>", 1);
        failed |= check_entity_document(schema, "<value><ref>a</ref></value>", 1);
        xmlSchemaFree(schema);
    }
    return failed;
}
