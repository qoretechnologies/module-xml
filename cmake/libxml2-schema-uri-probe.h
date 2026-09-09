/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Offline XSD 1.0 include/import/redefine URI resolution. The callback never
 * delegates unknown URLs, so configure cannot reach the network or filesystem.
 */
#include <libxml/parserInternals.h>
#include <libxml/xmlreader.h>
#include <libxml/xmlschemas.h>

static const char *schema_uri_expected;
static const char *schema_uri_resource;
static const char *schema_uri_second;
static const char *schema_uri_second_resource;
static unsigned schema_uri_calls;
static unsigned schema_uri_wrong;

static xmlParserInput *schema_uri_loader(const char *url, const char *public_id, xmlParserCtxt *context) {
    xmlParserInput *input;
    const char *resource = schema_uri_resource;
    (void)public_id;
    ++schema_uri_calls;
    if (url != NULL && schema_uri_second != NULL && strcmp(url, schema_uri_second) == 0) {
        resource = schema_uri_second_resource;
    } else if (url == NULL || strcmp(url, schema_uri_expected) != 0) {
        ++schema_uri_wrong;
        return (NULL);
    }
    input = xmlNewStringInputStream(context, BAD_CAST resource);
    if (input != NULL) {
        input->filename = xmlMemStrdup(url);
        if (input->filename == NULL) {
            xmlFreeInputStream(input);
            return (NULL);
        }
    }
    return (input);
}

static void schema_uri_diagnostic(void *context, const char *message, ...) {
    ++*(unsigned *)context;
    (void)message;
}

static int check_schema_uri_values(void) {
    static const char *const locations[][2] = {
        {"café 中文.xsd", "caf%C3%A9%20%E4%B8%AD%E6%96%87.xsd"},
        {"caf%C3%A9%20%E4%B8%AD%E6%96%87.xsd", "caf%C3%A9%20%E4%B8%AD%E6%96%87.xsd"},
        {"a%2Fb.xsd", "a%2Fb.xsd"},
        {"./a:b~.xsd", "a:b~.xsd"}};
    static const char *const kinds[] = {"include", "import", "redefine"};
    xmlExternalEntityLoader previous = xmlGetExternalEntityLoader();
    unsigned kind, index, failures = 0, checks = 0;
    xmlSetExternalEntityLoader(schema_uri_loader);
    for (kind = 0; kind < 3; ++kind) {
        for (index = 0; index < 4; ++index) {
            char source[2048], resource[512], expected[256];
            xmlDoc *document;
            xmlSchemaParserCtxt *parser;
            xmlSchema *schema;
            unsigned diagnostics = 0;
            ++checks;
            snprintf(resource, sizeof(resource),
                     "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'%s>"
                     "<xs:simpleType name='Count'><xs:restriction base='xs:int'/></xs:simpleType></xs:schema>",
                     kind == 1 ? " targetNamespace='urn:uri-types'" : "");
            snprintf(source, sizeof(source),
                     "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema' xmlns:t='urn:uri-types' "
                     "xml:base='café dir/'><xs:%s schemaLocation='%s'%s>%s</xs:%s>"
                     "<xs:element name='value' type='%s'/></xs:schema>",
                     kinds[kind], locations[index][0], kind == 1 ? " namespace='urn:uri-types'" : "",
                     kind == 2 ? "<xs:simpleType name='Count'><xs:restriction base='Count'>"
                                 "<xs:minInclusive value='10'/></xs:restriction></xs:simpleType>"
                               : "",
                     kinds[kind], kind == 1 ? "t:Count" : "Count");
            snprintf(expected, sizeof(expected), "http://schema-uri.invalid/caf%%C3%%A9%%20dir/%s",
                     locations[index][1]);
            schema_uri_expected = expected;
            schema_uri_resource = resource;
            schema_uri_calls = schema_uri_wrong = 0;
            document =
                xmlReadMemory(source, (int)strlen(source), "http://schema-uri.invalid/main.xsd", NULL, XML_PARSE_NONET);
            parser = document == NULL ? NULL : xmlSchemaNewDocParserCtxt(document);
            if (parser != NULL) {
                xmlSchemaSetParserErrors(parser, schema_uri_diagnostic, schema_uri_diagnostic, &diagnostics);
            }
            schema = parser == NULL ? NULL : xmlSchemaParse(parser);
            if (schema == NULL || diagnostics || schema_uri_calls != 1 || schema_uri_wrong) {
                ++failures;
                fprintf(stderr, "schema URI %s/%s failed (diagnostics=%u, calls=%u, wrong=%u)\n", kinds[kind],
                        locations[index][0], diagnostics, schema_uri_calls, schema_uri_wrong);
            }
            xmlSchemaFree(schema);
            xmlSchemaFreeParserCtxt(parser);
            xmlFreeDoc(document);
        }
    }
    xmlSetExternalEntityLoader(previous);
    schema_uri_expected = schema_uri_resource = NULL;
    printf("%u schema URI checks; %u failures\n", checks, failures);
    return (failures != 0);
}

static int check_schema_uri_hints(void) {
    static const char leaf[] = "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
                               "<xs:element name='value' type='xs:int'/></xs:schema>";
    xmlExternalEntityLoader previous = xmlGetExternalEntityLoader();
    static const char wrapper[] = "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
                                  "<xs:element name='value'><xs:complexType><xs:sequence><xs:any namespace='urn:items' "
                                  "processContents='strict'/></xs:sequence></xs:complexType></xs:element></xs:schema>";
    static const char namespaced[] = "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema' "
                                     "targetNamespace='urn:items'><xs:element name='item' type='xs:int'/></xs:schema>";
    unsigned streaming, has_base, invalid, combined, checks = 0, failures = 0;
    xmlSetExternalEntityLoader(schema_uri_loader);
    for (streaming = 0; streaming < 2; ++streaming) {
        for (has_base = 0; has_base < 2; ++has_base) {
            for (combined = 0; combined < 3; ++combined) {
                for (invalid = 0; invalid < 2; ++invalid) {
                    char source[512];
                    const char *base = has_base ? "http://schema-uri.invalid/main.xml" : NULL;
                    xmlSchemaValidCtxt *context = xmlSchemaNewValidCtxt(NULL);
                    unsigned diagnostics = 0;
                    int result = -1;
                    ++checks;
                    schema_uri_expected = "http://schema-uri.invalid/caf%C3%A9%20dir/leaf.xsd";
                    schema_uri_resource = combined == 1 ? wrapper : leaf;
                    schema_uri_second = combined ? "http://schema-uri.invalid/caf%C3%A9%20dir/item.xsd" : NULL;
                    schema_uri_second_resource = namespaced;
                    schema_uri_calls = schema_uri_wrong = 0;
                    if (combined == 0) {
                        snprintf(source, sizeof(source),
                                 "<value xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' "
                                 "xsi:noNamespaceSchemaLocation='  %scafé   dir/leaf.xsd  '>%s</value>",
                                 has_base ? "" : "http://schema-uri.invalid/", invalid ? "bad" : "17");
                    } else if (combined == 1) {
                        snprintf(source, sizeof(source),
                                 "<value xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' "
                                 "xsi:noNamespaceSchemaLocation='%scafé dir/leaf.xsd' "
                                 "xsi:schemaLocation='urn:items http://schema-uri.invalid/café%%20dir/item.xsd'>"
                                 "<i:item xmlns:i='urn:items'>%s</i:item></value>",
                                 has_base ? "" : "http://schema-uri.invalid/", invalid ? "bad" : "17");
                    } else {
                        snprintf(source, sizeof(source),
                                 "<i:item xmlns:i='urn:items' "
                                 "xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' "
                                 "xsi:schemaLocation='urn:items %scafé%%20dir/item.xsd'>%s</i:item>",
                                 has_base ? "" : "http://schema-uri.invalid/", invalid ? "bad" : "17");
                    }
                    if (context != NULL) {
                        xmlSchemaSetValidErrors(context, schema_uri_diagnostic, schema_uri_diagnostic, &diagnostics);
                        if (streaming) {
                            xmlTextReader *reader =
                                xmlReaderForMemory(source, (int)strlen(source), base, NULL, XML_PARSE_NONET);
                            if (reader != NULL && xmlTextReaderSchemaValidateCtxt(reader, context, 0) == 0) {
                                int status;
                                while ((status = xmlTextReaderRead(reader)) == 1) {
                                }
                                if (status == 0) {
                                    result = xmlTextReaderIsValid(reader) ? 0 : 1;
                                }
                            }
                            xmlFreeTextReader(reader);
                        } else {
                            xmlDoc *document = xmlReadMemory(source, (int)strlen(source), base, NULL, XML_PARSE_NONET);
                            if (document != NULL) {
                                result = xmlSchemaValidateDoc(context, document);
                            }
                            xmlFreeDoc(document);
                        }
                    }
                    xmlSchemaFreeValidCtxt(context);
                    if (result < 0 || (result != 0) != (invalid != 0) || (diagnostics != 0) != (invalid != 0) ||
                        schema_uri_calls != (combined == 1 ? 2u : 1u) || schema_uri_wrong) {
                        ++failures;
                        fprintf(stderr,
                                "schema hint stream=%u base=%u combined=%u invalid=%u: result=%d diagnostics=%u "
                                "calls=%u wrong=%u\n",
                                streaming, has_base, combined, invalid, result, diagnostics, schema_uri_calls,
                                schema_uri_wrong);
                    }
                }
            }
        }
    }
    xmlSetExternalEntityLoader(previous);
    schema_uri_expected = schema_uri_resource = NULL;
    schema_uri_second = schema_uri_second_resource = NULL;
    printf("%u schema URI hint checks; %u failures\n", checks, failures);
    return (failures != 0);
}
