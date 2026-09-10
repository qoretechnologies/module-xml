# Copyright (C) 2026 Qore Technologies, s.r.o.
# Preserve schema particle positions in the private dependency's automaton.
# Apply after occurrence fixes; pinned upstream sources remain unchanged.
set(_qore_xml_particle_identity_fix_dir "${CMAKE_CURRENT_LIST_DIR}")

function(qore_xml_fix_libxml2_particle_identity source_dir binary_dir)
    get_target_property(_sources LibXml2 SOURCES)
    foreach(_filename xmlregexp.c xmlschemas.c)
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
            message(FATAL_ERROR "Cannot locate libxml2 ${_filename} for particle identity fix")
        endif()
        if(IS_ABSOLUTE "${_input}")
            set(_path "${_input}")
        else()
            set(_path "${source_dir}/${_input}")
        endif()
        file(SHA256 "${_path}" _hash)
        if(_filename STREQUAL "xmlregexp.c")
            set(_original_hash 3b2ba46567d52d898864b9c3b7478066c25720cbb9ad69f5961f6b329cd64aaf)
            set(_fixed_hash 4a2b6dc0c21c91d147245ae20ed14a4ad239003e06e0c1ccea0c88cd75890c7c)
        elseif(_filename STREQUAL "xmlschemas.c")
            set(_original_hash bb8e5f2681e4e9ad0add506fede46027bf02c973147f23c744701942e381d213)
            set(_fixed_hash 98cd89311c1eb371b29e76076ab5c60c63c9e8786ed103f5f94ef0ed806971ef)
        endif()
        if(_hash STREQUAL _fixed_hash)
            continue()
        endif()
        if(NOT _hash STREQUAL _original_hash)
            message(FATAL_ERROR "Unexpected libxml2 ${_filename}; cannot apply particle identity fix")
        endif()
        file(READ "${_path}" _source)
        if(_filename STREQUAL "xmlregexp.c")
            string(REPLACE [==[#include <libxml/xmlautomata.h>]==]
                [==[#include <libxml/xmlautomata.h>
#include <libxml/hash.h>]==] _source "${_source}")
            string(REPLACE [==[    void *data;
};

typedef struct _xmlRegCounter]==]
                [==[    void *data;
    size_t particle; /* Schema position, independent of callback declaration. */
};

typedef struct _xmlRegCounter]==] _source "${_source}")
            string(REPLACE [==[    int depth;
};

struct _xmlRegexp]==]
                [==[    int depth;
    size_t particle; /* Zero for callers that do not assign schema positions. */
    size_t nbParticles;
    xmlHashTablePtr particleMap;
};

struct _xmlRegexp]==] _source "${_source}")
            string(REPLACE [==[    ret->type = type;
    ret->quant = XML_REGEXP_QUANT_ONCE;]==]
                [==[    ret->type = type;
    ret->particle = ctxt->particle;
    ret->quant = XML_REGEXP_QUANT_ONCE;]==] _source "${_source}")
            string(REPLACE [==[    ret->type = atom->type;
    ret->quant = atom->quant;]==]
                [==[    ret->type = atom->type;
    ret->particle = atom->particle;
    ret->quant = atom->quant;]==] _source "${_source}")
            string(REPLACE [==[    if (atom1->type != atom2->type)
        return(0);
    switch (atom1->type)]==]
                [==[    if (atom1->type != atom2->type)
        return(0);
    if (atom1->particle != atom2->particle) {
        return(0);
    }
    switch (atom1->type)]==] _source "${_source}")
            file(READ "${_qore_xml_particle_identity_fix_dir}/libxml2-particle-identity.inc" _bridge)
            string(REPLACE [==[/**
 * Allocate a new regexp and fill it with the result from the parser]==] "${_bridge}\n/**\n * Allocate a new regexp and fill it with the result from the parser" _source "${_source}")
            string(REPLACE [==[    if (ctxt->counters != NULL)
	xmlFree(ctxt->counters);
    xmlFree(ctxt);]==]
                [==[    if (ctxt->counters != NULL)
	xmlFree(ctxt->counters);
    xmlHashFree(ctxt->particleMap, xmlRegFreeParticleIdentity);
    xmlFree(ctxt);]==] _source "${_source}")
        elseif(_filename STREQUAL "xmlschemas.c")
            string(REPLACE [==[#include "private/string.h"]==]
                [==[#include "private/string.h"

/* Private bridge; no installed libxml2 API change. */
XML_HIDDEN int xmlAutomataPushParticle(xmlAutomata *am, const void *source, size_t *parent);
XML_HIDDEN void xmlAutomataPopParticle(xmlAutomata *am, size_t parent);]==] _source "${_source}")
            string(FIND "${_source}" "static int\nxmlSchemaBuildAContentModel(" _start)
            string(SUBSTRING "${_source}" ${_start} -1 _tail)
            string(FIND "${_tail}" "\n/**" _end)
            string(SUBSTRING "${_tail}" 0 ${_end} _body)
            set(_original_body "${_body}")
            string(REPLACE [==[    int ret = 0, tmp2;

]==]
                [==[    int ret = 0, tmp2;
    size_t parent;

]==] _body "${_body}")
            string(REPLACE [==[
    switch (particle->children->type) {
]==]
                [==[
    if (xmlAutomataPushParticle(pctxt->am, particle, &parent) < 0) {
        xmlSchemaPErrMemory(pctxt);
        return 0;
    }
    switch (particle->children->type) {
]==] _body "${_body}")
            string(REPLACE [==[            while (sub != NULL) {
                pctxt->state = tmp;
]==]
                [==[            while (sub != NULL) {
                size_t allParent;
                if (xmlAutomataPushParticle(pctxt->am, sub, &allParent) < 0) {
                    xmlSchemaPErrMemory(pctxt);
                    goto particle_done;
                }
                pctxt->state = tmp;
]==] _body "${_body}")
            string(REPLACE [==[                        "<element> particle has no term");
                    return(ret);
                };
]==]
                [==[                        "<element> particle has no term");
                    goto particle_done;
                };
]==] _body "${_body}")
            string(REPLACE [==[                }
                sub = (xmlSchemaParticlePtr) sub->next;
]==]
                [==[                }
                xmlAutomataPopParticle(pctxt->am, allParent);
                sub = (xmlSchemaParticlePtr) sub->next;
]==] _body "${_body}")
            string(REPLACE [==[		WXS_ITEM_TYPE_NAME(particle->children), NULL);
            return(ret);
    }
]==]
                [==[		WXS_ITEM_TYPE_NAME(particle->children), NULL);
            goto particle_done;
    }
]==] _body "${_body}")
            string(REPLACE [==[    }
    return(ret);
}
]==]
                [==[    }
particle_done:
    xmlAutomataPopParticle(pctxt->am, parent);
    return ret;
}
]==] _body "${_body}")
            string(REPLACE "${_original_body}" "${_body}" _source "${_source}")
        endif()
        string(SHA256 _result_hash "${_source}")
        if(NOT _result_hash STREQUAL _fixed_hash)
            message(FATAL_ERROR "Pinned libxml2 ${_filename} particle identity fix did not match")
        endif()
        file(MAKE_DIRECTORY "${binary_dir}/qore-particle-identity-fix")
        set(_replacement "${binary_dir}/qore-particle-identity-fix/${_filename}")
        file(WRITE "${_replacement}.tmp" "${_source}")
        configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
        list(REMOVE_ITEM _sources "${_input}")
        list(APPEND _sources "${_replacement}")
    endforeach()
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied libxml2 schema particle identity fix in the build tree")
endfunction()
