/* Copyright (C) 2026 Qore Technologies, s.r.o. */
#include <libxml/xmlschemastypes.h>
#include <libxml/xmlschemas.h>
#include <libxml/parser.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    char line[8192];
    size_t length;
    int status = 0;
    xmlInitParser();
    while (fgets(line, sizeof(line), stdin) != NULL) {
        length = strlen(line);
        char *type = line, *text = strchr(line, '\t'), *peer;
        xmlSchemaTypePtr builtin;
        xmlSchemaValPtr value = NULL, copy = NULL, other = NULL;
        const xmlChar *canonical = NULL;
        int result, relation = 99, canonical_result = 99;
        if (text == NULL || length == 0 || line[length - 1] != '\n') {
            status = 2;
            break;
        }
        line[length - 1] = 0;
        *text++ = 0;
        peer = strchr(text, '\t');
        if (peer != NULL) {
            *peer++ = 0;
        }
        builtin = xmlSchemaGetPredefinedType(BAD_CAST type, BAD_CAST "http://www.w3.org/2001/XMLSchema");
        result = xmlSchemaValidatePredefinedType(builtin, BAD_CAST text, &value);
        if (result < 0 || (result > 0 && value != NULL)) {
            status = 4;
            goto cleanup;
        }
        if (result == 0) {
            copy = xmlSchemaCopyValue(value);
            if (copy == NULL) {
                status = 3;
                goto cleanup;
            }
            xmlSchemaFreeValue(value);
            value = NULL;
            canonical_result = xmlSchemaGetCanonValue(copy, &canonical);
            if (peer != NULL) {
                int peer_result = xmlSchemaValidatePredefinedType(builtin, BAD_CAST peer, &other);
                if (peer_result < 0 || (peer_result > 0 && other != NULL)) {
                    status = 4;
                    goto cleanup;
                }
                if (peer_result == 0) {
                    relation = xmlSchemaCompareValues(copy, other);
                }
            }
        }
        printf("%d\t%d\t%d\t%s\n", result, canonical_result, relation, canonical ? (const char *)canonical : "");
cleanup:
        xmlFree((void *)canonical);
        xmlSchemaFreeValue(value);
        xmlSchemaFreeValue(copy);
        xmlSchemaFreeValue(other);
        if (status != 0) {
            break;
        }
    }
    if (ferror(stdin)) {
        status = 2;
    }
    xmlCleanupParser();
    return status;
}
