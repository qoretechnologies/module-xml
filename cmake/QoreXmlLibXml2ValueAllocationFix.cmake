# Copyright (C) 2026 Qore Technologies, s.r.o.
# Preserve scalar allocation errors and enforce unsigned lexical forms.
function(qore_xml_fix_libxml2_value_allocation source_dir binary_dir)
    get_target_property(_sources LibXml2 SOURCES)
    set(_input "")
    foreach(_entry IN LISTS _sources)
        get_filename_component(_name "${_entry}" NAME)
        if(_name STREQUAL "xmlschemastypes.c")
            if(_input)
                message(FATAL_ERROR "Duplicate libxml2 xmlschemastypes.c target source")
            endif()
            set(_input "${_entry}")
        endif()
    endforeach()
    if(NOT _input)
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemastypes.c for value allocation errors")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "ea2f33e8a41cb9da632115b0239767bc5c896369745f79f7c284a4f73736d960")
        return()
    endif()
    if(NOT _hash STREQUAL "6e30d75155a3f9a6f452e0696ca479eeae9a9381edabdaa9a3e32cb9b06eeb13")
        message(FATAL_ERROR "Unexpected libxml2 xmlschemastypes.c; cannot apply value allocation errors")
    endif()
    file(READ "${_path}" _source)
    string(REPLACE [==[                /* add sign */
                if (ret < 0)
                    goto valIntegerReturn1;
                decimal.str[0] = sign;]==]
        [==[                /* Keep allocation failure distinct from an invalid lexical. */
                if (ret == -1) {
                    xmlFree(decimal.str);
                    goto error;
                }
                if (ret < 0) {
                    goto valIntegerReturn1;
                }
                decimal.str[0] = sign;]==] _source "${_source}")
    string(REPLACE [==[                if (*cur == '-') {
                    sign = '-';
                    cur++;
                } else if (*cur == '+')
                    cur++;
                ret = xmlSchemaParseUInt(&cur, &decimal);]==]
        [==[                /* XSD 1.0 unsigned builtins have a digits-only lexical space.
                 * nonNegativeInteger, in contrast, permits signed zero. */
                if ((*cur == '+' || *cur == '-') &&
                    (type->builtInType == XML_SCHEMAS_ULONG ||
                     type->builtInType == XML_SCHEMAS_UINT ||
                     type->builtInType == XML_SCHEMAS_USHORT ||
                     type->builtInType == XML_SCHEMAS_UBYTE)) {
                    goto return1;
                }
                if (*cur == '-') {
                    sign = '-';
                    cur++;
                } else if (*cur == '+') {
                    cur++;
                }
                ret = xmlSchemaParseUInt(&cur, &decimal);]==] _source "${_source}")
    string(REPLACE [==[v->value.str = xmlStrdup(value);]==]
        [==[v->value.str = xmlStrdup(value);
                    if (v->value.str == NULL) {
                        xmlSchemaFreeValue(v);
                        goto error;
                    }]==] _source "${_source}")
    string(REPLACE [==[v->value.str = xmlStrndup(start, end - start);
		    *val = v;]==]
        [==[v->value.str = xmlStrndup(start, end - start);
                     if (v->value.str == NULL) {
                         xmlSchemaFreeValue(v);
                         goto error;
                     }
		    *val = v;]==] _source "${_source}")
    string(REPLACE [==[                    uri = xmlParseURI((const char *) tmpval);
		    xmlFree(tmpval);
                    if (uri == NULL)
                        goto return1;
                    xmlFreeURI(uri);]==]
        [==[                    ret = xmlParseURISafe((const char *) tmpval, &uri);
                    xmlFree(tmpval);
                    if (ret < 0) {
                        goto error;
                    }
                    if (ret != 0) {
                        goto return1;
                    }
                    xmlFreeURI(uri);]==] _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "ea2f33e8a41cb9da632115b0239767bc5c896369745f79f7c284a4f73736d960")
        message(FATAL_ERROR "Pinned libxml2 value allocation errors fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-value-allocation-fix")
    set(_replacement "${binary_dir}/qore-value-allocation-fix/xmlschemastypes.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied libxml2 value allocation errors assessment in the build tree")
endfunction()
