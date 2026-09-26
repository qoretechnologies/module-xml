# Copyright (C) 2026 Qore Technologies, s.r.o.
# Validate XSD 1.0 Name-derived datatypes with the XML 1.0 Second Edition name characters.
#
# XSD 1.0 Part 2 defines Name, NCName, QName and NMTOKEN, and ID, IDREF, ENTITY and the list types derived from
# them, with the productions of XML 1.0 Second Edition (Appendix B character classes). libxml2 2.15 validates them
# with the broader XML 1.0 Fifth Edition characters, so schema validation accepted values such as "Ͱa" or
# "\U00010000a" that XSD 1.0, Xerces and libxml2 before 2.15 reject. The schema processor now scans names with the
# Second Edition tables (XML_SCAN_OLD10); XML parsing, DTD validation and the public xmlValidate*() functions keep
# the Fifth Edition rules. Apply after every other fix of xmlschemas.c and xmlschemastypes.c.
function(qore_xml_fix_libxml2_name_edition source_dir binary_dir)
    get_target_property(_sources LibXml2 SOURCES)
    foreach(_filename IN ITEMS xmlschemastypes.c xmlschemas.c)
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
            message(FATAL_ERROR "Cannot locate libxml2 ${_filename} for XSD name characters")
        endif()
        if(IS_ABSOLUTE "${_input}")
            set(_path "${_input}")
        else()
            set(_path "${source_dir}/${_input}")
        endif()
        file(SHA256 "${_path}" _hash)
        if(_filename STREQUAL "xmlschemastypes.c")
            set(_original_hash 6debab3ae761ff1c04378c79e429ea85c4d9932604a50cf69d9f70b4daee61b3)
            set(_fixed_hash fa6cf776e777678ac2d706a62acd513a467a47b65a550717287f2189b1927707)
        else()
            set(_original_hash e04a1d236f1879c41c18d154db436d32e7bd21dcccd3eae0b4c1ed816ec3a0d9)
            set(_fixed_hash 0a948d8914296d9ca7a69fd55937f8950a12080f3ef22d4f3f5e6c493b351cfe)
        endif()
        if(_hash STREQUAL _fixed_hash)
            continue()
        endif()
        if(NOT _hash STREQUAL _original_hash)
            message(FATAL_ERROR "Unexpected libxml2 ${_filename}; cannot apply the XSD name character fix")
        endif()
        file(READ "${_path}" _source)
        # Every name check of the schema processor validates an XSD datatype.
        string(REPLACE "xmlValidateNMToken(" "xmlSchemaValidateNMToken10(" _source "${_source}")
        string(REPLACE "xmlValidateNCName(" "xmlSchemaValidateNCName10(" _source "${_source}")
        string(REPLACE "xmlValidateQName(" "xmlSchemaValidateQName10(" _source "${_source}")
        string(REPLACE "xmlValidateName(" "xmlSchemaValidateName10(" _source "${_source}")
        if(_filename STREQUAL "xmlschemastypes.c")
            string(REPLACE [==[#include "private/error.h"
#include "private/threads.h"
]==] [==[#include "private/error.h"
#include "private/threads.h"
#include "private/parser.h"

#include <stdint.h>

/*
 * Qore: XSD 1.0 defines Name, NCName, QName and NMTOKEN, and the types
 * derived from them, with the XML 1.0 Second Edition name productions
 * (Appendix B character classes). XML 1.0 parsing uses the Fifth Edition
 * characters since libxml2 2.15; the schema processor scans with the Second
 * Edition tables (XML_SCAN_OLD10), as libxml2 did before 2.15.
 */
XML_HIDDEN int xmlSchemaValidateName10(const xmlChar *value, int space);
XML_HIDDEN int xmlSchemaValidateNCName10(const xmlChar *value, int space);
XML_HIDDEN int xmlSchemaValidateQName10(const xmlChar *value, int space);
XML_HIDDEN int xmlSchemaValidateNMToken10(const xmlChar *value, int space);

/* Returns the end of the name that starts value, or NULL if none does. */
static const xmlChar *
xmlSchemaScanName10(const xmlChar *value, int flags) {
    const xmlChar *cur = xmlScanName(value, SIZE_MAX, flags | XML_SCAN_OLD10);

    return(((cur == NULL) || (cur == value)) ? NULL : cur);
}

static const xmlChar *
xmlSchemaSkipBlanks10(const xmlChar *cur, int space) {
    if (space) {
        while (IS_BLANK_CH(*cur))
            cur++;
    }
    return(cur);
}

static int
xmlSchemaValidateNameFlags10(const xmlChar *value, int space, int flags) {
    const xmlChar *cur;

    if (value == NULL)
        return(-1);
    cur = xmlSchemaScanName10(xmlSchemaSkipBlanks10(value, space), flags);
    if (cur == NULL)
        return(1);
    return(*xmlSchemaSkipBlanks10(cur, space) != 0);
}

int
xmlSchemaValidateName10(const xmlChar *value, int space) {
    return(xmlSchemaValidateNameFlags10(value, space, 0));
}

int
xmlSchemaValidateNCName10(const xmlChar *value, int space) {
    return(xmlSchemaValidateNameFlags10(value, space, XML_SCAN_NC));
}

int
xmlSchemaValidateNMToken10(const xmlChar *value, int space) {
    return(xmlSchemaValidateNameFlags10(value, space, XML_SCAN_NMTOKEN));
}

int
xmlSchemaValidateQName10(const xmlChar *value, int space) {
    const xmlChar *cur;

    if (value == NULL)
        return(-1);
    cur = xmlSchemaScanName10(xmlSchemaSkipBlanks10(value, space), XML_SCAN_NC);
    if (cur == NULL)
        return(1);
    if (*cur == ':') {
        cur = xmlSchemaScanName10(cur + 1, XML_SCAN_NC);
        if (cur == NULL)
            return(1);
    }
    return(*xmlSchemaSkipBlanks10(cur, space) != 0);
}
]==] _source "${_source}")
        else()
            string(REPLACE [==[#include "private/string.h"
]==] [==[#include "private/string.h"

/* Qore: XSD 1.0 name productions; see xmlschemastypes.c. */
XML_HIDDEN int xmlSchemaValidateNCName10(const xmlChar *value, int space);
XML_HIDDEN int xmlSchemaValidateQName10(const xmlChar *value, int space);
]==] _source "${_source}")
        endif()
        string(SHA256 _result_hash "${_source}")
        if(NOT _result_hash STREQUAL _fixed_hash)
            message(FATAL_ERROR "Pinned libxml2 XSD name character fix did not match ${_filename}")
        endif()
        file(MAKE_DIRECTORY "${binary_dir}/qore-name-edition-fix")
        set(_replacement "${binary_dir}/qore-name-edition-fix/${_filename}")
        file(WRITE "${_replacement}.tmp" "${_source}")
        configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
        list(REMOVE_ITEM _sources "${_input}")
        list(APPEND _sources "${_replacement}")
        message(STATUS "XML module: applied libxml2 XSD name character fix to ${_filename} in the build tree")
    endforeach()
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
endfunction()
