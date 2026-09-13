/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 numeric/boolean constraint lexicals, including list/union members.
 * Keep the schema spelling of other atomic families: QName, in particular,
 * has no context-independent canonical lexical representation in XSD 1.0.
 */
static int
qoreXmlIsNumericDefault(xmlSchemaValPtr val)
{
    switch (xmlSchemaGetValType(val)) {
        case XML_SCHEMAS_DECIMAL:
        case XML_SCHEMAS_BOOLEAN:
        case XML_SCHEMAS_INTEGER:
        case XML_SCHEMAS_NPINTEGER:
        case XML_SCHEMAS_NINTEGER:
        case XML_SCHEMAS_NNINTEGER:
        case XML_SCHEMAS_PINTEGER:
        case XML_SCHEMAS_INT:
        case XML_SCHEMAS_UINT:
        case XML_SCHEMAS_LONG:
        case XML_SCHEMAS_ULONG:
        case XML_SCHEMAS_SHORT:
        case XML_SCHEMAS_USHORT:
        case XML_SCHEMAS_BYTE:
        case XML_SCHEMAS_UBYTE:
            return (1);
        default:
            return (0);
    }
}

/* A NULL result means that there is no numeric/boolean member to rewrite.
 * All allocation failures leave the output NULL; schema/instance owners keep
 * their original constraint and computed value throughout this operation. */
static int
qoreXmlNumericDefaultLexical(xmlSchemaValPtr val, const xmlChar *lexical,
                            xmlChar **result)
{
    xmlSchemaValPtr item;
    xmlBufPtr buffer;
    const xmlChar *cursor = lexical;
    int numeric = 0, list, first = 1;
    *result = NULL;
    for (item = val; item != NULL; item = xmlSchemaValueGetNext(item)) {
        numeric |= qoreXmlIsNumericDefault(item);
    }
    if (!numeric) {
        return (0);
    }
    buffer = xmlBufCreate(50);
    if (buffer == NULL) {
        return (-1);
    }
    list = xmlSchemaValueGetNext(val) != NULL;
    for (item = val; item != NULL; item = xmlSchemaValueGetNext(item)) {
        const xmlChar *text, *canonical = NULL;
        size_t length;
        if (list) {
            while (IS_BLANK_CH(*cursor)) {
                ++cursor;
            }
            text = cursor;
            while (*cursor != 0 && !IS_BLANK_CH(*cursor)) {
                ++cursor;
            }
            length = cursor - text;
        } else {
            text = lexical;
            length = strlen((const char *)text);
        }
        if (qoreXmlIsNumericDefault(item)) {
            if (xmlSchemaGetCanonValue(item, &canonical) != 0 || canonical == NULL) {
                xmlFree((void *)canonical);
                xmlBufFree(buffer);
                return (-1);
            }
            text = canonical;
            /* libxml2 retains a minus sign on numeric zero. XSD 1.0's
             * canonical integer/decimal zero has no sign. */
            if (text[0] == '-') {
                const xmlChar *digit = text + 1;
                while (*digit == '0' || *digit == '.') {
                    ++digit;
                }
                if (*digit == 0) {
                    ++text;
                }
            }
            length = strlen((const char *)text);
        }
        if ((!first && xmlBufAdd(buffer, BAD_CAST " ", 1) < 0) ||
            xmlBufAdd(buffer, text, length) < 0) {
            xmlFree((void *)canonical);
            xmlBufFree(buffer);
            return (-1);
        }
        xmlFree((void *)canonical);
        first = 0;
    }
    *result = xmlBufDetach(buffer);
    xmlBufFree(buffer);
    return (*result == NULL ? -1 : 0);
}

static int
qoreXmlCheckNumericDefault(xmlSchemaAbstractCtxtPtr ctxt, xmlNodePtr node,
                          xmlSchemaTypePtr type, const xmlChar *lexical,
                          xmlSchemaValPtr value)
{
    xmlChar *canonical = NULL;
    int ret = qoreXmlNumericDefaultLexical(value, lexical, &canonical);
    if (ret == 0 && canonical != NULL) {
        ret = xmlSchemaVCheckCVCSimpleType(ctxt, node, type,
                                          canonical, NULL, 1, 1, 0);
    }
    xmlFree(canonical);
    return (ret);
}
