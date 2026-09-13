/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 Part 1 3.12.2/6 and Part 2 3.2.19. */
static int check_notations(void) {
    static const struct {
        const char *declaration;
        const char *types;
        const char *element_type;
        int valid;
    } cases[] = {
        {"<xs:notation name='  item  ' public='' />", "", "xs:string", 1},
        {"<xs:notation name='item' system='' />", "", "xs:string", 1},
        {"<xs:notation name='item' public='[a]' xmlns:f='urn:f' f:info='x'/>", "", "xs:string", 1},
        {"<xs:notation name='item'/>", "", "xs:string", 0},
        {"<xs:notation name='item' public='a' typo='x'/>", "", "xs:string", 0},
        {"<xs:notation name='item' public='a' xs:typo='x'/>", "", "xs:string", 0},
        {"<xs:notation name='item' public='a'/>", "", "xs:NOTATION", 0},
        {"", "<xs:simpleType name='N'><xs:restriction base='xs:NOTATION'/></xs:simpleType>", "N", 0},
        {"", "<xs:simpleType name='N'><xs:restriction base='xs:NOTATION'/></xs:simpleType>", "xs:string", 1},
        {"", "<xs:simpleType name='N'><xs:list itemType='xs:NOTATION'/></xs:simpleType>", "N", 0},
        {"", "<xs:simpleType name='N'><xs:union memberTypes='xs:NOTATION xs:string'/></xs:simpleType>", "N", 0},
        {"<xs:notation name='item' public='a'/>",
         "<xs:simpleType name='N'><xs:restriction base='xs:NOTATION'><xs:enumeration value='item'/>"
         "</xs:restriction></xs:simpleType>", "N", 1}
    };
    unsigned int i;
    int result = 0;
    for (i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
        char source[2048];
        xmlSchemaParserCtxtPtr parser;
        xmlSchemaPtr schema;
        int length = snprintf(source, sizeof(source),
            "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>%s%s"
            "<xs:element name='value' type='%s'/></xs:schema>",
            cases[i].declaration, cases[i].types, cases[i].element_type);
        if (length < 0 || (size_t) length >= sizeof(source)) {
            return 1;
        }
        parser = xmlSchemaNewMemParserCtxt(source, length);
        if (parser == NULL) {
            return 1;
        }
        xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
        schema = xmlSchemaParse(parser);
        result |= (schema != NULL) != cases[i].valid;
        if (schema != NULL && cases[i].valid) {
            result |= check_qname_document(schema, "<value>item</value>", 1);
        }
        xmlSchemaFree(schema);
        xmlSchemaFreeParserCtxt(parser);
    }
    return result;
}
