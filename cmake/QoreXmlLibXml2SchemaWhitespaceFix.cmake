# Copyright (C) 2026 Qore Technologies, s.r.o.
# Treat declaration CDATA as character content; retain complete annotation subtrees.
function(qore_xml_fix_libxml2_schema_whitespace source_dir binary_dir)
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
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemas.c for schema declaration whitespace")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "a3db543b225021533cf966759c304f7a955ef85b1b645c1828334413b61b7004")
        return()
    endif()
    if(NOT _hash STREQUAL "75e468136eaa0dbf8c95071194d41937d6da6f188ee799a47cf50902a98ad65b")
        message(FATAL_ERROR "Unexpected libxml2 xmlschemas.c; cannot apply schema declaration whitespace")
    endif()
    file(READ "${_path}" _source)
    string(REPLACE [==[    (((n)->type == XML_TEXT_NODE) && (xmlSchemaIsBlank((n)->content, -1)))]==]
        [==[    ((((n)->type == XML_TEXT_NODE) || ((n)->type == XML_CDATA_SECTION_NODE)) && \
     (xmlSchemaIsBlank((n)->content, -1)))]==] _source "${_source}")
    string(REPLACE [==[        if (cur->type == XML_TEXT_NODE) {
            if (IS_BLANK_NODE(cur)) {
                if (xmlNodeGetSpacePreserve(cur) != 1) {
                    delete = cur;
                }
            }
]==]
        [==[        /* Annotation payload is not schema declaration content. */
        if (IS_SCHEMA(cur, "appinfo") || IS_SCHEMA(cur, "documentation")) {
            goto skip_children;
        }
        if ((cur->type == XML_TEXT_NODE) || (cur->type == XML_CDATA_SECTION_NODE)) {
            if (IS_BLANK_NODE(cur)) {
                /* Declaration whitespace is ignorable even with xml:space. */
                delete = cur;
            }
]==] _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "a3db543b225021533cf966759c304f7a955ef85b1b645c1828334413b61b7004")
        message(FATAL_ERROR "Pinned libxml2 schema declaration whitespace fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-schema-whitespace-fix")
    set(_replacement "${binary_dir}/qore-schema-whitespace-fix/xmlschemas.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied libxml2 schema declaration whitespace assessment in the build tree")
endfunction()
