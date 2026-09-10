/* Copyright (C) 2026 Qore Technologies, s.r.o. */
#include <libxml/xmlmemory.h>
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include "../../cmake/libxml2-particle-counter-lexical.inc"
#include "../../cmake/libxml2-particle-counter-values.inc"

static void print_value(const uint32_t *value, size_t size) {
    while (size > 1 && value[size - 1] == 0) {
        --size;
    }
    printf("%u", value[size - 1]);
    while (--size != 0) {
        printf("%09u", value[size - 1]);
    }
}

int main(int argc, char **argv) {
    xmlRegCountBounds *bounds = NULL;
    xmlRegCountLexical initial;
    uint32_t *value = NULL;
    unsigned long steps, advanced = 0;
    char *end;
    int code = 2, small;
    if (argc != 7 || (strcmp(argv[3], "0") != 0 && strcmp(argv[3], "1") != 0)
            || (strcmp(argv[4], "0") != 0 && strcmp(argv[4], "1") != 0)) {
        return 2;
    }
    errno = 0;
    steps = strtoul(argv[6], &end, 10);
    if (errno || end == argv[6] || *end || steps > 100) {
        return 2;
    }
    bounds = xmlRegCountNewBounds(argv[1], argv[2], argv[3][0] == '1', argv[4][0] == '1');
    if (bounds == NULL || xmlRegCountParse(argv[5], 0, &initial) < 0) {
        goto done;
    }
    value = xmlMalloc(bounds->size * sizeof(*value));
    if (value == NULL) {
        goto done;
    }
    memset(value, 0, bounds->size * sizeof(*value));
    if (initial.length / 9 + (initial.length % 9 != 0) > bounds->size) {
        if (!bounds->unbounded) {
            goto done;
        }
        memcpy(value, bounds->digits, bounds->size * sizeof(*value));
    } else {
        xmlRegCountRead(value, &initial);
        if (bounds->unbounded && xmlRegCountCompare(value, bounds->digits, bounds->size) > 0) {
            memcpy(value, bounds->digits, bounds->size * sizeof(*value));
        }
        if (!bounds->unbounded && xmlRegCountCompare(value, bounds->digits + bounds->size, bounds->size) > 0) {
            goto done;
        }
    }
    for (; advanced < steps; ++advanced) {
        if (xmlRegCountIncrement(bounds, value) < 0) {
            break;
        }
    }
    print_value(bounds->digits, bounds->size);
    putchar(' ');
    if (bounds->unbounded) {
        putchar('u');
    } else {
        print_value(bounds->digits + bounds->size, bounds->size);
    }
    putchar(' ');
    print_value(value, bounds->size);
    printf(" %lu %d %d ", advanced, xmlRegCountCanIncrement(bounds, value), xmlRegCountInRange(bounds, value));
    if (xmlRegCountAsInt(bounds->digits, bounds->size, &small) == 0) {
        printf("%d ", small);
    } else {
        printf("wide ");
    }
    if (!bounds->unbounded && xmlRegCountAsInt(bounds->digits + bounds->size, bounds->size, &small) == 0) {
        printf("%d\n", small);
    } else {
        printf("wide\n");
    }
    code = 0;
done:
    xmlFree(value);
    xmlFree(bounds);
    return code;
}
