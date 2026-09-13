/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Exact XSD 1.0 calendar value; both strings are exclusively owned.
 * Year magnitude has at least four digits; fractions have no trailing zeros.
 */
typedef struct _xmlSchemaValDate xmlSchemaValDate;
typedef xmlSchemaValDate *xmlSchemaValDatePtr;
struct _xmlSchemaValDate {
    xmlChar *year;
    xmlChar *fraction;
    size_t yearLength;
    size_t fractionLength;
    int negative;
    int mon, day, hour, min, sec;
    int tz_flag, tzo;
};
