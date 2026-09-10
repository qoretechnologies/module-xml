/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Probe exact occurrence attributes and executable nullable/finite models.
 * Include after libxml2-qname-probe.h for shared DOM/reader diagnostics.
 */
#define QORE_XML_RANGE_HIGH "100000000000000000000000000000000000000000000000000000000000000000000000000000000"
#define QORE_XML_RANGE_LOW "99999999999999999999999999999999999999999999999999999999999999999999999999999999"
static int check_particle_ranges(void) {
    static const struct {
        const char *declarations;
        const char *content;
        int schemaValid;
        const char *document;
        int documentValid;
    } cases[] = {
        {"", "<xs:sequence><xs:element name='a' minOccurs='" QORE_XML_RANGE_HIGH "' maxOccurs='"
             QORE_XML_RANGE_HIGH "'/><xs:element name='a'/></xs:sequence>", 1, "<r/>", 0},
        {"", "<xs:sequence><xs:element name='a' type='xs:string' maxOccurs='" QORE_XML_RANGE_HIGH
             "'/></xs:sequence>", 1, "<r><a>value</a><a>value</a></r>", 1},
        {"", "<xs:sequence minOccurs='2' maxOccurs='" QORE_XML_RANGE_HIGH
             "'><xs:element name='a'/><xs:element name='b'/></xs:sequence>", 1, "<r><a/><b/></r>", 0},
        {"", "<xs:sequence><xs:sequence minOccurs='" QORE_XML_RANGE_HIGH "' maxOccurs='" QORE_XML_RANGE_HIGH
             "'><xs:element name='a' minOccurs='0'/></xs:sequence><xs:element name='b'/></xs:sequence>",
             1, "<r><a/><a/><b/></r>", 1},
        {"", "<xs:sequence><xs:sequence minOccurs='" QORE_XML_RANGE_LOW "' maxOccurs='" QORE_XML_RANGE_LOW
             "'><xs:element name='b' minOccurs='0'/><xs:element name='a' minOccurs='" QORE_XML_RANGE_LOW
             "' maxOccurs='" QORE_XML_RANGE_HIGH "'/></xs:sequence><xs:element name='b'/></xs:sequence>",
             1, "<r/>", 0},
        {"", "<xs:sequence><xs:sequence minOccurs='" QORE_XML_RANGE_HIGH "' maxOccurs='" QORE_XML_RANGE_HIGH
             "'><xs:element name='b' minOccurs='0'/><xs:element name='a' minOccurs='" QORE_XML_RANGE_LOW
             "' maxOccurs='" QORE_XML_RANGE_HIGH "'/></xs:sequence><xs:element name='b'/></xs:sequence>",
             0, "<r/>", 0},
        {"", "<xs:sequence minOccurs='0' maxOccurs='0'><xs:element name='a' minOccurs='"
             QORE_XML_RANGE_HIGH "' maxOccurs='" QORE_XML_RANGE_LOW "'/></xs:sequence>", 0, "<r/>", 0},
        {"<xs:complexType name='Base'><xs:sequence minOccurs='" QORE_XML_RANGE_HIGH "' maxOccurs='"
             QORE_XML_RANGE_HIGH "'><xs:element name='a' minOccurs='0'/></xs:sequence></xs:complexType>",
             "<xs:complexContent><xs:extension base='Base'><xs:sequence><xs:element name='b'/>"
             "</xs:sequence></xs:extension></xs:complexContent>", 1, "<r><a/><b/></r>", 1}
    };
    int result = 0;
    for (size_t index = 0; index < sizeof(cases) / sizeof(cases[0]); ++index) {
        char source[2048];
        xmlSchemaParserCtxtPtr parser;
        xmlSchemaPtr schema;
        int diagnostics = 0;
        int size = snprintf(source, sizeof(source),
            "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>%s"
            "<xs:element name='r'><xs:complexType>%s</xs:complexType></xs:element></xs:schema>",
            cases[index].declarations, cases[index].content);
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
        if ((schema != NULL) != cases[index].schemaValid || (diagnostics == 0) != cases[index].schemaValid) {
            result = 1;
        }
        if (schema != NULL) {
            result |= check_qname_document(schema, cases[index].document, cases[index].documentValid);
            xmlSchemaFree(schema);
        }
    }
    return result;
}
#undef QORE_XML_RANGE_HIGH
#undef QORE_XML_RANGE_LOW
