/* Copyright (C) 2026 Qore Technologies, s.r.o. */
#include <fenv.h>

static int check_ieee_values(void) {
    static const struct {
        const char *type, *lexical, *canonical;
    } values[] = {
        {"float", "0", "0.0E0"}, {"double", "-0", "0.0E0"},
        {"float", "0.1", "1.0E-1"}, {"double", "0.1", "1.0E-1"},
        {"float", "16777217", "1.6777216E7"},
        {"double", "1.2345678901234567", "1.2345678901234567E0"},
        {"float", "1e-45", "1.0E-45"}, {"double", "5e-324", "5.0E-324"},
        {"float", "1e999999999999999999999999999999", "INF"},
        {"double", "-1e-999999999999999999999999999999", "0.0E0"},
        {"float", "INF", "INF"}, {"double", "-INF", "-INF"},
        {"float", "NaN", "NaN"}, {"double", " \tNaN\r\n", "NaN"},
        {"float", "\t-INF\n", "-INF"}, {"double", "+.125e+1", "1.25E0"}
    };
    static const char *invalid[] = {"1e", "1e+", "1e-", "+INF", "-NaN", "nan", "inf",
        "1 2", "0x1p0", "1,25", ".", "", "--1", "+-1", "1e2x"};
    static const int modes[] = {FE_TONEAREST, FE_DOWNWARD, FE_UPWARD, FE_TOWARDZERO};
    fenv_t environment;
    unsigned int mode, item;
    int failed = 0;
    if (feholdexcept(&environment) != 0) {
        return 1;
    }
    for (mode = 0; mode < sizeof(modes) / sizeof(modes[0]); ++mode) {
        if (fesetround(modes[mode]) != 0) {
            failed = 1;
            break;
        }
        for (item = 0; item < sizeof(values) / sizeof(values[0]); ++item) {
            xmlSchemaTypePtr type = xmlSchemaGetPredefinedType(BAD_CAST values[item].type,
                BAD_CAST "http://www.w3.org/2001/XMLSchema");
            xmlSchemaValPtr value = NULL, again = NULL;
            const xmlChar *canonical = NULL;
            if (xmlSchemaValidatePredefinedType(type, BAD_CAST values[item].lexical, NULL) != 0
                    || xmlSchemaValidatePredefinedType(type, BAD_CAST values[item].lexical, &value) != 0
                    || value == NULL || xmlSchemaGetCanonValue(value, &canonical) != 0 || canonical == NULL
                    || !xmlStrEqual(canonical, BAD_CAST values[item].canonical)
                    || xmlSchemaValidatePredefinedType(type, canonical, &again) != 0 || again == NULL
                    || xmlSchemaCompareValues(value, again) != 0 || fegetround() != modes[mode]) {
                failed = 1;
            }
            xmlFree((void *)canonical);
            xmlSchemaFreeValue(value);
            xmlSchemaFreeValue(again);
        }
        for (item = 0; item < sizeof(invalid) / sizeof(invalid[0]); ++item) {
            int wide;
            for (wide = 0; wide < 2; ++wide) {
                xmlSchemaTypePtr type = xmlSchemaGetPredefinedType(BAD_CAST (wide ? "double" : "float"),
                    BAD_CAST "http://www.w3.org/2001/XMLSchema");
                xmlSchemaValPtr value = NULL;
                if (xmlSchemaValidatePredefinedType(type, BAD_CAST invalid[item], NULL) <= 0
                        || xmlSchemaValidatePredefinedType(type, BAD_CAST invalid[item], &value) <= 0
                        || value != NULL) {
                    failed = 1;
                }
                xmlSchemaFreeValue(value);
            }
        }
    }
    if (fesetenv(&environment) != 0) {
        failed = 1;
    }
    return failed;
}
