/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Included after libxml2-qname-probe.h for DOM/reader validation and diagnostics.
 */
static int check_occurs_values(void) {
    static const struct {
        const char* minimum;
        const char* maximum;
        int valid;
        int empty;
        int two;
        int element;
    } cases[] = {
        {"+0", "+1", 1, 1, 0, 0},
        {"-000", "  unbounded  ", 1, 1, 1, 0},
        {" +001 ", " +002 ", 1, 0, 1, 0},
        {"-0", "-0", 1, 1, 0, 0},
        {"-1", "1", 0, 0, 0, 0},
        {"+", "1", 0, 0, 0, 0},
        {"0", "unbounded extra", 0, 0, 0, 0},
        {"0", "-0001", 0, 0, 0, 0},
        {"0", "+ 1", 0, 0, 0, 0},
        {"0", "1.0", 0, 0, 0, 0},
        {"0", "", 0, 0, 0, 0},
        {"unbounded", "unbounded", 0, 0, 0, 0},
        {"0", "0", 1, 1, 0, 1}
    };
    unsigned int index;
    int result = 0;
    for (index = 0; index < sizeof(cases) / sizeof(cases[0]); ++index) {
        char source[768];
        xmlSchemaParserCtxtPtr parser;
        xmlSchemaPtr schema;
        int diagnostics = 0;
        const char* format = cases[index].element ?
            "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
            "<xs:element name='r'><xs:complexType><xs:sequence>"
            "<xs:element name='v' type='xs:int' minOccurs='%s' maxOccurs='%s'/>"
            "</xs:sequence></xs:complexType></xs:element></xs:schema>" :
            "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
            "<xs:element name='r'><xs:complexType><xs:sequence minOccurs='%s' maxOccurs='%s'>"
            "<xs:element name='v' type='xs:int'/></xs:sequence></xs:complexType></xs:element></xs:schema>";
        int size = snprintf(source, sizeof(source), format,
            cases[index].minimum, cases[index].maximum);
        if (size < 0 || (size_t)size >= sizeof(source)) {
            return 1;
        }
        parser = xmlSchemaNewMemParserCtxt(source, size);
        if (!parser) {
            return 1;
        }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, &diagnostics);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if ((schema != NULL) != cases[index].valid || (diagnostics == 0) != cases[index].valid) {
            result = 1;
        }
        if (schema) {
            result |= check_qname_document(schema, "<r/>", cases[index].empty);
            result |= check_qname_document(schema, "<r><v>1</v><v>2</v></r>", cases[index].two);
            xmlSchemaFree(schema);
        }
    }
    return result;
}
