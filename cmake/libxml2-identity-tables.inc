/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 3.11.5: inherited conflicts are absent; local entries take precedence.
 * Entries borrow keys and selected nodes owned by the validation context.
 */
static int
xmlSchemaIDCEqualTuples(xmlSchemaPSVIIDCNodePtr a,
                       xmlSchemaPSVIIDCNodePtr b, int count)
{
    int i;
    for (i = 0; i < count; i++) {
        int ret = xmlSchemaAreValuesEqual(a->keys[i]->val, b->keys[i]->val);
        if (ret != 1) {
            return ret;
        }
    }
    return 1;
}

static int
xmlSchemaIDCFillNodeTables(xmlSchemaValidCtxtPtr vctxt,
                          xmlSchemaNodeInfoPtr ielem)
{
    xmlSchemaIDCMatcherPtr matcher;
    for (matcher = ielem->idcMatchers; matcher != NULL; matcher = matcher->next) {
        xmlSchemaPSVIIDCBindingPtr bind;
        int i, fields, inherited;
        if ((matcher->aidc->def->type == XML_SCHEMA_TYPE_IDC_KEYREF) ||
            WXS_ILIST_IS_EMPTY(matcher->targets)) {
            continue;
        }
        if ((!vctxt->createIDCNodeTables) &&
            ((matcher->aidc->keyrefDepth == -1) ||
             (matcher->aidc->keyrefDepth > vctxt->depth))) {
            continue;
        }
        bind = xmlSchemaIDCAcquireBinding(vctxt, matcher);
        if (bind == NULL) {
            xmlSchemaVErrMemory(vctxt);
            return -1;
        }
        if ((bind->nbNodes == 0) && WXS_ILIST_IS_EMPTY(bind->dupls)) {
            xmlFree(bind->nodeTable);
            bind->nodeTable = (xmlSchemaPSVIIDCNodePtr *)matcher->targets->items;
            bind->sizeNodes = matcher->targets->sizeItems;
            bind->nbNodes = matcher->targets->nbItems;
            matcher->targets->items = NULL;
            matcher->targets->sizeItems = 0;
            matcher->targets->nbItems = 0;
            if (matcher->htab != NULL) {
                xmlHashFree(matcher->htab, xmlFreeIDCHashEntry);
                matcher->htab = NULL;
            }
            continue;
        }
        fields = matcher->aidc->def->nbFields;
        inherited = bind->nbNodes;
        for (i = 0; i < matcher->targets->nbItems; i++) {
            xmlSchemaPSVIIDCNodePtr node = matcher->targets->items[i];
            int j, found = 0;
            /* Local uniqueness was checked while collecting matcher targets.
             * A local entry supersedes every inherited conflicting candidate. */
            if (bind->dupls != NULL) {
                for (j = 0; j < bind->dupls->nbItems;) {
                    int ret = xmlSchemaIDCEqualTuples(node, bind->dupls->items[j], fields);
                    if (ret < 0) {
                        return -1;
                    }
                    if (ret == 1) {
                        bind->dupls->items[j] = bind->dupls->items[--bind->dupls->nbItems];
                    } else {
                        j++;
                    }
                }
            }
            for (j = 0; j < inherited; j++) {
                int ret = xmlSchemaIDCEqualTuples(node, bind->nodeTable[j], fields);
                if (ret < 0) {
                    return -1;
                }
                if (ret == 1) {
                    bind->nodeTable[j] = node;
                    found = 1;
                    break;
                }
            }
            if ((!found) && (xmlSchemaIDCAppendNodeTableItem(vctxt, bind, node) < 0)) {
                return -1;
            }
        }
    }
    return 0;
}

static int
xmlSchemaIDCInheritNode(xmlSchemaValidCtxtPtr vctxt,
                       xmlSchemaPSVIIDCBindingPtr bind, xmlSchemaPSVIIDCNodePtr node,
                       int *inherited, int conflicts)
{
    int j, fields = bind->definition->nbFields;
    if (bind->dupls != NULL) {
        for (j = 0; j < conflicts; j++) {
            int ret = xmlSchemaIDCEqualTuples(node, bind->dupls->items[j], fields);
            if (ret < 0) {
                return -1;
            }
            if (ret == 1) {
                return 0;
            }
        }
    }
    for (j = 0; j < *inherited; j++) {
        xmlSchemaPSVIIDCNodePtr previous = bind->nodeTable[j];
        int ret = xmlSchemaIDCEqualTuples(node, previous, fields);
        if (ret < 0) {
            return -1;
        }
        if (ret == 0) {
            continue;
        }
        if (bind->dupls == NULL) {
            bind->dupls = xmlSchemaItemListCreate();
            if (bind->dupls == NULL) {
                xmlSchemaVErrMemory(vctxt);
                return -1;
            }
        }
        if (xmlSchemaItemListAdd(bind->dupls, previous) < 0) {
            xmlSchemaVErrMemory(vctxt);
            return -1;
        }
        /* Keep the preexisting entries in a prefix. The child table is
         * already unique, so comparing its newly appended entries is both
         * unnecessary and quadratic when the receiving table starts empty. */
        bind->nodeTable[j] = bind->nodeTable[--*inherited];
        --bind->nbNodes;
        if (*inherited != bind->nbNodes) {
            bind->nodeTable[*inherited] = bind->nodeTable[bind->nbNodes];
        }
        return 0;
    }
    /* An earlier conflict can leave an empty table; distinct later values
     * must still be appended. */
    return xmlSchemaIDCAppendNodeTableItem(vctxt, bind, node);
}

static int
xmlSchemaBubbleIDCNodeTables(xmlSchemaValidCtxtPtr vctxt)
{
    xmlSchemaPSVIIDCBindingPtr bind;
    xmlSchemaPSVIIDCBindingPtr *parent = &vctxt->elemInfos[vctxt->depth - 1]->idcTable;
    for (bind = vctxt->inode->idcTable; bind != NULL; bind = bind->next) {
        xmlSchemaPSVIIDCBindingPtr target;
        xmlSchemaIDCAugPtr aidc;
        int i, inherited, conflicts, needed = vctxt->createIDCNodeTables;
        if (bind->nbNodes == 0) {
            continue;
        }
        for (aidc = vctxt->aidcs; (!needed) && (aidc != NULL); aidc = aidc->next) {
            if (aidc->def == bind->definition) {
                needed = (aidc->keyrefDepth != -1) && (aidc->keyrefDepth < vctxt->depth);
                break;
            }
        }
        if (!needed) {
            continue;
        }
        for (target = *parent; target != NULL; target = target->next) {
            if (target->definition == bind->definition) {
                break;
            }
        }
        if (target == NULL) {
            target = xmlSchemaIDCNewBinding(bind->definition);
            if (target == NULL) {
                xmlSchemaVErrMemory(vctxt);
                return -1;
            }
            /* Publish before appending so failure cleanup owns every allocation. */
            target->next = *parent;
            *parent = target;
        }
        inherited = target->nbNodes;
        conflicts = target->dupls == NULL ? 0 : target->dupls->nbItems;
        for (i = 0; i < bind->nbNodes; i++) {
            if (xmlSchemaIDCInheritNode(vctxt, target, bind->nodeTable[i], &inherited, conflicts) < 0) {
                return -1;
            }
        }
        /* Do not propagate bind->dupls: those entries are already absent from
         * this child's node table. Conflicts among siblings belong to parent. */
    }
    return 0;
}
