/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Sparse predicate sets and symbolic count thresholds for native attribution.
 * Included after the exact-arithmetic helper by the private schema checker.
 */
#include <libxml/hash.h>

typedef struct _xmlSchemaUpaTerm xmlSchemaUpaTerm;
struct _xmlSchemaUpaTerm {
    const xmlChar *name;
    const xmlChar *namespaceName;
    void *wildcard;
    xmlChar key[32];
};
typedef struct _xmlSchemaUpaEntry xmlSchemaUpaEntry;
struct _xmlSchemaUpaEntry {
    xmlSchemaUpaEntry *next;
    xmlSchemaUpaEntry *wildcardNext;
    xmlSchemaUpaTerm *term;
    const xmlSchemaUpaRatio *threshold;
};
typedef struct _xmlSchemaUpaMap xmlSchemaUpaMap;
struct _xmlSchemaUpaMap {
    xmlSchemaUpaMap *ownerNext;
    xmlHashTablePtr table;
    xmlSchemaUpaEntry *first;
    xmlSchemaUpaEntry *wildcards;
    size_t size;
};
typedef struct {
    xmlSchemaUpaMemory memory;
    xmlSchemaUpaMap *maps;
    const xmlSchemaUpaInt *zeroInt;
    const xmlSchemaUpaInt *oneInt;
    const xmlSchemaUpaRatio *zero;
    const xmlSchemaUpaRatio *one;
    int (*overlap)(void *, const xmlSchemaUpaTerm *, const xmlSchemaUpaTerm *);
    void *overlapData;
    int hasWildcards;
} xmlSchemaUpaContext;
typedef struct {
    int nullable;
    int empty;
    xmlSchemaUpaMap *first;
    xmlSchemaUpaMap *follow;
    const xmlSchemaUpaRatio *ratio;
    const xmlSchemaUpaRatio *plain;
    const xmlSchemaUpaRatio *continuing;
} xmlSchemaUpaInfo;

static int
xmlSchemaUpaInit(xmlSchemaUpaContext *context) {
    context->zeroInt = xmlSchemaUpaDecimalInt(&context->memory, "0", 1);
    context->oneInt = xmlSchemaUpaDecimalInt(&context->memory, "1", 1);
    context->zero = xmlSchemaUpaNewRatio(&context->memory, context->zeroInt, context->oneInt);
    context->one = xmlSchemaUpaNewRatio(&context->memory, context->oneInt, context->oneInt);
    return context->memory.failed ? -1 : 0;
}

static void
xmlSchemaUpaCleanup(xmlSchemaUpaContext *context) {
    for (xmlSchemaUpaMap *map = context->maps; map != NULL; map = map->ownerNext) {
        xmlHashFree(map->table, NULL);
    }
    context->maps = NULL;
    xmlSchemaUpaFreeMemory(&context->memory);
}

static const xmlSchemaUpaRatio *
xmlSchemaUpaMinimum(xmlSchemaUpaContext *context, const xmlSchemaUpaRatio *left,
                    const xmlSchemaUpaRatio *right) {
    if (left == NULL) {
        return right;
    }
    if (right == NULL || left == right) {
        return left;
    }
    return xmlSchemaUpaCompareRatio(&context->memory, left, right) <= 0 ? left : right;
}

static const xmlSchemaUpaRatio *
xmlSchemaUpaMaximum(xmlSchemaUpaContext *context, const xmlSchemaUpaRatio *left,
                    const xmlSchemaUpaRatio *right) {
    if (left == NULL || right == NULL) {
        return NULL;
    }
    return xmlSchemaUpaCompareRatio(&context->memory, left, right) >= 0 ? left : right;
}

static int
xmlSchemaUpaApplies(const xmlSchemaUpaRatio *threshold) {
    return threshold != NULL && xmlSchemaUpaCompareInt(threshold->numerator, threshold->denominator) <= 0;
}

static const xmlSchemaUpaRatio *
xmlSchemaUpaThreshold(xmlSchemaUpaContext *context, const xmlSchemaUpaInt *numerator,
                      const xmlSchemaUpaInt *denominator) {
    if (context->memory.failed || numerator == NULL || denominator == NULL
            || (denominator->size == 1 && denominator->digit[0] == 0)) {
        context->memory.failed = 1;
        return NULL;
    }
    if (xmlSchemaUpaCompareInt(numerator, denominator) <= 0) {
        return context->zero;
    }
    return xmlSchemaUpaNewRatio(&context->memory, numerator, denominator);
}

static const xmlSchemaUpaRatio *
xmlSchemaUpaScale(xmlSchemaUpaContext *context, const xmlSchemaUpaRatio *value,
                  const xmlSchemaUpaInt *count) {
    if (value == NULL) {
        return NULL;
    }
    if (count == NULL) {
        return context->zero;
    }
    return xmlSchemaUpaThreshold(context, value->numerator,
        xmlSchemaUpaMultiplyInt(&context->memory, value->denominator, count, 0));
}

static const xmlSchemaUpaRatio *
xmlSchemaUpaWithContext(xmlSchemaUpaContext *context, const xmlSchemaUpaRatio *value, int inherit) {
    return inherit ? value : xmlSchemaUpaApplies(value) ? context->zero : NULL;
}

static xmlSchemaUpaEntry *
xmlSchemaUpaLookup(const xmlSchemaUpaMap *map, const xmlSchemaUpaTerm *term) {
    return map == NULL ? NULL : xmlHashLookup(map->table, term->key);
}

static void
xmlSchemaUpaPut(xmlSchemaUpaContext *context, xmlSchemaUpaMap **target, xmlSchemaUpaTerm *term,
                const xmlSchemaUpaRatio *threshold) {
    xmlSchemaUpaMap *map = *target;
    xmlSchemaUpaEntry *entry;
    if (threshold == NULL || context->memory.failed) {
        return;
    }
    if (map == NULL) {
        map = xmlSchemaUpaAllocate(&context->memory, sizeof(*map), 0);
        if (map == NULL) {
            return;
        }
        map->table = xmlHashCreate(0);
        if (map->table == NULL) {
            context->memory.failed = 1;
            return;
        }
        map->ownerNext = context->maps;
        context->maps = map;
        *target = map;
    }
    entry = xmlSchemaUpaLookup(map, term);
    if (entry != NULL) {
        entry->threshold = xmlSchemaUpaMinimum(context, entry->threshold, threshold);
        return;
    }
    entry = xmlSchemaUpaAllocate(&context->memory, sizeof(*entry), 0);
    if (entry == NULL) {
        return;
    }
    entry->term = term;
    entry->threshold = threshold;
    if (xmlHashAddEntry(map->table, term->key, entry) < 0) {
        context->memory.failed = 1;
        return;
    }
    entry->next = map->first;
    map->first = entry;
    if (term->wildcard != NULL) {
        entry->wildcardNext = map->wildcards;
        map->wildcards = entry;
    }
    ++map->size;
}

static void
xmlSchemaUpaMerge(xmlSchemaUpaContext *context, xmlSchemaUpaMap **target,
                  const xmlSchemaUpaMap *source) {
    if (source != NULL) {
        for (const xmlSchemaUpaEntry *entry = source->first; entry != NULL; entry = entry->next) {
            xmlSchemaUpaPut(context, target, entry->term, entry->threshold);
            if (context->memory.failed) {
                return;
            }
        }
    }
}

static xmlSchemaUpaMap *
xmlSchemaUpaContexts(xmlSchemaUpaContext *context, const xmlSchemaUpaMap *source, int inherit) {
    xmlSchemaUpaMap *result = NULL;
    if (source != NULL) {
        for (const xmlSchemaUpaEntry *entry = source->first; entry != NULL; entry = entry->next) {
            xmlSchemaUpaPut(context, &result, entry->term,
                xmlSchemaUpaWithContext(context, entry->threshold, inherit));
            if (context->memory.failed) {
                return NULL;
            }
        }
    }
    return result;
}

static const xmlSchemaUpaRatio *
xmlSchemaUpaIntersection(xmlSchemaUpaContext *context, const xmlSchemaUpaMap *follow,
                         const xmlSchemaUpaMap *first) {
    const xmlSchemaUpaRatio *result = NULL;
    if (follow == NULL || first == NULL) {
        return NULL;
    }
    if (!context->hasWildcards) {
        const xmlSchemaUpaMap *smaller = follow->size < first->size ? follow : first;
        for (const xmlSchemaUpaEntry *entry = smaller->first; entry != NULL; entry = entry->next) {
            const xmlSchemaUpaEntry *found = xmlSchemaUpaLookup(follow, entry->term);
            if (found != NULL && xmlSchemaUpaLookup(first, entry->term) != NULL) {
                result = xmlSchemaUpaMinimum(context, result, found->threshold);
                if (context->memory.failed) {
                    return NULL;
                }
            }
        }
        return result;
    }
    for (const xmlSchemaUpaEntry *left = follow->first; left != NULL; left = left->next) {
        if (xmlSchemaUpaLookup(first, left->term) != NULL) {
            result = xmlSchemaUpaMinimum(context, result, left->threshold);
        }
        for (const xmlSchemaUpaEntry *right = left->term->wildcard != NULL ? first->first : first->wildcards;
                right != NULL; right = left->term->wildcard != NULL ? right->next : right->wildcardNext) {
            if (context->overlap(context->overlapData, left->term, right->term)) {
                result = xmlSchemaUpaMinimum(context, result, left->threshold);
            }
            if (context->memory.failed) {
                return NULL;
            }
        }
    }
    return result;
}

static xmlSchemaUpaInfo
xmlSchemaUpaCopyInfo(xmlSchemaUpaContext *context, const xmlSchemaUpaInfo *source) {
    xmlSchemaUpaInfo result = *source;
    result.first = NULL;
    result.follow = NULL;
    xmlSchemaUpaMerge(context, &result.first, source->first);
    xmlSchemaUpaMerge(context, &result.follow, source->follow);
    return result;
}

/* The accumulator owns its mutable maps; published child summaries are immutable. */
static void
xmlSchemaUpaCombine(xmlSchemaUpaContext *context, xmlSchemaUpaInfo *left,
                    const xmlSchemaUpaInfo *right, int choice) {
    xmlSchemaUpaInfo result = {0};
    const xmlSchemaUpaRatio *overlap, *base;
    const xmlSchemaUpaMap *lf, *rf;
    if (left->empty || right->empty) {
        if (choice) {
            if (left->empty) {
                *left = xmlSchemaUpaCopyInfo(context, right);
            }
        } else {
            memset(left, 0, sizeof(*left));
            left->empty = 1;
        }
        return;
    }
    overlap = xmlSchemaUpaIntersection(context, left->first, right->first);
    if (choice) {
        result.nullable = left->nullable || right->nullable;
        result.ratio = xmlSchemaUpaMaximum(context, left->ratio, right->ratio);
        result.plain = xmlSchemaUpaMinimum(context, overlap,
            xmlSchemaUpaMinimum(context, left->plain, right->plain));
        result.continuing = xmlSchemaUpaMinimum(context, overlap,
            xmlSchemaUpaMinimum(context, left->continuing, right->continuing));
        result.continuing = xmlSchemaUpaMinimum(context, result.continuing,
            xmlSchemaUpaMinimum(context, xmlSchemaUpaIntersection(context, left->follow, right->first),
                xmlSchemaUpaIntersection(context, right->follow, left->first)));
        xmlSchemaUpaMerge(context, &left->first, right->first);
        xmlSchemaUpaMerge(context, &left->follow, right->follow);
    } else {
        result.nullable = left->nullable && right->nullable;
        lf = right->nullable ? left->follow : xmlSchemaUpaContexts(context, left->follow, 0);
        rf = left->nullable ? right->follow : xmlSchemaUpaContexts(context, right->follow, 0);
        result.ratio = left->nullable ? (right->nullable ? NULL : right->ratio)
            : right->nullable ? left->ratio : context->one;
        base = xmlSchemaUpaMinimum(context, xmlSchemaUpaIntersection(context, lf, right->first),
            left->nullable ? overlap : NULL);
        result.plain = xmlSchemaUpaMinimum(context, base,
            xmlSchemaUpaMinimum(context, xmlSchemaUpaWithContext(context, left->plain, right->nullable),
                xmlSchemaUpaWithContext(context, right->plain, left->nullable)));
        result.continuing = xmlSchemaUpaMinimum(context, base,
            xmlSchemaUpaMinimum(context, xmlSchemaUpaWithContext(context,
                    right->nullable ? left->continuing : left->plain, right->nullable),
                xmlSchemaUpaWithContext(context, left->nullable ? right->continuing : right->plain,
                    left->nullable)));
        result.continuing = xmlSchemaUpaMinimum(context, result.continuing,
            xmlSchemaUpaMinimum(context, xmlSchemaUpaIntersection(context, rf, left->first),
                !left->nullable && right->nullable ? overlap : NULL));
        if (right->nullable) {
            xmlSchemaUpaMerge(context, &left->follow, right->first);
            xmlSchemaUpaMerge(context, &left->follow, rf);
        } else {
            left->follow = NULL;
            xmlSchemaUpaMerge(context, &left->follow, rf);
        }
        if (left->nullable) {
            xmlSchemaUpaMerge(context, &left->first, right->first);
        }
    }
    left->nullable = result.nullable;
    left->ratio = result.ratio;
    left->plain = result.plain;
    left->continuing = result.continuing;
}

static xmlSchemaUpaInfo
xmlSchemaUpaRepeat(xmlSchemaUpaContext *context, const xmlSchemaUpaInfo *child,
                   const xmlSchemaUpaInt *minimum, const xmlSchemaUpaInt *maximum) {
    xmlSchemaUpaInfo result = {0};
    const xmlSchemaUpaRatio *flexible = NULL;
    int zeroMinimum = xmlSchemaUpaCompareInt(minimum, context->zeroInt) == 0;
    if ((maximum != NULL && xmlSchemaUpaCompareInt(maximum, context->zeroInt) == 0)
            || (child->empty && zeroMinimum)) {
        result.nullable = 1;
        return result;
    }
    if (child->empty) {
        return xmlSchemaUpaCopyInfo(context, child);
    }
    if (child->nullable) {
        minimum = context->zeroInt;
        zeroMinimum = 1;
    }
    result = *child;
    result.first = NULL;
    result.follow = NULL;
    xmlSchemaUpaMerge(context, &result.first, child->first);
    if (context->memory.failed) {
        return result;
    }
    result.nullable = zeroMinimum || child->nullable;
    if (maximum != NULL && xmlSchemaUpaCompareInt(maximum, context->oneInt) == 0) {
        xmlSchemaUpaMerge(context, &result.follow, child->follow);
        if (zeroMinimum) {
            result.ratio = NULL;
        }
        return result;
    }
    result.follow = NULL;
    if (child->follow != NULL) {
        for (const xmlSchemaUpaEntry *entry = child->follow->first; entry != NULL; entry = entry->next) {
            xmlSchemaUpaPut(context, &result.follow, entry->term,
                xmlSchemaUpaScale(context, entry->threshold, maximum));
            if (context->memory.failed) {
                return result;
            }
        }
    }
    if (maximum == NULL || xmlSchemaUpaCompareInt(minimum, maximum) != 0 || child->ratio == NULL) {
        flexible = context->zero;
    } else if (xmlSchemaUpaCompareInt(child->ratio->numerator, child->ratio->denominator) > 0) {
        xmlSchemaUpaInt *difference = xmlSchemaUpaSubtractInt(&context->memory,
            child->ratio->numerator, child->ratio->denominator);
        if (context->memory.failed) {
            return result;
        }
        flexible = xmlSchemaUpaThreshold(context, child->ratio->numerator,
            xmlSchemaUpaMultiplyInt(&context->memory, difference, maximum, 0));
    }
    if (flexible != NULL && child->first != NULL) {
        for (const xmlSchemaUpaEntry *entry = child->first->first; entry != NULL; entry = entry->next) {
            xmlSchemaUpaPut(context, &result.follow, entry->term, flexible);
            if (context->memory.failed) {
                return result;
            }
        }
    }
    if (zeroMinimum || maximum == NULL || child->ratio == NULL) {
        result.ratio = NULL;
    } else if (xmlSchemaUpaCompareInt(minimum, maximum) != 0) {
        result.ratio = xmlSchemaUpaNewRatio(&context->memory,
            xmlSchemaUpaMultiplyInt(&context->memory, child->ratio->numerator, maximum, 0),
            xmlSchemaUpaMultiplyInt(&context->memory, child->ratio->denominator, minimum, 0));
    }
    result.plain = xmlSchemaUpaScale(context, child->continuing, maximum);
    result.continuing = result.plain;
    return result;
}
