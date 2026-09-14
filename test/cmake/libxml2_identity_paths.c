/* Copyright (C) 2026 Qore Technologies, s.r.o. */
#include <libxml/parser.h>
#include <libxml/pattern.h>
#include <libxml/dict.h>
#include <stdio.h>

int main(void) {
    static const struct {
        const char *path;
        int valid;
    } cases[] = {
        {NULL, 0}, {"", 0}, {" ", 0}, {"row|", 0}, {"row|other|", 0},
        {"row| |other", 0}, {"row||other", 0}, {"|row", 0},
        {"row", 1}, {"row|other", 1}, {"row | other", 1}
    };
    static const int modes[] = {XML_PATTERN_DEFAULT, XML_PATTERN_XPATH,
                               XML_PATTERN_XSSEL, XML_PATTERN_XSFIELD};
    unsigned int i, j;
    int use_dict;
    int checks = 0;
    xmlInitParser();
    for (use_dict = 0; use_dict < 2; ++use_dict) {
        xmlDict *dict = use_dict ? xmlDictCreate() : NULL;
        if (use_dict && dict == NULL) {
            return 1;
        }
        for (i = 0; i < sizeof(cases) / sizeof(cases[0]); ++i) {
            for (j = 0; j < sizeof(modes) / sizeof(modes[0]); ++j) {
                xmlPattern *pattern = NULL;
                int status = xmlPatternCompileSafe((const xmlChar *) cases[i].path, dict, modes[j], NULL, &pattern);
                int valid = status == 0 && pattern != NULL;
                if (valid != cases[i].valid || (!cases[i].valid && (status != 1 || pattern != NULL))) {
                    fprintf(stderr, "pattern case %u mode %d dictionary %d: status %d\n",
                            i, modes[j], use_dict, status);
                    xmlFreePattern(pattern);
                    xmlDictFree(dict);
                    xmlCleanupParser();
                    return 1;
                }
                xmlFreePattern(pattern);
                ++checks;
            }
        }
        xmlDictFree(dict);
    }
    xmlCleanupParser();
    printf("identity path syntax and recovery: %d checks passed\n", checks);
    return 0;
}
