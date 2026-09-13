/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Namespace lookup has an explicit status and borrows namespace storage only
 * until the caller copies it. Default lexicals use their declaration scope;
 * ENTITY checks and instance identity owners keep their document context.
 */
static int
qoreXmlLookupNamespace(xmlSchemaValidCtxtPtr vctxt, xmlNodePtr declaration,
                       const xmlChar *prefix, const xmlChar **uri) {
    xmlNodePtr node = declaration;
    xmlNsPtr ns = NULL;
    *uri = NULL;
    if (xmlStrEqual(prefix, BAD_CAST "xml")) {
        *uri = XML_XML_NAMESPACE;
        return 0;
    }
    if (vctxt != NULL && node == NULL) {
        node = vctxt->defaultNamespaceNode;
        if (node == NULL && vctxt->sax != NULL) {
            int i, j;
            for (i = vctxt->depth; i >= 0; --i) {
                xmlSchemaNodeInfoPtr info = vctxt->elemInfos[i];
                for (j = 0; j < info->nbNsBindings; ++j) {
                    if (xmlStrEqual(prefix, info->nsBindings[j * 2])) {
                        const xmlChar *found = info->nsBindings[j * 2 + 1];
                        *uri = found != NULL && found[0] != 0 ? found : NULL;
                        return 0;
                    }
                }
            }
            return 0;
        }
#ifdef LIBXML_READER_ENABLED
        if (node == NULL && vctxt->reader != NULL) {
            node = xmlTextReaderCurrentNode(vctxt->reader);
        }
#endif
        if (node == NULL && vctxt->inode != NULL) {
            node = vctxt->inode->node;
        }
    }
    if (node == NULL) {
        return -1;
    }
    if (node->type == XML_ATTRIBUTE_NODE) {
        node = node->parent;
    }
    if (xmlSearchNsSafe(node, prefix, &ns) < 0) {
        return -1;
    }
    if (ns != NULL && ns->href != NULL && ns->href[0] != 0) {
        *uri = ns->href;
    }
    return 0;
}

static int
qoreXmlValidateScopedQName(xmlSchemaValidCtxtPtr vctxt, xmlNodePtr node,
                           xmlSchemaPtr schema, const xmlChar *text,
                           xmlSchemaValPtr *value, int needed, int notation) {
    xmlChar *prefix = NULL, *local = NULL;
    const xmlChar *uri = NULL;
    int ret = qoreXmlQNameParts(text, &prefix, &local);
    if (value != NULL) {
        *value = NULL;
    }
    if (ret == 0) {
        ret = qoreXmlLookupNamespace(vctxt, node, prefix, &uri);
    }
    if (ret == 0 && prefix != NULL && uri == NULL) {
        ret = 1;
    }
    if (ret == 0 && notation && xmlSchemaGetNotation(schema, local, uri) == NULL) {
        ret = 1;
    }
    if (ret == 0 && needed && value != NULL) {
        *value = qoreXmlQNameValue(uri, local, notation);
        if (*value == NULL) {
            ret = -1;
        }
    }
    xmlFree(prefix);
    xmlFree(local);
    return ret;
}
