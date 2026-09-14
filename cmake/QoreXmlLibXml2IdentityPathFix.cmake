# Copyright (C) 2026 Qore Technologies, s.r.o.
# Reject empty paths and trailing union separators in the native pattern compiler.
function(qore_xml_fix_libxml2_identity_paths source_dir binary_dir)
    get_target_property(_sources LibXml2 SOURCES)
    set(_input "")
    foreach(_entry IN LISTS _sources)
        get_filename_component(_name "${_entry}" NAME)
        if(_name STREQUAL "pattern.c")
            if(_input)
                message(FATAL_ERROR "Duplicate libxml2 pattern.c target source")
            endif()
            set(_input "${_entry}")
        endif()
    endforeach()
    if(NOT _input)
        message(FATAL_ERROR "Cannot locate libxml2 pattern.c for identity XPath")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "6cfb68f5caa9e54dea6992164251c947be863ac07e93c06412f7d3f0372f9ec6")
        return()
    endif()
    if(NOT _hash STREQUAL "645f248f321015426fad6f8526fff549059d94abba81b5646708f5ede5908e8a")
        message(FATAL_ERROR "Unexpected libxml2 pattern.c; cannot apply identity XPath")
    endif()
    file(READ "${_path}" _source)
    string(REPLACE [==[    if (pattern == NULL) {]==]
        [==[    if ((pattern == NULL) || (pattern[0] == 0)) {]==] _source "${_source}")
    string(REPLACE [==[	else {
	    tmp = xmlStrndup(start, or - start);]==] [==[	else {
            /* A union separator requires another nonempty path. */
            if (or[1] == 0) {
                error = 1;
                goto error;
            }
	    tmp = xmlStrndup(start, or - start);]==] _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "6cfb68f5caa9e54dea6992164251c947be863ac07e93c06412f7d3f0372f9ec6")
        message(FATAL_ERROR "Pinned libxml2 identity XPath fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-identity-path-fix")
    set(_replacement "${binary_dir}/qore-identity-path-fix/pattern.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied libxml2 identity XPath assessment in the build tree")
endfunction()
