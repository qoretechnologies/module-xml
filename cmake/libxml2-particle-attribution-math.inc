/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Exact positive rational arithmetic for counted particle attribution.
 * Included by the private schema checker; no public libxml2 API is added.
 */
#include <stdint.h>
#include <stddef.h>
#include <string.h>

#define XML_SCHEMA_UPA_BASE UINT64_C(1000000000)

typedef union _xmlSchemaUpaBlock xmlSchemaUpaBlock;
union _xmlSchemaUpaBlock {
    xmlSchemaUpaBlock *next;
    uint64_t alignment;
};
typedef struct {
    xmlSchemaUpaBlock *blocks;
    int failed;
} xmlSchemaUpaMemory;
typedef struct {
    size_t size;
    uint32_t digit[];
} xmlSchemaUpaInt;
typedef struct {
    const xmlSchemaUpaInt *numerator;
    const xmlSchemaUpaInt *denominator;
} xmlSchemaUpaRatio;

static void *
xmlSchemaUpaAllocate(xmlSchemaUpaMemory *memory, size_t bytes, int temporary) {
    xmlSchemaUpaBlock *block;
    if (memory->failed || bytes > SIZE_MAX - sizeof(*block)) {
        memory->failed = 1;
        return NULL;
    }
    block = xmlMalloc(sizeof(*block) + bytes);
    if (block == NULL) {
        memory->failed = 1;
        return NULL;
    }
    if (!temporary) {
        block->next = memory->blocks;
        memory->blocks = block;
    }
    memset(block + 1, 0, bytes);
    return block + 1;
}

static void
xmlSchemaUpaFreeTemporary(void *pointer) {
    if (pointer != NULL) {
        xmlFree((xmlSchemaUpaBlock *)pointer - 1);
    }
}

static void
xmlSchemaUpaFreeMemory(xmlSchemaUpaMemory *memory) {
    while (memory->blocks != NULL) {
        xmlSchemaUpaBlock *block = memory->blocks;
        memory->blocks = block->next;
        xmlFree(block);
    }
}

static xmlSchemaUpaInt *
xmlSchemaUpaNewInt(xmlSchemaUpaMemory *memory, size_t size, int temporary) {
    xmlSchemaUpaInt *value;
    if (size == 0 || size > (SIZE_MAX - sizeof(*value)) / sizeof(value->digit[0])) {
        memory->failed = 1;
        return NULL;
    }
    value = xmlSchemaUpaAllocate(memory, sizeof(*value) + size * sizeof(value->digit[0]), temporary);
    if (value != NULL) {
        value->size = size;
    }
    return value;
}

static void
xmlSchemaUpaNormalizeInt(xmlSchemaUpaInt *value) {
    while (value->size > 1 && value->digit[value->size - 1] == 0) {
        --value->size;
    }
}

static xmlSchemaUpaInt *
xmlSchemaUpaDecimalInt(xmlSchemaUpaMemory *memory, const char *source, size_t length) {
    size_t offset = 0;
    xmlSchemaUpaInt *value;
    if (length == 0) {
        memory->failed = 1;
        return NULL;
    }
    value = xmlSchemaUpaNewInt(memory, length / 9 + (length % 9 != 0), 0);
    if (value == NULL) {
        return NULL;
    }
    while (length != 0) {
        size_t begin = length > 9 ? length - 9 : 0;
        uint32_t digit = 0;
        for (size_t index = begin; index < length; ++index) {
            if (source[index] < '0' || source[index] > '9') {
                memory->failed = 1;
                return NULL;
            }
            digit = digit * 10 + (source[index] - '0');
        }
        value->digit[offset++] = digit;
        length = begin;
    }
    xmlSchemaUpaNormalizeInt(value);
    return value;
}

static int
xmlSchemaUpaCompareInt(const xmlSchemaUpaInt *left, const xmlSchemaUpaInt *right) {
    if (left->size != right->size) {
        return left->size < right->size ? -1 : 1;
    }
    for (size_t index = left->size; index > 0; --index) {
        if (left->digit[index - 1] != right->digit[index - 1]) {
            return left->digit[index - 1] < right->digit[index - 1] ? -1 : 1;
        }
    }
    return 0;
}

static xmlSchemaUpaInt *
xmlSchemaUpaMultiplyInt(xmlSchemaUpaMemory *memory, const xmlSchemaUpaInt *left,
                       const xmlSchemaUpaInt *right, int temporary) {
    xmlSchemaUpaInt *value;
    if (left->size > SIZE_MAX - right->size) {
        memory->failed = 1;
        return NULL;
    }
    value = xmlSchemaUpaNewInt(memory, left->size + right->size, temporary);
    if (value == NULL) {
        return NULL;
    }
    for (size_t i = 0; i < left->size; ++i) {
        uint64_t carry = 0;
        for (size_t j = 0; j < right->size; ++j) {
            uint64_t total = value->digit[i + j] + (uint64_t)left->digit[i] * right->digit[j] + carry;
            value->digit[i + j] = total % XML_SCHEMA_UPA_BASE;
            carry = total / XML_SCHEMA_UPA_BASE;
        }
        value->digit[i + right->size] = carry;
    }
    xmlSchemaUpaNormalizeInt(value);
    return value;
}

static xmlSchemaUpaInt *
xmlSchemaUpaSubtractInt(xmlSchemaUpaMemory *memory, const xmlSchemaUpaInt *left,
                       const xmlSchemaUpaInt *right) {
    xmlSchemaUpaInt *value;
    int64_t borrow = 0;
    if (xmlSchemaUpaCompareInt(left, right) < 0) {
        memory->failed = 1;
        return NULL;
    }
    value = xmlSchemaUpaNewInt(memory, left->size, 0);
    if (value == NULL) {
        return NULL;
    }
    for (size_t index = 0; index < left->size; ++index) {
        int64_t digit = (int64_t)left->digit[index]
            - (index < right->size ? right->digit[index] : 0) - borrow;
        borrow = digit < 0;
        value->digit[index] = digit + (borrow ? (int64_t)XML_SCHEMA_UPA_BASE : 0);
    }
    xmlSchemaUpaNormalizeInt(value);
    return value;
}

static xmlSchemaUpaRatio *
xmlSchemaUpaNewRatio(xmlSchemaUpaMemory *memory, const xmlSchemaUpaInt *numerator,
                    const xmlSchemaUpaInt *denominator) {
    xmlSchemaUpaRatio *ratio;
    if (numerator == NULL || denominator == NULL
            || (denominator->size == 1 && denominator->digit[0] == 0)) {
        memory->failed = 1;
        return NULL;
    }
    ratio = xmlSchemaUpaAllocate(memory, sizeof(*ratio), 0);
    if (ratio != NULL) {
        ratio->numerator = numerator;
        ratio->denominator = denominator;
    }
    return ratio;
}

/* Cross-products are temporary and freed immediately, including failure paths. */
static int
xmlSchemaUpaCompareRatio(xmlSchemaUpaMemory *memory, const xmlSchemaUpaRatio *left,
                        const xmlSchemaUpaRatio *right) {
    xmlSchemaUpaInt *a = xmlSchemaUpaMultiplyInt(memory, left->numerator, right->denominator, 1);
    xmlSchemaUpaInt *b = xmlSchemaUpaMultiplyInt(memory, right->numerator, left->denominator, 1);
    int result = (a != NULL && b != NULL) ? xmlSchemaUpaCompareInt(a, b) : 0;
    xmlSchemaUpaFreeTemporary(a);
    xmlSchemaUpaFreeTemporary(b);
    return result;
}
