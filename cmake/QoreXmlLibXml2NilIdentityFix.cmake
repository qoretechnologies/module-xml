# Copyright (C) 2026 Qore Technologies, s.r.o.
# Apply the approved nil-as-missing identity value interpretation.
function(qore_xml_fix_libxml2_nil_identities source_dir binary_dir)
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
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemas.c for nil identity value")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "d3ea6afbb2128b714b8d2156515062b351a11fdfec4ba3928ee531a0b6f873c8")
        return()
    endif()
    if(NOT _hash STREQUAL "d9a04c6fd2030696ba7b226d6e7512bbefc3152fe2e958c708f1770c2d938973")
        message(FATAL_ERROR "Unexpected libxml2 xmlschemas.c; cannot apply nil identity value")
    endif()
    file(READ "${_path}" _source)
    string(REPLACE [==[	if (sto->type == XPATH_STATE_OBJ_TYPE_IDC_FIELD) {
            /* XSD 1.0]==] [==[	if (sto->type == XPATH_STATE_OBJ_TYPE_IDC_FIELD) {
            /* Nil has no identity value, but still counts as a selected node.
             * Keep an owned key with val == NULL until tuple qualification. */
            int nil = (vctxt->inode->nodeType == XML_ELEMENT_NODE) &&
                (vctxt->inode->flags & XML_SCHEMA_ELEM_INFO_NILLED);
            /* XSD 1.0]==] _source "${_source}")
    string(REPLACE [==[	    if ((key == NULL) && (vctxt->inode->val == NULL)) {]==] [==[	    if ((key == NULL) && (vctxt->inode->val == NULL) && !nil) {]==] _source "${_source}")
    string(REPLACE [==[		    key->val = vctxt->inode->val;
		    vctxt->inode->val = NULL;]==] [==[                    key->val = nil ? NULL : vctxt->inode->val;
                    if (!nil) {
                        vctxt->inode->val = NULL;
                    }]==] _source "${_source}")
    string(REPLACE [==[		if ((*keySeq)[i] == NULL) {
		    /*
		    * Not qualified, if not all fields did resolve.]==] [==[                if (((*keySeq)[i] == NULL) || ((*keySeq)[i]->val == NULL)) {
		    /*
		    * Not qualified, if any field is absent or nil.]==] _source "${_source}")
    string(REPLACE [==[		if (keySeq == NULL) {
		    xmlSchemaVErrMemory(NULL);]==] [==[		if (keySeq == NULL) {
		    xmlSchemaVErrMemory(vctxt);]==] _source "${_source}")
    string(REPLACE [==[		    if (key == NULL) {
			xmlSchemaVErrMemory(NULL);]==] [==[		    if (key == NULL) {
			xmlSchemaVErrMemory(vctxt);]==] _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "d3ea6afbb2128b714b8d2156515062b351a11fdfec4ba3928ee531a0b6f873c8")
        message(FATAL_ERROR "Pinned libxml2 nil identity value fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-nil-identity-fix")
    set(_replacement "${binary_dir}/qore-nil-identity-fix/xmlschemas.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied libxml2 nil identity value assessment in the build tree")
endfunction()
