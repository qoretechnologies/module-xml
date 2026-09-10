/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Exact component attribution before content-model automaton reduction.
 * Included in xmlschemas.c after native model construction helpers.
 */
static int xmlSchemaCheckCVCWildcardNamespace(xmlSchemaWildcardPtr wild, const xmlChar *ns);

typedef struct _xmlSchemaUpaNode xmlSchemaUpaNode;
struct _xmlSchemaUpaNode {
    xmlSchemaTreeItemPtr item;
    xmlSchemaUpaNode *parent;
    xmlSchemaTreeItemPtr cursor;
    xmlSchemaUpaInfo info;
    const xmlSchemaUpaInt *minimum;
    const xmlSchemaUpaInt *maximum;
    int status;
    int allNullable;
    int allEmpty;
};
typedef struct {
    xmlSchemaUpaContext context;
    xmlSchemaParserCtxtPtr parser;
    xmlHashTablePtr nodes;
    xmlHashTablePtr names;
    xmlHashTablePtr wildcards;
    size_t termCount;
} xmlSchemaUpaSchema;

static xmlHashTablePtr
xmlSchemaUpaNewTable(xmlSchemaUpaContext *context) {
    xmlSchemaUpaMap *owner = xmlSchemaUpaAllocate(&context->memory, sizeof(*owner), 0);
    if (owner == NULL) {
        return NULL;
    }
    owner->table = xmlHashCreate(0);
    if (owner->table == NULL) {
        context->memory.failed = 1;
        return NULL;
    }
    owner->ownerNext = context->maps;
    context->maps = owner;
    return owner->table;
}

static int
xmlSchemaUpaPointerKey(xmlSchemaUpaContext *context, char *key, size_t size, const void *pointer) {
    int length = snprintf(key, size, "%p", pointer);
    if (length < 0 || (size_t)length >= size) {
        context->memory.failed = 1;
        return -1;
    }
    return 0;
}

static xmlSchemaUpaTerm *
xmlSchemaUpaSchemaTerm(xmlSchemaUpaSchema *schema, const xmlChar *name,
                       const xmlChar *namespaceName, xmlSchemaWildcardPtr wildcard) {
    char pointerKey[32 + 2 * sizeof(void*)];
    xmlHashTablePtr table = wildcard == NULL ? schema->names : schema->wildcards;
    xmlSchemaUpaTerm *term;
    int length;
    if (namespaceName != NULL && namespaceName[0] == 0) {
        namespaceName = NULL;
    }
    if (wildcard != NULL) {
        if (xmlSchemaUpaPointerKey(&schema->context, pointerKey, sizeof(pointerKey), wildcard) < 0) {
            return NULL;
        }
        name = BAD_CAST pointerKey;
        namespaceName = NULL;
    }
    term = xmlHashLookup2(table, name, namespaceName);
    if (term != NULL) {
        return term;
    }
    term = xmlSchemaUpaAllocate(&schema->context.memory, sizeof(*term), 0);
    if (term == NULL || schema->termCount == SIZE_MAX) {
        schema->context.memory.failed = 1;
        return NULL;
    }
    length = snprintf((char *)term->key, sizeof(term->key), "%zu", schema->termCount++);
    if (length < 0 || (size_t)length >= sizeof(term->key)) {
        schema->context.memory.failed = 1;
        return NULL;
    }
    term->name = wildcard == NULL ? name : NULL;
    term->namespaceName = namespaceName;
    term->wildcard = wildcard;
    if (xmlHashAddEntry2(table, name, namespaceName, term) < 0) {
        schema->context.memory.failed = 1;
        return NULL;
    }
    return term;
}

static int
xmlSchemaUpaSchemaOverlap(void *data ATTRIBUTE_UNUSED, const xmlSchemaUpaTerm *left,
                          const xmlSchemaUpaTerm *right) {
    xmlSchemaWildcardPtr a = left->wildcard, b = right->wildcard;
    if (a == NULL && b == NULL) {
        return xmlStrEqual(left->name, right->name)
            && xmlStrEqual(left->namespaceName, right->namespaceName);
    }
    if (a == NULL) {
        return xmlSchemaCheckCVCWildcardNamespace(b, left->namespaceName) == 0;
    }
    if (b == NULL) {
        return xmlSchemaCheckCVCWildcardNamespace(a, right->namespaceName) == 0;
    }
    if (a->nsSet != NULL) {
        for (xmlSchemaWildcardNsPtr ns = a->nsSet; ns != NULL; ns = ns->next) {
            if (xmlSchemaCheckCVCWildcardNamespace(b, ns->value) == 0) {
                return 1;
            }
        }
        return 0;
    }
    if (b->nsSet != NULL) {
        for (xmlSchemaWildcardNsPtr ns = b->nsSet; ns != NULL; ns = ns->next) {
            if (xmlSchemaCheckCVCWildcardNamespace(a, ns->value) == 0) {
                return 1;
            }
        }
        return 0;
    }
    return 1;
}

static xmlSchemaUpaNode *
xmlSchemaUpaGetNode(xmlSchemaUpaSchema *schema, xmlSchemaTreeItemPtr item) {
    char key[32 + 2 * sizeof(void*)];
    xmlSchemaUpaNode *node;
    if (xmlSchemaUpaPointerKey(&schema->context, key, sizeof(key), item) < 0) {
        return NULL;
    }
    node = xmlHashLookup(schema->nodes, BAD_CAST key);
    if (node != NULL) {
        return node;
    }
    node = xmlSchemaUpaAllocate(&schema->context.memory, sizeof(*node), 0);
    if (node == NULL) {
        return NULL;
    }
    node->item = item;
    if (xmlHashAddEntry(schema->nodes, BAD_CAST key, node) < 0) {
        schema->context.memory.failed = 1;
        return NULL;
    }
    return node;
}

/* Copied base particles retain their original source for exact finite counts. */
static const xmlSchemaUpaInt *
xmlSchemaUpaOccurrence(xmlSchemaUpaSchema *schema, xmlSchemaParticlePtr particle, int maximum) {
    xmlSchemaParticlePtr source = particle->countSource != NULL ? particle->countSource : particle;
    xmlAttrPtr attribute = xmlSchemaGetPropNode(source->node, maximum ? "maxOccurs" : "minOccurs");
    xmlChar *allocated = NULL;
    const xmlChar *lexical;
    const char *start, *end;
    char buffer[32];
    int negative = 0;
    xmlSchemaUpaInt *value;
    if (attribute == NULL) {
        int count = maximum ? source->maxOccurs : source->minOccurs;
        if (maximum && count == UNBOUNDED) {
            return NULL;
        }
        snprintf(buffer, sizeof(buffer), "%d", count);
        lexical = BAD_CAST buffer;
    } else {
        allocated = xmlNodeGetContent((xmlNodePtr)attribute);
        if (allocated == NULL) {
            schema->context.memory.failed = 1;
            return NULL;
        }
        lexical = allocated;
    }
    start = (const char *)lexical;
    while (IS_BLANK_CH(*start)) {
        ++start;
    }
    end = start + strlen(start);
    while (end > start && IS_BLANK_CH(end[-1])) {
        --end;
    }
    if (maximum && end - start == 9 && memcmp(start, "unbounded", 9) == 0) {
        xmlFree(allocated);
        return NULL;
    }
    if (start < end && (*start == '+' || *start == '-')) {
        negative = *start == '-';
        ++start;
    }
    value = xmlSchemaUpaDecimalInt(&schema->context.memory, start, (size_t)(end - start));
    xmlFree(allocated);
    if (value != NULL && negative && xmlSchemaUpaCompareInt(value, schema->context.zeroInt) != 0) {
        schema->context.memory.failed = 1;
        return NULL;
    }
    return value;
}

static void
xmlSchemaUpaElementNames(xmlSchemaUpaSchema *schema, xmlSchemaUpaInfo *info, xmlSchemaElementPtr declaration) {
    xmlSchemaUpaTerm *term;
    if (!(declaration->flags & XML_SCHEMAS_ELEM_ABSTRACT)) {
        term = xmlSchemaUpaSchemaTerm(schema, declaration->name, declaration->targetNamespace, NULL);
        if (term == NULL) {
            return;
        }
        xmlSchemaUpaPut(&schema->context, &info->first, term, schema->context.zero);
    }
    if (declaration->flags & XML_SCHEMAS_ELEM_SUBST_GROUP_HEAD) {
        xmlSchemaSubstGroupPtr group = xmlSchemaSubstGroupGet(schema->parser, declaration);
        if (group != NULL) {
            for (int index = 0; index < group->members->nbItems; ++index) {
                xmlSchemaElementPtr member = group->members->items[index];
                if (!(member->flags & XML_SCHEMAS_ELEM_ABSTRACT)) {
                    term = xmlSchemaUpaSchemaTerm(schema, member->name, member->targetNamespace, NULL);
                    if (term == NULL) {
                        return;
                    }
                    xmlSchemaUpaPut(&schema->context, &info->first, term, schema->context.zero);
                }
                if (schema->context.memory.failed) {
                    return;
                }
            }
        }
    }
    info->empty = info->first == NULL;
    info->ratio = schema->context.one;
}

static int
xmlSchemaUpaVisit(xmlSchemaUpaSchema *schema, xmlSchemaTreeItemPtr root) {
    xmlSchemaUpaNode *node = xmlSchemaUpaGetNode(schema, root);
    if (node == NULL) {
        return -1;
    }
    if (node->status == 2) {
        return 0;
    }
    while (node != NULL) {
        xmlSchemaTypeType kind = node->item->type;
        if (node->status == 0) {
            node->status = 1;
            switch (kind) {
                case XML_SCHEMA_TYPE_PARTICLE:
                    node->minimum = xmlSchemaUpaOccurrence(schema, (xmlSchemaParticlePtr)node->item, 0);
                    node->maximum = xmlSchemaUpaOccurrence(schema, (xmlSchemaParticlePtr)node->item, 1);
                    if (schema->context.memory.failed) {
                        return -1;
                    }
                    if (node->maximum != NULL
                            && xmlSchemaUpaCompareInt(node->minimum, node->maximum) > 0) {
                        xmlSchemaPCustomErr(schema->parser, XML_SCHEMAP_P_PROPS_CORRECT_2_1,
                            WXS_BASIC_CAST node->item, WXS_ITEM_NODE(node->item),
                            "The minimum occurrence count exceeds the maximum occurrence count", NULL);
                        return 1;
                    }
                    if (node->maximum != NULL
                            && xmlSchemaUpaCompareInt(node->maximum, schema->context.zeroInt) == 0) {
                        node->info.nullable = 1;
                    } else {
                        node->cursor = node->item->children;
                        if (node->cursor == NULL) {
                            node->info.nullable = 1;
                        }
                    }
                    break;
                case XML_SCHEMA_TYPE_SEQUENCE:
                    node->info.nullable = 1;
                    node->cursor = node->item->children;
                    break;
                case XML_SCHEMA_TYPE_CHOICE:
                case XML_SCHEMA_TYPE_ALL:
                    node->info.empty = 1;
                    node->allNullable = 1;
                    node->cursor = node->item->children;
                    break;
                case XML_SCHEMA_TYPE_GROUP:
                    node->cursor = node->item->children;
                    node->info.nullable = node->cursor == NULL;
                    break;
                case XML_SCHEMA_TYPE_ELEMENT:
                    xmlSchemaUpaElementNames(schema, &node->info, (xmlSchemaElementPtr)node->item);
                    break;
                case XML_SCHEMA_TYPE_ANY: {
                    xmlSchemaUpaTerm *term = xmlSchemaUpaSchemaTerm(schema, NULL, NULL,
                        (xmlSchemaWildcardPtr)node->item);
                    if (term == NULL) {
                        return -1;
                    }
                    schema->context.hasWildcards = 1;
                    xmlSchemaUpaPut(&schema->context, &node->info.first, term, schema->context.zero);
                    node->info.ratio = schema->context.one;
                    break;
                }
                default:
                    xmlSchemaPCustomErr(schema->parser, XML_SCHEMAP_INTERNAL,
                        WXS_BASIC_CAST node->item, WXS_ITEM_NODE(node->item),
                        "Unexpected component in particle attribution", NULL);
                    return 1;
            }
        }
        if (schema->context.memory.failed) {
            return -1;
        }
        if (node->cursor != NULL) {
            xmlSchemaUpaNode *child = xmlSchemaUpaGetNode(schema, node->cursor);
            if (child == NULL) {
                return -1;
            }
            if (child->status == 1) {
                xmlSchemaPCustomErr(schema->parser, XML_SCHEMAP_INTERNAL,
                    WXS_BASIC_CAST node->item, WXS_ITEM_NODE(node->item),
                    "Cyclic component in particle attribution", NULL);
                return 1;
            }
            if (child->status == 0) {
                child->parent = node;
                node = child;
                continue;
            }
            if (kind == XML_SCHEMA_TYPE_PARTICLE) {
                ((xmlSchemaParticlePtr)node->item)->termNullable = child->info.nullable;
                node->info = xmlSchemaUpaRepeat(&schema->context, &child->info, node->minimum, node->maximum);
                node->cursor = NULL;
            } else if (kind == XML_SCHEMA_TYPE_GROUP) {
                node->info = xmlSchemaUpaCopyInfo(&schema->context, &child->info);
                node->cursor = NULL;
            } else {
                xmlSchemaUpaCombine(&schema->context, &node->info, &child->info, kind != XML_SCHEMA_TYPE_SEQUENCE);
                node->allNullable = node->allNullable && child->info.nullable;
                node->allEmpty = node->allEmpty || child->info.empty;
                node->cursor = node->cursor->next;
            }
            continue;
        }
        if (kind == XML_SCHEMA_TYPE_ALL) {
            node->info.empty = node->allEmpty;
            node->info.nullable = node->allNullable;
        }
        if (xmlSchemaUpaApplies(node->info.plain)) {
            xmlSchemaPCustomErr(schema->parser, XML_SCHEMAP_NOT_DETERMINISTIC,
                WXS_BASIC_CAST node->item, WXS_ITEM_NODE(node->item),
                "The content model violates unique particle attribution", NULL);
            return 1;
        }
        node->status = 2;
        node = node->parent;
    }
    return 0;
}

static int
xmlSchemaCheckParticleAttributions(xmlSchemaParserCtxtPtr parser, xmlSchemaTreeItemPtr *items, int count) {
    xmlSchemaUpaSchema schema = {0};
    int result = 0;
    schema.parser = parser;
    schema.context.overlap = xmlSchemaUpaSchemaOverlap;
    if (xmlSchemaUpaInit(&schema.context) < 0) {
        result = -1;
        goto done;
    }
    schema.nodes = xmlSchemaUpaNewTable(&schema.context);
    schema.names = xmlSchemaUpaNewTable(&schema.context);
    schema.wildcards = xmlSchemaUpaNewTable(&schema.context);
    if (schema.context.memory.failed) {
        result = -1;
        goto done;
    }
    for (int index = 0; index < count; ++index) {
        xmlSchemaTreeItemPtr root = NULL;
        if (items[index]->type == XML_SCHEMA_TYPE_COMPLEX) {
            xmlSchemaTypePtr type = (xmlSchemaTypePtr)items[index];
            if (type->contentType == XML_SCHEMA_CONTENT_ELEMENTS || type->contentType == XML_SCHEMA_CONTENT_MIXED) {
                root = (xmlSchemaTreeItemPtr)WXS_TYPE_PARTICLE(type);
            }
        } else if (items[index]->type == XML_SCHEMA_TYPE_GROUP) {
            root = items[index];
        }
        if (root != NULL) {
            result = xmlSchemaUpaVisit(&schema, root);
            if (result != 0) {
                break;
            }
        }
    }
done:
    if (result < 0) {
        xmlSchemaPErrMemory(parser);
    }
    xmlSchemaUpaCleanup(&schema.context);
    return result;
}
