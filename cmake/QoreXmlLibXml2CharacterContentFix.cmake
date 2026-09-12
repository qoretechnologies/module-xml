# Copyright (C) 2026 Qore Technologies, s.r.o.
# Assess character children independently of XML text/CDATA event boundaries.
function(qore_xml_fix_libxml2_character_content source_dir binary_dir)
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
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemas.c for instance character content")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "66f535648dac9eeb14727fb7b87550507beca80b9239fa371877931db93e2d0a")
        return()
    endif()
    if(NOT _hash STREQUAL "a3db543b225021533cf966759c304f7a955ef85b1b645c1828334413b61b7004")
        message(FATAL_ERROR "Unexpected libxml2 xmlschemas.c; cannot apply instance character content")
    endif()
    file(READ "${_path}" _source)
    string(REPLACE [==[		  int nodeType, const xmlChar *value, int len,]==]
        [==[		  const xmlChar *value, int len,]==] _source "${_source}")
    string(REPLACE [==[    if (consumed != NULL)
	*consumed = 0;
    if (INODE_NILLED(vctxt->inode)) {]==]
        [==[    if (consumed != NULL)
	*consumed = 0;
    /* Empty text/CDATA events have no character information item children.
     * Do not consume a reader-owned value or discard the element default. */
    if ((value == NULL) || (len == 0) || ((len < 0) && (value[0] == 0))) {
        return (0);
    }
    vctxt->inode->flags &= ~XML_SCHEMA_ELEM_INFO_EMPTY;
    if (INODE_NILLED(vctxt->inode)) {]==] _source "${_source}")
    string(REPLACE [==[	if ((nodeType != XML_TEXT_NODE) ||
	    (! xmlSchemaIsBlank((xmlChar *) value, len))) {]==]
        [==[	if (!xmlSchemaIsBlank((xmlChar *) value, len)) {]==] _source "${_source}")
    string(REPLACE [==[    if (vctxt->inode->flags & XML_SCHEMA_ELEM_INFO_EMPTY)
	vctxt->inode->flags ^= XML_SCHEMA_ELEM_INFO_EMPTY;
]==]
        [==[]==] _source "${_source}")
    string(REPLACE [==[	    if ((ielem != NULL) && (ielem->flags & XML_SCHEMA_ELEM_INFO_EMPTY))
		ielem->flags ^= XML_SCHEMA_ELEM_INFO_EMPTY;
]==]
        [==[]==] _source "${_source}")
    string(REPLACE [==[xmlSchemaVPushText(vctxt, XML_TEXT_NODE, ch, len,]==]
        [==[xmlSchemaVPushText(vctxt, ch, len,]==] _source "${_source}")
    string(REPLACE [==[xmlSchemaVPushText(vctxt, XML_CDATA_SECTION_NODE, ch, len,]==]
        [==[xmlSchemaVPushText(vctxt, ch, len,]==] _source "${_source}")
    string(REPLACE [==[xmlSchemaVPushText(vctxt, node->type, node->content,]==]
        [==[xmlSchemaVPushText(vctxt, node->content,]==] _source "${_source}")
    string(REPLACE [==[xmlSchemaVPushText(vctxt, nodeType, BAD_CAST value,]==]
        [==[xmlSchemaVPushText(vctxt, BAD_CAST value,]==] _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "66f535648dac9eeb14727fb7b87550507beca80b9239fa371877931db93e2d0a")
        message(FATAL_ERROR "Pinned libxml2 instance character content fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-character-content-fix")
    set(_replacement "${binary_dir}/qore-character-content-fix/xmlschemas.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied libxml2 instance character content assessment in the build tree")
endfunction()
