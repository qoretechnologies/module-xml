/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * The four built-in instance attributes participate in identity assessment
 * independently of ordinary attribute uses and the owner's content variety. */
static int
xmlSchemaVInstanceAttributes(xmlSchemaValidCtxtPtr vctxt)
{
    int i, result = 0;
    for (i = 0; i < vctxt->nbAttrInfos; i++) {
        xmlSchemaAttrInfoPtr attr = vctxt->attrInfos[i];
        int matched, ret;
        switch (attr->metaType) {
            case XML_SCHEMA_ATTR_INFO_META_XSI_TYPE:
                attr->typeDef = xmlSchemaGetBuiltInType(XML_SCHEMAS_QNAME);
                break;
            case XML_SCHEMA_ATTR_INFO_META_XSI_NIL:
                attr->typeDef = xmlSchemaGetBuiltInType(XML_SCHEMAS_BOOLEAN);
                break;
            case XML_SCHEMA_ATTR_INFO_META_XSI_SCHEMA_LOC:
                if (vctxt->xsiLocationType.type == 0) {
                    vctxt->xsiLocationType.type = XML_SCHEMA_TYPE_SIMPLE;
                    vctxt->xsiLocationType.flags = XML_SCHEMAS_TYPE_VARIETY_LIST;
                    vctxt->xsiLocationType.baseType = xmlSchemaGetBuiltInType(XML_SCHEMAS_ANYSIMPLETYPE);
                    vctxt->xsiLocationType.subtypes = xmlSchemaGetBuiltInType(XML_SCHEMAS_ANYURI);
                }
                attr->typeDef = &vctxt->xsiLocationType;
                break;
            case XML_SCHEMA_ATTR_INFO_META_XSI_NO_NS_SCHEMA_LOC:
                attr->typeDef = xmlSchemaGetBuiltInType(XML_SCHEMAS_ANYURI);
                break;
            default:
                continue;
        }
        ACTIVATE_ATTRIBUTE(attr);
        matched = vctxt->xpathStates == NULL ? 0 : xmlSchemaXPathEvaluate(vctxt, XML_ATTRIBUTE_NODE);
        if (matched < 0) {
            result = -1;
            break;
        }
        /* xsi:nil may already own its value from element assessment. Reuse it. */
        ret = attr->val != NULL ? 0 : xmlSchemaVCheckCVCSimpleType(ACTXT_CAST vctxt,
            attr->node, attr->typeDef, attr->value, matched ? &attr->val : NULL, 1, 1, 0);
        if (ret < 0) {
            result = -1;
            break;
        }
        if (matched && (ret == 0)) {
            ret = xmlSchemaXPathProcessHistory(vctxt, vctxt->depth + 1);
        } else if (vctxt->xpathStates != NULL) {
            if (matched) {
                xmlSchemaIDCStateObjPtr state;
                /* Invalid values have no key. Discard their recorded field
                 * matches before popping the stream states; stale history
                 * would keep a field active past its selector's lifetime. */
                for (state = vctxt->xpathStates; state != NULL; state = state->next) {
                    if (state->nbHistory != 0 &&
                            state->history[state->nbHistory - 1] == vctxt->depth + 1) {
                        state->nbHistory--;
                    }
                }
            }
            ret = xmlSchemaXPathPop(vctxt);
        }
        if (ret < 0) {
            result = -1;
            break;
        }
    }
    ACTIVATE_ELEM;
    return result;
}
