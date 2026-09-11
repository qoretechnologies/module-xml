# Copyright (C) 2026 Qore Technologies, s.r.o.
# Apply the normative source-schema default to anonymous simple types.
function(qore_xml_fix_libxml2_type_finals source_dir binary_dir)
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
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemas.c for type final defaults")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "250a17b9625c8996116bc3c1e103e8463fbc018c2b83170bfa754d555e627c1e")
        return()
    endif()
    if(NOT _hash STREQUAL "b519fc7f08c902a01b328307f8c7b43f510b366c6641c3b5974b5f0da2f6637d")
        message(FATAL_ERROR "Unexpected libxml2 xmlschemas.c; cannot apply type final defaults")
    endif()
    file(READ "${_path}" _source)
    string(REPLACE [==[	type->type = XML_SCHEMA_TYPE_SIMPLE;
	type->contentType = XML_SCHEMA_CONTENT_SIMPLE;
	/*
	* Check for illegal attributes.
]==] [==[	type->type = XML_SCHEMA_TYPE_SIMPLE;
	type->contentType = XML_SCHEMA_CONTENT_SIMPLE;
        /* XSD 1.0 Datatypes 4.1.2 applies finalDefault to anonymous types too. */
        if (schema->flags & XML_SCHEMAS_FINAL_DEFAULT_RESTRICTION) {
            type->flags |= XML_SCHEMAS_TYPE_FINAL_RESTRICTION;
        }
        if (schema->flags & XML_SCHEMAS_FINAL_DEFAULT_LIST) {
            type->flags |= XML_SCHEMAS_TYPE_FINAL_LIST;
        }
        if (schema->flags & XML_SCHEMAS_FINAL_DEFAULT_UNION) {
            type->flags |= XML_SCHEMAS_TYPE_FINAL_UNION;
        }
	/*
	* Check for illegal attributes.
]==] _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "250a17b9625c8996116bc3c1e103e8463fbc018c2b83170bfa754d555e627c1e")
        message(FATAL_ERROR "Pinned libxml2 type final default fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-type-final-fix")
    set(_replacement "${binary_dir}/qore-type-final-fix/xmlschemas.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied libxml2 anonymous type final defaults in the build tree")
endfunction()
