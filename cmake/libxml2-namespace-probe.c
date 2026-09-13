/* Copyright (C) 2026 Qore Technologies, s.r.o. */
#include <libxml/xmlreader.h>
#include <libxml/xmlschemastypes.h>
#include <stdio.h>
#include <string.h>
#include "libxml2-qname-probe.h"
#include "libxml2-uri-probe.h"
#include "libxml2-schema-uri-probe.h"
#include "libxml2-entity-probe.h"
#include "libxml2-id-binding-probe.h"
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
#include "libxml2-numeric-defaults-probe.h"
#include "libxml2-ieee-probe.h"
#include "libxml2-calendar-probe.h"
#include "libxml2-element-defaults-probe.h"
#include "libxml2-notation-probe.h"
#include "libxml2-annotation-probe.h"

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
    /* Flush completed checks before probing a library's builtin particle paths. */
    fflush(stdout);
    {
        int builtin_particles = check_builtin_particles();
        result |= builtin_particles;
        printf("builtin_particles=%s\n", builtin_particles ? "FAIL" : "PASS");
    }
    {
        int id_bindings = check_id_bindings();
        result |= id_bindings;
        printf("id_bindings=%s\n", id_bindings ? "FAIL" : "PASS");
    }
    {
        int numeric_defaults = check_numeric_defaults();
        result |= numeric_defaults;
        printf("numeric_defaults=%s\n", numeric_defaults ? "FAIL" : "PASS");
    }
    {
        int ieee = check_ieee_values();
        result |= ieee;
        printf("ieee_values=%s\n", ieee ? "FAIL" : "PASS");
    }
    {
        int calendar = check_calendar_values();
        int constraints = check_calendar_constraints();
        result |= calendar | constraints;
        printf("calendar_values=%s\n", calendar ? "FAIL" : "PASS");
        printf("calendar_constraints=%s\n", constraints ? "FAIL" : "PASS");
    }
    {
        int defaults = check_element_defaults();
        int namespaces = check_default_namespaces();
        int allocation = check_qname_allocation();
        result |= defaults | namespaces | allocation;
        printf("element_defaults=%s\n", defaults ? "FAIL" : "PASS");
        printf("default_namespaces=%s\n", namespaces ? "FAIL" : "PASS");
        printf("qname_allocation=%s\n", allocation ? "FAIL" : "PASS");
    }
    {
        int annotations = check_annotations();
        result |= annotations;
        printf("annotations=%s\n", annotations ? "FAIL" : "PASS");
        int notations = check_notations();
        result |= notations;
        printf("notations=%s\n", notations ? "FAIL" : "PASS");
    }
    xmlCleanupParser();
    return result;
}
