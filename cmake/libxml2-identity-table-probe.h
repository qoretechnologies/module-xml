/* Copyright (C) 2026 Qore Technologies, s.r.o. */
static int check_identity_tables(void) {
    static const char *sources[] = {
        "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"bucket\"><xs:complexType><xs:sequence><xs:element name=\"row\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:attribute name=\"id\" type=\"xs:integer\"/></xs:complexType></xs:element></xs:sequence></xs:complexType><xs:key name=\"K\"><xs:selector xpath=\"row\"/><xs:field xpath=\"@id\"/></xs:key></xs:element><xs:element name=\"root\"><xs:complexType><xs:sequence><xs:element ref=\"bucket\" minOccurs=\"0\" maxOccurs=\"unbounded\"/><xs:element name=\"ref\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:attribute name=\"id\" type=\"xs:integer\"/></xs:complexType></xs:element></xs:sequence></xs:complexType><xs:keyref name=\"R\" refer=\"K\"><xs:selector xpath=\"ref\"/><xs:field xpath=\"@id\"/></xs:keyref></xs:element></xs:schema>",
        "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"bucket\"><xs:complexType><xs:sequence><xs:element ref=\"bucket\" minOccurs=\"0\" maxOccurs=\"unbounded\"/><xs:element name=\"row\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:attribute name=\"id\" type=\"xs:integer\"/></xs:complexType></xs:element></xs:sequence></xs:complexType><xs:key name=\"K\"><xs:selector xpath=\"row\"/><xs:field xpath=\"@id\"/></xs:key></xs:element><xs:element name=\"root\"><xs:complexType><xs:sequence><xs:element ref=\"bucket\"/><xs:element name=\"ref\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:attribute name=\"id\" type=\"xs:integer\"/></xs:complexType></xs:element></xs:sequence></xs:complexType><xs:keyref name=\"R\" refer=\"K\"><xs:selector xpath=\"ref\"/><xs:field xpath=\"@id\"/></xs:keyref></xs:element></xs:schema>",
        "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:element name=\"bucket\"><xs:complexType><xs:sequence><xs:element ref=\"bucket\" minOccurs=\"0\" maxOccurs=\"unbounded\"/><xs:element name=\"row\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:attribute name=\"id\" type=\"xs:integer\"/></xs:complexType></xs:element></xs:sequence></xs:complexType><xs:key name=\"K\"><xs:selector xpath=\".//row\"/><xs:field xpath=\"@id\"/></xs:key></xs:element><xs:element name=\"root\"><xs:complexType><xs:sequence><xs:element ref=\"bucket\"/><xs:element name=\"ref\" minOccurs=\"0\" maxOccurs=\"unbounded\"><xs:complexType><xs:attribute name=\"id\" type=\"xs:integer\"/></xs:complexType></xs:element></xs:sequence></xs:complexType><xs:keyref name=\"R\" refer=\"K\"><xs:selector xpath=\"ref\"/><xs:field xpath=\"@id\"/></xs:keyref></xs:element></xs:schema>",
    };
    static const struct { int schema; const char *document; int valid; } cases[] = {
        {0, "<root><bucket><row id=\"1\"/></bucket><bucket><row id=\"1\"/></bucket><bucket><row id=\"2\"/></bucket><ref id=\"1\"/></root>", 0},
        {0, "<root><bucket><row id=\"1\"/></bucket><bucket><row id=\"1\"/></bucket><bucket><row id=\"2\"/></bucket><ref id=\"2\"/></root>", 1},
        {1, "<root><bucket><bucket><row id=\"1\"/></bucket><bucket><row id=\"1\"/></bucket><row id=\"1\"/></bucket><ref id=\"1\"/></root>", 1},
        {1, "<root><bucket><bucket><row id=\"1\"/></bucket><bucket><row id=\"1\"/></bucket><row id=\"2\"/></bucket><ref id=\"1\"/></root>", 0},
        {1, "<root><bucket><bucket><bucket><row id=\"1\"/></bucket><bucket><row id=\"1\"/></bucket></bucket><bucket><row id=\"1\"/></bucket></bucket><ref id=\"1\"/></root>", 1},
        {1, "<root><bucket><bucket><row id=\"1\"/></bucket><bucket><bucket><row id=\"1\"/></bucket><bucket><row id=\"1\"/></bucket></bucket></bucket><ref id=\"1\"/></root>", 1},
        {2, "<root><bucket><bucket><row id=\"1\"/></bucket></bucket><ref id=\"1\"/></root>", 1},
    };
    unsigned int i;
    int result = 0;
    for (i = 0; i < sizeof(cases) / sizeof(cases[0]); i++) {
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(sources[cases[i].schema],
            (int)strlen(sources[cases[i].schema]));
        xmlSchemaPtr schema;
        if (parser == NULL) {
            return 1;
        }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        if (schema == NULL) {
            result = 1;
        } else {
            result |= check_qname_document(schema, cases[i].document, cases[i].valid);
        }
        xmlSchemaFree(schema);
        xmlSchemaFreeParserCtxt(parser);
    }
    return result;
}
