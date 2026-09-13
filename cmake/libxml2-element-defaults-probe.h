/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 canonical actual-type assessment; declaration QName bindings are
 * independent of the instance's bindings. Included after the shared probes.
 */
static int check_element_defaults(void) {
    static const char source[] =
        "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
        "<xs:simpleType name='Canonical'><xs:restriction base='xs:boolean'>"
        "<xs:pattern value='true'/></xs:restriction></xs:simpleType>"
        "<xs:simpleType name='Original'><xs:restriction base='xs:boolean'>"
        "<xs:pattern value='1'/></xs:restriction></xs:simpleType>"
        "<xs:element name='value' type='xs:boolean' default='1'/></xs:schema>";
    static const char *documents[] = {
        "<value xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xsi:type='Canonical'/>",
        "<value xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xsi:type='Canonical'><!--empty--></value>",
        "<value xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xsi:type='Original'/>",
        "<value xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xsi:type='Original'>1</value>"
    };
    xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, sizeof(source) - 1);
    xmlSchemaPtr schema;
    unsigned int i;
    int result = 0;
    if (parser == NULL) {
        return 1;
    }
    xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
    schema = xmlSchemaParse(parser);
    xmlSchemaFreeParserCtxt(parser);
    if (schema == NULL) {
        return 1;
    }
    for (i = 0; i < sizeof(documents)/sizeof(documents[0]); ++i) {
        result |= check_qname_document(schema, documents[i], i != 2);
    }
    xmlSchemaFree(schema);
    return result;
}

static int check_default_namespaces(void) {
    static const char source[] =
        "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema' xmlns:p='urn:part'>"
        "<xs:element name='value'><xs:complexType><xs:sequence>"
        "<xs:element name='item' type='xs:QName' default='p:item'/>"
        "<xs:element name='peer' type='xs:QName'/></xs:sequence></xs:complexType>"
        "<xs:unique name='key'><xs:selector xpath='item|peer'/><xs:field xpath='.'/></xs:unique>"
        "</xs:element></xs:schema>";
    static const char *documents[] = {
        "<value xmlns:p='urn:shadow' xmlns:q='urn:part'><item/><peer>q:item</peer></value>",
        "<value xmlns:p='urn:shadow' xmlns:q='urn:part'><item/><peer>p:item</peer></value>",
        "<value xmlns:q='urn:part'><item/><peer>q:other</peer></value>"
    };
    xmlSchemaParserCtxtPtr parser = xmlSchemaNewMemParserCtxt(source, sizeof(source) - 1);
    xmlSchemaPtr schema;
    unsigned int i;
    int result = 0;
    if (parser == NULL) {
        return 1;
    }
    xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, NULL);
    schema = xmlSchemaParse(parser);
    xmlSchemaFreeParserCtxt(parser);
    if (schema == NULL) {
        return 1;
    }
    for (i = 0; i < sizeof(documents)/sizeof(documents[0]); ++i) {
        result |= check_qname_document(schema, documents[i], i != 0);
    }
    xmlSchemaFree(schema);
    return result;
}

static int check_qname_allocation(void) {
    static const char document[] = "<value xmlns:p='urn:part'/>";
    xmlDocPtr doc = xmlReadMemory(document, sizeof(document) - 1, NULL, NULL, XML_PARSE_NONET);
    xmlSchemaTypePtr type = xmlSchemaGetBuiltInType(XML_SCHEMAS_QNAME);
    unsigned int count = 0, fault;
    int failed = 0;
    if (doc == NULL || type == NULL) {
        xmlFreeDoc(doc);
        return 1;
    }
    for (fault = 0; fault <= count; ++fault) {
        xmlSchemaValPtr value = NULL;
        int result;
        value_probe_failures = 0;
        value_probe_attempts = 0;
        value_probe_fail_at = fault;
        value_probe_armed = 1;
        result = xmlSchemaValPredefTypeNode(type, BAD_CAST "p:item", &value, xmlDocGetRootElement(doc));
        value_probe_armed = 0;
        if (fault == 0) {
            count = value_probe_attempts;
            failed = result != 0 || value == NULL;
        } else {
            failed = value_probe_failures == 0 || result != -1 || value != NULL;
        }
        xmlSchemaFreeValue(value);
        if (failed) {
            break;
        }
    }
    xmlFreeDoc(doc);
    return failed;
}
