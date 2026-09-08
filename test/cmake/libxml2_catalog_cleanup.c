/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Regression for owned catalog errors discarded by xmlResolveFromCatalog.
 */
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <libxml/xmlreader.h>
#include <libxml/xmlschemas.h>
#include <libxml/xmlmemory.h>
#include <libxml/catalog.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static size_t allocations;
static unsigned catalog_errors;
static void* allocate(size_t size) {
    void* p = malloc(size);
    if (p) {
        ++allocations;
    }
    return p;
}
static void release(void* p) {
    if (p) {
        assert(allocations > 0);
        --allocations;
        free(p);
    }
}
static void* resize(void* p, size_t size) {
    if (!p) {
        return allocate(size);
    }
    if (!size) {
        release(p);
        return NULL;
    }
    return realloc(p, size);
}
static char* duplicate(const char* s) {
    size_t size = strlen(s) + 1;
    char* p = allocate(size);
    if (p) {
        memcpy(p, s, size);
    }
    return p;
}
static const char types[] = "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema' targetNamespace='urn:types'>"
    "<xs:simpleType name='Count'><xs:restriction base='xs:int'/></xs:simpleType></xs:schema>";
static const char schema[] = "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema' xmlns:t='urn:types'>"
    "<xs:import namespace='urn:types' schemaLocation='types.xsd'/>"
    "<xs:element name='value' type='t:Count'/></xs:schema>";
static int match(const char* url) {
    (void)url;
    return 1;
}
static void* open_input(const char* url) {
    (void)url;
    const char** cursor = allocate(sizeof(*cursor));
    assert(cursor);
    /* Returning an XSD for the catalog URL intentionally triggers a catalog error. */
    *cursor = types;
    return cursor;
}
static int read_input(void* context, char* buffer, int length) {
    const char** cursor = context;
    size_t count = strlen(*cursor);
    assert(length >= 0);
    if (count > (size_t)length) {
        count = (size_t)length;
    }
    memcpy(buffer, *cursor, count);
    *cursor += count;
    return (int)count;
}
static int close_input(void* context) {
    release(context);
    return 0;
}
static void error_handler(void* context, const xmlError* error) {
    (void)context;
    if (error->domain == XML_FROM_CATALOG) {
        ++catalog_errors;
        assert(error->code == XML_CATALOG_NOT_CATALOG);
    }
}
int main(void) {
    assert(!xmlMemSetup(release, allocate, resize, duplicate));
    for (unsigned previous_error = 0; previous_error < 2; ++previous_error) {
        xmlInitParser();
        xmlSetStructuredErrorFunc(NULL, error_handler);
        /* Force this in-memory catalog fixture independently of host configuration. */
        xmlInitializeCatalog();
        assert(xmlLoadCatalog("qore-invalid-catalog.xml") == 0);
        assert(xmlRegisterInputCallbacks(match, open_input, read_input, close_input) >= 0);
        if (previous_error) {
            xmlDocPtr doc = xmlReadMemory("<broken>", 8, NULL, NULL, 0);
            assert(!doc);
            assert(xmlGetLastError());
        }
        unsigned before = catalog_errors;
        xmlSchemaParserCtxtPtr context = xmlSchemaNewMemParserCtxt(schema, sizeof(schema) - 1);
        assert(context);
        xmlSchemaPtr parsed = xmlSchemaParse(context);
        assert(parsed);
        assert(catalog_errors > before);
        xmlSchemaFreeParserCtxt(context);
        xmlSchemaFree(parsed);
        xmlCleanupParser();
        if (allocations) {
            fprintf(stderr, "catalog cleanup retained %zu allocations\n", allocations);
            return 1;
        }
    }
    puts("catalog cleanup: PASS (including saved-error restoration)");
    return 0;
}
