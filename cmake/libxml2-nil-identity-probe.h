/* Copyright (C) 2026 Qore Technologies, s.r.o. */
static int check_nil_identities(void) {
    static const struct {
        const char *kind, *document;
        int valid;
    } cases[] = {
        {"unique", "<row><n xsi:nil='true'/></row><row><n xsi:nil='true'/></row>", 1},
        {"unique", "<row><n>1</n></row><row><n>1</n></row>", 0},
        {"unique", "<row><n xsi:nil='true'/><n xsi:nil='true'/></row>", 0},
        {"unique", "<row><n xsi:nil='true'/><n>1</n></row>", 0},
        {"unique", "<row><n>1</n><n xsi:nil='true'/></row>", 0},
        {"keyref", "<row><n xsi:nil='true'/></row>", 1},
        {"keyref", "<row><n>1</n></row>", 0},
        {"keyref", "<row><n xsi:nil='true'/><n xsi:nil='true'/></row>", 0},
        {"keyref", "<row><n xsi:nil='true'/><n>1</n></row>", 0},
        {"keyref", "<row/>", 1}
    };
    unsigned int i;
    int result = 0;
    for (i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        char source[2048], document[512];
        xmlSchemaParserCtxtPtr parser;
        xmlSchemaPtr schema;
        int length = snprintf(source, sizeof(source),
            "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
            "<xs:element name='value'><xs:complexType><xs:sequence>"
            "<xs:element name='row' minOccurs='0' maxOccurs='unbounded'><xs:complexType>"
            "<xs:sequence><xs:element name='n' type='xs:int' nillable='true'"
            " minOccurs='0' maxOccurs='unbounded'/></xs:sequence></xs:complexType></xs:element>"
            "</xs:sequence></xs:complexType>"
            "<xs:key name='Base'><xs:selector xpath='absent'/><xs:field xpath='.'/></xs:key>"
            "<xs:%s name='K'%s><xs:selector xpath='row'/><xs:field xpath='n'/></xs:%s>"
            "</xs:element></xs:schema>", cases[i].kind,
            strcmp(cases[i].kind, "keyref") == 0 ? " refer='Base'" : "", cases[i].kind);
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
