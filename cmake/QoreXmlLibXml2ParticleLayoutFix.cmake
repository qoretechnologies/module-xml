# Copyright (C) 2026 Qore Technologies, s.r.o.
# Keep builtin and parsed schema particles on the same private layout.
set(_qore_xml_particle_layout_fix_dir "${CMAKE_CURRENT_LIST_DIR}")
function(qore_xml_fix_libxml2_particle_layout source_dir binary_dir)
    file(SHA256 "${_qore_xml_particle_layout_fix_dir}/libxml2-particle-layout.h" _header_hash)
    if(NOT _header_hash STREQUAL "8df8edbee88e2f7806043996af823c99f8234b1047614f8c30daca0e8893c022")
        message(FATAL_ERROR "Unexpected shared libxml2 particle layout")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-particle-layout-fix")
    configure_file("${_qore_xml_particle_layout_fix_dir}/libxml2-particle-layout.h"
                   "${binary_dir}/qore-particle-layout-fix/libxml2-particle-layout.h" COPYONLY)
    target_include_directories(LibXml2 PRIVATE "${binary_dir}/qore-particle-layout-fix")
    foreach(_filename xmlschemas.c xmlschemastypes.c)
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
            message(FATAL_ERROR "Cannot locate libxml2 ${_filename} for shared particle layout")
        endif()
        if(IS_ABSOLUTE "${_input}")
            set(_path "${_input}")
        else()
            set(_path "${source_dir}/${_input}")
        endif()
        if(_filename STREQUAL "xmlschemas.c")
            set(_original_hash f133567c3025f2d8cbb0237b641c0661772eb6cd824abe66c3b0d47dd8d5c684)
            set(_fixed_hash 239c8ec7758547ff172911da21e345bdcc948eacd5142e6f556292d95cf7556c)
        else()
            set(_original_hash ea2f33e8a41cb9da632115b0239767bc5c896369745f79f7c284a4f73736d960)
            set(_fixed_hash 75d486173283b976fd3da5235f2e4063ed4b9bb875e952686a9cd10205aa646f)
        endif()
        file(SHA256 "${_path}" _hash)
        if(_hash STREQUAL _fixed_hash)
            continue()
        endif()
        if(NOT _hash STREQUAL _original_hash)
            message(FATAL_ERROR "Unexpected libxml2 ${_filename}; cannot apply shared particle layout")
        endif()
        file(READ "${_path}" _source)
        if(_filename STREQUAL "xmlschemas.c")
            string(REPLACE [==[typedef struct _xmlSchemaParticle xmlSchemaParticle;
typedef xmlSchemaParticle *xmlSchemaParticlePtr;
struct _xmlSchemaParticle {
    xmlSchemaTypeType type;
    xmlSchemaAnnotPtr annot;
    xmlSchemaTreeItemPtr next; /* next particle */
    xmlSchemaTreeItemPtr children; /* the "term" (e.g. a model group,
	a group definition, a XML_SCHEMA_EXTRA_QNAMEREF (if a reference),
        etc.) */
    int minOccurs;
    int maxOccurs;
    xmlNodePtr node;
    xmlSchemaParticlePtr countSource; /* Borrowed original occurrence source. */
    int termNullable; /* Intrinsic term can match an empty sequence. */
    int maxFinite; /* Numeric maximum is distinct from the unbounded sentinel. */
};]==]
                [==[#include "libxml2-particle-layout.h"]==] _source "${_source}")
            string(REPLACE [==[	if ((particle == NULL) ||
	    ((particle->type == XML_SCHEMA_TYPE_PARTICLE) &&
	    ((particle->children->type == XML_SCHEMA_TYPE_ALL) ||]==]
                [==[	if ((particle == NULL) ||
	    ((particle->type == XML_SCHEMA_TYPE_PARTICLE) &&
            /* A group reference retains a particle even if its term is empty. */
            ((particle->node == NULL) || !xmlStrEqual(particle->node->name, BAD_CAST "group")) &&
	    ((particle->children->type == XML_SCHEMA_TYPE_ALL) ||]==] _source "${_source}")
            string(REPLACE [==[    ret->termNullable = 0;]==]
                [==[    ret->termNullable = 0;
    ret->isBuiltin = 0;]==] _source "${_source}")
            string(REPLACE [==[                    ((xmlSchemaParticlePtr)node->item)->maxFinite = node->maximum != NULL;]==]
                [==[                    if (!((xmlSchemaParticlePtr)node->item)->isBuiltin) {
                        ((xmlSchemaParticlePtr)node->item)->maxFinite = node->maximum != NULL;
                    }]==] _source "${_source}")
            string(REPLACE [==[                ((xmlSchemaParticlePtr)node->item)->termNullable = child->info.nullable;]==]
                [==[                if (!((xmlSchemaParticlePtr)node->item)->isBuiltin) {
                    ((xmlSchemaParticlePtr)node->item)->termNullable = child->info.nullable;
                }]==] _source "${_source}")
        else()
            string(REPLACE [==[typedef struct _xmlSchemaParticle xmlSchemaParticle;
typedef xmlSchemaParticle *xmlSchemaParticlePtr;
struct _xmlSchemaParticle {
    xmlSchemaTypeType type;
    xmlSchemaAnnotPtr annot;
    xmlSchemaTreeItemPtr next;
    xmlSchemaTreeItemPtr children;
    int minOccurs;
    int maxOccurs;
    xmlNodePtr node;
};]==]
                [==[#include "libxml2-particle-layout.h"]==] _source "${_source}")
            string(REPLACE [==[    ret->maxOccurs = 1;]==]
                [==[    ret->maxOccurs = 1;
    ret->maxFinite = 1;
    ret->isBuiltin = 1;]==] _source "${_source}")
            string(REPLACE [==[	xmlSchemaTypeAnyTypeDef->subtypes = (xmlSchemaTypePtr) particle;]==]
                [==[	xmlSchemaTypeAnyTypeDef->subtypes = (xmlSchemaTypePtr) particle;
        particle->termNullable = 1;]==] _source "${_source}")
            string(REPLACE [==[	particle->maxOccurs = UNBOUNDED;]==]
                [==[	particle->maxOccurs = UNBOUNDED;
        particle->maxFinite = 0;]==] _source "${_source}")
        endif()
        string(SHA256 _hash "${_source}")
        if(NOT _hash STREQUAL _fixed_hash)
            message(FATAL_ERROR "Pinned libxml2 shared particle layout fix did not match ${_filename}")
        endif()
        set(_replacement "${binary_dir}/qore-particle-layout-fix/${_filename}")
        file(WRITE "${_replacement}.tmp" "${_source}")
        configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
        list(REMOVE_ITEM _sources "${_input}")
        list(APPEND _sources "${_replacement}")
        set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
        message(STATUS "XML module: applied shared libxml2 particle layout to ${_filename}")
    endforeach()
endfunction()
