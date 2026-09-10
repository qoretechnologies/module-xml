/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 cos-nonambig: declaration identity does not identify a particle use.
 * Include after libxml2-qname-probe.h for shared diagnostics and DOM/reader checks.
 */
static int check_particle_identity(void) {
    static const struct {
        const char* declarations;
        const char* content;
        const char* document;
        int valid;
    } cases[] = {
        {"", "<xs:choice><xs:element name='a'/><xs:element name='a'/></xs:choice>", "<r/>", 0},
        {"<xs:element name='a'/>",
         "<xs:choice><xs:element ref='a'/><xs:element ref='a'/></xs:choice>", "<r/>", 0},
        {"<xs:group name='G'><xs:sequence><xs:element name='a'/></xs:sequence></xs:group>",
         "<xs:choice><xs:group ref='G'/><xs:group ref='G'/></xs:choice>", "<r/>", 0},
        {"<xs:group name='G'><xs:sequence><xs:element name='a'/></xs:sequence></xs:group>",
         "<xs:sequence><xs:group ref='G'/><xs:group ref='G'/></xs:sequence>", "<r><a/><a/></r>", 1},
        {"", "<xs:all><xs:element name='a'/><xs:element name='a'/></xs:all>", "<r/>", 0},
        {"", "<xs:choice><xs:any namespace='##local'/><xs:any namespace='##local'/></xs:choice>", "<r/>", 0},
        {"", "<xs:choice><xs:any namespace='urn:a' processContents='skip'/>"
             "<xs:any namespace='urn:b' processContents='skip'/></xs:choice>", "<r><v xmlns='urn:b'/></r>", 1},
        {"", "<xs:sequence><xs:element name='a' type='xs:int' minOccurs='0' maxOccurs='unbounded'/>"
             "</xs:sequence>", "<r><a>7</a><a>11</a></r>", 1},
        {"", "<xs:sequence minOccurs='2' maxOccurs='unbounded'><xs:element name='a' type='xs:int'/>"
              "</xs:sequence>", "<r><a>7</a><a>11</a><a>13</a></r>", 1}
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
            }
            xmlSchemaFree(schema);
        }
    }
    return result;
}
