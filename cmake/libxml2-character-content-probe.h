/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 cvc-elt 3.2.1/5.1 and cvc-complex-type 2.1/2.3.
 * A CDATA event contributes characters, independently of its lexical boundary.
 * Included after libxml2-qname-probe.h for DOM/reader diagnostics and reuse.
 */
static int check_character_content(void) {
    static const struct {
        const char* declaration;
        const char* attributes;
        const char* content;
        int valid;
    } cases[] = {
        {"type='xs:int' nillable='true'/>", "xsi:nil='true'", "<![CDATA[]]>", 1},
        {"type='xs:int' nillable='true'/>", "xsi:nil='1'", "<![CDATA[]]><!--x--><![CDATA[]]>", 1},
        {"type='xs:int' nillable='true'/>", "xsi:nil='true'", "<![CDATA[ ]]>", 0},
        {"type='xs:int' nillable='true'/>", "xsi:nil='true'", "<![CDATA[17]]>", 0},
        {"type='xs:int' nillable='true'/>", "xsi:nil='true'", "<child/>", 0},
        {"type='xs:int' nillable='true'/>", "xsi:nil='false'", "<![CDATA[]]>", 0},
        {"type='xs:int' nillable='true'/>", "xsi:nil='false'", "1<![CDATA[7]]>", 1},
        {"type='xs:int' default='17'/>", "", "<![CDATA[]]>", 1},
        {"type='xs:int' fixed='17'/>", "", "<![CDATA[]]><!--x--><![CDATA[]]>", 1},
        {"type='xs:int' fixed='17'/>", "", "1<![CDATA[7]]>", 1},
        {"type='xs:int' fixed='17'/>", "", "<![CDATA[18]]>", 0},
        {"type='xs:anyType' fixed='17'/>", "", "<![CDATA[]]>", 1},
        {"type='xs:anySimpleType' fixed='17'/>", "", "<![CDATA[]]>", 1},
        {"type='xs:anyType' nillable='true'/>", "xsi:nil='1'", "<![CDATA[]]>", 1},
        {"type='xs:anySimpleType' nillable='true'/>", "xsi:nil='1'", "<![CDATA[]]>", 1},
        {"nillable='true'><xs:complexType><xs:attribute name='tag' use='required'/>"
            "</xs:complexType></xs:element>", "xsi:nil='true' tag='shipment'", "<![CDATA[]]>", 1},
        {"nillable='true'><xs:complexType><xs:attribute name='tag' use='required'/>"
            "</xs:complexType></xs:element>", "xsi:nil='true'", "<![CDATA[]]>", 0},
        {"><xs:complexType/></xs:element>", "", "<![CDATA[]]>", 1},
        {"><xs:complexType/></xs:element>", "", "<![CDATA[ ]]>", 0},
        {"><xs:complexType/></xs:element>", "", " ", 0},
        {"><xs:complexType><xs:sequence><xs:element name='child' minOccurs='0'/>"
            "</xs:sequence></xs:complexType></xs:element>", "", "<![CDATA[]]>", 1},
        {"><xs:complexType><xs:sequence><xs:element name='child' minOccurs='0'/>"
            "</xs:sequence></xs:complexType></xs:element>", "", "<![CDATA[ \t\n]]>", 1},
        {"><xs:complexType><xs:sequence><xs:element name='child' minOccurs='0'/>"
            "</xs:sequence></xs:complexType></xs:element>", "", "<![CDATA[ ]]><child/><![CDATA[\t]]>", 1},
        {"><xs:complexType><xs:sequence><xs:element name='child' minOccurs='0'/>"
            "</xs:sequence></xs:complexType></xs:element>", "", "<![CDATA[text]]>", 0}
    };
    unsigned int index;
    int result = 0;
    for (index = 0; index < sizeof(cases) / sizeof(cases[0]); ++index) {
        char source[1024], document[512];
        xmlSchemaParserCtxtPtr parser;
        xmlSchemaPtr schema;
        int diagnostics = 0;
        int length = snprintf(source, sizeof(source),
            "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
            "<xs:element name='root' %s</xs:schema>", cases[index].declaration);
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
        length = snprintf(document, sizeof(document),
            "<root xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' %s>%s</root>",
            cases[index].attributes, cases[index].content);
        if (length < 0 || (size_t)length >= sizeof(document)) {
            xmlSchemaFree(schema);
            return 1;
        }
        result |= check_qname_document(schema, document, cases[index].valid);
        xmlSchemaFree(schema);
    }
    return result;
}
