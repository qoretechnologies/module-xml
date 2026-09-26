/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 Name-derived datatypes use the XML 1.0 Second Edition name characters,
 * in instance values and in schema documents. */
static int check_name_edition_values(void) {
    static const char *types[] = {"Name", "NCName", "QName", "NMTOKEN"};
    /* Second Edition letters, combining characters and extenders; Fifth Edition only characters. */
    static const struct {
        const char *value;
        int valid;
        int nmtoken_valid;
    } cases[] = {
        {"Alpha", 1, 1},
        {"\xCE\x91\xCE\xBB\xCF\x86\xCE\xB1", 1, 1},     /* Greek letters */
        {"\xE4\xB8\xAD\xE6\x96\x87", 1, 1},             /* CJK ideographs */
        {"a\xCC\x81", 1, 1},                            /* U+0301 after a letter */
        {"a\xC2\xB7" "b", 1, 1},                        /* U+00B7 extender */
        {"\xCC\x81" "a", 0, 1},                         /* U+0301 cannot start a name */
        {"\xCD\xB0" "a", 0, 0},                         /* U+0370 */
        {"a\xCD\xB0", 0, 0},
        {"\xE2\x81\xB0" "a", 0, 0},                     /* U+2070 */
        {"\xF0\x90\x80\x80" "a", 0, 0},                 /* U+10000 */
        {"a\xF0\x90\x80\x80", 0, 0}
    };
    const char *source = "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
        "<xs:element name='Name' type='xs:Name'/><xs:element name='NCName' type='xs:NCName'/>"
        "<xs:element name='QName' type='xs:QName'/><xs:element name='NMTOKEN' type='xs:NMTOKEN'/>"
        "</xs:schema>";
    xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int) strlen(source));
    xmlSchemaPtr schema;
    unsigned int i, t;
    int result = 0;
    if (parser == NULL) {
        return 1;
    }
    xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
    schema = xmlSchemaParse(parser);
    xmlSchemaFreeParserCtxt(parser);
    if (schema == NULL) {
        return 1;
    }
    for (t = 0; t < sizeof(types) / sizeof(types[0]); ++t) {
        xmlSchemaTypePtr type = xmlSchemaGetPredefinedType(BAD_CAST types[t],
            BAD_CAST "http://www.w3.org/2001/XMLSchema");
        int nmtoken = !strcmp(types[t], "NMTOKEN");
        if (type == NULL) {
            result = 1;
            break;
        }
        for (i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
            int valid = nmtoken ? cases[i].nmtoken_valid : cases[i].valid;
            xmlSchemaValPtr value = NULL;
            char document[128];
            int status = xmlSchemaValidatePredefinedType(type, BAD_CAST cases[i].value, &value);
            int length = snprintf(document, sizeof(document), "<%s>%s</%s>", types[t], cases[i].value, types[t]);
            result |= status < 0 || (status == 0) != valid;
            xmlSchemaFreeValue(value);
            if (length < 0 || (size_t) length >= sizeof(document)) {
                result = 1;
                break;
            }
            result |= check_qname_document(schema, document, valid);
        }
    }
    xmlSchemaFree(schema);
    /* Schema documents: component names are NCNames and ids are IDs. */
    for (i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        char document[256];
        int attribute;
        for (attribute = 0; attribute < 2; ++attribute) {
            int length = snprintf(document, sizeof(document),
                "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
                "<xs:element name='%s' id='%s' type='xs:string'/></xs:schema>",
                attribute ? "value" : cases[i].value, attribute ? cases[i].value : "value");
            xmlSchemaParserCtxtPtr component;
            xmlSchemaPtr parsed;
            if (length < 0 || (size_t) length >= sizeof(document)) {
                return 1;
            }
            component = xmlSchemaNewMemParserCtxt(document, length);
            if (component == NULL) {
                return 1;
            }
            xmlSchemaSetParserErrors(component, qname_schema_error, qname_schema_error, NULL);
            parsed = xmlSchemaParse(component);
            xmlSchemaFreeParserCtxt(component);
            result |= (parsed != NULL) != cases[i].valid;
            xmlSchemaFree(parsed);
        }
    }
    return result;
}
