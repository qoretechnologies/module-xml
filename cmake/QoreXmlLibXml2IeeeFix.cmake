# Copyright (C) 2026 Qore Technologies, s.r.o.
# Direct IEEE conversion and canonical XSD 1.0 float/double spelling.
function(qore_xml_fix_libxml2_ieee source_dir binary_dir)
    if(NOT CMAKE_CXX_COMPILER_LOADED)
        message(FATAL_ERROR "Enable CXX before creating LibXml2 for the private IEEE correction")
    endif()
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
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemastypes.c for IEEE conversion")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "b5ca81d4c9dc39164694404ce5f350d44ef544854dde4bbe3bad3973127419ff")
        return()
    endif()
    if(NOT _hash STREQUAL "5ee42ab1be11d50536bffe5f0f54d2080a0e79758c5d0ce33ee5d5a4cee580be")
        message(FATAL_ERROR "Unexpected libxml2 xmlschemastypes.c; cannot apply IEEE conversion")
    endif()
    file(READ "${_path}" _source)
    string(FIND "${_source}" "        case XML_SCHEMAS_FLOAT:\n        case XML_SCHEMAS_DOUBLE: {" _start)
    string(FIND "${_source}" "        case XML_SCHEMAS_BOOLEAN:{" _end)
    if(_start LESS 0 OR _end LESS _start)
        message(FATAL_ERROR "Cannot locate native IEEE validation block")
    endif()
    string(SUBSTRING "${_source}" 0 ${_start} _prefix)
    string(SUBSTRING "${_source}" ${_end} -1 _suffix)
    file(READ "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/libxml2-ieee-validation.inc" _validation)
    set(_source "${_prefix}${_validation}${_suffix}")
    string(FIND "${_source}" "\tcase XML_SCHEMAS_FLOAT: {" _start)
    string(SUBSTRING "${_source}" ${_start} -1 _rest)
    string(FIND "${_rest}" "\tdefault:" _length)
    if(_start LESS 0 OR _length LESS 0)
        message(FATAL_ERROR "Cannot locate native IEEE canonical block")
    endif()
    math(EXPR _end "${_start} + ${_length}")
    string(SUBSTRING "${_source}" 0 ${_start} _prefix)
    string(SUBSTRING "${_source}" ${_end} -1 _suffix)
    set(_canonical [==[        case XML_SCHEMAS_FLOAT:
        case XML_SCHEMAS_DOUBLE: {
            char text[64];
            int length = val->type == XML_SCHEMAS_FLOAT
                ? qoreXmlFormatFloat(val->value.f, text, sizeof(text))
                : qoreXmlFormatDouble(val->value.d, text, sizeof(text));
            if (length < 0) {
                return (-1);
            }
            *retValue = xmlStrdup(BAD_CAST text);
            break;
        }
]==])
    set(_source "${_prefix}${_canonical}${_suffix}")
    string(REPLACE "static int\nxmlSchemaValAtomicType(" [==[/* Private C ABI; implementations use locale-independent C++17 charconv. */
extern int qoreXmlFormatFloat(float value, char *output, size_t capacity);
extern int qoreXmlFormatDouble(double value, char *output, size_t capacity);
extern int qoreXmlParseFloat(const char *first, const char *last, float *output);
extern int qoreXmlParseDouble(const char *first, const char *last, double *output);

static int
xmlSchemaValAtomicType(]==] _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "b5ca81d4c9dc39164694404ce5f350d44ef544854dde4bbe3bad3973127419ff")
        message(FATAL_ERROR "Pinned libxml2 IEEE fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-ieee-fix")
    set(_replacement "${binary_dir}/qore-ieee-fix/xmlschemastypes.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}" "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/libxml2-ieee.cpp")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    target_compile_features(LibXml2 PRIVATE cxx_std_17)
    set_target_properties(LibXml2 PROPERTIES CXX_VISIBILITY_PRESET hidden)
    message(STATUS "XML module: applied libxml2 IEEE conversion in the build tree")
endfunction()
