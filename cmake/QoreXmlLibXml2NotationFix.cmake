# Copyright (C) 2026 Qore Technologies, s.r.o.
# Validate XSD 1.0 notation declarations and enumeration-derived type uses.
function(qore_xml_fix_libxml2_notations source_dir binary_dir)
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
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemas.c for notation declaration and type-use")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "6a53603c1b78e8f8894da3e52ed9b68635a223e7a11ac4b48a67825c3efbabd2")
        return()
    endif()
    if(NOT _hash STREQUAL "e55e7f6d2189d5d8658f7c1aaefb1b0ea25bf7cafb3c445f828b6f81ace6cfab")
        message(FATAL_ERROR "Unexpected libxml2 xmlschemas.c; cannot apply notation declaration and type-use")
    endif()
    file(READ "${_path}" _source)
    file(READ "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/libxml2-notation-parse.inc" _parser)
    string(FIND "${_source}" "static xmlSchemaNotationPtr\nxmlSchemaParseNotation(" _start)
    if(_start LESS 0)
        message(FATAL_ERROR "Cannot locate libxml2 notation parser")
    endif()
    string(SUBSTRING "${_source}" ${_start} -1 _rest)
    string(FIND "${_rest}" "\n/**" _length)
    if(_length LESS 0)
        message(FATAL_ERROR "Cannot locate libxml2 notation parser end")
    endif()
    math(EXPR _end "${_start} + ${_length}")
    string(SUBSTRING "${_source}" 0 ${_start} _prefix)
    string(SUBSTRING "${_source}" ${_end} -1 _suffix)
    set(_source "${_prefix}${_parser}${_suffix}")
    file(READ "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/libxml2-notation-use.inc" _uses)
    string(REPLACE "static int\nxmlSchemaCheckAttrPropsCorrect("
        "${_uses}\nstatic int\nxmlSchemaCheckAttrPropsCorrect(" _source "${_source}")
    string(REPLACE [==[    /*
    * Apply some constraints for element declarations.
    */]==] [==[    if (qoreXmlCheckNotationUses(pctxt, items, nbItems) != 0) {
        goto exit_error;
    }

    /*
    * Apply some constraints for element declarations.
    */]==] _source "${_source}")
    string(REPLACE [==[    val = xmlNodeGetContent(node);
    if (val == NULL)
	val = xmlStrdup((xmlChar *)"");]==] [==[    val = node == NULL ? xmlStrdup(BAD_CAST "") : xmlNodeGetContent(node);
    if (val == NULL) {
        xmlSchemaPErrMemory(ctxt);
        return NULL;
    }]==] _source "${_source}")
    string(REPLACE [==[    value = xmlSchemaGetNodeContentNoDict((xmlNodePtr) attr);
    ret = xmlValidateNCName(value, 1);]==] [==[    value = xmlSchemaGetNodeContentNoDict((xmlNodePtr) attr);
    if (value == NULL) {
        xmlSchemaPErrMemory(ctxt);
        return -1;
    }
    ret = xmlValidateNCName(value, 1);]==] _source "${_source}")
    string(REPLACE [==[	    xmlChar *strip;
            int res;

	    /*
	    * TODO: Use xmlSchemaStrip here; it's not exported at this
	    * moment.
	    */
	    strip = xmlSchemaCollapseString(value);
	    if (strip != NULL) {
		xmlFree((xmlChar *) value);
		value = strip;
	    }
	    res = xmlAddIDSafe(attr, value);]==] [==[            const xmlChar *start = value, *end;
            size_t length;
            int res;

            /* NCName validation already forbids internal whitespace. Trim the
             * owned buffer in place, without an ambiguous nullable allocation. */
            while (IS_BLANK_CH(*start)) {
                ++start;
            }
            end = start + xmlStrlen(start);
            while (end > start && IS_BLANK_CH(end[-1])) {
                --end;
            }
            length = (size_t) (end - start);
            memmove((xmlChar *) value, start, length);
            ((xmlChar *) value)[length] = 0;
            res = xmlAddIDSafe(attr, value);]==] _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "6a53603c1b78e8f8894da3e52ed9b68635a223e7a11ac4b48a67825c3efbabd2")
        message(FATAL_ERROR "Pinned libxml2 notation declaration and type-use fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-notation-fix")
    set(_replacement "${binary_dir}/qore-notation-fix/xmlschemas.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied libxml2 notation declaration and type-use assessment in the build tree")
endfunction()
