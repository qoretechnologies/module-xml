/* Copyright (C) 2026 Qore Technologies, s.r.o. */
/* Diagnostic/hash text must retain both parts of an expanded name. */
static int check_instance_identity_names(void) {
    static const struct { const char *uri; const char *name; const char *text; } cases[] = {
        {"urn:a", "first", "{urn:a}first"},
        {"urn:a", "second", "{urn:a}second"},
        {"urn:b", "first", "{urn:b}first"},
        {NULL, "first", "first"},
    };
    unsigned int i;
    int notation;
    for (notation = 0; notation < 2; ++notation) {
        for (i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
            xmlChar *uri = cases[i].uri == NULL ? NULL : xmlStrdup(BAD_CAST cases[i].uri);
            xmlChar *name = xmlStrdup(BAD_CAST cases[i].name);
            xmlSchemaValPtr value;
            const xmlChar *text = NULL;
            int status;
            if (name == NULL || (cases[i].uri != NULL && uri == NULL)) {
                xmlFree(uri);
                xmlFree(name);
                return 1;
            }
            value = notation ? xmlSchemaNewNOTATIONValue(name, uri) : xmlSchemaNewQNameValue(uri, name);
            if (value == NULL) {
                xmlFree(uri);
                xmlFree(name);
                return 1;
            }
            status = xmlSchemaGetCanonValue(value, &text);
            status = status != 0 || text == NULL || !xmlStrEqual(text, BAD_CAST cases[i].text);
            xmlFree((void *)text);
            xmlSchemaFreeValue(value);
            if (status) {
                return 1;
            }
        }
    }
    return 0;
}

static int check_instance_identities(void) {
    static const char *sources[] = {
        "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><xs:element name=\"root\"><xs:complexType><xs:sequence><xs:element name=\"row\" type=\"xs:anyType\" nillable=\"true\" maxOccurs=\"unbounded\"/></xs:sequence></xs:complexType><xs:unique name=\"K\"><xs:selector xpath=\"row\"/><xs:field xpath=\"@xsi:type\"/></xs:unique></xs:element></xs:schema>",
        "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><xs:element name=\"root\"><xs:complexType><xs:sequence><xs:element name=\"row\" type=\"xs:anyType\" nillable=\"true\" maxOccurs=\"unbounded\"/></xs:sequence></xs:complexType><xs:key name=\"K\"><xs:selector xpath=\"row\"/><xs:field xpath=\"@xsi:type\"/></xs:key></xs:element></xs:schema>",
        "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><xs:element name=\"root\"><xs:complexType><xs:sequence><xs:element name=\"row\" type=\"xs:anyType\" nillable=\"true\" maxOccurs=\"unbounded\"/></xs:sequence></xs:complexType><xs:unique name=\"K\"><xs:selector xpath=\"row\"/><xs:field xpath=\"@xsi:nil\"/></xs:unique></xs:element></xs:schema>",
        "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><xs:element name=\"root\"><xs:complexType><xs:sequence><xs:element name=\"row\" type=\"xs:anyType\" nillable=\"true\" maxOccurs=\"unbounded\"/></xs:sequence></xs:complexType><xs:key name=\"K\"><xs:selector xpath=\"row\"/><xs:field xpath=\"@xsi:nil\"/></xs:key></xs:element></xs:schema>",
        "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><xs:element name=\"root\"><xs:complexType><xs:sequence><xs:element name=\"row\" type=\"xs:anyType\" nillable=\"true\" maxOccurs=\"unbounded\"/></xs:sequence></xs:complexType><xs:unique name=\"K\"><xs:selector xpath=\"row\"/><xs:field xpath=\"@xsi:schemaLocation\"/></xs:unique></xs:element></xs:schema>",
        "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><xs:element name=\"root\"><xs:complexType><xs:sequence><xs:element name=\"row\" type=\"xs:anyType\" nillable=\"true\" maxOccurs=\"unbounded\"/></xs:sequence></xs:complexType><xs:key name=\"K\"><xs:selector xpath=\"row\"/><xs:field xpath=\"@xsi:schemaLocation\"/></xs:key></xs:element></xs:schema>",
        "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><xs:element name=\"root\"><xs:complexType><xs:sequence><xs:element name=\"row\" type=\"xs:anyType\" nillable=\"true\" maxOccurs=\"unbounded\"/></xs:sequence></xs:complexType><xs:unique name=\"K\"><xs:selector xpath=\"row\"/><xs:field xpath=\"@xsi:noNamespaceSchemaLocation\"/></xs:unique></xs:element></xs:schema>",
        "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><xs:element name=\"root\"><xs:complexType><xs:sequence><xs:element name=\"row\" type=\"xs:anyType\" nillable=\"true\" maxOccurs=\"unbounded\"/></xs:sequence></xs:complexType><xs:key name=\"K\"><xs:selector xpath=\"row\"/><xs:field xpath=\"@xsi:noNamespaceSchemaLocation\"/></xs:key></xs:element></xs:schema>",
        "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\"><xs:simpleType name=\"Uris\"><xs:list itemType=\"xs:anyURI\"/></xs:simpleType><xs:element name=\"root\"><xs:complexType><xs:sequence><xs:element name=\"row\" type=\"xs:anySimpleType\" maxOccurs=\"unbounded\"/></xs:sequence></xs:complexType><xs:unique name=\"K\"><xs:selector xpath=\"row\"/><xs:field xpath=\".\"/></xs:unique></xs:element></xs:schema>",
        "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><xs:simpleType name=\"Uris\"><xs:list itemType=\"xs:anyURI\"/></xs:simpleType><xs:simpleType name=\"ListFirst\"><xs:union memberTypes=\"Uris xs:anyURI\"/></xs:simpleType><xs:simpleType name=\"AtomFirst\"><xs:union memberTypes=\"xs:anyURI Uris\"/></xs:simpleType><xs:element name=\"root\"><xs:complexType><xs:sequence><xs:element name=\"row\" type=\"xs:anySimpleType\" maxOccurs=\"unbounded\"/></xs:sequence></xs:complexType><xs:unique name=\"K\"><xs:selector xpath=\"row\"/><xs:field xpath=\".\"/></xs:unique></xs:element></xs:schema>",
        "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><xs:simpleType name=\"Uris\"><xs:list itemType=\"xs:anyURI\"/></xs:simpleType><xs:simpleType name=\"ListFirst\"><xs:union memberTypes=\"Uris xs:anyURI\"/></xs:simpleType><xs:simpleType name=\"AtomFirst\"><xs:union memberTypes=\"xs:anyURI Uris\"/></xs:simpleType><xs:element name=\"root\"><xs:complexType><xs:sequence><xs:element name=\"a\"><xs:complexType><xs:attribute name=\"id\" type=\"ListFirst\" default=\"urn:a\"/></xs:complexType></xs:element><xs:element name=\"b\"><xs:complexType><xs:attribute name=\"id\" type=\"Uris\"/></xs:complexType></xs:element></xs:sequence></xs:complexType><xs:key name=\"K\"><xs:selector xpath=\"a | b\"/><xs:field xpath=\"@id\"/></xs:key></xs:element></xs:schema>",
        "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><xs:simpleType name=\"Uris\"><xs:list itemType=\"xs:anyURI\"/></xs:simpleType><xs:simpleType name=\"ListFirst\"><xs:union memberTypes=\"Uris xs:anyURI\"/></xs:simpleType><xs:simpleType name=\"AtomFirst\"><xs:union memberTypes=\"xs:anyURI Uris\"/></xs:simpleType><xs:element name=\"root\"><xs:complexType><xs:sequence><xs:element name=\"a\"><xs:complexType><xs:attribute name=\"id\" type=\"ListFirst\" default=\"\"/></xs:complexType></xs:element><xs:element name=\"b\"><xs:complexType><xs:attribute name=\"id\" type=\"Uris\"/></xs:complexType></xs:element></xs:sequence></xs:complexType><xs:key name=\"K\"><xs:selector xpath=\"a | b\"/><xs:field xpath=\"@id\"/></xs:key></xs:element></xs:schema>",
        "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><xs:simpleType name=\"Uris\"><xs:list itemType=\"xs:anyURI\"/></xs:simpleType><xs:simpleType name=\"ListFirst\"><xs:union memberTypes=\"Uris xs:anyURI\"/></xs:simpleType><xs:simpleType name=\"AtomFirst\"><xs:union memberTypes=\"xs:anyURI Uris\"/></xs:simpleType><xs:element name=\"root\"><xs:complexType><xs:sequence><xs:element name=\"a\" type=\"xs:anySimpleType\"/><xs:element name=\"b\" type=\"xs:anySimpleType\"/></xs:sequence></xs:complexType><xs:key name=\"K\"><xs:selector xpath=\"a\"/><xs:field xpath=\".\"/></xs:key><xs:keyref name=\"R\" refer=\"K\"><xs:selector xpath=\"b\"/><xs:field xpath=\".\"/></xs:keyref></xs:element></xs:schema>",
        "<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><xs:element name=\"root\"><xs:complexType><xs:sequence><xs:element name=\"row\" type=\"xs:anyType\" nillable=\"true\"/></xs:sequence></xs:complexType><xs:unique name=\"K\"><xs:selector xpath=\"row\"/><xs:field xpath=\"@*\"/></xs:unique></xs:element></xs:schema>",
    };
    static const struct { int schema; const char *document; int valid; } cases[] = {
        {0, "<root xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:s=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><row xsi:type=\"xs:string\">1</row><row xsi:type=\"s:string\">1</row></root>", 0},
        {1, "<root xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:s=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><row xsi:type=\"xs:string\">1</row><row xsi:type=\"xs:integer\">1</row></root>", 1},
        {2, "<root xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:s=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><row xsi:nil=\"false\"></row><row xsi:nil=\"0\"></row></root>", 0},
        {3, "<root xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:s=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><row xsi:nil=\"false\"></row><row xsi:nil=\"1\"></row></root>", 1},
        {4, "<root xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:s=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><row xsi:schemaLocation=\"urn:a a.xsd\"></row><row xsi:schemaLocation=\"  urn:a   a.xsd  \"></row></root>", 0},
        {5, "<root xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:s=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><row xsi:schemaLocation=\"urn:a a.xsd\"></row><row xsi:schemaLocation=\"urn:a b.xsd\"></row></root>", 1},
        {6, "<root xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:s=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><row xsi:noNamespaceSchemaLocation=\"a.xsd\"></row><row xsi:noNamespaceSchemaLocation=\"  a.xsd  \"></row></root>", 0},
        {7, "<root xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:s=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><row xsi:noNamespaceSchemaLocation=\"a.xsd\"></row><row xsi:noNamespaceSchemaLocation=\"b.xsd\"></row></root>", 1},
        {8, "<root xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><row xsi:type=\"Uris\">urn:a</row><row xsi:type=\"xs:anyURI\">urn:a</row></root>", 1},
        {9, "<root xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><row xsi:type=\"ListFirst\">urn:a</row><row xsi:type=\"AtomFirst\">urn:a</row></root>", 1},
        {9, "<root xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><row xsi:type=\"ListFirst\">urn:a</row><row xsi:type=\"Uris\">urn:a</row></root>", 0},
        {9, "<root xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><row xsi:type=\"ListFirst\"></row><row xsi:type=\"AtomFirst\"></row></root>", 1},
        {10, "<root><a/><b id=\"urn:a\"/></root>", 0},
        {11, "<root><a/><b id=\"urn:other\"/></root>", 1},
        {12, "<root xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><a xsi:type=\"Uris\">urn:a</a><b xsi:type=\"xs:anyURI\">urn:a</b></root>", 0},
        {13, "<root xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"><row xsi:type=\"xs:string\" xsi:nil=\"false\"/></root>", 0},
    };
    unsigned int i;
    int result = check_instance_identity_names();
    for (i = 0; i < sizeof(cases) / sizeof(cases[0]); i++) {
        xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(sources[cases[i].schema],
            (int)strlen(sources[cases[i].schema]));
        xmlSchemaPtr schema;
        if (parser == NULL) {
            return 1;
        }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        if (schema == NULL) {
            result = 1;
        } else {
            result |= check_qname_document(schema, cases[i].document, cases[i].valid);
        }
        xmlSchemaFree(schema);
        xmlSchemaFreeParserCtxt(parser);
    }
    return result;
}
