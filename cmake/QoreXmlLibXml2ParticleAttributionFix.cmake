# Copyright (C) 2026 Qore Technologies, s.r.o.
# Exact counted component attribution after particle identity fixes.
# Keep the pinned upstream sources unchanged; compile the checked build copy.
set(_qore_xml_particle_attribution_fix_dir "${CMAKE_CURRENT_LIST_DIR}")

function(qore_xml_fix_libxml2_particle_attribution source_dir binary_dir)
    get_target_property(_sources LibXml2 SOURCES)
    set(_input "")
    foreach(_entry IN LISTS _sources)
        get_filename_component(_name "${_entry}" NAME)
        if(_name STREQUAL "xmlschemas.c")
            if(_input)
                message(FATAL_ERROR "Duplicate libxml2 xmlschemas.c target source")
            endif()
            set(_input "${_entry}")
        endif()
    endforeach()
    if(NOT _input)
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemas.c for particle attribution fix")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    set(_original_hash 98cd89311c1eb371b29e76076ab5c60c63c9e8786ed103f5f94ef0ed806971ef)
    set(_fixed_hash 9576ea27a4e0b0f67076b04db27c6bd0737b2e4e58e9f08ad906992a4ad544fc)
    if(_hash STREQUAL _fixed_hash)
        return()
    endif()
    if(NOT _hash STREQUAL _original_hash)
        message(FATAL_ERROR "Unexpected libxml2 xmlschemas.c; cannot apply particle attribution fix")
    endif()
    file(READ "${_path}" _source)
    set(_helpers "")
    string(REPLACE [==[    int maxOccurs;
    xmlNodePtr node;
};]==]
        [==[    int maxOccurs;
    xmlNodePtr node;
    xmlSchemaParticlePtr countSource; /* Borrowed original occurrence source. */
    int termNullable; /* Intrinsic term can match an empty sequence. */
};]==] _source "${_source}")
    string(REPLACE [==[    ret->maxOccurs = max;]==]
        [==[    ret->maxOccurs = max;
    ret->countSource = NULL;
    ret->termNullable = 0;]==] _source "${_source}")
    string(REPLACE [==[		    particle->children =
			((xmlSchemaParticlePtr) baseType->subtypes)->children;]==]
        [==[		    particle->children =
			((xmlSchemaParticlePtr) baseType->subtypes)->children;
                    particle->countSource = (xmlSchemaParticlePtr)baseType->subtypes;
                    if (particle->countSource->countSource != NULL) {
                        particle->countSource = particle->countSource->countSource;
                    }]==] _source "${_source}")
    string(REPLACE [==[    } else if (xmlRegexpIsDeterminist(type->contModel) != 1) {
        xmlSchemaPCustomErr(ctxt,
	    XML_SCHEMAP_NOT_DETERMINISTIC,
	    /* XML_SCHEMAS_ERR_NOTDETERMINIST, */
	    WXS_BASIC_CAST type, type->node,
	    "The content model is not determinist", NULL);
    } else {
    }]==]
        [==[    }
    /* Component attribution was checked before automaton reduction.  Keep
     * the executor's computed counter/backtracking flags unchanged. */]==] _source "${_source}")
    string(REPLACE [==[    /*
    * Finally we can build the automaton from the content model of]==]
        [==[    ret = xmlSchemaCheckParticleAttributions(pctxt, items, nbItems);
    if (ret < 0) {
        goto exit_failure;
    }
    if (ret > 0) {
        goto exit_error;
    }

    /*
    * Finally we can build the automaton from the content model of]==] _source "${_source}")
    string(REPLACE [==[static int
xmlSchemaBuildContentModelForSubstGroup(xmlSchemaParserCtxtPtr pctxt,
	xmlSchemaParticlePtr particle, int counter, xmlAutomataStatePtr end)
{
    xmlAutomataStatePtr start, tmp;
    xmlSchemaElementPtr elemDecl, member;
    xmlSchemaSubstGroupPtr substGroup;
    int i;
    int ret = 0;

    elemDecl = (xmlSchemaElementPtr) particle->children;
    /*
    * Wrap the substitution group with a CHOICE.
    */
    start = pctxt->state;
    if (end == NULL)
	end = xmlAutomataNewState(pctxt->am);
    substGroup = xmlSchemaSubstGroupGet(pctxt, elemDecl);
    if (substGroup == NULL) {
	xmlSchemaPErr(pctxt, WXS_ITEM_NODE(particle),
	    XML_SCHEMAP_INTERNAL,
	    "Internal error: xmlSchemaBuildContentModelForSubstGroup, "
	    "declaration is marked having a subst. group but none "
	    "available.\n", elemDecl->name, NULL);
	return(0);
    }
    if (counter >= 0) {
	/*
	* NOTE that we put the declaration in, even if it's abstract.
	* However, an error will be raised during *validation* if an element
	* information item shall be validated against an abstract element
	* declaration.
	*/
	tmp = xmlAutomataNewCountedTrans(pctxt->am, start, NULL, counter);
        xmlAutomataNewTransition2(pctxt->am, tmp, end,
	            elemDecl->name, elemDecl->targetNamespace, elemDecl);
	/*
	* Add subst. group members.
	*/
	for (i = 0; i < substGroup->members->nbItems; i++) {
	    member = (xmlSchemaElementPtr) substGroup->members->items[i];
            xmlAutomataNewTransition2(pctxt->am, tmp, end,
		               member->name, member->targetNamespace, member);
	}
    } else if (particle->maxOccurs == 1) {
	/*
	* NOTE that we put the declaration in, even if it's abstract,
	*/
	xmlAutomataNewEpsilon(pctxt->am,
	    xmlAutomataNewTransition2(pctxt->am,
	    start, NULL,
	    elemDecl->name, elemDecl->targetNamespace, elemDecl), end);
	/*
	* Add subst. group members.
	*/
	for (i = 0; i < substGroup->members->nbItems; i++) {
	    member = (xmlSchemaElementPtr) substGroup->members->items[i];
	    /*
	    * NOTE: This fixes bug #341150. xmlAutomataNewOnceTrans2()
	    *  was incorrectly used instead of xmlAutomataNewTransition2()
	    *  (seems like a copy&paste bug from the XML_SCHEMA_TYPE_ALL
	    *  section in xmlSchemaBuildAContentModel() ).
	    * TODO: Check if xmlAutomataNewOnceTrans2() was instead
	    *  intended for the above "counter" section originally. I.e.,
	    *  check xs:all with subst-groups.
	    *
	    * tmp = xmlAutomataNewOnceTrans2(pctxt->am, start, NULL,
	    *	               member->name, member->targetNamespace,
	    *		       1, 1, member);
	    */
	    tmp = xmlAutomataNewTransition2(pctxt->am, start, NULL,
		member->name, member->targetNamespace, member);
	    xmlAutomataNewEpsilon(pctxt->am, tmp, end);
	}
    } else {
	xmlAutomataStatePtr hop;
	int maxOccurs = particle->maxOccurs == UNBOUNDED ?
	    UNBOUNDED : particle->maxOccurs - 1;
	int minOccurs = particle->minOccurs < 1 ? 0 : particle->minOccurs - 1;

	counter =
	    xmlAutomataNewCounter(pctxt->am, minOccurs,
	    maxOccurs);
	hop = xmlAutomataNewState(pctxt->am);

	xmlAutomataNewEpsilon(pctxt->am,
	    xmlAutomataNewTransition2(pctxt->am,
	    start, NULL,
	    elemDecl->name, elemDecl->targetNamespace, elemDecl),
	    hop);
	/*
	 * Add subst. group members.
	 */
	for (i = 0; i < substGroup->members->nbItems; i++) {
	    member = (xmlSchemaElementPtr) substGroup->members->items[i];
	    xmlAutomataNewEpsilon(pctxt->am,
		xmlAutomataNewTransition2(pctxt->am,
		start, NULL,
		member->name, member->targetNamespace, member),
		hop);
	}
	xmlAutomataNewCountedTrans(pctxt->am, hop, start, counter);
	xmlAutomataNewCounterTrans(pctxt->am, hop, end, counter);
    }
    if (particle->minOccurs == 0) {
	xmlAutomataNewEpsilon(pctxt->am, start, end);
        ret = 1;
    }
    pctxt->state = end;
    return(ret);
}
]==]
        [==[static int
xmlSchemaBuildContentModelForSubstGroup(xmlSchemaParserCtxtPtr pctxt,
	xmlSchemaParticlePtr particle, int counter, xmlAutomataStatePtr end)
{
    xmlAutomataStatePtr start, tmp;
    xmlSchemaElementPtr elemDecl, member;
    xmlSchemaSubstGroupPtr substGroup;
    int i;
    int ret = 0;

    elemDecl = (xmlSchemaElementPtr) particle->children;
    /*
    * Wrap the substitution group with a CHOICE.
    */
    start = pctxt->state;
    if (end == NULL)
	end = xmlAutomataNewState(pctxt->am);
    substGroup = xmlSchemaSubstGroupGet(pctxt, elemDecl);
    if (substGroup == NULL) {
	xmlSchemaPErr(pctxt, WXS_ITEM_NODE(particle),
	    XML_SCHEMAP_INTERNAL,
	    "Internal error: xmlSchemaBuildContentModelForSubstGroup, "
	    "declaration is marked having a subst. group but none "
	    "available.\n", elemDecl->name, NULL);
	return(0);
    }
    if (counter >= 0) {
	tmp = xmlAutomataNewCountedTrans(pctxt->am, start, NULL, counter);
        xmlSchemaNewElementTransition(pctxt->am, tmp, end, elemDecl);
	/*
	* Add subst. group members.
	*/
	for (i = 0; i < substGroup->members->nbItems; i++) {
	    member = (xmlSchemaElementPtr) substGroup->members->items[i];
            xmlSchemaNewElementTransition(pctxt->am, tmp, end, member);
	}
    } else if (particle->maxOccurs == 1) {
	xmlAutomataNewEpsilon(pctxt->am,
	    xmlSchemaNewElementTransition(pctxt->am, start, NULL, elemDecl), end);
	/*
	* Add subst. group members.
	*/
	for (i = 0; i < substGroup->members->nbItems; i++) {
	    member = (xmlSchemaElementPtr) substGroup->members->items[i];
	    /*
	    * NOTE: This fixes bug #341150. xmlAutomataNewOnceTrans2()
	    *  was incorrectly used instead of xmlAutomataNewTransition2()
	    *  (seems like a copy&paste bug from the XML_SCHEMA_TYPE_ALL
	    *  section in xmlSchemaBuildAContentModel() ).
	    * TODO: Check if xmlAutomataNewOnceTrans2() was instead
	    *  intended for the above "counter" section originally. I.e.,
	    *  check xs:all with subst-groups.
	    *
	    * tmp = xmlAutomataNewOnceTrans2(pctxt->am, start, NULL,
	    *	               member->name, member->targetNamespace,
	    *		       1, 1, member);
	    */
	    tmp = xmlSchemaNewElementTransition(pctxt->am, start, NULL, member);
	    xmlAutomataNewEpsilon(pctxt->am, tmp, end);
	}
    } else {
	xmlAutomataStatePtr hop;
	int maxOccurs = particle->maxOccurs == UNBOUNDED ?
	    UNBOUNDED : particle->maxOccurs - 1;
	int minOccurs = particle->minOccurs < 1 ? 0 : particle->minOccurs - 1;

	counter =
	    xmlAutomataNewCounter(pctxt->am, minOccurs,
	    maxOccurs);
	hop = xmlAutomataNewState(pctxt->am);

	xmlAutomataNewEpsilon(pctxt->am,
	    xmlSchemaNewElementTransition(pctxt->am, start, NULL, elemDecl),
	    hop);
	/*
	 * Add subst. group members.
	 */
	for (i = 0; i < substGroup->members->nbItems; i++) {
	    member = (xmlSchemaElementPtr) substGroup->members->items[i];
	    xmlAutomataNewEpsilon(pctxt->am,
		xmlSchemaNewElementTransition(pctxt->am, start, NULL, member),
		hop);
	}
	xmlAutomataNewCountedTrans(pctxt->am, hop, start, counter);
	xmlAutomataNewCounterTrans(pctxt->am, hop, end, counter);
    }
    if (particle->minOccurs == 0) {
	xmlAutomataNewEpsilon(pctxt->am, start, end);
        ret = 1;
    }
    pctxt->state = end;
    return(ret);
}
]==] _source "${_source}")
    string(REPLACE [==[    if (((xmlSchemaElementPtr) particle->children)->flags &
	XML_SCHEMAS_ELEM_SUBST_GROUP_HEAD) {]==]
        [==[    if (!xmlSchemaHasUsableElementName(ctxt, (xmlSchemaElementPtr)particle->children)) {
        xmlAutomataStatePtr start = ctxt->state;
        ctxt->state = xmlAutomataNewState(ctxt->am);
        if (particle->minOccurs == 0) {
            xmlAutomataNewEpsilon(ctxt->am, start, ctxt->state);
            return 1;
        }
        return 0;
    }
    if (((xmlSchemaElementPtr) particle->children)->flags &
	XML_SCHEMAS_ELEM_SUBST_GROUP_HEAD) {]==] _source "${_source}")
    string(REPLACE [==[            xmlSchemaElementPtr elemDecl;

            ret = 1;]==]
        [==[            xmlSchemaElementPtr elemDecl;
            int emptyLanguage = 0;

            ret = 1;]==] _source "${_source}")
    string(REPLACE [==[                if (elemDecl->flags & XML_SCHEMAS_ELEM_SUBST_GROUP_HEAD) {]==]
        [==[                if (!xmlSchemaHasUsableElementName(pctxt, elemDecl)) {
                    emptyLanguage |= sub->minOccurs != 0;
                } else if (elemDecl->flags & XML_SCHEMAS_ELEM_SUBST_GROUP_HEAD) {]==] _source "${_source}")
    string(REPLACE [==[            pctxt->state =
                xmlAutomataNewAllTrans(pctxt->am, pctxt->state, NULL, 0);]==]
        [==[            pctxt->state = emptyLanguage ? xmlAutomataNewState(pctxt->am)
                : xmlAutomataNewAllTrans(pctxt->am, pctxt->state, NULL, 0);]==] _source "${_source}")
    string(FIND "${_source}" "static int\nxmlSchemaBuildAContentModel(" _begin)
    string(SUBSTRING "${_source}" ${_begin} -1 _tail)
    string(FIND "${_tail}" "\n/**" _end)
    string(SUBSTRING "${_tail}" 0 ${_end} _body)
    set(_original_body "${_body}")
    string(REPLACE "particle->minOccurs" "minimum" _body "${_body}")
    string(REPLACE "    size_t parent;" "    size_t parent;\n    int minimum;" _body "${_body}")
    string(REPLACE "\n    if (xmlAutomataPushParticle"
        "\n    minimum = particle->termNullable ? 0 : particle->minOccurs;\n    if (xmlAutomataPushParticle" _body "${_body}")
    string(REPLACE "${_original_body}" "${_body}" _source "${_source}")
    file(READ "${_qore_xml_particle_attribution_fix_dir}/libxml2-particle-attribution-elements.inc" _elements)
    string(REPLACE [==[static int
xmlSchemaBuildContentModelForSubstGroup(]==] "${_elements}\nstatic int\nxmlSchemaBuildContentModelForSubstGroup(" _source "${_source}")
    file(READ "${_qore_xml_particle_attribution_fix_dir}/libxml2-particle-attribution-math.inc" _helper)
    string(APPEND _helpers "${_helper}\n")
    file(READ "${_qore_xml_particle_attribution_fix_dir}/libxml2-particle-attribution-sets.inc" _helper)
    string(APPEND _helpers "${_helper}\n")
    file(READ "${_qore_xml_particle_attribution_fix_dir}/libxml2-particle-attribution-schema.inc" _helper)
    string(APPEND _helpers "${_helper}\n")
    string(REPLACE [==[static void
xmlSchemaBuildContentModel(]==] "${_helpers}static void\nxmlSchemaBuildContentModel(" _source "${_source}")
    string(SHA256 _result_hash "${_source}")
    if(NOT _result_hash STREQUAL _fixed_hash)
        message(FATAL_ERROR "Pinned libxml2 xmlschemas.c particle attribution fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-particle-attribution-fix")
    set(_replacement "${binary_dir}/qore-particle-attribution-fix/xmlschemas.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied exact libxml2 particle attribution fix in the build tree")
endfunction()
