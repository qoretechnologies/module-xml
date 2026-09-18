# Copyright (C) 2026 Qore Technologies, s.r.o.
# Validate XSD 1.0 absolute anyURI content independently of RFC 3986 resolution.
function(qore_xml_fix_libxml2_anyuri source_dir binary_dir)
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
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemastypes.c for anyURI content")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "3957d5387654b6a5b1bc150c995fea4a96dbfc5eee55818a6d3334e258c30baf")
        return()
    endif()
    if(NOT _hash STREQUAL "68dda4b794ceb9bd8819c6158f1917b062b021f9017ab4bcb11a6b3886040d97")
        message(FATAL_ERROR "Unexpected libxml2 xmlschemastypes.c; cannot apply anyURI content")
    endif()
    file(READ "${_path}" _source)
    string(REPLACE [==[                    if (ret != 0) {
                        goto return1;
                    }
                    xmlFreeURI(uri);
]==] [==[                    if (ret != 0) {
                        goto return1;
                    }
                    /* XSD 1.0 retains RFC 2396: an absolute URI needs a
                     * hierarchical or opaque part before its fragment.
                     * The shared RFC 3986 parser also accepts empty parts. */
                    if (uri->scheme != NULL) {
                        const xmlChar *part = value + strlen(uri->scheme) + 1;
                        if ((*part == 0) || (*part == '#')) {
                            xmlFreeURI(uri);
                            goto return1;
                        }
                    }
                    xmlFreeURI(uri);
]==] _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "3957d5387654b6a5b1bc150c995fea4a96dbfc5eee55818a6d3334e258c30baf")
        message(FATAL_ERROR "Pinned libxml2 anyURI content fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-anyuri-fix")
    set(_replacement "${binary_dir}/qore-anyuri-fix/xmlschemastypes.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied libxml2 anyURI content assessment in the build tree")
endfunction()
