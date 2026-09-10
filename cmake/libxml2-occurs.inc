/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 Part 2 sections 3.3.20.1 and 4.3.6: occurrence attributes
 * use nonNegativeInteger lexical forms and collapse XML whitespace.
 * Keep libxml2's existing integer representation and range diagnostics.
 */
static int
xmlSchemaParseOccursLexical(const xmlChar *value, int allowUnbounded,
                           int *result)
{
    const xmlChar *cur = value;
    int negative = 0;
    int ret = 0;

    while (IS_BLANK_CH(*cur)) {
        cur++;
    }
    if (allowUnbounded && (xmlStrncmp(cur, BAD_CAST "unbounded", 9) == 0)) {
        cur += 9;
        while (IS_BLANK_CH(*cur)) {
            cur++;
        }
        if (*cur != 0) {
            return -1;
        }
        *result = UNBOUNDED;
        return 0;
    }
    if ((*cur == '+') || (*cur == '-')) {
        negative = (*cur == '-');
        cur++;
    }
    if ((*cur < '0') || (*cur > '9')) {
        return -1;
    }
    while ((*cur >= '0') && (*cur <= '9')) {
        int digit = *cur - '0';
        if (ret > (INT_MAX - digit) / 10) {
            ret = INT_MAX;
        } else {
            ret = ret * 10 + digit;
        }
        cur++;
    }
    while (IS_BLANK_CH(*cur)) {
        cur++;
    }
    if ((*cur != 0) || (negative && (ret != 0))) {
        return -1;
    }
    *result = ret;
    return 0;
}

static int
xmlSchemaGetOccurs(xmlSchemaParserCtxtPtr ctxt, xmlNodePtr node,
                   const char *property, int min, int max, int def,
                   const char *expected, int allowUnbounded)
{
    const xmlChar *value;
    xmlAttrPtr attr = xmlSchemaGetPropNode(node, property);
    int result;

    if (attr == NULL) {
        return def;
    }
    value = xmlSchemaGetNodeContent(ctxt, (xmlNodePtr) attr);
    if (value == NULL) {
        return def;
    }
    if ((xmlSchemaParseOccursLexical(value, allowUnbounded, &result) != 0) ||
        (result < min) || ((max != -1) && (result > max))) {
        xmlSchemaPSimpleTypeErr(ctxt, XML_SCHEMAP_S4S_ATTR_INVALID_VALUE,
            NULL, (xmlNodePtr) attr, NULL, expected, value, NULL, NULL, NULL);
        return def;
    }
    return result;
}

static int
xmlGetMaxOccurs(xmlSchemaParserCtxtPtr ctxt, xmlNodePtr node,
                int min, int max, int def, const char *expected)
{
    return xmlSchemaGetOccurs(ctxt, node, "maxOccurs", min, max, def, expected,
                              max == UNBOUNDED);
}

static int
xmlGetMinOccurs(xmlSchemaParserCtxtPtr ctxt, xmlNodePtr node,
                int min, int max, int def, const char *expected)
{
    return xmlSchemaGetOccurs(ctxt, node, "minOccurs", min, max, def, expected, 0);
}
