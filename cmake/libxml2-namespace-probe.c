/* Copyright (C) 2026 Qore Technologies, s.r.o. */
#include <libxml/xmlreader.h>
#include <libxml/xmlschemastypes.h>
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
#include "libxml2-element-consistency-probe.h"
#include "libxml2-wildcard-id-probe.h"
#include "libxml2-wildcard-type-probe.h"
#include "libxml2-schema-whitespace-probe.h"
#include "libxml2-character-content-probe.h"
#include "libxml2-value-space-probe.h"
#include "libxml2-value-allocation-probe.h"

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
    if (prepare_value_allocation()) {
        return 1;
    }
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
        int consistency = check_element_consistency();
        int wildcard_ids = (check_wildcard_ids() | check_id_type_schemas());
        int wildcard_types = check_wildcard_types();
        int schema_whitespace = check_schema_whitespace();
        int character_content = check_character_content();
        int fixed_values = check_fixed_values();
        int time_values = check_time_values();
        int value_allocation = check_value_allocation();
        int unsigned_values = check_unsigned_values();
        uris |= check_schema_uri_values();
        uris |= check_schema_uri_hints();
        result |= qnames | unions | uris | entities | occurs | particles | attribution | ranges | finals | substitutions | consistency | wildcard_ids | wildcard_types | schema_whitespace | character_content | fixed_values | time_values | value_allocation | unsigned_values;
        printf("libxml2 headers=%s runtime=%s namespace_identity=%s qname_values=%s qname_unions=%s uri_identity=%s entity_values=%s occurs_values=%s particle_identity=%s particle_attribution=%s particle_ranges=%s type_final_defaults=%s element_substitution=%s element_consistency=%s wildcard_ids=%s wildcard_types=%s schema_whitespace=%s character_content=%s fixed_values=%s time_values=%s value_allocation=%s unsigned_values=%s\n",
            LIBXML_DOTTED_VERSION, xmlParserVersion, result ? "FAIL" : "PASS", qnames ? "FAIL" : "PASS",
            unions ? "FAIL" : "PASS", uris ? "FAIL" : "PASS", entities ? "FAIL" : "PASS", occurs ? "FAIL" : "PASS", particles ? "FAIL" : "PASS", attribution ? "FAIL" : "PASS", ranges ? "FAIL" : "PASS", finals ? "FAIL" : "PASS", substitutions ? "FAIL" : "PASS", consistency ? "FAIL" : "PASS", wildcard_ids ? "FAIL" : "PASS", wildcard_types ? "FAIL" : "PASS", schema_whitespace ? "FAIL" : "PASS", character_content ? "FAIL" : "PASS", fixed_values ? "FAIL" : "PASS", time_values ? "FAIL" : "PASS", value_allocation ? "FAIL" : "PASS", unsigned_values ? "FAIL" : "PASS");
    }
    xmlCleanupParser();
    return result;
}
