/* Copyright (C) 2026 Qore Technologies, s.r.o. */
static int
check_element_consistency_schema(const char *definitions, const char *content,
                                 int valid, const char *children) {
    char source[8192], document[2048];
    int diagnostics = 0, result = 0;
    int length = snprintf(source, sizeof(source),
        "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema' xmlns:t='urn:edc' targetNamespace='urn:edc'>"
        "%s<xs:element name='root'><xs:complexType>%s</xs:complexType></xs:element></xs:schema>", definitions, content);
    xmlSchemaParserCtxtPtr parser;
    xmlSchemaPtr schema;
    if (length < 0 || (size_t)length >= sizeof(source)) {
        return 1;
    }
    parser = xmlSchemaNewMemParserCtxt(source, length);
    if (parser == NULL) {
        return 1;
    }
    xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, &diagnostics);
    schema = xmlSchemaParse(parser);
    if (valid) {
        if (schema == NULL || diagnostics) {
            result = 1;
        } else {
            length = snprintf(document, sizeof(document), "<t:root xmlns:t='urn:edc'>%s</t:root>", children);
            if (length < 0 || (size_t)length >= sizeof(document)) {
                result = 1;
            } else {
                result |= check_qname_document(schema, document, 1);
                result |= check_qname_document(schema, "<wrong/>", 0);
            }
        }
    } else {
        const xmlError *error = xmlGetLastError();
        /* These required sequences isolate EDC from nondeterministic models. */
        if (schema != NULL || diagnostics == 0 || error == NULL
                || error->domain != XML_FROM_SCHEMASP || error->code == XML_ERR_NO_MEMORY) {
            result = 1;
        }
    }
    xmlSchemaFree(schema);
    xmlSchemaFreeParserCtxt(parser);
    xmlResetLastError();
    return result;
}

static int
check_element_consistency(void) {
    const char *types[] = {"xs:int", "xs:decimal", "t:Named"};
    const char *blocks[] = {"", "extension", "restriction", "substitution", "#all"};
    char definitions[2048], content[2048], groups[4096], children[256];
    int result = 0, size;
    for (int first = 0; first < 3; ++first) {
        for (int second = 0; second < 3; ++second) {
            size = snprintf(content, sizeof(content),
                "<xs:sequence><xs:element name='x' type='%s'/><xs:element name='x' type='%s'/></xs:sequence>",
                types[first], types[second]);
            if (size < 0 || (size_t)size >= sizeof(content)) {
                return 1;
            }
            result |= check_element_consistency_schema(
                "<xs:simpleType name='Named'><xs:restriction base='xs:int'/></xs:simpleType>", content,
                first == second, "<x>17</x><x>18</x>");
        }
    }
    for (int block = 0; block < 5; ++block) {
        for (int qualified = 0; qualified < 2; ++qualified) {
            for (int unused = 0; unused < 2; ++unused) {
                int valid = !qualified || block >= 2;
                size = snprintf(definitions, sizeof(definitions),
                    "<xs:element name='head' type='xs:decimal' block='%s'/>"
                    "<xs:element name='middle' type='xs:decimal' abstract='true' substitutionGroup='t:head'/>"
                    "<xs:element name='member' type='xs:int' substitutionGroup='t:middle'/>", blocks[block]);
                if (size < 0 || (size_t)size >= sizeof(definitions)) {
                    return 1;
                }
                size = snprintf(content, sizeof(content),
                    "<xs:sequence><xs:element ref='t:head'/><xs:element name='member' type='xs:string' form='%s'/></xs:sequence>",
                    qualified ? "qualified" : "unqualified");
                if (size < 0 || (size_t)size >= sizeof(content)) {
                    return 1;
                }
                size = snprintf(groups, sizeof(groups), "%s<xs:group name='Unused'>%s</xs:group>", definitions, content);
                if (size < 0 || (size_t)size >= sizeof(groups)) {
                    return 1;
                }
                size = snprintf(children, sizeof(children), "<t:head>17</t:head><%smember>text</%smember>",
                    qualified ? "t:" : "", qualified ? "t:" : "");
                if (size < 0 || (size_t)size >= sizeof(children)) {
                    return 1;
                }
                result |= check_element_consistency_schema(unused ? groups : definitions,
                    unused ? "<xs:sequence/>" : content, valid, unused ? "" : children);
            }
        }
    }
    result |= check_element_consistency_schema("",
        "<xs:sequence><xs:element name='x'><xs:simpleType><xs:restriction base='xs:int'/></xs:simpleType></xs:element>"
        "<xs:element name='x'><xs:simpleType><xs:restriction base='xs:int'/></xs:simpleType></xs:element></xs:sequence>", 0, "");
    result |= check_element_consistency_schema(
        "<xs:element name='x'><xs:simpleType><xs:restriction base='xs:int'/></xs:simpleType></xs:element>",
        "<xs:sequence><xs:element ref='t:x'/><xs:element ref='t:x'/></xs:sequence>", 1, "<t:x>17</t:x><t:x>18</t:x>");
    result |= check_element_consistency_schema("",
        "<xs:sequence><xs:element name='x' type='xs:int'/>"
        "<xs:element name='x' type='xs:string' minOccurs='0' maxOccurs='0'/></xs:sequence>", 1, "<x>17</x>");
    result |= check_element_consistency_schema("",
        "<xs:sequence><xs:element name='x' type='xs:int'/><xs:element name='child'><xs:complexType><xs:sequence>"
        "<xs:element name='x' type='xs:string'/></xs:sequence></xs:complexType></xs:element></xs:sequence>", 1,
        "<x>17</x><child><x>text</x></child>");
    result |= check_element_consistency_schema("",
        "<xs:sequence><xs:element name='child'><xs:complexType><xs:sequence><xs:element name='x' type='xs:int'/>"
        "<xs:element name='x' type='xs:string'/></xs:sequence></xs:complexType></xs:element></xs:sequence>", 0, "");
    return result;
}
