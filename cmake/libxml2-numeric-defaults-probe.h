/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 e-props-correct.2 and a-props-correct.2 require canonical validity.
 * Included after libxml2-qname-probe.h for schema diagnostics.
 */
static int check_numeric_defaults(void) {
    static const char *types[] = {"int", "boolean", "decimal", "hexBinary", "base64Binary"};
    static const char *values[] = {"+017", "1", "017.00", "ab00ff", "Y W J j"};
    static const char *patterns[] = {"\\+017", "1", "017\\.00", "ab00ff", "Y W J j"};
    static const char *canonical[] = {"17", "true", "17\\.0", "AB00FF", "YWJj"};
    unsigned int kind, item, valid, attribute;
    for (kind = 0; kind < 2; ++kind) {
        for (item = 0; item < sizeof(types) / sizeof(types[0]); ++item) {
            for (valid = 0; valid < 2; ++valid) {
                for (attribute = 0; attribute < 2; ++attribute) {
                    char source[1024];
                    int diagnostics = 0;
                    int length = snprintf(source, sizeof(source),
                        "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
                        "<xs:simpleType name='Value'><xs:restriction base='xs:%s'>"
                        "<xs:pattern value='%s%s%s'/></xs:restriction></xs:simpleType>"
                        "<xs:%s name='value' type='Value' %s='%s'/></xs:schema>",
                        types[item], patterns[item], valid ? "|" : "", valid ? canonical[item] : "",
                        attribute ? "attribute" : "element", kind ? "fixed" : "default", values[item]);
                    xmlSchemaParserCtxtPtr parser;
                    xmlSchemaPtr schema;
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
                    if ((schema != NULL) != valid || (diagnostics == 0) != valid) {
                        xmlSchemaFree(schema);
                        return 1;
                    }
                    xmlSchemaFree(schema);
                }
            }
        }
    }
    return 0;
}
