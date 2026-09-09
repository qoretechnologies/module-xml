/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Included after libxml2-qname-probe.h, whose document checks also exercise
 * DOM/reader validation and recovery after a rejected document.
 */

static int check_entity_document(xmlSchemaPtr schema, const char* document, int expected) {
    xmlSchemaValidCtxtPtr context = xmlSchemaNewValidCtxt(schema);
    xmlParserInputBufferPtr input;
    int diagnostics = 0;
    int status;
    int result = check_qname_document(schema, document, expected);
    if (!context) {
        return 1;
    }
    xmlSchemaSetValidErrors(context, qname_schema_error, qname_schema_error, &diagnostics);
    input = xmlParserInputBufferCreateMem(document, (int)strlen(document), XML_CHAR_ENCODING_NONE);
    if (!input) {
        xmlSchemaFreeValidCtxt(context);
        return 1;
    }
    /* The stream validator owns input and has no application SAX callbacks. */
    status = xmlSchemaValidateStream(context, input, XML_CHAR_ENCODING_NONE, NULL, NULL);
    if (status < 0 || (status == 0) != expected || (diagnostics == 0) != expected) {
        result = 1;
    }
    xmlSchemaFreeValidCtxt(context);
    return result;
}

static int check_entity_schema_facets(void) {
    static const char* types[] = {"xs:ENTITIES", "xs:IDREFS", "xs:NMTOKENS"};
    static const char* facets[] = {"length", "minLength", "maxLength"};
    unsigned int i, j, bound;
    for (i = 0; i < sizeof(types) / sizeof(types[0]); ++i) {
        for (j = 0; j < sizeof(facets) / sizeof(facets[0]); ++j) {
            for (bound = 0; bound <= 1; ++bound) {
                char source[1024];
                xmlSchemaParserCtxtPtr parser;
                xmlSchemaPtr schema;
                int diagnostics = 0;
                int valid;
                int size = snprintf(source, sizeof(source),
                    "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
                    "<xs:simpleType name='Base'><xs:restriction base='%s'/></xs:simpleType>"
                    "<xs:simpleType name='Derived'><xs:restriction base='Base'>"
                    "<xs:%s value='%u'/></xs:restriction></xs:simpleType>"
                    "<xs:element name='value' type='Derived'/></xs:schema>", types[i], facets[j], bound);
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
                valid = schema != NULL;
                if (schema) {
                    xmlSchemaFree(schema);
                }
                if (valid != (bound != 0) || (diagnostics == 0) != (bound != 0)) {
                    fprintf(stderr, "ENTITY list facet schema failed: type=%s facet=%s bound=%u\n",
                        types[i], facets[j], bound);
                    return 1;
                }
            }
        }
    }
    return 0;
}

static int check_entity_values(void) {
    static const char* types[] = {
        "xs:ENTITY", "Choice", "xs:ENTITIES", "Pair", "EntityText", "TextEntity",
        "EntityInt", "Items", "DerivedEntities"
    };
    static const char* declarations[] = {
        "", "<!ENTITY photo SYSTEM 'photo.gif' NDATA gif>", "<!ENTITY photo 'text'>",
        "<!ENTITY photo 'text'><!ENTITY photo SYSTEM 'photo.gif' NDATA gif>",
        "<!ENTITY photo SYSTEM 'photo.gif' NDATA gif><!ENTITY photo 'text'>",
        "<!ENTITY % photo 'parameter'>",
        "<!ENTITY % photo 'parameter'><!ENTITY photo SYSTEM 'photo.gif' NDATA gif>",
        "<!ENTITY photo SYSTEM 'photo.xml'>", "", "", "", "", "", ""
    };
    static const char* values[] = {
        "photo", "photo", "photo", "photo", "photo", "photo", "photo", "photo",
        "", "17", "p:photo", "photo other", " photo ", "lt"
    };
    static const int expected[9][14] = {
        {0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0},
        {0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0},
        {0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0},
        {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0},
        {0, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0},
        {1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
        {0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0},
        {0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0},
        {0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0}
    };
    unsigned int i, j;
    int result = check_entity_schema_facets();
    for (i = 0; i < sizeof(types) / sizeof(types[0]); ++i) {
        char source[2048];
        xmlSchemaParserCtxtPtr parser;
        xmlSchemaPtr schema;
        int diagnostics = 0;
        int size = snprintf(source, sizeof(source),
            "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
            "<xs:simpleType name='Choice'><xs:restriction base='xs:ENTITY'>"
            "<xs:enumeration value='photo'/></xs:restriction></xs:simpleType>"
            "<xs:simpleType name='Pair'><xs:restriction base='xs:ENTITIES'>"
            "<xs:length value='2'/><xs:enumeration value='photo other'/></xs:restriction></xs:simpleType>"
            "<xs:simpleType name='EntityText'><xs:union memberTypes='xs:ENTITY xs:string'/></xs:simpleType>"
            "<xs:simpleType name='TextEntity'><xs:union memberTypes='xs:string xs:ENTITY'/></xs:simpleType>"
            "<xs:simpleType name='EntityInt'><xs:union memberTypes='xs:ENTITY xs:int'/></xs:simpleType>"
            "<xs:simpleType name='Items'><xs:list itemType='xs:ENTITY'/></xs:simpleType>"
            "<xs:simpleType name='DerivedEntities'><xs:restriction base='xs:ENTITIES'/></xs:simpleType>"
            "<xs:element name='value'><xs:complexType><xs:simpleContent><xs:extension base='%s'>"
            "<xs:attribute name='category' type='%s' use='required'/>"
            "</xs:extension></xs:simpleContent></xs:complexType></xs:element></xs:schema>", types[i], types[i]);
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
        if (!schema || diagnostics) {
            if (schema) {
                xmlSchemaFree(schema);
            }
            return 1;
        }
        for (j = 0; j < sizeof(values) / sizeof(values[0]); ++j) {
            char document[1024];
            const char* declared = j == 11 || j == 12
                ? "<!ENTITY photo SYSTEM 'photo.gif' NDATA gif><!ENTITY other SYSTEM 'other.gif' NDATA gif>"
                : declarations[j];
            size = snprintf(document, sizeof(document),
                "<!DOCTYPE value [<!NOTATION gif SYSTEM 'image/gif'>%s]>"
                "<value category='%s'>%s</value>", declared, values[j], values[j]);
            if (size < 0 || (size_t)size >= sizeof(document)) {
                xmlSchemaFree(schema);
                return 1;
            }
            if (check_entity_document(schema, document, expected[i][j])) {
                fprintf(stderr, "ENTITY validation failed: type=%s document=%u expected=%d\n",
                    types[i], j, expected[i][j]);
                result = 1;
            }
        }
        xmlSchemaFree(schema);
    }
    return result;
}
