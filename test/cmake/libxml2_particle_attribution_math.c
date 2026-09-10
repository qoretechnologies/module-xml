/* Copyright (C) 2026 Qore Technologies, s.r.o. */
#include <libxml/xmlmemory.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../../cmake/libxml2-particle-attribution-math.inc"
static void print(const xmlSchemaUpaInt *v) {
    printf("%u", v->digit[v->size - 1]);
    for (size_t index = v->size - 1; index > 0; --index) {
        printf("%09u", v->digit[index - 1]);
    }
    putchar('\n');
}
int main(int argc, char **argv) {
    xmlSchemaUpaMemory memory = {0};
    xmlSchemaUpaInt *a, *b, *c, *d, *result;
    int code = 0;
    if ((argc != 4 && argc != 6)
            || (argc == 4 && strcmp(argv[1], "compare") != 0 && strcmp(argv[1], "multiply") != 0
                && strcmp(argv[1], "subtract") != 0)
            || (argc == 6 && strcmp(argv[1], "ratio") != 0)) {
        return 2;
    }
    a = xmlSchemaUpaDecimalInt(&memory, argv[2], strlen(argv[2]));
    b = xmlSchemaUpaDecimalInt(&memory, argv[3], strlen(argv[3]));
    if (memory.failed) {
        code = 2;
        goto done;
    }
    if (argc == 6) {
        xmlSchemaUpaRatio *left, *right;
        c = xmlSchemaUpaDecimalInt(&memory, argv[4], strlen(argv[4]));
        d = xmlSchemaUpaDecimalInt(&memory, argv[5], strlen(argv[5]));
        left = xmlSchemaUpaNewRatio(&memory, a, b);
        right = xmlSchemaUpaNewRatio(&memory, c, d);
        if (!memory.failed) {
            int value = xmlSchemaUpaCompareRatio(&memory, left, right);
            if (!memory.failed) {
                printf("%d\n", value);
            }
        }
    } else if (strcmp(argv[1], "compare") == 0) {
        printf("%d\n", xmlSchemaUpaCompareInt(a, b));
    } else {
        result = strcmp(argv[1], "multiply") == 0
            ? xmlSchemaUpaMultiplyInt(&memory, a, b, 0) : xmlSchemaUpaSubtractInt(&memory, a, b);
        if (!memory.failed) {
            print(result);
        }
    }
    if (memory.failed) {
        code = 2;
    }
done:
    xmlSchemaUpaFreeMemory(&memory);
    return code;
}
