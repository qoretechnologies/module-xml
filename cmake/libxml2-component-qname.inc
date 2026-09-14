/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Resolve component QNames after their mandatory whitespace collapse. */
#include "private/tree.h"
static int
xmlSchemaPValAttrNodeQNameValue(xmlSchemaParserCtxtPtr ctxt,
                               xmlSchemaPtr schema,
                               xmlSchemaBasicItemPtr ownerItem,
                               xmlAttrPtr attr,
                               const xmlChar *value,
                               const xmlChar **uri,
                               const xmlChar **local)
{
    const xmlChar *pref, *end, *part;
    xmlNsPtr ns;
    int len, ret;

    *uri = NULL;
    *local = NULL;
    if (value == NULL) {
        /* The checked content extractor has already reported the failure. */
        return -1;
    }
    ret = xmlValidateQName(value, 1);
    if (ret > 0) {
        xmlSchemaPSimpleTypeErr(ctxt, XML_SCHEMAP_S4S_ATTR_INVALID_VALUE,
            ownerItem, (xmlNodePtr) attr,
            xmlSchemaGetBuiltInType(XML_SCHEMAS_QNAME),
            NULL, value, NULL, NULL, NULL);
        *local = value;
        return ctxt->err;
    }
    if (ret < 0) {
        goto memory;
    }

    /* QName validation forbids internal whitespace. Intern bounded slices of
     * the original dictionary-owned spelling without allocating a trim buffer. */
    while (IS_BLANK_CH(*value)) {
        ++value;
    }
    end = value + xmlStrlen(value);
    while (end > value && IS_BLANK_CH(end[-1])) {
        --end;
    }
    part = xmlSplitQName3(value, &len);
    if (part == NULL) {
        if (xmlSearchNsSafe(attr->parent, NULL, &ns) < 0) {
            goto memory;
        }
        if (ns != NULL && ns->href != NULL && ns->href[0] != 0) {
            *uri = xmlDictLookup(ctxt->dict, ns->href, -1);
            if (*uri == NULL) {
                goto memory;
            }
        } else if (schema->flags & XML_SCHEMAS_INCLUDING_CONVERT_NS) {
            *uri = ctxt->targetNamespace;
        }
        *local = xmlDictLookup(ctxt->dict, value, (int) (end - value));
        if (*local == NULL) {
            goto memory;
        }
        return 0;
    }
    *local = xmlDictLookup(ctxt->dict, part, (int) (end - part));
    if (*local == NULL) {
        goto memory;
    }
    pref = xmlDictLookup(ctxt->dict, value, len);
    if (pref == NULL) {
        goto memory;
    }
    if (xmlSearchNsSafe(attr->parent, pref, &ns) < 0) {
        goto memory;
    }
    if (ns == NULL) {
        xmlSchemaPSimpleTypeErr(ctxt, XML_SCHEMAP_S4S_ATTR_INVALID_VALUE,
            ownerItem, (xmlNodePtr) attr,
            xmlSchemaGetBuiltInType(XML_SCHEMAS_QNAME), NULL, value,
            "The value '%s' of simple type 'xs:QName' has no "
            "corresponding namespace declaration in scope", value, NULL);
        return ctxt->err;
    }
    *uri = xmlDictLookup(ctxt->dict, ns->href, -1);
    if (*uri == NULL) {
        goto memory;
    }
    return 0;
memory:
    *uri = NULL;
    *local = NULL;
    xmlSchemaPErrMemory(ctxt);
    return -1;
}
