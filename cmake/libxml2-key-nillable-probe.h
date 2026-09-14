/* Copyright (C) 2026 Qore Technologies, s.r.o. */
static int check_key_nillable(void) {
    static const struct {
        const char *kind, *nillable, *content, *field, *document;
        int valid;
    } cases[] = {
        {"key", "true", "", ".", "<row>1</row>", 0},
        {"key", "true", "", ".", "<row xsi:nil='false'>1</row>", 0},
        {"key", "true", "", ".", "<row xsi:nil='true'/>", 0},
        {"key", "false", "", ".", "<row>1</row>", 1},
        {"unique", "true", "", ".", "<row>1</row>", 1},
        {"unique", "true", "", ".", "<row xsi:nil='false'>1</row>", 1},
        {"key", "true", "complex", ".", "<row>1</row>", 0},
        {"key", "false", "complex", ".", "<row>1</row>", 1},
        {"key", "true", "attribute", "@id", "<row xsi:nil='true' id='1'/>", 1},
        {"key", "true", "attribute", "@id", "<row xsi:nil='false' id='1'/>", 1}
    };
    unsigned int i;
    int result = 0;
    for (i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        char source[2048], document[256];
        xmlSchemaParserCtxtPtr parser;
        xmlSchemaPtr schema;
        const char *content = " type='xs:int'/>";
        int length;
        if (strcmp(cases[i].content, "complex") == 0) {
            content = "><xs:complexType><xs:simpleContent><xs:extension base='xs:int'/>"
                "</xs:simpleContent></xs:complexType></xs:element>";
        } else if (strcmp(cases[i].content, "attribute") == 0) {
            content = "><xs:complexType><xs:attribute name='id' type='xs:int'/>"
                "</xs:complexType></xs:element>";
        }
        length = snprintf(source, sizeof(source),
            "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
            "<xs:element name='value'><xs:complexType><xs:sequence>"
            "<xs:element name='row' nillable='%s'%s</xs:sequence></xs:complexType>"
            "<xs:%s name='K'><xs:selector xpath='row'/><xs:field xpath='%s'/>"
            "</xs:%s></xs:element></xs:schema>", cases[i].nillable, content,
            cases[i].kind, cases[i].field, cases[i].kind);
        if (length < 0 || (size_t) length >= sizeof(source)) {
            return 1;
        }
        parser = xmlSchemaNewMemParserCtxt(source, length);
        if (parser == NULL) {
            return 1;
        }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        length = snprintf(document, sizeof(document),
            "<value xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>%s</value>",
            cases[i].document);
        if (schema == NULL || length < 0 || (size_t) length >= sizeof(document)) {
            result = 1;
        } else {
            result |= check_qname_document(schema, document, cases[i].valid);
        }
        xmlSchemaFree(schema);
        xmlSchemaFreeParserCtxt(parser);
    }
    return result;
}
