/* Copyright (C) 2026 Qore Technologies, s.r.o. */
static int check_calendar_values(void) {
    static const struct { const char *type, *lexical, *canonical; } values[] = {
        {"dateTime", "2000-01-01T00:00:00.100+01:00", "1999-12-31T23:00:00.1Z"},
        {"dateTime", "-0001-12-31T24:00:00Z", "0001-01-01T00:00:00Z"},
        {"dateTime", "999999999999999999999999999999999999-12-31T24:00:00",
                     "1000000000000000000000000000000000000-01-01T00:00:00"},
        {"time", "00:00:00.123456789012345678900+01:00", "23:00:00.1234567890123456789Z"},
        {"time", "24:00:00", "00:00:00"},
        {"date", "2002-10-10+13:00", "2002-10-09-11:00"},
        {"date", "2002-10-10-14:00", "2002-10-11+10:00"},
        {"date", "-0001-01-01Z", "-0001-01-01Z"},
        {"gYear", "2000+01:00", "2000+01:00"},
        {"gYearMonth", "2000-02+01:00", "2000-02+01:00"},
        {"gMonth", "--02+01:00", "--02+01:00"},
        {"gMonthDay", "--02-29+01:00", "--02-29+01:00"},
        {"gDay", "---01+01:00", "---01+01:00"}
    };
    static const struct { const char *type, *lexical; } invalid[] = {
        {"date", "0000-01-01"}, {"date", "02000-01-01"}, {"date", "1900-02-29"},
        {"time", "24:00:00.00001"}, {"time", "01:00:00+14:01"}, {"time", "01:00:00."},
        {"dateTime", "2000-01-01T00:00:00junk"}, {"gMonth", "--01--"}
    };
    unsigned int i;
    int failed = 0;
    for (i = 0; i < sizeof(values) / sizeof(values[0]); ++i) {
        xmlSchemaTypePtr type = xmlSchemaGetPredefinedType(BAD_CAST values[i].type,
            BAD_CAST "http://www.w3.org/2001/XMLSchema");
        xmlSchemaValPtr value = NULL, copy = NULL, again = NULL;
        const xmlChar *canonical = NULL;
        if (xmlSchemaValidatePredefinedType(type, BAD_CAST values[i].lexical, NULL) != 0 ||
                xmlSchemaValidatePredefinedType(type, BAD_CAST values[i].lexical, &value) != 0 || value == NULL) {
            failed = 1;
        } else {
            copy = xmlSchemaCopyValue(value);
        }
        xmlSchemaFreeValue(value);
        if (copy == NULL || xmlSchemaGetCanonValue(copy, &canonical) != 0 || canonical == NULL ||
                !xmlStrEqual(canonical, BAD_CAST values[i].canonical) ||
                xmlSchemaValidatePredefinedType(type, canonical, &again) != 0 || again == NULL ||
                xmlSchemaCompareValues(copy, again) != 0) {
            failed = 1;
        }
        xmlFree((void *)canonical);
        xmlSchemaFreeValue(copy);
        xmlSchemaFreeValue(again);
    }
    for (i = 0; i < sizeof(invalid) / sizeof(invalid[0]); ++i) {
        xmlSchemaTypePtr type = xmlSchemaGetPredefinedType(BAD_CAST invalid[i].type,
            BAD_CAST "http://www.w3.org/2001/XMLSchema");
        xmlSchemaValPtr value = NULL;
        if (xmlSchemaValidatePredefinedType(type, BAD_CAST invalid[i].lexical, NULL) <= 0 ||
                xmlSchemaValidatePredefinedType(type, BAD_CAST invalid[i].lexical, &value) <= 0 || value != NULL) {
            failed = 1;
        }
        xmlSchemaFreeValue(value);
    }
    {
        xmlSchemaTypePtr type = xmlSchemaGetPredefinedType(BAD_CAST "time",
            BAD_CAST "http://www.w3.org/2001/XMLSchema");
        xmlSchemaValPtr left = NULL, right = NULL;
        if (xmlSchemaValidatePredefinedType(type, BAD_CAST "12:00:00.1234567890123456789Z", &left) != 0 ||
                xmlSchemaValidatePredefinedType(type, BAD_CAST "12:00:00.1234567890123456790Z", &right) != 0 ||
                left == NULL || right == NULL || xmlSchemaCompareValues(left, right) != -1) {
            failed = 1;
        }
        xmlSchemaFreeValue(left);
        xmlSchemaFreeValue(right);
    }
    return failed;
}

static int check_calendar_constraints(void) {
    static const char *types[] = {"dateTime", "time", "date"};
    static const char *values[] = {"2000-01-01T00:00:00.100+01:00", "24:00:00", "2002-10-10+13:00"};
    static const char *patterns[] = {"2000-01-01T00:00:00[.]100[+]01:00", "24:00:00", "2002-10-10[+]13:00"};
    static const char *canonical[] = {"1999-12-31T23:00:00[.]1Z", "00:00:00", "2002-10-09-11:00"};
    unsigned int kind, item, valid, attribute;
    for (kind = 0; kind < 2; ++kind) {
        for (item = 0; item < sizeof(types) / sizeof(types[0]); ++item) {
            for (valid = 0; valid < 2; ++valid) {
                for (attribute = 0; attribute < 2; ++attribute) {
                    char source[1024];
                    int diagnostics = 0;
                    int length = snprintf(source, sizeof(source),
                        "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
                        "<xs:simpleType name='Value'><xs:restriction base='xs:%s'>"
                        "<xs:pattern value='%s%s%s'/></xs:restriction></xs:simpleType>"
                        "<xs:%s name='value' type='Value' %s='%s'/></xs:schema>",
                        types[item], patterns[item], valid ? "|" : "", valid ? canonical[item] : "",
                        attribute ? "attribute" : "element", kind ? "fixed" : "default", values[item]);
                    xmlSchemaParserCtxtPtr parser;
                    xmlSchemaPtr schema;
                    if (length < 0 || (size_t)length >= sizeof(source)) {
                        return 1;
                    }
                    parser = xmlSchemaNewMemParserCtxt(source, length);
                    if (parser == NULL) {
                        return 1;
                    }
                    xmlSchemaSetParserErrors(parser, qname_schema_error, qname_schema_error, &diagnostics);
                    schema = xmlSchemaParse(parser);
                    xmlSchemaFreeParserCtxt(parser);
                    if ((schema != NULL) != valid || (diagnostics == 0) != valid) {
                        xmlSchemaFree(schema);
                        return 1;
                    }
                    xmlSchemaFree(schema);
                }
            }
        }
    }
    return 0;
}
