# Copyright (C) 2026 Qore Technologies, s.r.o.
# Enforce XSD 1.0 key fields against the assessed element declaration.
function(qore_xml_fix_libxml2_key_nillable source_dir binary_dir)
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
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemas.c for key nillable declaration")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "d9a04c6fd2030696ba7b226d6e7512bbefc3152fe2e958c708f1770c2d938973")
        return()
    endif()
    if(NOT _hash STREQUAL "783526c8640e5f59f7d48caa81fc2903728365500f647333e6a55deee195e141")
        message(FATAL_ERROR "Unexpected libxml2 xmlschemas.c; cannot apply key nillable declaration")
    endif()
    file(READ "${_path}" _source)
    string(REPLACE [==[	if (sto->type == XPATH_STATE_OBJ_TYPE_IDC_FIELD) {
	    /*
	    * NOTE: According to]==] [==[	if (sto->type == XPATH_STATE_OBJ_TYPE_IDC_FIELD) {
            /* XSD 1.0 cvc-identity-constraint 4.2.3 applies to the
             * field element's declaration, independently of xsi:nil. */
            if ((vctxt->inode->nodeType == XML_ELEMENT_NODE) &&
                (sto->matcher->aidc->def->type == XML_SCHEMA_TYPE_IDC_KEY) &&
                (vctxt->inode->decl != NULL) &&
                (vctxt->inode->decl->flags & XML_SCHEMAS_ELEM_NILLABLE)) {
                VERROR(XML_SCHEMAV_CVC_IDC,
                    WXS_BASIC_CAST sto->matcher->aidc->def,
                    "A key field cannot be assessed by a nillable element declaration");
                sto->nbHistory--;
                goto deregister_check;
            }
	    /*
	    * NOTE: According to]==] _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "d9a04c6fd2030696ba7b226d6e7512bbefc3152fe2e958c708f1770c2d938973")
        message(FATAL_ERROR "Pinned libxml2 key nillable declaration fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-key-nillable-fix")
    set(_replacement "${binary_dir}/qore-key-nillable-fix/xmlschemas.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied libxml2 key nillable declaration assessment in the build tree")
endfunction()
