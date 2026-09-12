# Copyright (C) 2026 Qore Technologies, s.r.o.
# Compare validated fixed constraints in the XSD 1.0 value space.
function(qore_xml_fix_libxml2_fixed_values source_dir binary_dir)
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
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemas.c for typed fixed values")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "f133567c3025f2d8cbb0237b641c0661772eb6cd824abe66c3b0d47dd8d5c684")
        return()
    endif()
    if(NOT _hash STREQUAL "66f535648dac9eeb14727fb7b87550507beca80b9239fa371877931db93e2d0a")
        message(FATAL_ERROR "Unexpected libxml2 xmlschemas.c; cannot apply typed fixed values")
    endif()
    file(READ "${_path}" _source)
    string(REPLACE [==[    if (inode->flags & XML_SCHEMA_NODE_INFO_VALUE_NEEDED)
	return (xmlSchemaVCheckCVCSimpleType(]==]
        [==[    if ((inode->flags & XML_SCHEMA_NODE_INFO_VALUE_NEEDED) ||
        (inode->decl != NULL && (inode->decl->flags & XML_SCHEMAS_ELEM_FIXED)))
	return (xmlSchemaVCheckCVCSimpleType(]==] _source "${_source}")
    string(REPLACE [==[		    if (! xmlStrEqual(inode->value,
			    inode->decl->value)) {]==]
        [==[                    int equal = xmlSchemaAreValuesEqual(inode->val, inode->decl->defVal);
                    if (equal < 0) {
                        VERROR_INT("xmlSchemaValidatorPopElem", "comparing the fixed element value");
                        goto internal_error;
                    }
                    if (!equal) {]==] _source "${_source}")
    string(REPLACE [==[    int ret;

    while (x != NULL) {
	/* Same types. */]==]
        [==[    int ret;

    /* Empty lists have no value nodes; distinguish them from nonempty lists. */
    if (x == NULL || y == NULL) {
        return (x == y);
    }
    while (x != NULL) {
	/* Same types. */]==] _source "${_source}")
    string(REPLACE [==[    if ((inode->flags & XML_SCHEMA_NODE_INFO_VALUE_NEEDED) ||
        (inode->decl != NULL && (inode->decl->flags & XML_SCHEMAS_ELEM_FIXED)))
	return (xmlSchemaVCheckCVCSimpleType(
	    ACTXT_CAST vctxt, NULL,
	    type, value, &(inode->val), 1, 1, 0));
    else
	return (xmlSchemaVCheckCVCSimpleType(
	    ACTXT_CAST vctxt, NULL,
	    type, value, NULL, 1, 0, 0));]==]
        [==[    if ((inode->flags & XML_SCHEMA_NODE_INFO_VALUE_NEEDED) ||
        (inode->decl != NULL && (inode->decl->flags & XML_SCHEMAS_ELEM_FIXED))) {
        return (xmlSchemaVCheckCVCSimpleType(ACTXT_CAST vctxt, NULL,
            type, value, &(inode->val), 1, 1, 0));
    } else {
        return (xmlSchemaVCheckCVCSimpleType(ACTXT_CAST vctxt, NULL,
            type, value, NULL, 1, 0, 0));
    }]==] _source "${_source}")
    string(REPLACE [==[		    /*
		    * VAL TODO: *actual value* is the normalized value, impl.
		    *           this.
		    * VAL TODO: Report invalid & expected values as well.
		    * VAL TODO: Implement a comparison with the computed values.
		    */
]==]
        [==[                    /* Compare the already validated actual values. */
]==] _source "${_source}")
    string(REPLACE [==[	    tmpValue = xmlStrndup(cur, end - cur);
	    len++;]==]
        [==[	    tmpValue = xmlStrndup(cur, end - cur);
            if (tmpValue == NULL) {
                AERROR_INT("xmlSchemaVCheckCVCSimpleType", "copying a list item");
                goto internal_error;
            }
	    len++;]==] _source "${_source}")
    string(REPLACE [==[	ptx = xmlSchemaGetPrimitiveType(tx);
	pty = xmlSchemaGetPrimitiveType(ty);]==]
        [==[	ptx = xmlSchemaGetPrimitiveType(tx);
	pty = xmlSchemaGetPrimitiveType(ty);
        /* libxml2 stores an untyped anySimpleType value as a string.
         * Use that value family for equality with string restrictions;
         * the declared schema type and stored value stay unchanged. */
        if (WXS_IS_ANY_SIMPLE_TYPE(ptx)) {
            ptx = xmlSchemaGetBuiltInType(XML_SCHEMAS_STRING);
        }
        if (WXS_IS_ANY_SIMPLE_TYPE(pty)) {
            pty = xmlSchemaGetBuiltInType(XML_SCHEMAS_STRING);
        }]==] _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "f133567c3025f2d8cbb0237b641c0661772eb6cd824abe66c3b0d47dd8d5c684")
        message(FATAL_ERROR "Pinned libxml2 typed fixed values fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-fixed-value-fix")
    set(_replacement "${binary_dir}/qore-fixed-value-fix/xmlschemas.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied libxml2 typed fixed values assessment in the build tree")
endfunction()
