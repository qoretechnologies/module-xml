/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Exact nonNegativeInteger occurrence views; borrowed input, no allocation.
 */
#include <stddef.h>
#include <string.h>

typedef struct {
    const char *digits;
    size_t length;
    int unbounded;
} xmlRegCountLexical;

static int
xmlRegCountBlank(char value) {
    return value == ' ' || value == '\t' || value == '\r' || value == '\n';
}

static int
xmlRegCountParse(const char *source, int allowUnbounded, xmlRegCountLexical *value) {
    const char *start, *end;
    int negative = 0;
    memset(value, 0, sizeof(*value));
    if (source == NULL) {
        return -1;
    }
    start = source;
    while (xmlRegCountBlank(*start)) {
        ++start;
    }
    end = start + strlen(start);
    while (end > start && xmlRegCountBlank(end[-1])) {
        --end;
    }
    if (allowUnbounded && end - start == 9 && memcmp(start, "unbounded", 9) == 0) {
        value->unbounded = 1;
        return 0;
    }
    if (start < end && (*start == '+' || *start == '-')) {
        negative = *start == '-';
        ++start;
    }
    if (start == end) {
        return -1;
    }
    for (const char *cursor = start; cursor < end; ++cursor) {
        if (*cursor < '0' || *cursor > '9' || (negative && *cursor != '0')) {
            return -1;
        }
    }
    while (end - start > 1 && *start == '0') {
        ++start;
    }
    value->digits = start;
    value->length = (size_t)(end - start);
    return 0;
}

static int
xmlRegCountCompareLexical(const xmlRegCountLexical *left, const xmlRegCountLexical *right) {
    int result;
    if (left->unbounded || right->unbounded) {
        return left->unbounded - right->unbounded;
    }
    if (left->length != right->length) {
        return left->length < right->length ? -1 : 1;
    }
    result = memcmp(left->digits, right->digits, left->length);
    return (result > 0) - (result < 0);
}
