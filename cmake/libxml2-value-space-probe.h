/* Copyright (C) 2026 Qore Technologies, s.r.o. */
static int check_time_values(void) {
    static const char *source =
        "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
        "<xs:element name='root' type='xs:time' fixed='12:00:00Z'/></xs:schema>";
    xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
    xmlSchemaPtr schema;
    int diagnostics = 0, result;
    if (parser == NULL) {
        return 1;
    }
    xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, &diagnostics);
    schema = xmlSchemaParse(parser);
    xmlSchemaFreeParserCtxt(parser);
    if (schema == NULL || diagnostics != 0) {
        xmlSchemaFree(schema);
        return 1;
    }
    result = check_qname_document(schema, "<root>14:00:00+02:00</root>", 1);
    result |= check_qname_document(schema, "<root>07:00:00-05:00</root>", 1);
    result |= check_qname_document(schema, "<root>14:00:01+02:00</root>", 0);
    result |= check_qname_document(schema, "<root>12:00:00</root>", 0);
    xmlSchemaFree(schema);
    return result;
}

static int check_unsigned_values(void) {
    static const xmlSchemaValType types[] = {
        XML_SCHEMAS_ULONG, XML_SCHEMAS_UINT, XML_SCHEMAS_USHORT, XML_SCHEMAS_UBYTE
    };
    size_t index;
    for (index = 0; index < sizeof(types) / sizeof(types[0]); ++index) {
        xmlSchemaTypePtr type = xmlSchemaGetBuiltInType(types[index]);
        if (type == NULL || xmlSchemaValidatePredefinedType(type, BAD_CAST "0017", NULL) != 0 ||
            xmlSchemaValidatePredefinedType(type, BAD_CAST "+17", NULL) <= 0 ||
            xmlSchemaValidatePredefinedType(type, BAD_CAST "-0", NULL) <= 0 ||
            xmlSchemaValidatePredefinedType(type, BAD_CAST "+0", NULL) <= 0) {
            return 1;
        }
    }
    return 0;
}

static int check_fixed_values(void) {
    static const struct {
        const char *type, *fixed, *equivalent, *different, *attributes;
    } cases[] = {
        {"xs:int", "+0017", "17", "18", ""},
        {"xs:decimal", "-0.00", "0.0", "0.1", ""},
        {"xs:boolean", "1", "true", "false", ""},
        {"List", "17 0", "+017 -0", "17", ""},
        {"List", "", " ", "17", ""},
        {"xs:anySimpleType", "part", "part", "other",
         " xmlns:xs='http://www.w3.org/2001/XMLSchema'"
         " xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xsi:type='xs:string'"}
    };
    size_t index;
    int result = 0;
    for (index = 0; index < sizeof(cases) / sizeof(cases[0]); ++index) {
        char source[512], document[256];
        xmlSchemaParserCtxtPtr parser;
        xmlSchemaPtr schema;
        int diagnostics = 0, length = snprintf(source, sizeof(source),
            "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
            "<xs:simpleType name='List'><xs:list itemType='xs:int'/></xs:simpleType>"
            "<xs:element name='root' type='%s' fixed='%s'/></xs:schema>", cases[index].type, cases[index].fixed);
        if (length < 0 || (size_t)length >= sizeof(source)) {
            return 1;
        }
        parser = xmlSchemaNewMemParserCtxt(source, length);
        if (parser == NULL) {
            return 1;
        }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, &diagnostics);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if (schema == NULL || diagnostics != 0) {
            xmlSchemaFree(schema);
            return 1;
        }
        length = snprintf(document, sizeof(document), "<root%s>%s</root>", cases[index].attributes, cases[index].equivalent);
        if (length < 0 || (size_t)length >= sizeof(document)) {
            xmlSchemaFree(schema);
            return 1;
        }
        result |= check_qname_document(schema, document, 1);
        length = snprintf(document, sizeof(document), "<root%s>%s</root>", cases[index].attributes, cases[index].different);
        if (length < 0 || (size_t)length >= sizeof(document)) {
            xmlSchemaFree(schema);
            return 1;
        }
        result |= check_qname_document(schema, document, 0);
        xmlSchemaFree(schema);
    }
    return result;
}
