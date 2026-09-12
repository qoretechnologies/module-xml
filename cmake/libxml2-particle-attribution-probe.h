/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 component attribution with feasible counted contexts.
 * Include after libxml2-qname-probe.h for shared diagnostics and DOM/reader checks.
 */
static int check_particle_attribution(void) {
    static const struct {
        const char* declarations;
        const char* content;
        const char* document;
        int valid;
        const char* invalidDocument;
    } cases[] = {
        {"", "<xs:sequence><xs:element name='a' type='xs:string' minOccurs='2' maxOccurs='2' fixed='first'/>"
             "<xs:element name='a' type='xs:string' fixed='last'/></xs:sequence>",
             "<r><a>first</a><a>first</a><a>last</a></r>", 1, NULL},
        {"", "<xs:sequence><xs:element name='a' minOccurs='2' maxOccurs='3'/>"
             "<xs:element name='a'/></xs:sequence>", "<r/>", 0, NULL},
        {"", "<xs:sequence><xs:sequence minOccurs='2' maxOccurs='2'><xs:element name='b' minOccurs='0'/>"
             "<xs:element name='a' minOccurs='2' maxOccurs='3'/></xs:sequence><xs:element name='b'/></xs:sequence>",
             "<r><a/><a/><a/><a/><b/></r>", 1, NULL},
        {"", "<xs:sequence><xs:sequence minOccurs='3' maxOccurs='3'><xs:element name='b' minOccurs='0'/>"
             "<xs:element name='a' minOccurs='2' maxOccurs='3'/></xs:sequence><xs:element name='b'/></xs:sequence>",
             "<r/>", 0, NULL},
        {"", "<xs:sequence><xs:choice/><xs:choice><xs:element name='a'/><xs:element name='a'/>"
             "</xs:choice></xs:sequence>", "<r/>", 0, NULL},
        {"<xs:group name='Unused'><xs:choice><xs:element name='a'/><xs:element name='a'/></xs:choice></xs:group>",
             "<xs:sequence/>", "<r/>", 0, NULL},
        {"", "<xs:sequence><xs:sequence minOccurs='0' maxOccurs='0'><xs:choice>"
             "<xs:element name='a'/><xs:element name='a'/></xs:choice></xs:sequence><xs:element name='b'/>"
             "</xs:sequence>", "<r><b/></r>", 1, NULL},
        {"<xs:element name='h' type='xs:string' abstract='true'/>"
             "<xs:element name='m' type='xs:string' substitutionGroup='h'/>",
             "<xs:choice><xs:element ref='h'/><xs:element name='h' type='xs:string'/></xs:choice>",
             "<r><h>local</h></r>", 1, NULL},
        {"", "<xs:sequence minOccurs='0' maxOccurs='2'><xs:sequence maxOccurs='2'>"
             "<xs:element name='a' minOccurs='0'/></xs:sequence></xs:sequence>",
             "<r><a/><a/><a/><a/></r>", 1, "<r><a/><a/><a/><a/><a/></r>"},
        {"", "<xs:sequence minOccurs='2' maxOccurs='2'><xs:choice><xs:sequence maxOccurs='2'>"
             "<xs:element name='b' minOccurs='0'/></xs:sequence><xs:element name='a' minOccurs='0'/>"
             "</xs:choice></xs:sequence>", "<r><a/><b/><b/></r>", 1, "<r><a/><a/><b/></r>"},
        {"", "<xs:sequence><xs:sequence minOccurs='1073741823' maxOccurs='1073741823'>"
             "<xs:sequence maxOccurs='2'><xs:element name='a' minOccurs='0'/></xs:sequence>"
             "</xs:sequence><xs:element name='b'/></xs:sequence>", "<r><b/></r>", 1, "<r><c/></r>"}
    };
    unsigned int index;
    int result = 0;
    for (index = 0; index < sizeof(cases) / sizeof(cases[0]); ++index) {
        char source[1024];
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
            if (cases[index].valid) {
                result |= check_qname_document(schema, cases[index].document, 1);
                if (cases[index].invalidDocument != NULL) {
                    result |= check_qname_document(schema, cases[index].invalidDocument, 0);
                }
            }
            xmlSchemaFree(schema);
        }
    }
    return result;
}

/* Keep this independent from earlier checks: defective private backports can
 * crash while traversing builtin particles, and earlier diagnostics remain useful. */
static int check_builtin_particles(void) {
    static const char *source =
        "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
        "<xs:element name='known' type='xs:int'/>"
        "<xs:element name='r'><xs:complexType><xs:complexContent>"
        "<xs:extension base='xs:anyType'><xs:sequence/></xs:extension>"
        "</xs:complexContent></xs:complexType></xs:element></xs:schema>";
    xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
    xmlSchemaPtr schema;
    int diagnostics = 0, result;
    if (parser == NULL) {
        return 1;
    }
    xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, &diagnostics);
    schema = xmlSchemaParse(parser);
    xmlSchemaFreeParserCtxt(parser);
    if (schema == NULL || diagnostics != 0) {
        xmlSchemaFree(schema);
        return 1;
    }
    result = check_qname_document(schema, "<r>before<unknown/><known>17</known>after</r>", 1);
    result |= check_qname_document(schema, "<r><known>bad</known></r>", 0);
    xmlSchemaFree(schema);
    /* An empty group reference still supplies effective content. Its derived
     * type must explicitly remain mixed, unlike an absent/empty sequence. */
    for (int mixed = 0; mixed <= 1; ++mixed) {
        char grouped[768];
        int size = snprintf(grouped, sizeof(grouped),
            "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
            "<xs:element name='known' type='xs:int'/>"
            "<xs:group name='Empty'><xs:sequence/></xs:group>"
            "<xs:element name='r'><xs:complexType><xs:complexContent mixed='%s'>"
            "<xs:extension base='xs:anyType'><xs:group ref='Empty'/></xs:extension>"
            "</xs:complexContent></xs:complexType></xs:element></xs:schema>", mixed ? "true" : "false");
        if (size < 0 || (size_t)size >= sizeof(grouped)) {
            return 1;
        }
        parser = xmlSchemaNewMemParserCtxt(grouped, size);
        if (parser == NULL) {
            return 1;
        }
        diagnostics = 0;
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, &diagnostics);
        schema = xmlSchemaParse(parser);
        xmlSchemaFreeParserCtxt(parser);
        if ((schema != NULL) != mixed || (diagnostics == 0) != mixed) {
            result = 1;
        }
        if (schema != NULL) {
            if (mixed) {
                result |= check_qname_document(schema, "<r>before<unknown/><known>17</known>after</r>", 1);
                result |= check_qname_document(schema, "<r><known>bad</known></r>", 0);
            }
            xmlSchemaFree(schema);
        }
    }
    return result;
}
