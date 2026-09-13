# Copyright (C) 2026 Qore Technologies, s.r.o.
# Own exact calendar components throughout parsing, comparison and formatting.
function(qore_xml_fix_libxml2_calendar source_dir binary_dir)
    function(_qore_xml_calendar_block begin end replacement)
        string(FIND "${_source}" "${begin}" _start)
        if(_start LESS 0)
            message(FATAL_ERROR "Cannot locate native calendar block: ${begin}")
        endif()
        string(SUBSTRING "${_source}" ${_start} -1 _rest)
        string(FIND "${_rest}" "${end}" _length)
        if(_length LESS 0)
            message(FATAL_ERROR "Cannot locate native calendar block end: ${end}")
        endif()
        math(EXPR _end "${_start} + ${_length}")
        string(SUBSTRING "${_source}" 0 ${_start} _prefix)
        string(SUBSTRING "${_source}" ${_end} -1 _suffix)
        set(_source "${_prefix}${replacement}${_suffix}" PARENT_SCOPE)
    endfunction()
    set(_cases "")
    foreach(_type DATETIME TIME DATE GYEAR GYEARMONTH GMONTH GMONTHDAY GDAY)
        string(APPEND _cases "        case XML_SCHEMAS_${_type}:\n")
    endforeach()
    foreach(_filename xmlschemastypes.c xmlschemas.c)
        get_target_property(_sources LibXml2 SOURCES)
        set(_input "")
        foreach(_entry IN LISTS _sources)
            get_filename_component(_name "${_entry}" NAME)
            if(_name STREQUAL _filename)
                if(_input)
                    message(FATAL_ERROR "Duplicate libxml2 ${_filename} target source")
                endif()
                set(_input "${_entry}")
            endif()
        endforeach()
        if(NOT _input)
            message(FATAL_ERROR "Cannot locate libxml2 ${_filename} for exact calendars")
        endif()
        if(IS_ABSOLUTE "${_input}")
            set(_path "${_input}")
        else()
            set(_path "${source_dir}/${_input}")
        endif()
        if(_filename STREQUAL "xmlschemastypes.c")
            set(_original_hash b5ca81d4c9dc39164694404ce5f350d44ef544854dde4bbe3bad3973127419ff)
            set(_fixed_hash ef29c959276faab580a51e192a7e2f6ac25d187e36cdc0cbbea2fc41e08649b1)
        else()
            set(_original_hash 94d7a4f40ae09c15dad7c4d40f98b8042c294d943401abc03b530eeb2075e35d)
            set(_fixed_hash 64f3d39c4c022aa7dcda27020259ebe500c0a6f0fcfaa93d421a3852ba7f9513)
        endif()
        file(SHA256 "${_path}" _hash)
        if(_hash STREQUAL _fixed_hash)
            continue()
        endif()
        if(NOT _hash STREQUAL _original_hash)
            message(FATAL_ERROR "Unexpected libxml2 ${_filename}; cannot apply exact calendars")
        endif()
        file(READ "${_path}" _source)
        if(_filename STREQUAL "xmlschemastypes.c")
            file(READ "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/libxml2-calendar-type.inc" _type)
            file(READ "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/libxml2-calendar.inc" _implementation)
            _qore_xml_calendar_block("/* Date value */" "/* Duration value */" "${_type}\n")
            _qore_xml_calendar_block("/**\n * Parses a xs:gYear" "/**\n * Converts a base64" "")
            _qore_xml_calendar_block("/**\n * Check that `dateTime`" "/**\n * Check that `duration`" "${_implementation}\n")
            _qore_xml_calendar_block("/**\n * Compute a new date/time" "/**\n * Compare 2 string" "")
            foreach(_name daysInMonth daysInMonthLeap dayInYearByMonth dayInLeapYearByMonth)
                string(REGEX REPLACE "static const (unsigned int|long) ${_name}\\[12\\] =[ \t\r\n]*\\{[^}]+\\};\n" "" _source "${_source}")
            endforeach()
            string(REPLACE [==[xmlSchemaFreeValue(xmlSchemaVal *value) {
    xmlSchemaValPtr prev;

    while (value != NULL) {
	switch (value->type) {]==]
                "xmlSchemaFreeValue(xmlSchemaVal *value) {\n    xmlSchemaValPtr prev;\n\n    while (value != NULL) {\n\tswitch (value->type) {\n${_cases}            xmlFree(value->value.date.year);\n            xmlFree(value->value.date.fraction);\n            break;" _source "${_source}")
            string(REPLACE [==[    memcpy(ret, v, sizeof(xmlSchemaVal));
    ret->next = NULL;
    return ret;]==] [==[    memcpy(ret, v, sizeof(xmlSchemaVal));
    ret->next = NULL;
    if (qoreXmlCalendarType(v->type) && qoreXmlCalendarCopy(&ret->value.date, &v->value.date) != 0) {
        xmlFree(ret);
        return NULL;
    }
    return ret;]==] _source "${_source}")
            _qore_xml_calendar_block("\tcase XML_SCHEMAS_GYEAR: {" "\tcase XML_SCHEMAS_HEXBINARY:"
                "${_cases}            return qoreXmlCalendarCanonical(val, retValue);\n")
        else()
            string(REPLACE [==[qoreXmlNeedsCanonicalDefault(xmlSchemaValPtr val)
{
    switch (xmlSchemaGetValType(val)) {]==] [==[qoreXmlNeedsCanonicalDefault(xmlSchemaValPtr val)
{
    switch (xmlSchemaGetValType(val)) {
        case XML_SCHEMAS_DATETIME:
        case XML_SCHEMAS_TIME:
        case XML_SCHEMAS_DATE:]==] _source "${_source}")
        endif()
        string(SHA256 _hash "${_source}")
        if(NOT _hash STREQUAL _fixed_hash)
            message(FATAL_ERROR "Pinned libxml2 exact calendar fix did not match ${_filename}: ${_hash}")
        endif()
        file(MAKE_DIRECTORY "${binary_dir}/qore-calendar-fix")
        set(_replacement "${binary_dir}/qore-calendar-fix/${_filename}")
        file(WRITE "${_replacement}.tmp" "${_source}")
        configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
        list(REMOVE_ITEM _sources "${_input}")
        list(APPEND _sources "${_replacement}")
        set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
        message(STATUS "XML module: applied exact libxml2 calendars to ${_filename}")
    endforeach()
endfunction()
