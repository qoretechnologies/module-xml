/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 anyURI uses RFC 2396, including nonempty absolute URI content. */
static int check_anyuri_values(void) {
    static const struct {
        const char *value;
        int valid;
    } cases[] = {
        {"", 1}, {"#fragment", 1}, {"?query", 1}, {"../part", 1},
        {"a:", 0}, {"a:#fragment", 0}, {"A+1.2-3:", 0}, {"urn:#", 0},
        {"  http:  ", 0}, {"a:?", 1}, {"a:/", 1}, {"a://", 1},
        {"a:x", 1}, {"urn:catalog", 1}, {"a:%23", 1}, {"a: #fragment", 1}
    };
    const char *source = "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
        "<xs:element name='value' type='xs:anyURI'/></xs:schema>";
    xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int) strlen(source));
    xmlSchemaPtr schema;
    xmlSchemaTypePtr type = xmlSchemaGetPredefinedType(BAD_CAST "anyURI",
        BAD_CAST "http://www.w3.org/2001/XMLSchema");
    unsigned int i;
    int result = 0;
    if (parser == NULL || type == NULL) {
        xmlSchemaFreeParserCtxt(parser);
        return 1;
    }
    xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
    schema = xmlSchemaParse(parser);
    xmlSchemaFreeParserCtxt(parser);
    if (schema == NULL) {
        return 1;
    }
    for (i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        xmlSchemaValPtr value = NULL;
        char document[256];
        int status = xmlSchemaValidatePredefinedType(type, BAD_CAST cases[i].value, &value);
        int length = snprintf(document, sizeof(document), "<value>%s</value>", cases[i].value);
        result |= status < 0 || (status == 0) != cases[i].valid;
        result |= (value != NULL) != cases[i].valid;
        xmlSchemaFreeValue(value);
        if (length < 0 || (size_t) length >= sizeof(document)) {
            result = 1;
            break;
        }
        result |= check_qname_document(schema, document, cases[i].valid);
    }
    xmlSchemaFree(schema);
    return result;
}
