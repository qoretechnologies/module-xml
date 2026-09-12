/* Copyright (C) 2026 Qore Technologies, s.r.o. */

/* XSD 1.0 cvc-complex-type 2.3 permits XML S in element-only declarations.
 * CDATA boundaries do not change character information items. */
static int check_schema_whitespace_source(const char* source, int expected) {
    int mode;
    int result = 0;
    for (mode = 0; mode < 2; ++mode) {
        xmlDocPtr doc = NULL;
        xmlSchemaParserCtxtPtr parser = NULL;
        xmlSchemaPtr schema = NULL;
        int diagnostics = 0;
        if (mode) {
            doc = xmlReadMemory(source, (int)strlen(source), NULL, "UTF-8", XML_PARSE_NONET);
            if (doc) {
                parser = xmlSchemaNewDocParserCtxt(doc);
            }
        } else {
            parser = xmlSchemaNewMemParserCtxt(source, (int)strlen(source));
        }
        if (parser) {
            xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, &diagnostics);
            schema = xmlSchemaParse(parser);
        }
        if (!parser || (schema != NULL) != expected || (diagnostics == 0) != expected) {
            result = 1;
        }
        xmlSchemaFree(schema);
        xmlSchemaFreeParserCtxt(parser);
        xmlFreeDoc(doc);
    }
    return result;
}

/* The compiler may clean declaration nodes in a caller-supplied DOM. It must
 * retain annotation character data, markup, comments and processing instructions. */
static int check_schema_annotation_content(const char* space) {
    char source[2048];
    xmlDocPtr doc = NULL;
    xmlNodePtr annotation;
    xmlSchemaParserCtxtPtr parser = NULL;
    xmlSchemaPtr schema = NULL;
    xmlBufferPtr before = xmlBufferCreate();
    xmlBufferPtr after = xmlBufferCreate();
    int result = 1;
    int diagnostics = 0;
    int size = snprintf(source, sizeof(source),
        "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema' %s>"
        "<xs:annotation><xs:appinfo> \n<![CDATA[ \t]]>"
        "<sample xmlns='urn:example'><xs:element>illustrative text</xs:element> \t </sample>"
        "<!-- application note --><?application retain?> </xs:appinfo>"
        "<xs:documentation> \n<![CDATA[ \t]]><text xmlns='urn:example'>first</text> "
        "<text xmlns='urn:example'>second</text>\n<!-- documentation note --><?docs retain?>"
        "</xs:documentation></xs:annotation><xs:element name='value' type='xs:string'/>"
        "</xs:schema>", space);
    if (size < 0 || (size_t)size >= sizeof(source) || !before || !after) {
        goto cleanup;
    }
    doc = xmlReadMemory(source, size, NULL, "UTF-8", XML_PARSE_NONET);
    if (!doc || !xmlDocGetRootElement(doc)) {
        goto cleanup;
    }
    annotation = xmlDocGetRootElement(doc)->children;
    if (!annotation || xmlNodeDump(before, doc, annotation, 0, 0) < 0) {
        goto cleanup;
    }
    parser = xmlSchemaNewDocParserCtxt(doc);
    if (!parser) {
        goto cleanup;
    }
    xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, &diagnostics);
    schema = xmlSchemaParse(parser);
    if (!schema || diagnostics || xmlNodeDump(after, doc, annotation, 0, 0) < 0) {
        goto cleanup;
    }
    if (!xmlStrEqual(xmlBufferContent(before), xmlBufferContent(after))) {
        goto cleanup;
    }
    result = check_qname_document(schema, "<value>unchanged</value>", 1);
cleanup:
    xmlSchemaFree(schema);
    xmlSchemaFreeParserCtxt(parser);
    xmlFreeDoc(doc);
    xmlBufferFree(before);
    xmlBufferFree(after);
    return result;
}

static int check_schema_whitespace(void) {
    static const char* tokens[] = {
        " \t\r\n ", "<![CDATA[ \t\n]]>", "&#32;&#9;&#13;&#10;", " <!-- comment --> ",
        "unexpected", "&#160;", "<![CDATA[unexpected]]>", " \n x \t "
    };
    static const char* containers[] = {
        "<xs:complexType name='Value'>%s</xs:complexType>",
        "<xs:complexType name='Value'><xs:sequence>%s</xs:sequence></xs:complexType>",
        "<xs:element name='value' type='xs:string'>%s</xs:element>",
        "<xs:simpleType name='Value'><xs:restriction base='xs:string'>%s</xs:restriction></xs:simpleType>",
        "<xs:simpleType name='Value'><xs:restriction base='xs:string'>"
        "<xs:length value='3'>%s</xs:length></xs:restriction></xs:simpleType>",
        "%s"
    };
    static const char* spaces[] = {"", "xml:space='preserve'"};
    unsigned int token, container, space;
    int result = 0;
    for (space = 0; space < sizeof(spaces) / sizeof(spaces[0]); ++space) {
        for (token = 0; token < sizeof(tokens) / sizeof(tokens[0]); ++token) {
            for (container = 0; container < sizeof(containers) / sizeof(containers[0]); ++container) {
                char body[512];
                char source[1024];
                int size = snprintf(body, sizeof(body), containers[container], tokens[token]);
                if (size < 0 || (size_t)size >= sizeof(body)) {
                    return 1;
                }
                size = snprintf(source, sizeof(source),
                    "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema' %s>%s</xs:schema>",
                    spaces[space], body);
                if (size < 0 || (size_t)size >= sizeof(source)) {
                    return 1;
                }
                result |= check_schema_whitespace_source(source, token < 4);
            }
        }
        result |= check_schema_annotation_content(spaces[space]);
    }
    return result;
}
