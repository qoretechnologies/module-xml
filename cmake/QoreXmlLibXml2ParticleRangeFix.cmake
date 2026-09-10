# Copyright (C) 2026 Qore Technologies, s.r.o.
# Exact finite occurrence bounds in native schema compilation and execution.
set(_qore_xml_particle_range_fix_dir "${CMAKE_CURRENT_LIST_DIR}")

function(qore_xml_fix_libxml2_particle_ranges source_dir binary_dir)
    foreach(_filename xmlschemas.c xmlregexp.c)
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
            message(FATAL_ERROR "Cannot locate libxml2 ${_filename} for exact particle ranges")
        endif()
        if(IS_ABSOLUTE "${_input}")
            set(_path "${_input}")
        else()
            set(_path "${source_dir}/${_input}")
        endif()
        if(_filename STREQUAL "xmlschemas.c")
            set(_original_hash 9576ea27a4e0b0f67076b04db27c6bd0737b2e4e58e9f08ad906992a4ad544fc)
            set(_fixed_hash b519fc7f08c902a01b328307f8c7b43f510b366c6641c3b5974b5f0da2f6637d)
        else()
            set(_original_hash 80dc294af5eea03f6623c2c4386721ce949e5ef361f7c6fb10fadc3d2519486d)
            set(_fixed_hash 8a778c1f9a0790d48bcaf22c6e4dea20ff6168cf35c8720129e15fbe9369bdd2)
        endif()
        file(SHA256 "${_path}" _hash)
        if(_hash STREQUAL _fixed_hash)
            continue()
        endif()
        if(NOT _hash STREQUAL _original_hash)
            message(FATAL_ERROR "Unexpected libxml2 ${_filename}; cannot apply exact particle ranges")
        endif()
        file(READ "${_path}" _source)
        if(_filename STREQUAL "xmlschemas.c")
        string(REPLACE [==[    int termNullable; /* Intrinsic term can match an empty sequence. */]==] [==[    int termNullable; /* Intrinsic term can match an empty sequence. */
    int maxFinite; /* Numeric maximum is distinct from the unbounded sentinel. */]==] _source "${_source}")
        string(REPLACE [==[    ret->termNullable = 0;]==] [==[    ret->termNullable = 0;
    ret->maxFinite = max != UNBOUNDED;]==] _source "${_source}")
        string(REPLACE [==[                    node->maximum = xmlSchemaUpaOccurrence(schema, (xmlSchemaParticlePtr)node->item, 1);]==] [==[                    node->maximum = xmlSchemaUpaOccurrence(schema, (xmlSchemaParticlePtr)node->item, 1);
                    ((xmlSchemaParticlePtr)node->item)->maxFinite = node->maximum != NULL;]==] _source "${_source}")
        string(REPLACE [==[(result < min) || ((max != -1) && (result > max)))]==] [==[(result < min) || ((max != -1 && max != UNBOUNDED) && (result > max)))]==] _source "${_source}")
        string(REPLACE [==[    return result;
}

static int
xmlGetMaxOccurs]==] [==[    return result > UNBOUNDED ? UNBOUNDED : result;
}

static int
xmlGetMaxOccurs]==] _source "${_source}")
        set(_helpers "")
        file(READ "${_qore_xml_particle_range_fix_dir}/libxml2-particle-counter-lexical.inc" _helper)
        string(APPEND _helpers "${_helper}\n")
        string(REPLACE [==[static int
xmlSchemaPCheckParticleCorrect_2(]==] "${_helpers}static int
xmlSchemaPCheckParticleCorrect_2(" _source "${_source}")
        string(REPLACE [==[    if ((maxOccurs == 0) && ( minOccurs == 0))
	return (0);]==] [==[    if (minOccurs >= UNBOUNDED && maxOccurs >= UNBOUNDED) {
        xmlAttrPtr lowAttribute = xmlSchemaGetPropNode(node, "minOccurs");
        xmlAttrPtr highAttribute = xmlSchemaGetPropNode(node, "maxOccurs");
        if (lowAttribute != NULL && highAttribute != NULL) {
            const xmlChar *low = xmlSchemaGetNodeContent(ctxt, (xmlNodePtr)lowAttribute);
            const xmlChar *high = xmlSchemaGetNodeContent(ctxt, (xmlNodePtr)highAttribute);
            xmlRegCountLexical minimum, maximum;
            if (low == NULL || high == NULL) {
                return -1;
            }
            if (xmlRegCountParse((const char *)low, 0, &minimum) == 0
                    && xmlRegCountParse((const char *)high, 1, &maximum) == 0
                    && xmlRegCountCompareLexical(&minimum, &maximum) > 0) {
                xmlSchemaPCustomAttrErr(ctxt, XML_SCHEMAP_P_PROPS_CORRECT_2_1,
                    NULL, NULL, lowAttribute,
                    "The value must not be greater than the value of 'maxOccurs'");
                return XML_SCHEMAP_P_PROPS_CORRECT_2_1;
            }
        }
    }
    if ((maxOccurs == 0) && ( minOccurs == 0))
	return (0);]==] _source "${_source}")
        set(_helpers "")
        file(READ "${_qore_xml_particle_range_fix_dir}/libxml2-particle-counter-schema.inc" _helper)
        string(APPEND _helpers "${_helper}\n")
        string(REPLACE [==[static int
xmlSchemaHasUsableElementName(]==] "${_helpers}static int
xmlSchemaHasUsableElementName(" _source "${_source}")
        string(FIND "${_source}" "static int\nxmlSchemaBuildContentModelForSubstGroup(" _begin)
        string(SUBSTRING "${_source}" ${_begin} -1 _tail)
        string(FIND "${_tail}" "/* Copyright (C) 2026 Qore Technologies, s.r.o.\n * Exact positive rational arithmetic" _end)
        string(SUBSTRING "${_tail}" 0 ${_end} _body)
        set(_original_body "${_body}")
        string(REPLACE [==[(particle->maxOccurs >= UNBOUNDED)]==] [==[(!particle->maxFinite)]==] _body "${_body}")
        string(REPLACE [==[xmlAutomataNewCounter(pctxt->am, minOccurs,
	    maxOccurs)]==] [==[xmlSchemaNewExactCounter(pctxt, particle, minOccurs, maxOccurs, 1)]==] _body "${_body}")
        string(REPLACE [==[xmlAutomataNewCounter(ctxt->am, minOccurs, maxOccurs)]==] [==[xmlSchemaNewExactCounter(ctxt, particle, minOccurs, maxOccurs, 1)]==] _body "${_body}")
        string(REPLACE [==[xmlAutomataNewCounter(pctxt->am, minOccurs, maxOccurs)]==] [==[xmlSchemaNewExactCounter(pctxt, particle, minOccurs, maxOccurs, 1)]==] _body "${_body}")
        string(REPLACE [==[xmlAutomataNewCounter(pctxt->am,
                            minimum - 1, UNBOUNDED)]==] [==[xmlSchemaNewExactCounter(pctxt, particle, minimum - 1, UNBOUNDED, 1)]==] _body "${_body}")
        string(REPLACE [==[xmlAutomataNewCounter(pctxt->am,
                        minimum - 1,
                        particle->maxOccurs - 1)]==] [==[xmlSchemaNewExactCounter(pctxt, particle, minimum - 1, particle->maxOccurs - 1, 1)]==] _body "${_body}")
        string(REPLACE "${_original_body}" "${_body}" _source "${_source}")
        else()
        set(_helpers "")
        file(READ "${_qore_xml_particle_range_fix_dir}/libxml2-particle-counter-lexical.inc" _helper)
        string(APPEND _helpers "${_helper}\n")
        file(READ "${_qore_xml_particle_range_fix_dir}/libxml2-particle-counter-values.inc" _helper)
        string(APPEND _helpers "${_helper}\n")
        string(REPLACE [==[typedef struct _xmlRegCounter xmlRegCounter;]==] "${_helpers}typedef struct _xmlRegCounter xmlRegCounter;" _source "${_source}")
        string(REPLACE [==[struct _xmlRegCounter {
    int min;
    int max;
};]==] [==[struct _xmlRegCounter {
    int min;
    int max;
    xmlRegCountBounds *exact;
};]==] _source "${_source}")
        string(REPLACE [==[    int nbCounters;
    xmlRegCounter *counters;]==] [==[    int nbCounters;
    xmlRegCounter *counters;
    size_t wideCountSize;]==] _source "${_source}")
        string(REPLACE [==[    int *schemaEmptySeen; /* Counter increments since the last input token. */]==] [==[    int *schemaEmptySeen; /* Counter increments since the last input token. */
    uint32_t *wideCounts;
    uint32_t *errWideCounts;]==] _source "${_source}")
        set(_helpers "")
        file(READ "${_qore_xml_particle_range_fix_dir}/libxml2-particle-counter-automata.inc" _helper)
        string(APPEND _helpers "${_helper}\n")
        string(REPLACE [==[static xmlRegexpPtr
xmlRegEpxFromParse(]==] "${_helpers}static xmlRegexpPtr
xmlRegEpxFromParse(" _source "${_source}")
        string(REPLACE [==[    ret->counters = ctxt->counters;]==] [==[    ret->counters = ctxt->counters;
    ret->wideCountSize = ctxt->wideCountSize;]==] _source "${_source}")
        string(REPLACE [==[    ctxt->counters[ctxt->nbCounters].max = -1;]==] [==[    ctxt->counters[ctxt->nbCounters].max = -1;
    ctxt->counters[ctxt->nbCounters].exact = NULL;]==] _source "${_source}")
        string(REPLACE [==[    if (ctxt->counters != NULL)
	xmlFree(ctxt->counters);]==] [==[    if (ctxt->counters != NULL) {
        for (i = 0; i < ctxt->nbCounters; ++i) {
            xmlFree(ctxt->counters[i].exact);
        }
        xmlFree(ctxt->counters);
    }]==] _source "${_source}")
        string(REPLACE [==[    if (regexp->counters != NULL)
	xmlFree(regexp->counters);]==] [==[    if (regexp->counters != NULL) {
        for (i = 0; i < regexp->nbCounters; ++i) {
            xmlFree(regexp->counters[i].exact);
        }
        xmlFree(regexp->counters);
    }]==] _source "${_source}")
        string(REPLACE [==[                xmlMalloc((size_t)exec->comp->nbCounters * sizeof(int)
                    * (exec->schemaEmptySeen != NULL ? 2 : 1));]==] [==[                xmlMalloc(xmlRegCounterStorageSize(exec->comp, 0));]==] _source "${_source}")
        string(REPLACE [==[        if (exec->schemaEmptySeen != NULL) {
            memcpy(exec->rollbacks[exec->nbRollbacks].counts + exec->comp->nbCounters,
                exec->schemaEmptySeen, (size_t)exec->comp->nbCounters * sizeof(int));
        }]==] [==[        if (exec->schemaEmptySeen != NULL) {
            memcpy(exec->rollbacks[exec->nbRollbacks].counts + exec->comp->nbCounters,
                exec->schemaEmptySeen, (size_t)exec->comp->nbCounters * sizeof(int));
        }
        if (exec->wideCounts != NULL) {
            memcpy(exec->rollbacks[exec->nbRollbacks].counts + (size_t)exec->comp->nbCounters * 2,
                exec->wideCounts, exec->comp->wideCountSize * sizeof(uint32_t));
        }]==] _source "${_source}")
        string(REPLACE [==[            if (exec->schemaEmptySeen != NULL) {
                memcpy(exec->schemaEmptySeen,
                    exec->rollbacks[exec->nbRollbacks].counts + exec->comp->nbCounters,
                    (size_t)exec->comp->nbCounters * sizeof(int));
            }]==] [==[            if (exec->schemaEmptySeen != NULL) {
                memcpy(exec->schemaEmptySeen,
                    exec->rollbacks[exec->nbRollbacks].counts + exec->comp->nbCounters,
                    (size_t)exec->comp->nbCounters * sizeof(int));
            }
            if (exec->wideCounts != NULL) {
                memcpy(exec->wideCounts,
                    exec->rollbacks[exec->nbRollbacks].counts + (size_t)exec->comp->nbCounters * 2,
                    exec->comp->wideCountSize * sizeof(uint32_t));
            }]==] _source "${_source}")
        string(REPLACE [==[        /* Keep diagnostics and schema epsilon progress in the same allocation. */
        if ((size_t)comp->nbCounters > SIZE_MAX / (sizeof(int) * slots)) {
            xmlFree(exec);
            return NULL;
        }
        exec->counts = xmlMalloc((size_t)comp->nbCounters * sizeof(int) * slots);]==] [==[        size_t bytes = xmlRegCounterStorageSize(comp, 1);
        /* One allocation owns ordinary counts, progress, exact counts and diagnostics. */
        if (bytes == 0) {
            xmlFree(exec);
            return NULL;
        }
        exec->counts = xmlMalloc(bytes);]==] _source "${_source}")
        string(REPLACE [==[        memset(exec->counts, 0, (size_t)comp->nbCounters * sizeof(int) * slots);]==] [==[        memset(exec->counts, 0, bytes);
        if (comp->wideCountSize != 0) {
            exec->wideCounts = (uint32_t *)(exec->counts + (size_t)comp->nbCounters * slots);
            exec->errWideCounts = exec->wideCounts + comp->wideCountSize;
        }]==] _source "${_source}")
        string(REPLACE [==[                    && exec->counts[trans->counter] < exec->comp->counters[trans->counter].max;]==] [==[                    && xmlRegCounterCanIncrement(exec, trans->counter, 0);]==] _source "${_source}")
        string(FIND "${_source}" "static int\nxmlRegExecPushStringInternal(" _begin)
        string(SUBSTRING "${_source}" ${_begin} -1 _tail)
        string(FIND "${_tail}" "\n/**" _end)
        string(SUBSTRING "${_tail}" 0 ${_end} _body)
        set(_original_body "${_body}")
        string(REPLACE [==[		int count;
		xmlRegCounterPtr counter;

		/*
		 * A counted transition.
		 */

		count = exec->counts[trans->count];
		counter = &exec->comp->counters[trans->count];
		ret = ((count >= counter->min) && (count <= counter->max));]==] [==[                ret = xmlRegCounterInRange(exec, trans->count);]==] _body "${_body}")
        string(REPLACE [==[		    xmlRegCounterPtr counter;
		    int count;

		    count = exec->counts[trans->counter];
		    counter = &exec->comp->counters[trans->counter];
		    if (count >= counter->max)
			ret = 0;]==] [==[                    if (!xmlRegCounterCanIncrement(exec, trans->counter, 0)) {
                        ret = 0;
                    }]==] _body "${_body}")
        string(REPLACE [==[&& exec->counts[trans->counter] >= exec->comp->counters[trans->counter].max)]==] [==[&& !xmlRegCounterCanIncrement(exec, trans->counter, 0))]==] _body "${_body}")
        string(REPLACE [==[exec->counts[trans->counter]++;]==] [==[if (xmlRegCounterIncrement(exec, trans->counter) < 0) {
                        exec->status = XML_REGEXP_INTERNAL_ERROR;
                        break;
                    }]==] _body "${_body}")
        string(REPLACE [==[exec->counts[trans->count] = 0;]==] [==[xmlRegCounterReset(exec, trans->count);]==] _body "${_body}")
        string(REPLACE [==[		    memcpy(exec->errCounts, exec->counts,
			   exec->comp->nbCounters * sizeof(int));]==] [==[		    memcpy(exec->errCounts, exec->counts,
			   exec->comp->nbCounters * sizeof(int));
                if (exec->wideCounts != NULL) {
                    memcpy(exec->errWideCounts, exec->wideCounts, exec->comp->wideCountSize * sizeof(uint32_t));
                }]==] _body "${_body}")
        string(REPLACE [==[                if (exec->comp->nbCounters)
                    memcpy(exec->errCounts, exec->counts,
                           exec->comp->nbCounters * sizeof(int));]==] [==[                if (exec->comp->nbCounters) {
                    memcpy(exec->errCounts, exec->counts,
                           exec->comp->nbCounters * sizeof(int));
                }
                if (exec->wideCounts != NULL) {
                    memcpy(exec->errWideCounts, exec->wideCounts, exec->comp->wideCountSize * sizeof(uint32_t));
                }]==] _body "${_body}")
        string(REPLACE "${_original_body}" "${_body}" _source "${_source}")
        string(REPLACE [==[		xmlRegCounterPtr counter = NULL;
		int count;

		if (err)
		    count = exec->errCounts[trans->counter];
		else
		    count = exec->counts[trans->counter];
		if (exec->comp != NULL)
		    counter = &exec->comp->counters[trans->counter];
		if ((counter == NULL) || (count < counter->max)) {]==] [==[                if (exec->comp == NULL || xmlRegCounterCanIncrement(exec, trans->counter, err)) {]==] _source "${_source}")
        endif()
        string(SHA256 _result_hash "${_source}")
        if(NOT _result_hash STREQUAL _fixed_hash)
            message(FATAL_ERROR "Pinned libxml2 ${_filename} exact particle range fix did not match")
        endif()
        file(MAKE_DIRECTORY "${binary_dir}/qore-particle-ranges-fix")
        set(_replacement "${binary_dir}/qore-particle-ranges-fix/${_filename}")
        file(WRITE "${_replacement}.tmp" "${_source}")
        configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
        list(REMOVE_ITEM _sources "${_input}")
        list(APPEND _sources "${_replacement}")
        set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    endforeach()
    message(STATUS "XML module: applied exact libxml2 particle ranges in the build tree")
endfunction()
