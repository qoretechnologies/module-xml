/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * XSD 1.0 section 3.9.4: abstract declarations contribute no matching name.
 * Keep emitted transitions consistent with the attribution predicates.
 */
static int
xmlSchemaHasUsableElementName(xmlSchemaParserCtxtPtr parser, xmlSchemaElementPtr element) {
    xmlSchemaSubstGroupPtr group;
    if (!(element->flags & XML_SCHEMAS_ELEM_ABSTRACT)) {
        return 1;
    }
    if (!(element->flags & XML_SCHEMAS_ELEM_SUBST_GROUP_HEAD)) {
        return 0;
    }
    group = xmlSchemaSubstGroupGet(parser, element);
    if (group == NULL) {
        /* Let the existing builder report the missing resolved component. */
        return 1;
    }
    for (int index = 0; index < group->members->nbItems; ++index) {
        xmlSchemaElementPtr member = group->members->items[index];
        if (!(member->flags & XML_SCHEMAS_ELEM_ABSTRACT)) {
            return 1;
        }
    }
    return 0;
}

static xmlAutomataStatePtr
xmlSchemaNewElementTransition(xmlAutomataPtr automaton, xmlAutomataStatePtr from,
                               xmlAutomataStatePtr to, xmlSchemaElementPtr element) {
    if (element->flags & XML_SCHEMAS_ELEM_ABSTRACT) {
        /* A disconnected target represents the empty language, not epsilon. */
        return to == NULL ? xmlAutomataNewState(automaton) : to;
    }
    return xmlAutomataNewTransition2(automaton, from, to, element->name,
        element->targetNamespace, element);
}
