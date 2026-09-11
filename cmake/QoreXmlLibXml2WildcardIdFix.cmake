# Copyright (C) 2026 Qore Technologies, s.r.o.
# Report detected XSD wildcard ID attribute constraint violations.
function(qore_xml_fix_libxml2_wildcard_ids source_dir binary_dir)
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
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemas.c for wildcard ID reporting")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "3a78da4283035b2691688766e2bd6dda205a14cf36ce8430af3ec03677d2e80f")
        return()
    endif()
    if(NOT _hash STREQUAL "a918602d87b2ed7a35f0d7d26189e9190365123966feb8525a9aba2344711d67")
        message(FATAL_ERROR "Unexpected libxml2 xmlschemas.c; cannot apply wildcard ID reporting")
    endif()
    file(READ "${_path}" _source)
    string(REPLACE [==[	    case XML_SCHEMAS_ATTR_ERR_WILD_STRICT_NO_DECL:]==]
        [==[	    case XML_SCHEMAS_ATTR_ERR_WILD_DUPLICATE_ID:
		VERROR(XML_SCHEMAV_CVC_COMPLEX_TYPE_5_1, NULL,
		    "More than one attribute matched by the wildcard has an ID type");
		break;
	    case XML_SCHEMAS_ATTR_ERR_WILD_AND_USE_ID:
		VERROR(XML_SCHEMAV_CVC_COMPLEX_TYPE_5_2, NULL,
		    "An ID attribute matched by the wildcard is forbidden when the "
		    "type has a declared ID attribute use");
		break;
	    case XML_SCHEMAS_ATTR_ERR_WILD_STRICT_NO_DECL:]==] _source "${_source}")
    # Restrictions store their ancestor in baseType; subtypes is a list item or content.
    string(REPLACE [==[static int
xmlSchemaIsDerivedFromBuiltInType(xmlSchemaTypePtr type, int valType)
{
    if (type == NULL)
	return (0);
    if (WXS_IS_COMPLEX(type))
	return (0);
    if (type->type == XML_SCHEMA_TYPE_BASIC) {
	if (type->builtInType == valType)
	    return(1);
	if ((type->builtInType == XML_SCHEMAS_ANYSIMPLETYPE) ||
	    (type->builtInType == XML_SCHEMAS_ANYTYPE))
	    return (0);
	return(xmlSchemaIsDerivedFromBuiltInType(type->subtypes, valType));
    }
    return(xmlSchemaIsDerivedFromBuiltInType(type->subtypes, valType));
}
]==] [==[static int
xmlSchemaIsDerivedFromBuiltInType(xmlSchemaTypePtr type, int valType)
{
    if (type == NULL)
	return (0);
    if (WXS_IS_COMPLEX(type))
	return (0);
    if (type->type == XML_SCHEMA_TYPE_BASIC) {
	if (type->builtInType == valType)
	    return(1);
	if ((type->builtInType == XML_SCHEMAS_ANYSIMPLETYPE) ||
	    (type->builtInType == XML_SCHEMAS_ANYTYPE))
	    return (0);
	return(xmlSchemaIsDerivedFromBuiltInType(type->baseType, valType));
    }
    return(xmlSchemaIsDerivedFromBuiltInType(type->baseType, valType));
}
]==] _source "${_source}")
    # Check the lexical constraint before a typed default has been computed.
    string(REPLACE [==[    if ((use->defVal != NULL) && (WXS_ATTRUSE_TYPEDEF(use) != NULL)) {]==] [==[    if ((use->defVal == NULL) && (WXS_ATTRUSE_TYPEDEF(use) != NULL)) {]==] _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "3a78da4283035b2691688766e2bd6dda205a14cf36ce8430af3ec03677d2e80f")
        message(FATAL_ERROR "Pinned libxml2 wildcard ID reporting fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-wildcard-id-fix")
    set(_replacement "${binary_dir}/qore-wildcard-id-fix/xmlschemas.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied libxml2 wildcard ID reporting in the build tree")
endfunction()
