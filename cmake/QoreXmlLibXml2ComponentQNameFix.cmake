# Copyright (C) 2026 Qore Technologies, s.r.o.
# Normalize schema component QNames before namespace and component lookup.
function(qore_xml_fix_libxml2_component_qnames source_dir binary_dir)
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
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemas.c for component QName")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "783526c8640e5f59f7d48caa81fc2903728365500f647333e6a55deee195e141")
        return()
    endif()
    if(NOT _hash STREQUAL "76b6e1d1d3a5274693186762627f1a8979e7e9ff351b4f94c3629a2d34d5b742")
        message(FATAL_ERROR "Unexpected libxml2 xmlschemas.c; cannot apply component QName")
    endif()
    file(READ "${_path}" _source)
    file(READ "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/libxml2-component-qname.inc" _replacement_source)
    string(REPLACE [==[static int
xmlSchemaPValAttrNodeQNameValue(xmlSchemaParserCtxtPtr ctxt,
				       xmlSchemaPtr schema,
				       xmlSchemaBasicItemPtr ownerItem,
				       xmlAttrPtr attr,
				       const xmlChar *value,
				       const xmlChar **uri,
				       const xmlChar **local)
{
    const xmlChar *pref;
    xmlNsPtr ns;
    int len, ret;

    *uri = NULL;
    *local = NULL;
    ret = xmlValidateQName(value, 1);
    if (ret > 0) {
	xmlSchemaPSimpleTypeErr(ctxt,
	    XML_SCHEMAP_S4S_ATTR_INVALID_VALUE,
	    ownerItem, (xmlNodePtr) attr,
	    xmlSchemaGetBuiltInType(XML_SCHEMAS_QNAME),
	    NULL, value, NULL, NULL, NULL);
	*local = value;
	return (ctxt->err);
    } else if (ret < 0)
	return (-1);

    if (!strchr((char *) value, ':')) {
	ns = xmlSearchNs(attr->doc, attr->parent, NULL);
	if (ns && ns->href && ns->href[0])
	    *uri = xmlDictLookup(ctxt->dict, ns->href, -1);
	else if (schema->flags & XML_SCHEMAS_INCLUDING_CONVERT_NS) {
	    /* TODO: move XML_SCHEMAS_INCLUDING_CONVERT_NS to the
	    * parser context. */
	    /*
	    * This one takes care of included schemas with no
	    * target namespace.
	    */
	    *uri = ctxt->targetNamespace;
	}
	*local = xmlDictLookup(ctxt->dict, value, -1);
	return (0);
    }
    /*
    * At this point xmlSplitQName3 has to return a local name.
    */
    *local = xmlSplitQName3(value, &len);
    *local = xmlDictLookup(ctxt->dict, *local, -1);
    pref = xmlDictLookup(ctxt->dict, value, len);
    ns = xmlSearchNs(attr->doc, attr->parent, pref);
    if (ns == NULL) {
	xmlSchemaPSimpleTypeErr(ctxt,
	    XML_SCHEMAP_S4S_ATTR_INVALID_VALUE,
	    ownerItem, (xmlNodePtr) attr,
	    xmlSchemaGetBuiltInType(XML_SCHEMAS_QNAME), NULL, value,
	    "The value '%s' of simple type 'xs:QName' has no "
	    "corresponding namespace declaration in scope", value, NULL);
	return (ctxt->err);
    } else {
        *uri = xmlDictLookup(ctxt->dict, ns->href, -1);
    }
    return (0);
}
]==] "${_replacement_source}" _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "783526c8640e5f59f7d48caa81fc2903728365500f647333e6a55deee195e141")
        message(FATAL_ERROR "Pinned libxml2 component QName fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-component-qname-fix")
    set(_replacement "${binary_dir}/qore-component-qname-fix/xmlschemas.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied libxml2 component QName assessment in the build tree")
endfunction()
