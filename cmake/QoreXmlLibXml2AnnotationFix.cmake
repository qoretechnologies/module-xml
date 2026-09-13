# Copyright (C) 2026 Qore Technologies, s.r.o.
# Validate XSD 1.0 annotation attributes by expanded name and declared type.
function(qore_xml_fix_libxml2_annotations source_dir binary_dir)
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
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemas.c for annotation attribute")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "76b6e1d1d3a5274693186762627f1a8979e7e9ff351b4f94c3629a2d34d5b742")
        return()
    endif()
    if(NOT _hash STREQUAL "6a53603c1b78e8f8894da3e52ed9b68635a223e7a11ac4b48a67825c3efbabd2")
        message(FATAL_ERROR "Unexpected libxml2 xmlschemas.c; cannot apply annotation attribute")
    endif()
    file(READ "${_path}" _source)
    string(REPLACE [==[		    if (xmlStrEqual(attr->ns->href, xmlSchemaNs) ||
			(xmlStrEqual(attr->name, BAD_CAST "lang") &&
			(!xmlStrEqual(attr->ns->href, XML_XML_NAMESPACE)))) {]==] [==[                    if (xmlStrEqual(attr->ns->href, xmlSchemaNs)) {]==] _source "${_source}")
    string(REPLACE [==[	    /*
	    * Attribute "xml:lang".
	    */]==] [==[            xmlSchemaPValAttr(ctxt, NULL, child, "source",
                xmlSchemaGetBuiltInType(XML_SCHEMAS_ANYURI), NULL);
	    /*
	    * Attribute "xml:lang".
	    */]==] _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "76b6e1d1d3a5274693186762627f1a8979e7e9ff351b4f94c3629a2d34d5b742")
        message(FATAL_ERROR "Pinned libxml2 annotation attribute fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-annotation-fix")
    set(_replacement "${binary_dir}/qore-annotation-fix/xmlschemas.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied libxml2 annotation attribute assessment in the build tree")
endfunction()
