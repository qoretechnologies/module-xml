/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 Part 1 3.11.6: every XPath union arm is a nonempty path. */
static int check_identity_paths(void) {
    static const struct {
        const char *path;
        int valid;
    } cases[] = {
        {"row", 1}, {"row|other", 1}, {"row|", 0}, {"row |", 0},
        {"row|other|", 0}, {"row| |other", 0}, {" . // child::row / . ", 1}
    };
    unsigned int i;
    int field;
    int result = 0;
    for (i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        for (field = 0; field < 2; ++field) {
            char source[2048];
            xmlSchemaParserCtxtPtr parser;
            xmlSchemaPtr schema;
            int length = snprintf(source, sizeof(source),
                "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
                "<xs:element name='value'><xs:complexType/><xs:unique name='U'>"
                "<xs:selector xpath='%s'/><xs:field xpath='%s'/>"
                "</xs:unique></xs:element></xs:schema>",
                field ? "row" : cases[i].path, field ? cases[i].path : "@id");
            if (length < 0 || (size_t) length >= sizeof(source)) {
                return 1;
            }
            parser = xmlSchemaNewMemParserCtxt(source, length);
            if (parser == NULL) {
                return 1;
            }
            xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
            schema = xmlSchemaParse(parser);
            result |= (schema != NULL) != cases[i].valid;
            if (schema != NULL && cases[i].valid) {
                result |= check_qname_document(schema, "<value/>", 1);
            }
            xmlSchemaFree(schema);
            xmlSchemaFreeParserCtxt(parser);
        }
    }
    return result;
}
