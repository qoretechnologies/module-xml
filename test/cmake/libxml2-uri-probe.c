/* Copyright (C) 2026 Qore Technologies, s.r.o. */
#include "../../cmake/libxml2-uri-probe.h"
#include "../../cmake/libxml2-schema-uri-probe.h"

int main(void) {
    int result = check_uri_values();
    result |= check_schema_uri_values();
    result |= check_schema_uri_hints();
    xmlCleanupParser();
    return (result);
}
