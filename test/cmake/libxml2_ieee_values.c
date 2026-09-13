/* Copyright (C) 2026 Qore Technologies, s.r.o. */
#ifdef NDEBUG
#undef NDEBUG
#endif
#include QORE_XML_TYPES_SOURCE
#include <assert.h>
#include <fenv.h>
#include <inttypes.h>
#include <locale.h>
#include <stdio.h>
#include <string.h>

/* The Python oracle supplies XML lexicals and independently calculates the
 * expected IEEE bits. Read private computed values only in this test driver. */
int main(int argc, char **argv) {
    static const int modes[] = {FE_TONEAREST, FE_DOWNWARD, FE_UPWARD, FE_TOWARDZERO};
    char line[8192];
    fenv_t environment;
    size_t row = 0;
    int status = 0;
    if (argc > 2 || (argc == 2 && setlocale(LC_NUMERIC, argv[1]) == NULL)) {
        return 2;
    }
    assert(feholdexcept(&environment) == 0);
    xmlSchemaInitTypes();
    while (fgets(line, sizeof(line), stdin) != NULL) {
        size_t length = strlen(line);
        int wide;
        unsigned int mode;
        if (length < 3 || line[length - 1] != '\n' || line[1] != '\t'
                || (line[0] != '0' && line[0] != '1')) {
            status = 2;
            break;
        }
        line[length - 1] = 0;
        wide = line[0] == '1';
        for (mode = 0; mode < sizeof(modes) / sizeof(modes[0]); ++mode) {
            xmlSchemaTypePtr type = xmlSchemaGetPredefinedType(BAD_CAST (wide ? "double" : "float"),
                BAD_CAST "http://www.w3.org/2001/XMLSchema");
            xmlSchemaValPtr value = NULL;
            const xmlChar *canonical = NULL;
            uint64_t bits = 0;
            int lexical, computed, formatted = -1, flags;
            assert(fesetround(modes[mode]) == 0);
            assert(feclearexcept(FE_ALL_EXCEPT) == 0);
            assert(feraiseexcept(FE_DIVBYZERO) == 0);
            flags = fetestexcept(FE_ALL_EXCEPT);
            lexical = xmlSchemaValidatePredefinedType(type, BAD_CAST (line + 2), NULL);
            computed = xmlSchemaValidatePredefinedType(type, BAD_CAST (line + 2), &value);
            if (value != NULL) {
                formatted = xmlSchemaGetCanonValue(value, &canonical);
                if (wide) {
                    memcpy(&bits, &value->value.d, sizeof(bits));
                } else {
                    uint32_t narrow;
                    memcpy(&narrow, &value->value.f, sizeof(narrow));
                    bits = narrow;
                }
            }
            assert(fegetround() == modes[mode]);
            assert(fetestexcept(FE_ALL_EXCEPT) == flags);
            printf("%zu\t%u\t%d\t%d\t%d\t%016" PRIx64 "\t%s\n", row, mode,
                lexical, computed, formatted, bits, canonical == NULL ? "-" : (const char *)canonical);
            xmlFree((void *)canonical);
            xmlSchemaFreeValue(value);
        }
        ++row;
    }
    if (ferror(stdin)) {
        status = 2;
    }
    xmlCleanupParser();
    assert(fesetenv(&environment) == 0);
    return status;
}
