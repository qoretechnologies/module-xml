/* Copyright (C) 2026 Qore Technologies, s.r.o. */
#include <libxml/xmlreader.h>
#include <stdio.h>
#include <string.h>
#include "libxml2-qname-probe.h"
#include "libxml2-uri-probe.h"
#include "libxml2-schema-uri-probe.h"

static int check_namespace(const char* source, const char* expected) {
    xmlTextReaderPtr reader = xmlReaderForMemory(source, (int)strlen(source), NULL, "UTF-8", 0);
    int result = 0;
    int seen = 0;
    int status;
    if (!reader) {
        return 1;
    }
    while ((status = xmlTextReaderRead(reader)) == 1) {
        if (xmlTextReaderNodeType(reader) == XML_READER_TYPE_ELEMENT
                && xmlTextReaderDepth(reader) == 1) {
            xmlChar* lookup = xmlTextReaderLookupNamespace(reader, BAD_CAST "p");
            seen = 1;
            if (!xmlStrEqual(xmlTextReaderConstNamespaceUri(reader), BAD_CAST expected)
                    || !xmlStrEqual(lookup, BAD_CAST expected)) {
                result = 1;
            }
            xmlFree(lookup);
        }
    }
    xmlFreeTextReader(reader);
    return result || !seen || status < 0;
}

int main(void) {
    int result = 0;
    result |= check_namespace("<r xmlns:p='urn:a&amp;b'><p:x/></r>", "urn:a&b");
    result |= check_namespace("<r xmlns:p='urn:a&#38;b'><p:x/></r>", "urn:a&b");
    result |= check_namespace("<r xmlns:p='urn:a&#x26;b'><p:x/></r>", "urn:a&b");
    result |= check_namespace("<r xmlns:p='urn:a&amp;#38;b'><p:x/></r>", "urn:a&#38;b");
    {
        int qnames = check_qname_values();
        int unions = check_qname_unions();
        int uris = check_uri_values();
        uris |= check_schema_uri_values();
        uris |= check_schema_uri_hints();
        result |= qnames | unions | uris;
        printf("libxml2 headers=%s runtime=%s namespace_identity=%s qname_values=%s qname_unions=%s uri_identity=%s\n",
            LIBXML_DOTTED_VERSION, xmlParserVersion, result ? "FAIL" : "PASS", qnames ? "FAIL" : "PASS",
            unions ? "FAIL" : "PASS", uris ? "FAIL" : "PASS");
    }
    xmlCleanupParser();
    return result;
}
