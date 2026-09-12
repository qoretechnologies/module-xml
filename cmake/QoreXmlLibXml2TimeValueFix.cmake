# Copyright (C) 2026 Qore Technologies, s.r.o.
# Compare XSD time values without inventing dates for nonzero offsets.
function(qore_xml_fix_libxml2_time_values source_dir binary_dir)
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
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemastypes.c for time value comparison")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "6e30d75155a3f9a6f452e0696ca479eeae9a9381edabdaa9a3e32cb9b06eeb13")
        return()
    endif()
    if(NOT _hash STREQUAL "6c8d53841944eff6e81c63dbd3059a0f27abb3bdd114e4aa04f56e1b69f6d2bd")
        message(FATAL_ERROR "Unexpected libxml2 xmlschemastypes.c; cannot apply time value comparison")
    endif()
    file(READ "${_path}" _source)
    string(REPLACE [==[    /*
     * if the same type then calculate the difference
     */
    if (x->type == y->type) {]==]
        [==[    /* xs:time has no date. Normalize both clock readings modulo one day
     * when they have the same timezone presence; adding a duration to only
     * the nonzero-offset operand invents unequal missing date fields.
     * Compare integer minutes separately to retain fractional-second precision. */
    if (x->type == XML_SCHEMAS_TIME && y->type == XML_SCHEMAS_TIME &&
        x->value.date.tz_flag == y->value.date.tz_flag) {
        int p = ((int)x->value.date.hour * 60 + (int)x->value.date.min
                 - x->value.date.tzo) % 1440;
        int q = ((int)y->value.date.hour * 60 + (int)y->value.date.min
                 - y->value.date.tzo) % 1440;
        if (p < 0) {
            p += 1440;
        }
        if (q < 0) {
            q += 1440;
        }
        if (p != q) {
            return (p < q ? -1 : 1);
        }
        if (x->value.date.sec != y->value.date.sec) {
            return (x->value.date.sec < y->value.date.sec ? -1 : 1);
        }
        return (0);
    }
    /*
     * if the same type then calculate the difference
     */
    if (x->type == y->type) {]==] _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "6e30d75155a3f9a6f452e0696ca479eeae9a9381edabdaa9a3e32cb9b06eeb13")
        message(FATAL_ERROR "Pinned libxml2 time value comparison fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-time-value-fix")
    set(_replacement "${binary_dir}/qore-time-value-fix/xmlschemastypes.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied libxml2 time value comparison assessment in the build tree")
endfunction()
