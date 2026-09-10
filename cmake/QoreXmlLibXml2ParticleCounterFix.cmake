# Copyright (C) 2026 Qore Technologies, s.r.o.
# Preserve schema counter operations and bound empty-iteration traversal.
# Keep the pinned upstream sources unchanged; compile the checked build copy.

function(qore_xml_fix_libxml2_particle_counters source_dir binary_dir)
    get_target_property(_sources LibXml2 SOURCES)
    set(_input "")
    foreach(_entry IN LISTS _sources)
        get_filename_component(_name "${_entry}" NAME)
        if(_name STREQUAL "xmlregexp.c")
            if(_input)
                message(FATAL_ERROR "Duplicate libxml2 xmlregexp.c target source")
            endif()
            set(_input "${_entry}")
        endif()
    endforeach()
    if(NOT _input)
        message(FATAL_ERROR "Cannot locate libxml2 xmlregexp.c for particle counter fix")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    set(_original_hash 4a2b6dc0c21c91d147245ae20ed14a4ad239003e06e0c1ccea0c88cd75890c7c)
    set(_fixed_hash 80dc294af5eea03f6623c2c4386721ce949e5ef361f7c6fb10fadc3d2519486d)
    if(_hash STREQUAL _fixed_hash)
        return()
    endif()
    if(NOT _hash STREQUAL _original_hash)
        message(FATAL_ERROR "Unexpected libxml2 xmlregexp.c; cannot apply particle counter fix")
    endif()
    file(READ "${_path}" _source)
    string(REPLACE [==[		    xmlRegStateAddTrans(ctxt, from, NULL, ctxt->states[t1->to],
					-1, t1->count);]==] [==[                    /* Keep the increment carried across the epsilon path. */
		    xmlRegStateAddTrans(ctxt, from, NULL, ctxt->states[t1->to],
                                        ctxt->particleMap != NULL ? tcounter : -1, t1->count);]==] _source "${_source}")
    string(REPLACE [==[	    if (ret == 1) {
		if ((exec->callback != NULL) && (atom != NULL) &&]==] [==[            if (ret == 1 && (exec->comp->flags & AM_AUTOMATA_SCHEMA) && trans->counter >= 0
                    && exec->counts[trans->counter] >= exec->comp->counters[trans->counter].max) {
                continue;
            }
	    if (ret == 1) {
		if ((exec->callback != NULL) && (atom != NULL) &&]==] _source "${_source}")
    string(REPLACE [==[#define REGEXP_ALL_LAX_COUNTER	0x123457]==] [==[#define REGEXP_ALL_LAX_COUNTER	0x123457
#define REGEXP_SCHEMA_INCREMENT_COUNTER 0x123458]==] _source "${_source}")
    string(REPLACE [==[    xmlRegStateAddTrans(ctxt, from, NULL, to, counter, -1);]==] [==[    xmlRegStateAddTrans(ctxt, from, NULL, to, counter,
        ctxt->particleMap != NULL ? REGEXP_SCHEMA_INCREMENT_COUNTER : -1);]==] _source "${_source}")
    string(REPLACE [==[	    if (trans->count == REGEXP_ALL_LAX_COUNTER) {
		int i;]==] [==[            if (trans->count == REGEXP_SCHEMA_INCREMENT_COUNTER) {
                ret = exec->counts[trans->counter] < exec->comp->counters[trans->counter].max;
            } else if (trans->count == REGEXP_ALL_LAX_COUNTER) {
		int i;]==] _source "${_source}")
    string(REPLACE [==[#define AM_AUTOMATA_RNG 1]==] [==[#define AM_AUTOMATA_RNG 1
#define AM_AUTOMATA_SCHEMA 2]==] _source "${_source}")
    string(REPLACE [==[    *parent = am->particle;]==] [==[    am->flags |= AM_AUTOMATA_SCHEMA;
    *parent = am->particle;]==] _source "${_source}")
    string(REPLACE [==[    int *counts;

    /*
     * The input stack]==] [==[    int *counts;
    int *schemaEmptySeen; /* Counter increments since the last input token. */

    /*
     * The input stack]==] _source "${_source}")
    string(REPLACE [==[		xmlMalloc(exec->comp->nbCounters * sizeof(int));]==] [==[                xmlMalloc((size_t)exec->comp->nbCounters * sizeof(int)
                    * (exec->schemaEmptySeen != NULL ? 2 : 1));]==] _source "${_source}")
    string(REPLACE [==[	memcpy(exec->rollbacks[exec->nbRollbacks].counts, exec->counts,
	       exec->comp->nbCounters * sizeof(int));]==] [==[	memcpy(exec->rollbacks[exec->nbRollbacks].counts, exec->counts,
	       exec->comp->nbCounters * sizeof(int));
        if (exec->schemaEmptySeen != NULL) {
            memcpy(exec->rollbacks[exec->nbRollbacks].counts + exec->comp->nbCounters,
                exec->schemaEmptySeen, (size_t)exec->comp->nbCounters * sizeof(int));
        }]==] _source "${_source}")
    string(REPLACE [==[	    memcpy(exec->counts, exec->rollbacks[exec->nbRollbacks].counts,
	       exec->comp->nbCounters * sizeof(int));]==] [==[	    memcpy(exec->counts, exec->rollbacks[exec->nbRollbacks].counts,
	       exec->comp->nbCounters * sizeof(int));
            if (exec->schemaEmptySeen != NULL) {
                memcpy(exec->schemaEmptySeen,
                    exec->rollbacks[exec->nbRollbacks].counts + exec->comp->nbCounters,
                    (size_t)exec->comp->nbCounters * sizeof(int));
            }]==] _source "${_source}")
    string(REPLACE [==[        /*
	 * For error handling, exec->counts is allocated twice the size
	 * the second half is used to store the data in case of rollback
	 */
	exec->counts = (int *) xmlMalloc(comp->nbCounters * sizeof(int)
	                                 * 2);]==] [==[        size_t slots = (comp->flags & AM_AUTOMATA_SCHEMA) ? 3 : 2;
        /* Keep diagnostics and schema epsilon progress in the same allocation. */
        if ((size_t)comp->nbCounters > SIZE_MAX / (sizeof(int) * slots)) {
            xmlFree(exec);
            return NULL;
        }
        exec->counts = xmlMalloc((size_t)comp->nbCounters * sizeof(int) * slots);]==] _source "${_source}")
    string(REPLACE [==[        memset(exec->counts, 0, comp->nbCounters * sizeof(int) * 2);
	exec->errCounts = &exec->counts[comp->nbCounters];]==] [==[        memset(exec->counts, 0, (size_t)comp->nbCounters * sizeof(int) * slots);
        exec->errCounts = &exec->counts[comp->nbCounters];
        if (comp->flags & AM_AUTOMATA_SCHEMA) {
            exec->schemaEmptySeen = &exec->counts[(size_t)comp->nbCounters * 2];
        }]==] _source "${_source}")
    string(REPLACE [==[                ret = exec->counts[trans->counter] < exec->comp->counters[trans->counter].max;]==] [==[                /* Nullable repetitions have a zero effective minimum. A second
                 * increment without input would count another unnecessary empty
                 * iteration. Keep the progress mark across counter resets. */
                ret = !exec->schemaEmptySeen[trans->counter]
                    && exec->counts[trans->counter] < exec->comp->counters[trans->counter].max;]==] _source "${_source}")
    string(REPLACE [==[		if (trans->counter >= 0) {
		    exec->counts[trans->counter]++;
		}
		if ((trans->count >= 0) &&]==] [==[		if (trans->counter >= 0) {
		    exec->counts[trans->counter]++;
                    if (trans->count == REGEXP_SCHEMA_INCREMENT_COUNTER) {
                        exec->schemaEmptySeen[trans->counter] = 1;
                    }
		}
		if ((trans->count >= 0) &&]==] _source "${_source}")
    string(REPLACE [==[		if (trans->atom != NULL) {
		    if (exec->inputStack != NULL) {]==] [==[		if (trans->atom != NULL) {
                    if (exec->schemaEmptySeen != NULL) {
                        memset(exec->schemaEmptySeen, 0, (size_t)exec->comp->nbCounters * sizeof(int));
                    }
		    if (exec->inputStack != NULL) {]==] _source "${_source}")
    string(SHA256 _result_hash "${_source}")
    if(NOT _result_hash STREQUAL _fixed_hash)
        message(FATAL_ERROR "Pinned libxml2 xmlregexp.c particle counter fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-particle-counters-fix")
    set(_replacement "${binary_dir}/qore-particle-counters-fix/xmlregexp.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied exact libxml2 particle counter fix in the build tree")
endfunction()
