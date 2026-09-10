/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Exact native counter bounds and fixed-capacity execution values.
 * Include after libxml2-particle-counter-lexical.inc.
 */
#include <stdint.h>
#include <limits.h>

#define XML_REG_COUNT_BASE UINT32_C(1000000000)

typedef struct {
    size_t size;
    size_t offset;
    int unbounded;
    /* Two equally sized little-endian values: minimum, then finite maximum. */
    uint32_t digits[];
} xmlRegCountBounds;

static int
xmlRegCountCompare(const uint32_t *left, const uint32_t *right, size_t size) {
    for (size_t index = size; index > 0; --index) {
        if (left[index - 1] != right[index - 1]) {
            return left[index - 1] < right[index - 1] ? -1 : 1;
        }
    }
    return 0;
}

static void
xmlRegCountRead(uint32_t *digits, const xmlRegCountLexical *source) {
    size_t length = source->length, index = 0;
    while (length != 0) {
        size_t begin = length > 9 ? length - 9 : 0;
        uint32_t value = 0;
        for (size_t offset = begin; offset < length; ++offset) {
            value = value * 10 + (source->digits[offset] - '0');
        }
        digits[index++] = value;
        length = begin;
    }
}

/* Remove the first occurrence already emitted by the native model builder.
 * The effective minimum saturates at zero, but a finite maximum must cover it.
 */
static int
xmlRegCountSubtractFirst(uint32_t *digits, size_t size, int minimum) {
    for (size_t index = 0; index < size; ++index) {
        if (digits[index] != 0) {
            --digits[index];
            for (size_t low = 0; low < index; ++low) {
                digits[low] = XML_REG_COUNT_BASE - 1;
            }
            return 0;
        }
    }
    return minimum ? 0 : -1;
}

static xmlRegCountBounds *
xmlRegCountNewBounds(const char *minimum, const char *maximum, int firstEmitted, int nullable) {
    xmlRegCountLexical low, high;
    xmlRegCountBounds *bounds;
    size_t length, size, bytes;
    if ((firstEmitted != 0 && firstEmitted != 1)
            || xmlRegCountParse(minimum, 0, &low) < 0
            || xmlRegCountParse(maximum, 1, &high) < 0
            || xmlRegCountCompareLexical(&low, &high) > 0) {
        return NULL;
    }
    if (nullable && xmlRegCountParse("0", 0, &low) < 0) {
        return NULL;
    }
    length = low.length > high.length ? low.length : high.length;
    size = length / 9 + (length % 9 != 0);
    if (size == 0 || size > (SIZE_MAX - sizeof(*bounds)) / (2 * sizeof(uint32_t))) {
        return NULL;
    }
    bytes = sizeof(*bounds) + size * 2 * sizeof(uint32_t);
    bounds = xmlMalloc(bytes);
    if (bounds == NULL) {
        return NULL;
    }
    memset(bounds, 0, bytes);
    bounds->size = size;
    bounds->unbounded = high.unbounded;
    xmlRegCountRead(bounds->digits, &low);
    if (!high.unbounded) {
        xmlRegCountRead(bounds->digits + size, &high);
    }
    if (firstEmitted) {
        xmlRegCountSubtractFirst(bounds->digits, size, 1);
        if (!high.unbounded && xmlRegCountSubtractFirst(bounds->digits + size, size, 0) < 0) {
            xmlFree(bounds);
            return NULL;
        }
    }
    return bounds;
}

static int
xmlRegCountCanIncrement(const xmlRegCountBounds *bounds, const uint32_t *value) {
    return bounds->unbounded || xmlRegCountCompare(value, bounds->digits + bounds->size, bounds->size) < 0;
}

static int
xmlRegCountInRange(const xmlRegCountBounds *bounds, const uint32_t *value) {
    return xmlRegCountCompare(value, bounds->digits, bounds->size) >= 0
        && (bounds->unbounded || xmlRegCountCompare(value, bounds->digits + bounds->size, bounds->size) <= 0);
}

/* For an unbounded counter, all values at/above the minimum are equivalent.
 * Saturating there is exact and prevents overflow on arbitrarily long streams.
 * Finite counters retain their exact value through the inclusive maximum.
 */
static int
xmlRegCountIncrement(const xmlRegCountBounds *bounds, uint32_t *value) {
    if (!xmlRegCountCanIncrement(bounds, value)) {
        return -1;
    }
    if (bounds->unbounded && xmlRegCountCompare(value, bounds->digits, bounds->size) >= 0) {
        return 0;
    }
    for (size_t index = 0; index < bounds->size; ++index) {
        if (++value[index] < XML_REG_COUNT_BASE) {
            return 0;
        }
        value[index] = 0;
    }
    return -1;
}

static int
xmlRegCountAsInt(const uint32_t *value, size_t size, int *result) {
    uint64_t total = 0;
    for (size_t index = size; index > 0; --index) {
        if (total > ((uint64_t)INT_MAX - value[index - 1]) / XML_REG_COUNT_BASE) {
            return -1;
        }
        total = total * XML_REG_COUNT_BASE + value[index - 1];
    }
    *result = (int)total;
    return 0;
}
