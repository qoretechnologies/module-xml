/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 cvc-assess-elt 1.2 and cvc-wildcard: strict xsi:type assessment.
 * Included after libxml2-qname-probe.h for DOM/reader diagnostics and reuse.
 */
static int check_wildcard_types(void) {
    static const char* processing[] = {"strict", "lax", "skip"};
    static const struct {
        const char* content;
        int strict_valid;
        int lax_valid;
    } cases[] = {
        {"<%sknown>17</%sknown>", 1, 1},
        {"<%sknown>bad</%sknown>", 0, 0},
        {"<q:unknown>text</q:unknown>", 0, 1},
        {"<q:unknown xsi:type='xs:int'>17</q:unknown>", 1, 1},
        {"<q:unknown xsi:type='xs:int'>bad</q:unknown>", 0, 0},
        {"<q:unknown xsi:type='xs:Missing'>17</q:unknown>", 0, 0},
        {"<q:unknown xsi:type='%sRestricted'>5</q:unknown>", 1, 1},
        {"<q:unknown xsi:type='%sRestricted'>99</q:unknown>", 0, 0},
        {"<q:unknown xsi:type='%sRecord' tag='shipment'><code>17</code></q:unknown>", 1, 1},
        {"<q:unknown xsi:type='%sRecord' tag='shipment'><code>bad</code></q:unknown>", 0, 0},
        {"<q:unknown xsi:type='%sRecord'><code>17</code></q:unknown>", 0, 0},
        {"<q:unknown xsi:type='%sAbstract'/>", 0, 0},
        {"<q:unknown xsi:type='unbound:Type'>17</q:unknown>", 0, 0},
        {"<q:unknown xsi:type='xs:QName'>p:Stock</q:unknown>", 1, 1},
        {"<q:unknown xsi:type='xs:QName'>unbound:Stock</q:unknown>", 0, 0},
        {"<q:unknown><%sknown>bad</%sknown></q:unknown>", 0, 0},
        {"<q:unknown><%sknown>17</%sknown></q:unknown>", 0, 1},
        {"<%sknown xsi:type='xs:string'>17</%sknown>", 0, 0}
    };
    unsigned int mode, qualified, item;
    int result = 0;
    for (mode = 0; mode < 3; ++mode) {
        for (qualified = 0; qualified < 2; ++qualified) {
            char source[2048];
            const char* prefix = qualified ? "t:" : "";
            xmlSchemaParserCtxtPtr parser;
            xmlSchemaPtr schema;
            int diagnostics = 0;
            int length = snprintf(source, sizeof(source),
                "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema' xmlns:t='urn:wild-type'%s>"
                "<xs:element name='known' type='xs:int'/>"
                "<xs:simpleType name='Restricted'><xs:restriction base='xs:int'>"
                "<xs:maxInclusive value='9'/></xs:restriction></xs:simpleType>"
                "<xs:complexType name='Record'><xs:sequence><xs:element name='code' type='xs:int'/>"
                "</xs:sequence><xs:attribute name='tag' type='xs:string' use='required'/></xs:complexType>"
                "<xs:complexType name='Abstract' abstract='true'/>"
                "<xs:element name='root'><xs:complexType><xs:sequence>"
                "<xs:any processContents='%s' minOccurs='0' maxOccurs='unbounded'/>"
                "</xs:sequence></xs:complexType></xs:element></xs:schema>",
                qualified ? " targetNamespace='urn:wild-type'" : "", processing[mode]);
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
            for (item = 0; item < sizeof(cases) / sizeof(cases[0]); ++item) {
                char content[512], document[1024];
                int valid = mode == 2 || (mode == 0 ? cases[item].strict_valid : cases[item].lax_valid);
                length = snprintf(content, sizeof(content), cases[item].content, prefix, prefix);
                if (length < 0 || (size_t)length >= sizeof(content)) {
                    xmlSchemaFree(schema);
                    return 1;
                }
                length = snprintf(document, sizeof(document),
                    "<%sroot xmlns:t='urn:wild-type' xmlns:q='urn:child' xmlns:p='urn:products' "
                    "xmlns:xs='http://www.w3.org/2001/XMLSchema' "
                    "xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'>%s</%sroot>", prefix, content, prefix);
                if (length < 0 || (size_t)length >= sizeof(document)) {
                    xmlSchemaFree(schema);
                    return 1;
                }
                result |= check_qname_document(schema, document, valid);
            }
            xmlSchemaFree(schema);
        }
    }
    return result;
}
