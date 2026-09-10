/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * Preserve exact occurrence attributes when constructing native counters.
 */
XML_HIDDEN int
xmlAutomataSetExactCounter(xmlAutomata *automaton, int counter, const char *minimum,
                           const char *maximum, int firstEmitted, int nullable);

static int
xmlSchemaNewExactCounter(xmlSchemaParserCtxtPtr parser, xmlSchemaParticlePtr particle,
                         int minimum, int maximum, int firstEmitted) {
    xmlSchemaParticlePtr source;
    xmlAttrPtr attribute;
    const xmlChar *low, *high;
    char lowBuffer[32], highBuffer[32];
    int counter = xmlAutomataNewCounter(parser->am, minimum, maximum);
    if (counter < 0 || (particle->maxFinite && particle->minOccurs < UNBOUNDED
            && particle->maxOccurs < UNBOUNDED)) {
        return counter;
    }
    source = particle->countSource != NULL ? particle->countSource : particle;
    attribute = xmlSchemaGetPropNode(source->node, "minOccurs");
    if (attribute != NULL) {
        low = xmlSchemaGetNodeContent(parser, (xmlNodePtr)attribute);
    } else {
        snprintf(lowBuffer, sizeof(lowBuffer), "%d", source->minOccurs);
        low = BAD_CAST lowBuffer;
    }
    attribute = xmlSchemaGetPropNode(source->node, "maxOccurs");
    if (attribute != NULL) {
        high = xmlSchemaGetNodeContent(parser, (xmlNodePtr)attribute);
    } else if (!particle->maxFinite) {
        high = BAD_CAST "unbounded";
    } else {
        snprintf(highBuffer, sizeof(highBuffer), "%d", source->maxOccurs);
        high = BAD_CAST highBuffer;
    }
    if (low == NULL || high == NULL || xmlAutomataSetExactCounter(parser->am, counter,
            (const char *)low, (const char *)high, firstEmitted, particle->termNullable) < 0) {
        xmlSchemaPErrMemory(parser);
        return -1;
    }
    return counter;
}
