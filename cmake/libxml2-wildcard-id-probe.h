/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 cvc-complex-type.5.1/5.2, including derived IDs and absent uses.
 * Included after libxml2-qname-probe.h for DOM/reader validation and reuse.
 */
static int check_wildcard_ids(void) {
    static const char* processing[] = {"strict", "lax", "skip"};
    unsigned int mode, declared, derived, qualified, present, mask, reverse;
    int result = 0;
    for (mode = 0; mode < 3; ++mode) {
        for (declared = 0; declared < 2; ++declared) {
            for (derived = 0; derived < 2; ++derived) {
                for (qualified = 0; qualified < 2; ++qualified) {
                    char source[1536], use[128];
                    const char* prefix = qualified ? "t:" : "";
                    const char* type = derived ? (qualified ? "t:Identifier" : "Identifier") : "xs:ID";
                    xmlSchemaParserCtxtPtr parser;
                    xmlSchemaPtr schema;
                    int diagnostics = 0;
                    int length = snprintf(use, sizeof(use), declared ? "<xs:attribute name='id' type='%s'/>" : "%s",
                        declared ? type : "");
                    if (length < 0 || (size_t)length >= sizeof(use)) {
                        return 1;
                    }
                    length = snprintf(source, sizeof(source),
                        "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema' xmlns:t='urn:wild-id'%s>"
                        "<xs:simpleType name='Identifier'><xs:restriction base='xs:ID'/></xs:simpleType>"
                        "<xs:attribute name='first' type='%s'/><xs:attribute name='second' type='%s'/>"
                        "<xs:element name='root'><xs:complexType>%s<xs:anyAttribute processContents='%s'/>"
                        "</xs:complexType></xs:element></xs:schema>",
                        qualified ? " targetNamespace='urn:wild-id'" : "", type, type, use, processing[mode]);
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
                    if (schema == NULL || diagnostics) {
                        xmlSchemaFree(schema);
                        return 1;
                    }
                    for (present = 0; present < (declared ? 2u : 1u); ++present) {
                        for (mask = 0; mask < 4; ++mask) {
                            char first[64], second[64];
                            int valid = mode == 2 || (!declared && mask != 3) || !mask;
                            snprintf(first, sizeof(first), (mask & 1) ? "%sfirst='one' " : "%s",
                                (mask & 1) ? prefix : "");
                            snprintf(second, sizeof(second), (mask & 2) ? "%ssecond='two' " : "%s",
                                (mask & 2) ? prefix : "");
                            for (reverse = 0; reverse < (mask == 3 ? 2u : 1u); ++reverse) {
                                char document[256];
                                length = snprintf(document, sizeof(document), "<%sroot xmlns:t='urn:wild-id' %s%s%s/>",
                                    prefix, present ? "id='three' " : "", reverse ? second : first,
                                    reverse ? first : second);
                                if (length < 0 || (size_t)length >= sizeof(document)) {
                                    xmlSchemaFree(schema);
                                    return 1;
                                }
                                result |= check_qname_document(schema, document, valid);
                            }
                        }
                    }
                    xmlSchemaFree(schema);
                }
            }
        }
    }
    return result;
}

/* Schema rules using the same base-type ancestry helper: cvc-complex-type,
 * ct-props-correct.5, ag-props-correct.3, a-props-correct.3, e-props-correct.5.
 * List item and union member types do not replace their anySimpleType base.
 */
static int check_id_type_schemas(void) {
    static const char* definitions = "<xs:simpleType name=\"Identifier\"><xs:restriction base=\"xs:ID\"/></xs:simpleType> <xs:simpleType name=\"DeepId\"><xs:restriction base=\"Identifier\"/></xs:simpleType> <xs:simpleType name=\"Text\"><xs:restriction base=\"xs:string\"/></xs:simpleType> <xs:simpleType name=\"IdList\"><xs:list itemType=\"xs:ID\"/></xs:simpleType> <xs:simpleType name=\"InlineList\"><xs:list><xs:simpleType><xs:restriction base=\"xs:ID\"/> </xs:simpleType></xs:list></xs:simpleType> <xs:simpleType name=\"IdUnion\"><xs:union memberTypes=\"xs:ID xs:string\"/></xs:simpleType> <xs:simpleType name=\"InlineUnion\"><xs:union><xs:simpleType><xs:restriction base=\"xs:ID\"/> </xs:simpleType><xs:simpleType><xs:restriction base=\"xs:string\"/></xs:simpleType></xs:union></xs:simpleType> <xs:simpleType name=\"ListRestriction\"><xs:restriction base=\"IdList\"/></xs:simpleType> <xs:simpleType name=\"UnionRestriction\"><xs:restriction base=\"IdUnion\"/></xs:simpleType>";
    static const char* types[] = {"xs:ID", "Identifier", "DeepId", "Text", "IdList", "InlineList", "IdUnion", "InlineUnion", "ListRestriction", "UnionRestriction"};
    static const char* shapes[] = {
        "<xs:complexType name=\"Record\"><xs:attribute name=\"one\" type=\"%s\"/><xs:attribute name=\"two\" type=\"%s\"/></xs:complexType>",
        "<xs:attributeGroup name=\"Group\"><xs:attribute name=\"one\" type=\"%s\"/><xs:attribute name=\"two\" type=\"%s\"/></xs:attributeGroup>",
        "<xs:attribute name=\"a\" type=\"%s\" default=\"one\"/>",
        "<xs:attribute name=\"a\" type=\"%s\"/><xs:complexType name=\"Record\"><xs:attribute ref=\"a\" default=\"one\"/></xs:complexType>",
        "<xs:element name=\"value\" type=\"%s\" default=\"one\"/>",
        "<xs:element name=\"value\" default=\"one\"><xs:complexType><xs:simpleContent><xs:extension base=\"%s\"/></xs:simpleContent></xs:complexType></xs:element>",
        "<xs:attribute name=\"a\" type=\"%s\" fixed=\"one\"/>",
        "<xs:attribute name=\"a\" type=\"%s\"/><xs:complexType name=\"Record\"><xs:attribute ref=\"a\" fixed=\"one\"/></xs:complexType>",
        "<xs:element name=\"value\" type=\"%s\" fixed=\"one\"/>",
        "<xs:element name=\"value\" fixed=\"one\"><xs:complexType><xs:simpleContent><xs:extension base=\"%s\"/></xs:simpleContent></xs:complexType></xs:element>"
    };
    unsigned int type, shape;
    for (type = 0; type < sizeof(types) / sizeof(types[0]); ++type) {
        for (shape = 0; shape < sizeof(shapes) / sizeof(shapes[0]); ++shape) {
            char content[512], source[4096];
            int diagnostics = 0;
            int length = snprintf(content, sizeof(content), shapes[shape], types[type], types[type]);
            xmlSchemaParserCtxtPtr parser;
            xmlSchemaPtr schema;
            if (length < 0 || (size_t)length >= sizeof(content)) {
                return 1;
            }
            length = snprintf(source, sizeof(source),
                "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>%s%s</xs:schema>", definitions, content);
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
            if ((schema != NULL) != (type >= 3) || (diagnostics == 0) != (type >= 3)) {
                xmlSchemaFree(schema);
                return 1;
            }
            xmlSchemaFree(schema);
        }
    }
    return 0;
}
