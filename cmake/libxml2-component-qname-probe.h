/* Copyright (C) 2026 Qore Technologies, s.r.o. */
static int check_component_qnames(void) {
    static const struct {
        const char *reference;
        int valid;
    } cases[] = {{" K ", 1}, {"&#9;K&#10;", 1}, {" p:K ", 1},
                 {"K K", 0}, {"p: K", 0}, {"missing:K", 0}};
    unsigned int i;
    int result = 0;
    for (i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        char source[2048];
        xmlSchemaParserCtxtPtr parser;
        xmlSchemaPtr schema;
        int length = snprintf(source, sizeof(source),
            "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema' xmlns:p='urn:keys'"
            " xmlns='urn:keys' targetNamespace='urn:keys'>"
            "<xs:element name='value' type='  xs:string  '><xs:key name='K'>"
            "<xs:selector xpath='never'/><xs:field xpath='@id'/></xs:key>"
            "<xs:keyref name='R' refer='%s'><xs:selector xpath='never'/>"
            "<xs:field xpath='@id'/></xs:keyref></xs:element></xs:schema>", cases[i].reference);
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
            result |= check_qname_document(schema, "<value xmlns='urn:keys'/>", 1);
        }
        xmlSchemaFree(schema);
        xmlSchemaFreeParserCtxt(parser);
    }
    return result;
}
