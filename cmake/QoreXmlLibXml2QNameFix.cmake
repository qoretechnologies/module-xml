# Copyright (C) 2026 Qore Technologies, s.r.o.
# Correct QName identity at the dependency's lookup/comparison boundaries.
# Compile build-tree copies and preserve the checksum-pinned upstream sources.
function(qore_xml_replace_libxml2_qname_source source_dir binary_dir filename original_hash fixed_hash old new)
    set(_original "${source_dir}/${filename}")
    file(SHA256 "${_original}" _hash)
    if(_hash STREQUAL fixed_hash)
        return()
    endif()
    if(NOT _hash STREQUAL original_hash)
        message(FATAL_ERROR "Unexpected libxml2 ${filename}; cannot apply the QName identity fix")
    endif()
    file(READ "${_original}" _source)
    string(REPLACE "${old}" "${new}" _fixed "${_source}")
    string(SHA256 _fixed_hash "${_fixed}")
    if(NOT _fixed_hash STREQUAL fixed_hash)
        message(FATAL_ERROR "Pinned libxml2 QName fix did not match ${filename}")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-qname-fix")
    set(_replacement "${binary_dir}/qore-qname-fix/${filename}")
    file(WRITE "${_replacement}.tmp" "${_fixed}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    get_target_property(_sources LibXml2 SOURCES)
    list(FIND _sources "${filename}" _index)
    if(_index EQUAL -1)
        message(FATAL_ERROR "Cannot locate libxml2 ${filename} in target sources")
    endif()
    list(REMOVE_AT _sources ${_index})
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    target_include_directories(LibXml2 PRIVATE "${source_dir}")
    message(STATUS "XML module: applied libxml2 QName identity fix to ${filename} in the build tree")
endfunction()

function(qore_xml_fix_libxml2_qnames source_dir binary_dir)
    qore_xml_replace_libxml2_qname_source("${source_dir}" "${binary_dir}" xmlschemas.c
        bed8bfbfd61a2025b67b7a0e4d05ce50093e7a6bb5e43a3ebac343b8df4329a7
        e7910a943964ce25bac32479fec4b244e1b0080abd6ae7146210d88ca3877098
        "{\n    if (vctxt->sax != NULL) {\n"
        "{\n    /* The xml prefix is bound even without a namespace declaration. */\n    if (xmlStrEqual(prefix, BAD_CAST \"xml\")) {\n        return (XML_XML_NAMESPACE);\n    }\n    if (vctxt->sax != NULL) {\n")
    qore_xml_replace_libxml2_qname_source("${source_dir}" "${binary_dir}" xmlschemastypes.c
        08cac7d1dbdb617688ac5b36ab6fee75f634e5bf0372aa0e6569a0bebe3b0c8f
        714fdfd7fdde878bea05d970cb1035ba3ca8d305d0cee55c87806a5917b07f30
        "\t\t    (xmlStrEqual(x->value.qname.uri, y->value.qname.uri)))"
        "\t\t    (xmlStrEqual(x->value.qname.uri ? x->value.qname.uri : BAD_CAST \"\",\n                                y->value.qname.uri ? y->value.qname.uri : BAD_CAST \"\")))")
endfunction()
