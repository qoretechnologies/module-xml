# Copyright (C) 2026 Qore Technologies, s.r.o.
# libxml2 2.15.4 xmlResolveFromCatalog overwrites an owned temporary xmlError
# when restoring the previous error. Free that temporary before the assignment.
# Compile a corrected build-tree copy; never modify downloaded/offline sources.
function(qore_xml_fix_libxml2_catalog source_dir binary_dir)
    set(_original "${source_dir}/parserInternals.c")
    file(READ "${_original}" _source)
    set(_old "\n    *lastError = oldError;\n\n    return(code);\n")
    set(_new "\n    xmlResetError(lastError);\n    *lastError = oldError;\n\n    return(code);\n")
    string(FIND "${_source}" "${_new}" _already_fixed)
    if(NOT _already_fixed EQUAL -1)
        return()
    endif()
    # The fallback archive is pinned. Refuse an unexpected source override
    # rather than applying a guessed edit to different dependency code.
    file(SHA256 "${_original}" _hash)
    if(NOT _hash STREQUAL "62b005e11c8d9af96ee49bb4e9e5cc3f02dd3378d7d4cfb775a253dce43fe56b")
        message(FATAL_ERROR "Unexpected libxml2 parserInternals.c; cannot apply the catalog error ownership fix")
    endif()
    string(REPLACE "${_old}" "${_new}" _fixed "${_source}")
    if(_fixed STREQUAL _source)
        message(FATAL_ERROR "Pinned libxml2 catalog fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-catalog-fix")
    set(_replacement "${binary_dir}/qore-catalog-fix/parserInternals.c")
    # configure_file(COPYONLY) updates the compile input only when it changes.
    file(WRITE "${_replacement}.tmp" "${_fixed}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    get_target_property(_sources LibXml2 SOURCES)
    list(FIND _sources "parserInternals.c" _index)
    if(_index EQUAL -1)
        message(FATAL_ERROR "Cannot locate libxml2 catalog implementation in target sources")
    endif()
    list(REMOVE_AT _sources ${_index})
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    target_include_directories(LibXml2 PRIVATE "${source_dir}")
    message(STATUS "XML module: applied libxml2 catalog error ownership fix in the build tree")
endfunction()
