# Copyright (C) 2026 Qore Technologies, s.r.o.
# Assess strict element wildcards through an available xsi:type before rejecting.
function(qore_xml_fix_libxml2_wildcard_types source_dir binary_dir)
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
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemas.c for wildcard instance-type assessment")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "75e468136eaa0dbf8c95071194d41937d6da6f188ee799a47cf50902a98ad65b")
        return()
    endif()
    if(NOT _hash STREQUAL "3a78da4283035b2691688766e2bd6dda205a14cf36ce8430af3ec03677d2e80f")
        message(FATAL_ERROR "Unexpected libxml2 xmlschemas.c; cannot apply wildcard instance-type assessment")
    endif()
    file(READ "${_path}" _source)
    string(REPLACE [==[static int
xmlSchemaValidateElemWildcard(xmlSchemaValidCtxtPtr vctxt,
			      int *skip)
{
    xmlSchemaWildcardPtr wild = (xmlSchemaWildcardPtr) vctxt->inode->decl;
    /*
    * The namespace of the element was already identified to be
    * matching the wildcard.
    */
    if ((skip == NULL) || (wild == NULL) ||
	(wild->type != XML_SCHEMA_TYPE_ANY)) {
	VERROR_INT("xmlSchemaValidateElemWildcard",
	    "bad arguments");
	return (-1);
    }
    *skip = 0;
    if (wild->processContents == XML_SCHEMAS_ANY_SKIP) {
	/*
	* URGENT VAL TODO: Either we need to position the stream to the
	* next sibling, or walk the whole subtree.
	*/
	*skip = 1;
	return (0);
    }
    {
	xmlSchemaElementPtr decl = NULL;

	decl = xmlSchemaGetElem(vctxt->schema,
	    vctxt->inode->localName, vctxt->inode->nsName);
	if (decl != NULL) {
	    vctxt->inode->decl = decl;
	    return (0);
	}
    }
    if (wild->processContents == XML_SCHEMAS_ANY_STRICT) {
	/* VAL TODO: Change to proper error code. */
	VERROR(XML_SCHEMAV_CVC_ELT_1, NULL, /* WXS_BASIC_CAST wild */
	    "No matching global element declaration available, but "
	    "demanded by the strict wildcard");
	return (vctxt->err);
    }
    if (vctxt->nbAttrInfos != 0) {
	xmlSchemaAttrInfoPtr iattr;
	/*
	* SPEC Validation Rule: Schema-Validity Assessment (Element)
	* (1.2.1.2.1) - (1.2.1.2.3 )
	*
	* Use the xsi:type attribute for the type definition.
	*/
	iattr = xmlSchemaGetMetaAttrInfo(vctxt,
	    XML_SCHEMA_ATTR_INFO_META_XSI_TYPE);
	if (iattr != NULL) {
	    if (xmlSchemaProcessXSIType(vctxt, iattr,
		&(vctxt->inode->typeDef), NULL) == -1) {
		VERROR_INT("xmlSchemaValidateElemWildcard",
		    "calling xmlSchemaProcessXSIType() to "
		    "process the attribute 'xsi:nil'");
		return (-1);
	    }
	    /*
	    * Don't return an error on purpose.
	    */
	    return (0);
	}
    }
    /*
    * SPEC Validation Rule: Schema-Validity Assessment (Element)
    *
    * Fallback to "anyType".
    */
    vctxt->inode->typeDef =
	xmlSchemaGetBuiltInType(XML_SCHEMAS_ANYTYPE);
    return (0);
}
]==]
        [==[static int
xmlSchemaValidateElemWildcard(xmlSchemaValidCtxtPtr vctxt,
			      int *skip)
{
    xmlSchemaWildcardPtr wild = (xmlSchemaWildcardPtr) vctxt->inode->decl;
    /*
    * The namespace of the element was already identified to be
    * matching the wildcard.
    */
    if ((skip == NULL) || (wild == NULL) ||
	(wild->type != XML_SCHEMA_TYPE_ANY)) {
	VERROR_INT("xmlSchemaValidateElemWildcard",
	    "bad arguments");
	return (-1);
    }
    *skip = 0;
    if (wild->processContents == XML_SCHEMAS_ANY_SKIP) {
	/*
	* URGENT VAL TODO: Either we need to position the stream to the
	* next sibling, or walk the whole subtree.
	*/
	*skip = 1;
	return (0);
    }
    {
	xmlSchemaElementPtr decl = NULL;

	decl = xmlSchemaGetElem(vctxt->schema,
	    vctxt->inode->localName, vctxt->inode->nsName);
	if (decl != NULL) {
	    vctxt->inode->decl = decl;
	    return (0);
	}
    }
    if (vctxt->nbAttrInfos != 0) {
	xmlSchemaAttrInfoPtr iattr;
	/*
	* SPEC Validation Rule: Schema-Validity Assessment (Element)
	* (1.2.1.2.1) - (1.2.1.2.3 )
	*
	* Use the xsi:type attribute for the type definition.
	*/
	iattr = xmlSchemaGetMetaAttrInfo(vctxt,
	    XML_SCHEMA_ATTR_INFO_META_XSI_TYPE);
	if (iattr != NULL) {
	    if (xmlSchemaProcessXSIType(vctxt, iattr,
		&(vctxt->inode->typeDef), NULL) == -1) {
		VERROR_INT("xmlSchemaValidateElemWildcard",
		    "calling xmlSchemaProcessXSIType() to "
		    "process the attribute 'xsi:type'");
		return (-1);
	    }
	    /*
	    * Don't return an error on purpose.
	    */
	    return (0);
	}
    }
    /* Strict assessment can use either a declaration or an instance type. */
    if (wild->processContents == XML_SCHEMAS_ANY_STRICT) {
	VERROR(XML_SCHEMAV_CVC_ELT_1, NULL,
	    "No matching global element declaration or instance type "
	    "available, but demanded by the strict wildcard");
	return (vctxt->err);
    }
    /*
    * SPEC Validation Rule: Schema-Validity Assessment (Element)
    *
    * Fallback to "anyType".
    */
    vctxt->inode->typeDef =
	xmlSchemaGetBuiltInType(XML_SCHEMAS_ANYTYPE);
    return (0);
}
]==] _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "75e468136eaa0dbf8c95071194d41937d6da6f188ee799a47cf50902a98ad65b")
        message(FATAL_ERROR "Pinned libxml2 wildcard instance-type fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-wildcard-type-fix")
    set(_replacement "${binary_dir}/qore-wildcard-type-fix/xmlschemas.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied libxml2 wildcard instance-type assessment in the build tree")
endfunction()
