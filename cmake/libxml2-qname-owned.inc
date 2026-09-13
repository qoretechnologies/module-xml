/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Checked QName lexical parts and value ownership, shared by both native paths.
 */
#include "private/tree.h"

static int
qoreXmlQNameParts(const xmlChar *value, xmlChar **prefix, xmlChar **local) {
    const xmlChar *start, *end, *colon;
    size_t length;
    int ret;
    *prefix = NULL;
    *local = NULL;
    if (value == NULL) {
        return 1;
    }
    ret = xmlValidateQName(value, 1);
    if (ret != 0) {
        return ret;
    }
    start = value;
    while (IS_BLANK_CH(*start)) {
        ++start;
    }
    end = start + strlen((const char *)start);
    while (end != start && IS_BLANK_CH(end[-1])) {
        --end;
    }
    length = (size_t)(end - start);
    if (length > INT_MAX) {
        return -1;
    }
    colon = memchr(start, ':', length);
    if (colon != NULL) {
        *prefix = xmlStrndup(start, (int)(colon - start));
        if (*prefix == NULL) {
            return -1;
        }
        start = colon + 1;
    }
    *local = xmlStrndup(start, (int)(end - start));
    if (*local == NULL) {
        xmlFree(*prefix);
        *prefix = NULL;
        return -1;
    }
    return 0;
}

static xmlSchemaValPtr
qoreXmlQNameValue(const xmlChar *uri, const xmlChar *local, int notation) {
    xmlChar *name = xmlStrdup(local), *namespaceName = NULL;
    xmlSchemaValPtr value;
    if (name == NULL) {
        return NULL;
    }
    if (uri != NULL && uri[0] != 0) {
        namespaceName = xmlStrdup(uri);
        if (namespaceName == NULL) {
            xmlFree(name);
            return NULL;
        }
    }
    value = notation ? xmlSchemaNewNOTATIONValue(name, namespaceName)
                     : xmlSchemaNewQNameValue(namespaceName, name);
    if (value == NULL) {
        xmlFree(name);
        xmlFree(namespaceName);
    }
    return value;
}
