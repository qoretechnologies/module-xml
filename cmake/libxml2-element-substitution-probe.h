/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 Substitution Group OK (Transitive), including builtin restriction
 * and the union of all complex derivation methods and intermediate blocks.
 * Included after libxml2-qname-probe.h for DOM and reader validation helpers.
 */
static int check_element_substitution(void) {
    static const char* controls[] = {"", "restriction", "extension", "substitution", "#all"};
    unsigned int model, control, intermediate;
    int result = 0;
    for (model = 0; model < 5; ++model) {
        for (control = 0; control < 5; ++control) {
            for (intermediate = 0; intermediate < (model >= 3 ? 3u : 1u); ++intermediate) {
                char definitions[1024], source[2048];
                const char* head = model == 0 ? "xs:int" : model == 1 ? "xs:decimal" : model == 2 ? "U" : "B";
                const char* member = model < 3 ? "xs:int" : "D";
                const char* content = model < 3 ? "17" : "";
                char document[80];
                xmlSchemaParserCtxtPtr parser;
                xmlSchemaPtr schema;
                int diagnostics = 0;
                int size;
                int valid = control != 3 && control != 4 &&
                    (model == 0 || (control != 1 && (model < 3 || control != 2))) && intermediate == 0;
                definitions[0] = 0;
                if (model == 2) {
                    snprintf(definitions, sizeof(definitions),
                        "<xs:simpleType name='U'><xs:union memberTypes='xs:int xs:boolean'/></xs:simpleType>");
                } else if (model >= 3) {
                    const char* upper = model == 3 ? "extension" : "restriction";
                    const char* lower = model == 3 ? "restriction" : "extension";
                    size = snprintf(definitions, sizeof(definitions),
                        "<xs:complexType name='B'/><xs:complexType name='M' block='%s'>"
                        "<xs:complexContent><xs:%s base='B'/></xs:complexContent></xs:complexType>"
                        "<xs:complexType name='D' block='#all'><xs:complexContent><xs:%s base='M'/>"
                        "</xs:complexContent></xs:complexType>", controls[intermediate], upper, lower);
                    if (size < 0 || (size_t)size >= sizeof(definitions)) {
                        return 1;
                    }
                }
                size = snprintf(source, sizeof(source),
                    "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>%s"
                    "<xs:element name='head' type='%s' block='%s'/>"
                    "<xs:element name='member' type='%s' substitutionGroup='head'/>"
                    "<xs:element name='root'><xs:complexType><xs:sequence><xs:element ref='head'/>"
                    "</xs:sequence></xs:complexType></xs:element></xs:schema>",
                    definitions, head, controls[control], member);
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
                if (schema == NULL || diagnostics) {
                    xmlSchemaFree(schema);
                    return 1;
                }
                snprintf(document, sizeof(document), "<root><head>%s</head></root>", content);
                result |= check_qname_document(schema, document, 1);
                snprintf(document, sizeof(document), "<root><member>%s</member></root>", content);
                result |= check_qname_document(schema, document, valid);
                xmlSchemaFree(schema);
            }
        }
    }
    return result;
}
