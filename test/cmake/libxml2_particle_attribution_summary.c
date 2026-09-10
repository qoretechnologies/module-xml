/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Unit driver for postorder expression graphs, independent of schema parsing.
 */
#include <libxml/xmlmemory.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../../cmake/libxml2-particle-attribution-math.inc"
#include "../../cmake/libxml2-particle-attribution-sets.inc"
typedef struct {
    xmlSchemaUpaInfo info;
    unsigned left, right;
    char kind;
    int absent, present;
} TestNode;
static int run_case(unsigned count) {
    xmlSchemaUpaContext context = {0};
    xmlSchemaUpaTerm a = {.name = BAD_CAST "a", .key = "a"};
    xmlSchemaUpaTerm b = {.name = BAD_CAST "b", .key = "b"};
    TestNode *nodes;
    int accepted = 1, code = 2;
    if (count == 0 || count > 4096) {
        return 2;
    }
    nodes = calloc(count, sizeof(*nodes));
    if (nodes == NULL) {
        return 2;
    }
    if (xmlSchemaUpaInit(&context) < 0) {
        goto done;
    }
    for (unsigned index = 0; index < count; ++index) {
        char minimum[1024], maximum[1024];
        TestNode *node = &nodes[index];
        if (scanf(" %c %u %u %1023s %1023s", &node->kind, &node->left, &node->right, minimum, maximum) != 5) {
            goto done;
        }
        if (node->kind == 'a' || node->kind == 'b') {
            node->info.ratio = context.one;
            xmlSchemaUpaPut(&context, &node->info.first, node->kind == 'a' ? &a : &b, context.zero);
        } else if (node->kind == '0') {
            node->info.nullable = 1;
        } else if (node->kind == 'e') {
            node->info.empty = 1;
        } else if (node->left >= index || ((node->kind == 's' || node->kind == 'c') && node->right >= index)) {
            goto done;
        } else if (node->kind == 's' || node->kind == 'c') {
            node->info = xmlSchemaUpaCopyInfo(&context, &nodes[node->left].info);
            xmlSchemaUpaCombine(&context, &node->info, &nodes[node->right].info, node->kind == 'c');
        } else if (node->kind == 'r') {
            xmlSchemaUpaInt *low = xmlSchemaUpaDecimalInt(&context.memory, minimum, strlen(minimum));
            xmlSchemaUpaInt *high = strcmp(maximum, "u") == 0 ? NULL
                : xmlSchemaUpaDecimalInt(&context.memory, maximum, strlen(maximum));
            if (context.memory.failed || (high != NULL && xmlSchemaUpaCompareInt(low, high) > 0)) {
                goto done;
            }
            node->absent = high != NULL && xmlSchemaUpaCompareInt(high, context.zeroInt) == 0;
            node->info = xmlSchemaUpaRepeat(&context, &nodes[node->left].info, low, high);
        } else {
            goto done;
        }
        if (context.memory.failed) {
            goto done;
        }
    }
    nodes[count - 1].present = 1;
    for (unsigned index = count; index > 0; --index) {
        TestNode *node = &nodes[index - 1];
        if (!node->present) {
            continue;
        }
        if (xmlSchemaUpaApplies(node->info.plain)) {
            accepted = 0;
        }
        if (node->kind == 's' || node->kind == 'c' || (node->kind == 'r' && !node->absent)) {
            nodes[node->left].present = 1;
        }
        if (node->kind == 's' || node->kind == 'c') {
            nodes[node->right].present = 1;
        }
    }
    printf("%d\n", accepted);
    code = 0;
done:
    xmlSchemaUpaCleanup(&context);
    free(nodes);
    return code;
}
int main(void) {
    unsigned count;
    int status;
    while ((status = scanf("%u", &count)) == 1) {
        if (run_case(count) != 0) {
            return 2;
        }
    }
    return status == EOF && !ferror(stdin) ? 0 : 2;
}
