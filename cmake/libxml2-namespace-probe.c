/* Copyright (C) 2026 Qore Technologies, s.r.o. */
#include <libxml/xmlreader.h>
#include <stdio.h>
#include <string.h>
#include "libxml2-qname-probe.h"
#include "libxml2-uri-probe.h"
#include "libxml2-schema-uri-probe.h"
#include "libxml2-entity-probe.h"
#include "libxml2-occurs-probe.h"
#include "libxml2-particle-identity-probe.h"
#include "libxml2-particle-attribution-probe.h"
#include "libxml2-particle-range-probe.h"
#include "libxml2-type-final-probe.h"
#include "libxml2-element-substitution-probe.h"

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
        int entities = check_entity_values();
        int occurs = check_occurs_values();
        int particles = check_particle_identity();
        int attribution = check_particle_attribution();
        int ranges = check_particle_ranges();
        int finals = check_type_final_defaults();
        int substitutions = check_element_substitution();
        uris |= check_schema_uri_values();
        uris |= check_schema_uri_hints();
        result |= qnames | unions | uris | entities | occurs | particles | attribution | ranges | finals | substitutions;
        printf("libxml2 headers=%s runtime=%s namespace_identity=%s qname_values=%s qname_unions=%s uri_identity=%s entity_values=%s occurs_values=%s particle_identity=%s particle_attribution=%s particle_ranges=%s type_final_defaults=%s element_substitution=%s\n",
            LIBXML_DOTTED_VERSION, xmlParserVersion, result ? "FAIL" : "PASS", qnames ? "FAIL" : "PASS",
            unions ? "FAIL" : "PASS", uris ? "FAIL" : "PASS", entities ? "FAIL" : "PASS", occurs ? "FAIL" : "PASS", particles ? "FAIL" : "PASS", attribution ? "FAIL" : "PASS", ranges ? "FAIL" : "PASS", finals ? "FAIL" : "PASS", substitutions ? "FAIL" : "PASS");
    }
    xmlCleanupParser();
    return result;
}
