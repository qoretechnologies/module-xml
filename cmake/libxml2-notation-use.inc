/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 Part 2 3.2.19: NOTATION uses require an enumeration-derived type.
 * Intermediate atomic restrictions may remain unused until later restriction.
 */
static int
qoreXmlNotationPush(xmlSchemaItemListPtr pending, xmlSchemaTypePtr type,
                    xmlNodePtr node) {
    if (type == NULL) {
        return 0;
    }
    if (xmlSchemaItemListAdd(pending, type) < 0 ||
        xmlSchemaItemListAdd(pending, node) < 0) {
        return -1;
    }
    return 0;
}

/* Cached base-axis assessment prevents shared restriction chains from being
 * traversed once per declaration. Cache payloads are immutable status markers. */
static int
qoreXmlNotationAtomic(xmlSchemaTypePtr type, xmlHashTablePtr cache,
                       xmlSchemaItemListPtr path) {
    static const char states[3] = {0, 1, 2};
    xmlSchemaTypePtr base = type;
    int state = 0; /* other primitive, unrestricted NOTATION, enumerated NOTATION */
    path->nbItems = 0;
    while (base != NULL) {
        const char *cached;
        char key[2 * sizeof(void *) + 16];
        int length = snprintf(key, sizeof(key), "%p", (void *) base);
        if (length < 0 || (size_t) length >= sizeof(key)) {
            return -1;
        }
        cached = (const char *) xmlHashLookup(cache, BAD_CAST key);
        if (cached != NULL) {
            state = (int) (cached - states);
            break;
        }
        if (base->type == XML_SCHEMA_TYPE_BASIC) {
            state = base->builtInType == XML_SCHEMAS_NOTATION ? 1 : 0;
            break;
        }
        if (xmlSchemaItemListAdd(path, base) < 0) {
            return -1;
        }
        base = base->baseType;
    }
    while (path->nbItems != 0) {
        char key[2 * sizeof(void *) + 16];
        int length;
        base = (xmlSchemaTypePtr) path->items[--path->nbItems];
        if (state == 1) {
            xmlSchemaFacetPtr facet;
            for (facet = base->facets; facet != NULL; facet = facet->next) {
                if (facet->type == XML_SCHEMA_FACET_ENUMERATION) {
                    state = 2;
                    break;
                }
            }
        }
        length = snprintf(key, sizeof(key), "%p", (void *) base);
        if (length < 0 || (size_t) length >= sizeof(key) ||
            xmlHashAddEntry(cache, BAD_CAST key, (void *) &states[state]) < 0) {
            return -1;
        }
    }
    return state == 1;
}

static int
qoreXmlCheckNotationUses(xmlSchemaParserCtxtPtr ctxt,
                         xmlSchemaTreeItemPtr *items, int count) {
    xmlSchemaItemListPtr pending = NULL;
    xmlHashTablePtr visited = NULL, atomic = NULL;
    xmlSchemaItemListPtr path = NULL;
    int result = -1;
    int i;

    pending = xmlSchemaItemListCreate();
    visited = xmlHashCreate(0);
    atomic = xmlHashCreate(0);
    path = xmlSchemaItemListCreate();
    if (pending == NULL || visited == NULL || atomic == NULL || path == NULL) {
        goto memory_error;
    }
    for (i = 0; i < count; ++i) {
        xmlSchemaTreeItemPtr item = items[i];
        xmlSchemaTypePtr type = NULL;
        xmlNodePtr node = NULL;
        if (item->type == XML_SCHEMA_TYPE_ELEMENT) {
            xmlSchemaElementPtr element = (xmlSchemaElementPtr) item;
            type = WXS_ELEM_TYPEDEF(element);
            node = element->node;
        } else if (item->type == XML_SCHEMA_TYPE_ATTRIBUTE) {
            xmlSchemaAttributePtr attribute = (xmlSchemaAttributePtr) item;
            type = WXS_ATTR_TYPEDEF(attribute);
            node = attribute->node;
        } else if (item->type == XML_SCHEMA_TYPE_SIMPLE) {
            type = (xmlSchemaTypePtr) item;
            if (!WXS_IS_LIST(type) && !WXS_IS_UNION(type)) {
                continue;
            }
            node = type->node;
        }
        if (qoreXmlNotationPush(pending, type, node) < 0) {
            goto memory_error;
        }
    }
    while (pending->nbItems != 0) {
        xmlNodePtr node = (xmlNodePtr) pending->items[--pending->nbItems];
        xmlSchemaTypePtr type = (xmlSchemaTypePtr) pending->items[--pending->nbItems];
        int status;
        char key[2 * sizeof(void *) + 16];
        int length;

        if (WXS_IS_COMPLEX(type)) {
            type = type->contentTypeDef;
            if (type == NULL) {
                continue;
            }
        }
        /* Pointer keys retain component identity even for anonymous definitions. */
        length = snprintf(key, sizeof(key), "%p", (void *) type);
        if (length < 0 || (size_t) length >= sizeof(key)) {
            goto memory_error;
        }
        if (xmlHashLookup(visited, BAD_CAST key) != NULL) {
            continue;
        }
        if (xmlHashAddEntry(visited, BAD_CAST key, type) < 0) {
            goto memory_error;
        }
        if (WXS_IS_LIST(type)) {
            if (qoreXmlNotationPush(pending, type->subtypes, node) < 0) {
                goto memory_error;
            }
            continue;
        }
        if (WXS_IS_UNION(type)) {
            xmlSchemaTypeLinkPtr member;
            if (type->memberTypes == NULL) {
                if (qoreXmlNotationPush(pending, type->baseType, node) < 0) {
                    goto memory_error;
                }
            }
            for (member = type->memberTypes;
                 member != NULL; member = member->next) {
                if (qoreXmlNotationPush(pending, member->type, node) < 0) {
                    goto memory_error;
                }
            }
            continue;
        }
        status = qoreXmlNotationAtomic(type, atomic, path);
        if (status < 0) {
            goto memory_error;
        }
        if (status != 0) {
            xmlSchemaCustomErr(ACTXT_CAST ctxt,
                XML_SCHEMAP_S4S_ATTR_INVALID_VALUE, node, NULL,
                "A NOTATION type used by a declaration, list or union "
                "must be derived with an enumeration facet", NULL, NULL);
            result = ctxt->err;
            goto done;
        }
    }
    result = 0;
    goto done;

memory_error:
    xmlSchemaPErrMemory(ctxt);
done:
    xmlHashFree(atomic, NULL);
    xmlSchemaItemListFree(path);
    xmlHashFree(visited, NULL);
    xmlSchemaItemListFree(pending);
    return result;
}
