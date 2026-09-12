/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Verify zero-length text/CDATA events without weakening nonempty validation.
 * Include the selected source to exercise its shared text ownership boundary.
 */
#include QORE_XML_SCHEMA_SOURCE
#include <assert.h>
#include <stdio.h>

static void check_empty_event(int mode, const xmlChar* value, int length) {
    xmlSchemaValidCtxt context;
    xmlSchemaNodeInfo node;
    xmlSchemaType type;
    int consumed = 1;
    memset(&context, 0, sizeof(context));
    memset(&node, 0, sizeof(node));
    memset(&type, 0, sizeof(type));
    context.inode = &node;
    context.depth = 0;
    context.skipDepth = -1;
    node.typeDef = &type;
    node.flags = XML_SCHEMA_ELEM_INFO_EMPTY | XML_SCHEMA_ELEM_INFO_NILLED;
    type.contentType = XML_SCHEMA_CONTENT_EMPTY;
    assert(xmlSchemaVPushText(&context, value, length, mode, &consumed) == 0);
    assert(consumed == 0);
    assert(node.flags == (XML_SCHEMA_ELEM_INFO_EMPTY | XML_SCHEMA_ELEM_INFO_NILLED));
    assert(node.value == NULL);
    assert(context.err == 0);

    /* SAX chunks need not be NUL-terminated. A zero length must win over bytes
     * beyond that boundary, and the caller must not clear EMPTY prematurely. */
    if (length == 0) {
        xmlSchemaSAXHandleText(&context, value, length);
        assert(node.flags == (XML_SCHEMA_ELEM_INFO_EMPTY | XML_SCHEMA_ELEM_INFO_NILLED));
        xmlSchemaSAXHandleCDataSection(&context, value, length);
        assert(node.flags == (XML_SCHEMA_ELEM_INFO_EMPTY | XML_SCHEMA_ELEM_INFO_NILLED));
        assert(context.err == 0);
    }
}

int main(void) {
    const xmlChar nonterminated = 'x';
    int mode;
    xmlInitParser();
    for (mode = XML_SCHEMA_PUSH_TEXT_PERSIST; mode <= XML_SCHEMA_PUSH_TEXT_VOLATILE; ++mode) {
        xmlChar* owned = xmlStrdup(BAD_CAST "");
        if (owned == NULL) {
            xmlCleanupParser();
            return 1;
        }
        check_empty_event(mode, owned, -1);
        check_empty_event(mode, owned, 0);
        check_empty_event(mode, NULL, -1);
        check_empty_event(mode, &nonterminated, 0);
        /* Empty CREATED input was not consumed by the validator. */
        xmlFree(owned);
    }
    xmlCleanupParser();
    puts("Native character-event ownership: PASS");
    return 0;
}
