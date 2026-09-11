/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Included after libxml2-qname-probe.h for diagnostic and DOM/reader helpers.
 */
static int check_type_final_defaults(void) {
    static const char* methods[] = {"restriction", "list", "union"};
    unsigned int method, control;
    int result = 0;
    for (method = 0; method < 3; ++method) {
        for (control = 0; control < 4; ++control) {
            char source[768];
            xmlSchemaParserCtxtPtr parser;
            xmlSchemaPtr schema;
            int diagnostics = 0;
            int valid = control != method;
            int size = snprintf(source, sizeof(source),
                "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema' finalDefault='%s'>"
                "<xs:simpleType name='T' final=''><xs:%s><xs:simpleType>"
                "<xs:restriction base='xs:string'/></xs:simpleType></xs:%s></xs:simpleType>"
                "<xs:element name='v' type='T'/></xs:schema>",
                control < 3 ? methods[control] : "", methods[method], methods[method]);
            if (size < 0 || (size_t)size >= sizeof(source)) {
                return 1;
            }
            parser = xmlSchemaNewMemParserCtxt(source, size);
            if (parser == NULL) {
                return 1;
            }
            xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, &diagnostics);
            schema = xmlSchemaParse(parser);
            xmlSchemaFreeParserCtxt(parser);
            if ((schema != NULL) != valid || (diagnostics == 0) != valid) {
                result = 1;
            }
            if (schema != NULL) {
                result |= check_qname_document(schema, "<v>invoice</v>", 1);
                xmlSchemaFree(schema);
            }
        }
    }
    return result;
}
