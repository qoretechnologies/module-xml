# Copyright (C) 2026 Qore Technologies, s.r.o.
# Apply after the QName, URI and ENTITY fixes without modifying pinned source bytes.
set(_qore_xml_occurs_fix_dir "${CMAKE_CURRENT_LIST_DIR}")

function(qore_xml_fix_libxml2_occurs source_dir binary_dir)
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
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemas.c for occurrence parsing fix")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    set(_original_hash 955e8848f6446219f5b1546993ab55b27ed2512828c0cea5d6e30b6da1f3a105)
    set(_fixed_hash bb8e5f2681e4e9ad0add506fede46027bf02c973147f23c744701942e381d213)
    if(_hash STREQUAL _fixed_hash)
        return()
    endif()
    if(NOT _hash STREQUAL _original_hash)
        message(FATAL_ERROR "Unexpected libxml2 xmlschemas.c; cannot apply the occurrence parsing fix")
    endif()
    file(READ "${_path}" _source)
    string(FIND "${_source}" "\n/**\n * Get the maxOccurs property\n" _start)
    string(FIND "${_source}" "\n/**\n * Converts a boolean string value into 1 or 0.\n" _end)
    if(_start LESS 0 OR _end LESS _start)
        message(FATAL_ERROR "Cannot locate pinned libxml2 occurrence parser")
    endif()
    string(SUBSTRING "${_source}" 0 ${_start} _before)
    string(SUBSTRING "${_source}" ${_end} -1 _after)
    file(READ "${_qore_xml_occurs_fix_dir}/libxml2-occurs.inc" _replacement)
    set(_source "${_before}\n${_replacement}${_after}")
    # Local element declarations, like element references, contribute no particle
    # when both occurrence limits are zero (XSD 1.0 section 3.3.2).
    string(REPLACE [==[    if (topLevel)
	return ((xmlSchemaBasicItemPtr) decl);
    else {
	particle->children = (xmlSchemaTreeItemPtr) decl;
	return ((xmlSchemaBasicItemPtr) particle);
    }
]==]
        [==[    if (topLevel) {
        return ((xmlSchemaBasicItemPtr) decl);
    } else {
        particle->children = (xmlSchemaTreeItemPtr) decl;
        if ((min == 0) && (max == 0)) {
            return NULL;
        }
        return ((xmlSchemaBasicItemPtr) particle);
    }
]==] _source "${_source}")
    string(SHA256 _result_hash "${_source}")
    if(NOT _result_hash STREQUAL _fixed_hash)
        message(FATAL_ERROR "Pinned libxml2 occurrence fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-occurs-fix")
    set(_replacement "${binary_dir}/qore-occurs-fix/xmlschemas.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied libxml2 occurrence lexical parsing fix in the build tree")
endfunction()
