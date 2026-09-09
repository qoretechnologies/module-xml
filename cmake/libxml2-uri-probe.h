/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Standalone, offline URI identity and XML Base checks for the native dependency.
 * RFC 3986 sections 2.2, 2.3, 5.4; XML Base Second Edition section 3.1.
 */
#include <libxml/parser.h>
#include <libxml/tree.h>
#include <libxml/uri.h>
#include <stdio.h>
#include <string.h>

static unsigned uri_checks;
static unsigned uri_failures;

static void uri_check(const char *label, const xmlChar *actual, const char *expected) {
    ++uri_checks;
    if ((actual == NULL) != (expected == NULL) || (actual != NULL && strcmp((const char *)actual, expected) != 0)) {
        ++uri_failures;
        fprintf(stderr, "%s: expected <%s>, received <%s>\n", label, expected == NULL ? "NULL" : expected,
                actual == NULL ? "NULL" : (const char *)actual);
    }
}

static int check_uri_values(void) {
    uri_checks = uri_failures = 0;
    static const char *const resolution[][2] = {{"g:h", "g:h"},
                                                {"g", "http://a/b/c/g"},
                                                {"./g", "http://a/b/c/g"},
                                                {"g/", "http://a/b/c/g/"},
                                                {"/g", "http://a/g"},
                                                {"//g", "http://g"},
                                                {"?y", "http://a/b/c/d;p?y"},
                                                {"g?y", "http://a/b/c/g?y"},
                                                {"#s", "http://a/b/c/d;p?q#s"},
                                                {"g#s", "http://a/b/c/g#s"},
                                                {"g?y#s", "http://a/b/c/g?y#s"},
                                                {";x", "http://a/b/c/;x"},
                                                {"g;x", "http://a/b/c/g;x"},
                                                {"g;x?y#s", "http://a/b/c/g;x?y#s"},
                                                {"", "http://a/b/c/d;p?q"},
                                                {".", "http://a/b/c/"},
                                                {"./", "http://a/b/c/"},
                                                {"..", "http://a/b/"},
                                                {"../", "http://a/b/"},
                                                {"../g", "http://a/b/g"},
                                                {"../..", "http://a/"},
                                                {"../../", "http://a/"},
                                                {"../../g", "http://a/g"},
                                                {"../../../g", "http://a/g"},
                                                {"../../../../g", "http://a/g"},
                                                {"/./g", "http://a/g"},
                                                {"/../g", "http://a/g"},
                                                {"g.", "http://a/b/c/g."},
                                                {".g", "http://a/b/c/.g"},
                                                {"g..", "http://a/b/c/g.."},
                                                {"..g", "http://a/b/c/..g"},
                                                {"./../g", "http://a/b/g"},
                                                {"./g/.", "http://a/b/c/g/"},
                                                {"g/./h", "http://a/b/c/g/h"},
                                                {"g/../h", "http://a/b/c/h"},
                                                {"g;x=1/./y", "http://a/b/c/g;x=1/y"},
                                                {"g;x=1/../y", "http://a/b/c/y"},
                                                {"g?y/./x", "http://a/b/c/g?y/./x"},
                                                {"g?y/../x", "http://a/b/c/g?y/../x"},
                                                {"g#s/./x", "http://a/b/c/g#s/./x"},
                                                {"g#s/../x", "http://a/b/c/g#s/../x"},
                                                {"http:g", "http:g"},
                                                {"g%2Fh", "http://a/b/c/g%2Fh"},
                                                {"g%2fh", "http://a/b/c/g%2fh"},
                                                {"%2E/g", "http://a/b/c/%2E/g"},
                                                {"g%3Fh%23i%25j", "http://a/b/c/g%3Fh%23i%25j"},
                                                {"./g:h", "http://a/b/c/g:h"},
                                                {"~g", "http://a/b/c/~g"},
                                                {"g//h", "http://a/b/c/g//h"},
                                                {"g///h", "http://a/b/c/g///h"},
                                                {"g//../h", "http://a/b/c/g/h"},
                                                {"/g//../h", "http://a/g/h"},
                                                {"http://a/g/../h", "http://a/h"},
                                                {"http://a/g//h", "http://a/g//h"},
                                                {"//host/g/../h", "http://host/h"},
                                                {"%", NULL},
                                                {"%2", NULL},
                                                {"%GG", NULL},
                                                {"g h", NULL},
                                                {"http://[", NULL},
                                                {"http://a:bad/", NULL}};
    static const char *const bases[][2] = {
        {"rosé", "http://example.org/wine/rosé"},
        {"white wine", "http://example.org/wine/white wine"},
        {"中文/𝄞", "http://example.org/wine/中文/𝄞"},
        {"white%20wine", "http://example.org/wine/white%20wine"},
        {"white%2Fwine", "http://example.org/wine/white%2Fwine"},
        {"rosé%2Fwine", "http://example.org/wine/rosé%2Fwine"},
        {"rosé%FF", "http://example.org/wine/rosé%FF"},
        {"rosé%C3", "http://example.org/wine/rosé%C3"},
        {"rosé%00", "http://example.org/wine/rosé%00"},
        {"./a:b", "http://example.org/wine/a:b"},
        {"a//b", "http://example.org/wine/a//b"},
        {"a//../b", "http://example.org/wine/a/b"},
        {"a\t\n\r \"<>\\^`{|}\x7f", "http://example.org/wine/a\t\n\r \"<>\\^`{|}\x7f"},
        {"../café/./a", "http://example.org/café/a"},
        {"", "http://example.org/wine/"},
        {"%", NULL},
        {"%2", NULL},
        {"%GG", NULL}};
    static const char *const raw[] = {"http://u%3A:p%40ss@host.example/a%2Fb:c?q=a%2Fb#f%23g",
                                      "http://[::1]:8080/a:b@c!$&'()*+,;=d?name=~%7e",
                                      "file:///café", /* The strict raw URI API still rejects a raw LEIRI. */
                                      "http://example.org/%",
                                      "http://example.org/%2",
                                      "http://example.org/%GG"};
    size_t i;
    for (i = 0; i < sizeof(resolution) / sizeof(resolution[0]); ++i) {
        xmlChar *result = xmlBuildURI(BAD_CAST resolution[i][0], BAD_CAST "http://a/b/c/d;p?q");
        uri_check(resolution[i][0], result, resolution[i][1]);
        xmlFree(result);
    }
    for (i = 0; i < sizeof(bases) / sizeof(bases[0]); ++i) {
        static const char text[] = "<r xml:base='http://example.org/wine/'><e/></r>";
        xmlDoc *doc = xmlReadMemory(text, sizeof(text) - 1, "http://example.org/source.xml", NULL, 0);
        xmlNode *node;
        xmlChar *result;
        if (doc == NULL) {
            fprintf(stderr, "Could not construct XML Base fixture\n");
            return (1);
        }
        node = xmlDocGetRootElement(doc)->children;
        if (xmlSetNsProp(node, xmlSearchNs(doc, node, BAD_CAST "xml"), BAD_CAST "base", BAD_CAST bases[i][0]) == NULL) {
            xmlFreeDoc(doc);
            return (1);
        }
        result = xmlNodeGetBase(doc, node);
        uri_check(bases[i][0], result, bases[i][1]);
        xmlFree(result);
        result = xmlGetNsProp(node, BAD_CAST "base", XML_XML_NAMESPACE);
        uri_check("original XML Base attribute", result, bases[i][0]);
        xmlFree(result);
        xmlFreeDoc(doc);
    }
    for (i = 0; i < sizeof(raw) / sizeof(raw[0]); ++i) {
        xmlURI *uri = xmlParseURIRaw(raw[i], 1);
        xmlChar *result = uri == NULL ? NULL : xmlSaveUri(uri);
        uri_check("raw URI parse/save", result, i < 2 ? raw[i] : NULL);
        xmlFree(result);
        xmlFreeURI(uri);
    }
    {
        xmlURI *uri = xmlParseURI("http://host/a%2Fb?q=a%2Fb#f%23g");
        if (uri == NULL) {
            return (1);
        }
        uri_check("decoded public path", BAD_CAST uri->path, "/a/b");
        uri_check("decoded public query", BAD_CAST uri->query, "q=a/b");
        uri_check("decoded public fragment", BAD_CAST uri->fragment, "f#g");
        xmlFreeURI(uri);
    }
    printf("%u URI/XML Base checks; %u failures\n", uri_checks, uri_failures);
    return (uri_failures != 0);
}
