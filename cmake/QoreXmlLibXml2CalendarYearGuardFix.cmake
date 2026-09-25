# Copyright (C) 2026 Qore Technologies, s.r.o.
# Guard the year decrement of the exact calendar fix (libxml2-calendar.inc) against an all-zero year label.
#
# Validated XSD 1.0 year labels are nonzero and decrementing year 0001 changes the sign instead, so the decrement
# always finds a nonzero digit; the guard makes the invariant explicit instead of writing before the buffer if it
# were ever violated (GCC -Wstringop-overflow in optimized builds).
function(qore_xml_fix_libxml2_calendar_year_guard source_dir binary_dir)
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
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemastypes.c for the calendar year guard")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "6debab3ae761ff1c04378c79e429ea85c4d9932604a50cf69d9f70b4daee61b3")
        return()
    endif()
    if(NOT _hash STREQUAL "3957d5387654b6a5b1bc150c995fea4a96dbfc5eee55818a6d3334e258c30baf")
        message(FATAL_ERROR "Unexpected libxml2 xmlschemastypes.c; cannot apply the calendar year guard")
    endif()
    file(READ "${_path}" _source)
    string(REPLACE [==[        while (i != 0 && next[i - 1] == '0') {
            next[--i] = '9';
        }
        --next[i - 1];]==] [==[        while (i != 0 && next[i - 1] == '0') {
            next[--i] = '9';
        }
        /* validated year labels are nonzero, so a nonzero digit remains */
        if (i == 0) {
            xmlFree(next);
            return -1;
        }
        --next[i - 1];]==] _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "6debab3ae761ff1c04378c79e429ea85c4d9932604a50cf69d9f70b4daee61b3")
        message(FATAL_ERROR "Pinned libxml2 calendar year guard did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-calendar-year-guard")
    set(_replacement "${binary_dir}/qore-calendar-year-guard/xmlschemastypes.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied the libxml2 calendar year guard in the build tree")
endfunction()
