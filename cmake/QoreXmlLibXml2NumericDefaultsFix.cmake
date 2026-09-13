# Copyright (C) 2026 Qore Technologies, s.r.o.
# Assess canonical numeric/boolean/binary constraints under XSD 1.0.
function(qore_xml_fix_libxml2_numeric_defaults source_dir binary_dir)
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
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemas.c for numeric defaults")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "537c2cf44895f487c66c1fd2b07e76f87f408e264e75ce3cdb7a9f5ab0e6e11d")
        return()
    endif()
    if(NOT _hash STREQUAL "600f8d93bc1c8baf799e7de148e07ac3cda456b472d14b485498e20d8fd77583")
        message(FATAL_ERROR "Unexpected libxml2 xmlschemas.c; cannot apply numeric defaults")
    endif()
    file(READ "${_path}" _source)
    string(REPLACE [==[#include "private/error.h"]==]
        [==[#include "private/buf.h"
#include "private/error.h"]==] _source "${_source}")
    file(READ "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/libxml2-numeric-defaults.inc" _helper)
    string(REPLACE [==[static int
xmlSchemaParseCheckCOSValidDefault(]==]
        "${_helper}\nstatic int\nxmlSchemaParseCheckCOSValidDefault(" _source "${_source}")
    string(REPLACE [==[    if (ret < 0) {
	PERROR_INT("xmlSchemaParseCheckCOSValidDefault",]==]
        [==[    if (ret == 0 && val != NULL && *val != NULL) {
        xmlSchemaTypePtr simple = WXS_IS_SIMPLE(type) ? type : type->contentTypeDef;
        ret = qoreXmlCheckNumericDefault(ACTXT_CAST pctxt, node, simple, value, *val);
    }
    if (ret < 0) {
	PERROR_INT("xmlSchemaParseCheckCOSValidDefault",]==] _source "${_source}")
    string(REPLACE [==[	ret = xmlSchemaVCheckCVCSimpleType(ACTXT_CAST pctxt,
	    attr->node, WXS_ATTR_TYPEDEF(attr),
	    attr->defValue, &(attr->defVal),
	    1, 1, 0);]==]
        [==[	ret = xmlSchemaVCheckCVCSimpleType(ACTXT_CAST pctxt,
	    attr->node, WXS_ATTR_TYPEDEF(attr),
	    attr->defValue, &(attr->defVal),
	    1, 1, 0);
        if (ret == 0) {
            ret = qoreXmlCheckNumericDefault(ACTXT_CAST pctxt, attr->node,
                WXS_ATTR_TYPEDEF(attr), attr->defValue, attr->defVal);
        }]==] _source "${_source}")
    string(REPLACE [==[	ret = xmlSchemaVCheckCVCSimpleType(ACTXT_CAST ctxt,
	    use->node, WXS_ATTRUSE_TYPEDEF(use),
	    use->defValue, &(use->defVal),
	    1, 1, 0);]==]
        [==[	ret = xmlSchemaVCheckCVCSimpleType(ACTXT_CAST ctxt,
	    use->node, WXS_ATTRUSE_TYPEDEF(use),
	    use->defValue, &(use->defVal),
	    1, 1, 0);
        if (ret == 0) {
            ret = qoreXmlCheckNumericDefault(ACTXT_CAST ctxt, use->node,
                WXS_ATTRUSE_TYPEDEF(use), use->defValue, use->defVal);
        }]==] _source "${_source}")
    string(REPLACE [==[	* TODO: Don't care about the *canonical* stuff here, this requirement
	* will be removed in WXS 1.1 anyway.
]==]
        [==[	* Numeric and boolean members are checked in canonical form below.
]==] _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "537c2cf44895f487c66c1fd2b07e76f87f408e264e75ce3cdb7a9f5ab0e6e11d")
        message(FATAL_ERROR "Pinned libxml2 numeric defaults fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-numeric-defaults-fix")
    set(_replacement "${binary_dir}/qore-numeric-defaults-fix/xmlschemas.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied libxml2 numeric defaults assessment in the build tree")
endfunction()
