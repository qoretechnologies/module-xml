/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Check the notation representation before publishing its component.
 */
static xmlSchemaNotationPtr
xmlSchemaParseNotation(xmlSchemaParserCtxtPtr ctxt, xmlSchemaPtr schema,
                       xmlNodePtr node) {
    const xmlChar *name = NULL;
    xmlSchemaNotationPtr result;
    xmlNodePtr child;
    xmlAttrPtr attr;
    int identifiers = 0;
    int errors;

    if (ctxt == NULL || schema == NULL || node == NULL) {
        return NULL;
    }
    errors = ctxt->nberrors;
    for (attr = node->properties; attr != NULL; attr = attr->next) {
        if (attr->ns != NULL) {
            if (xmlStrEqual(attr->ns->href, xmlSchemaNs)) {
                xmlSchemaPIllegalAttrErr(ctxt, XML_SCHEMAP_S4S_ATTR_NOT_ALLOWED, NULL, attr);
            }
            continue;
        }
        if (xmlStrEqual(attr->name, BAD_CAST "name")) {
            if (xmlSchemaPValAttrNode(ctxt, NULL, attr,
                    xmlSchemaGetBuiltInType(XML_SCHEMAS_NCNAME), &name) != 0 || name == NULL) {
                return NULL;
            }
        } else if (xmlStrEqual(attr->name, BAD_CAST "id")) {
            if (xmlSchemaPValAttrNodeID(ctxt, attr) != 0) {
                return NULL;
            }
        } else if (xmlStrEqual(attr->name, BAD_CAST "public") ||
                   xmlStrEqual(attr->name, BAD_CAST "system")) {
            const xmlChar *value = NULL;
            int kind = xmlStrEqual(attr->name, BAD_CAST "public")
                ? XML_SCHEMAS_TOKEN : XML_SCHEMAS_ANYURI;
            ++identifiers;
            if (xmlSchemaPValAttrNode(ctxt, NULL, attr,
                    xmlSchemaGetBuiltInType(kind), &value) != 0 || value == NULL) {
                return NULL;
            }
        } else {
            xmlSchemaPIllegalAttrErr(ctxt, XML_SCHEMAP_S4S_ATTR_NOT_ALLOWED, NULL, attr);
        }
    }
    if (name == NULL) {
        xmlSchemaCustomErr(ACTXT_CAST ctxt, XML_SCHEMAP_NOTATION_NO_NAME,
            node, NULL, "A notation declaration requires a name", NULL, NULL);
    }
    if (identifiers == 0) {
        xmlSchemaCustomErr(ACTXT_CAST ctxt, XML_SCHEMAP_S4S_ATTR_MISSING,
            node, NULL, "A notation declaration requires a public or system identifier", NULL, NULL);
    }
    if (ctxt->nberrors != errors) {
        return NULL;
    }
    /* NCName uses collapsed whitespace. Validation does not replace the
     * dictionary's lexical string, so intern the validated trimmed name. */
    {
        const xmlChar *start = name, *end;
        while (IS_BLANK_CH(*start)) {
            ++start;
        }
        end = start + xmlStrlen(start);
        while (end > start && IS_BLANK_CH(end[-1])) {
            --end;
        }
        if (start != name || *end != 0) {
            name = xmlDictLookup(ctxt->dict, start, (int) (end - start));
            if (name == NULL) {
                xmlSchemaPErrMemory(ctxt);
                return NULL;
            }
        }
    }
    result = xmlSchemaAddNotation(ctxt, schema, name, ctxt->targetNamespace, node);
    if (result == NULL) {
        return NULL;
    }
    child = node->children;
    if (IS_SCHEMA(child, "annotation")) {
        result->annot = xmlSchemaParseAnnotation(ctxt, child, 1);
        child = child->next;
    }
    if (child != NULL) {
        xmlSchemaPContentErr(ctxt, XML_SCHEMAP_S4S_ELEM_NOT_ALLOWED,
            NULL, node, child, NULL, "(annotation?)");
    }
    return result;
}
