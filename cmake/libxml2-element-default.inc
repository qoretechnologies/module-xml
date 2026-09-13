/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 cvc-elt 5.1.1/5.1.2; approved canonical-actual-type identity.
 * Keep declaration metadata and instance document ownership unchanged.
 */
static int
qoreXmlValidateElementDefault(xmlSchemaValidCtxtPtr vctxt) {
    xmlSchemaNodeInfoPtr inode = vctxt->inode;
    xmlNodePtr previous = vctxt->defaultNamespaceNode;
    xmlChar *canonical = NULL;
    const xmlChar *lexical;
    int ret = qoreXmlNumericDefaultLexical(inode->decl->defVal,
                                          inode->decl->value, &canonical);
    if (ret < 0) {
        return -1;
    }
    lexical = canonical != NULL ? canonical : inode->decl->value;
    vctxt->defaultNamespaceNode = inode->decl->node;
    if (inode->flags & XML_SCHEMA_ELEM_INFO_LOCAL_TYPE) {
        ret = xmlSchemaCheckCOSValidDefault(vctxt, lexical, &(inode->val));
    } else if (WXS_IS_SIMPLE(inode->typeDef)) {
        ret = xmlSchemaVCheckINodeDataType(vctxt, inode, inode->typeDef, lexical);
    } else if (WXS_HAS_SIMPLE_CONTENT(inode->typeDef)) {
        ret = xmlSchemaVCheckINodeDataType(vctxt, inode, inode->typeDef->contentTypeDef, lexical);
    }
    vctxt->defaultNamespaceNode = previous;
    xmlFree(canonical);
    return ret;
}
