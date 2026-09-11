/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 cos-element-consistent after substitution membership resolution.
 * Each model has its own declaration scope; element types are separate models.
 * The iterative walk visits shared components once and never expands counts.
 */
static int
xmlSchemaEdcDeclaration(xmlSchemaUpaSchema *scope, xmlSchemaElementPtr declaration) {
    const xmlChar *ns = declaration->targetNamespace;
    xmlSchemaElementPtr previous;
    if (ns != NULL && ns[0] == 0) {
        ns = NULL;
    }
    previous = xmlHashLookup2(scope->names, declaration->name, ns);
    if (previous != NULL) {
        xmlSchemaTypePtr type = declaration->subtypes;
        /* Repeated references to one declaration do not introduce a second
         * declaration, including a global element with an anonymous type. */
        if (previous == declaration || (type != NULL && previous->subtypes == type
                && (WXS_TYPE_IS_GLOBAL(type) || type->type == XML_SCHEMA_TYPE_BASIC))) {
            return 0;
        }
        /* libxml2 has no dedicated cos-element-consistent error code. */
        xmlSchemaPCustomErr(scope->parser, XML_SCHEMAP_FAILED_PARSE,
            WXS_BASIC_CAST declaration, declaration->node,
            "cos-element-consistent: declarations with the same expanded name have inconsistent type definitions", NULL);
        return 1;
    }
    if (xmlHashAddEntry2(scope->names, declaration->name, ns, declaration) < 0) {
        scope->context.memory.failed = 1;
        return -1;
    }
    return 0;
}

static int
xmlSchemaEdcElement(xmlSchemaUpaSchema *scope, xmlSchemaElementPtr declaration) {
    int result = xmlSchemaEdcDeclaration(scope, declaration);
    if (result != 0) {
        return result;
    }
    if (declaration->flags & XML_SCHEMAS_ELEM_SUBST_GROUP_HEAD) {
        xmlSchemaSubstGroupPtr group = xmlSchemaSubstGroupGet(scope->parser, declaration);
        if (group != NULL) {
            for (int index = 0; index < group->members->nbItems; ++index) {
                xmlSchemaElementPtr member = group->members->items[index];
                if (!(member->flags & XML_SCHEMAS_ELEM_ABSTRACT)) {
                    result = xmlSchemaEdcDeclaration(scope, member);
                    if (result != 0) {
                        return result;
                    }
                }
            }
        }
    }
    return 0;
}

static int
xmlSchemaCheckElementConsistency(xmlSchemaParserCtxtPtr parser, xmlSchemaTreeItemPtr root) {
    xmlSchemaUpaSchema scope = {0};
    xmlSchemaUpaNode *node;
    int result = 0;
    scope.parser = parser;
    scope.nodes = xmlSchemaUpaNewTable(&scope.context);
    scope.names = xmlSchemaUpaNewTable(&scope.context);
    if (scope.context.memory.failed) {
        result = -1;
        goto done;
    }
    node = xmlSchemaUpaGetNode(&scope, root);
    if (node == NULL) {
        result = -1;
        goto done;
    }
    while (node != NULL) {
        xmlSchemaTypeType kind = node->item->type;
        if (node->status == 0) {
            node->status = 1;
            switch (kind) {
                case XML_SCHEMA_TYPE_PARTICLE:
                    if (((xmlSchemaParticlePtr)node->item)->maxOccurs != 0) {
                        node->cursor = node->item->children;
                    }
                    break;
                case XML_SCHEMA_TYPE_GROUP:
                case XML_SCHEMA_TYPE_SEQUENCE:
                case XML_SCHEMA_TYPE_CHOICE:
                case XML_SCHEMA_TYPE_ALL:
                    node->cursor = node->item->children;
                    break;
                case XML_SCHEMA_TYPE_ELEMENT:
                    result = xmlSchemaEdcElement(&scope, (xmlSchemaElementPtr)node->item);
                    if (result != 0) {
                        goto done;
                    }
                    break;
                case XML_SCHEMA_TYPE_ANY:
                    break;
                default:
                    xmlSchemaPCustomErr(parser, XML_SCHEMAP_INTERNAL,
                        WXS_BASIC_CAST node->item, WXS_ITEM_NODE(node->item),
                        "Unexpected component in element declaration consistency", NULL);
                    result = 1;
                    goto done;
            }
        }
        if (node->cursor != NULL) {
            xmlSchemaUpaNode *child = xmlSchemaUpaGetNode(&scope, node->cursor);
            if (child == NULL) {
                result = -1;
                goto done;
            }
            if (child->status == 1) {
                xmlSchemaPCustomErr(parser, XML_SCHEMAP_INTERNAL,
                    WXS_BASIC_CAST node->item, WXS_ITEM_NODE(node->item),
                    "Cyclic component in element declaration consistency", NULL);
                result = 1;
                goto done;
            }
            if (child->status == 0) {
                child->parent = node;
                node = child;
                continue;
            }
            node->cursor = kind == XML_SCHEMA_TYPE_PARTICLE || kind == XML_SCHEMA_TYPE_GROUP
                ? NULL : node->cursor->next;
        } else {
            node->status = 2;
            node = node->parent;
        }
    }
done:
    if (result < 0) {
        xmlSchemaPErrMemory(parser);
    }
    xmlSchemaUpaCleanup(&scope.context);
    return result;
}
