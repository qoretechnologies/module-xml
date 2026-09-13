/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 Part 1 3.13.2/3: annotation attributes. */
static int check_annotations(void) {
    static const struct {
        const char *declaration;
        int valid;
    } cases[] = {
        {"<xs:annotation><xs:documentation xmlns:a='urn:a' a:lang='metadata'/></xs:annotation>", 1},
        {"<xs:annotation><xs:documentation source='http://[bad'/></xs:annotation>", 0},
        {"<xs:annotation><xs:documentation source='../manual' xml:lang=' en-US '/></xs:annotation>", 1},
        {"<xs:annotation><xs:documentation xs:lang='en'/></xs:annotation>", 0},
        {"<xs:annotation><xs:documentation xml:lang='bad_lang'/></xs:annotation>", 0},
        {"<xs:annotation><xs:appinfo source='http://[bad'/></xs:annotation>", 0}
    };
    unsigned int i;
    int result = 0;
    for (i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        char source[2048];
        xmlSchemaParserCtxtPtr parser;
        xmlSchemaPtr schema;
        int length = snprintf(source, sizeof(source),
            "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>%s"
            "<xs:element name='value' type='xs:string'/></xs:schema>",
            cases[i].declaration);
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
            result |= check_qname_document(schema, "<value>item</value>", 1);
        }
        xmlSchemaFree(schema);
        xmlSchemaFreeParserCtxt(parser);
    }
    return result;
}
