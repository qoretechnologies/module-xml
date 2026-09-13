# Copyright (C) 2026 Qore Technologies, s.r.o.
# Canonical element defaults with checked, declaration-scoped QName ownership.
function(qore_xml_fix_libxml2_element_defaults source_dir binary_dir)
    function(_qore_xml_default_block begin end replacement)
        string(FIND "${_source}" "${begin}" _start)
        if(_start LESS 0)
            message(FATAL_ERROR "Cannot locate native default block: ${begin}")
        endif()
        string(SUBSTRING "${_source}" ${_start} -1 _rest)
        string(FIND "${_rest}" "${end}" _length)
        if(_length LESS 0)
            message(FATAL_ERROR "Cannot locate native default block end: ${end}")
        endif()
        math(EXPR _end "${_start} + ${_length}")
        string(SUBSTRING "${_source}" 0 ${_start} _prefix)
        string(SUBSTRING "${_source}" ${_end} -1 _suffix)
        set(_source "${_prefix}${replacement}${_suffix}" PARENT_SCOPE)
    endfunction()
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
            message(FATAL_ERROR "Cannot locate libxml2 ${_filename} for element defaults")
        endif()
        if(IS_ABSOLUTE "${_input}")
            set(_path "${_input}")
        else()
            set(_path "${source_dir}/${_input}")
        endif()
        if(_filename STREQUAL "xmlschemastypes.c")
            set(_original_hash ef29c959276faab580a51e192a7e2f6ac25d187e36cdc0cbbea2fc41e08649b1)
            set(_fixed_hash 2abe89c92ecc1219e6174237f9239fc088e6aa4e916c52869c52ae7ecf592bef)
        else()
            set(_original_hash 64f3d39c4c022aa7dcda27020259ebe500c0a6f0fcfaa93d421a3852ba7f9513)
            set(_fixed_hash e55e7f6d2189d5d8658f7c1aaefb1b0ea25bf7cafb3c445f828b6f81ace6cfab)
        endif()
        file(SHA256 "${_path}" _hash)
        if(_hash STREQUAL _fixed_hash)
            continue()
        endif()
        if(NOT _hash STREQUAL _original_hash)
            message(FATAL_ERROR "Unexpected libxml2 ${_filename}; cannot apply element defaults")
        endif()
        file(READ "${_path}" _source)
        file(READ "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/libxml2-qname-owned.inc" _owned)
        if(_filename STREQUAL "xmlschemastypes.c")
            string(REPLACE [==[/**
 * Cleanup the default XML Schemas type library
 *
 * @param value  the value to free
 */
]==] "${_owned}\n/**
 * Cleanup the default XML Schemas type library
 *
 * @param value  the value to free
 */
" _source "${_source}")
            _qore_xml_default_block([==[        case XML_SCHEMAS_QNAME:{]==] [==[        case XML_SCHEMAS_NCNAME:]==] [==[        case XML_SCHEMAS_QNAME: {
            xmlChar *prefix = NULL, *local = NULL;
            const xmlChar *uri = NULL;
            xmlNsPtr ns = NULL;
            ret = qoreXmlQNameParts(value, &prefix, &local);
            if (ret == 0 && node != NULL) {
                xmlNodePtr context = node->type == XML_ATTRIBUTE_NODE ? node->parent : node;
                if (xmlStrEqual(prefix, BAD_CAST "xml")) {
                    uri = XML_XML_NAMESPACE;
                } else if (xmlSearchNsSafe(context, prefix, &ns) < 0) {
                    ret = -1;
                } else if (ns != NULL && ns->href != NULL && ns->href[0] != 0) {
                    uri = ns->href;
                } else if (prefix != NULL) {
                    ret = 1;
                }
            }
            if (ret == 0 && val != NULL) {
                /* The context-free public API historically retains the lexical
                 * name. Contextual validation always stores an expanded name. */
                *val = qoreXmlQNameValue(uri, node != NULL ? local : value, 0);
                if (*val == NULL) {
                    ret = -1;
                }
            }
            xmlFree(prefix);
            xmlFree(local);
            goto done;
        }
]==])
            _qore_xml_default_block([==[	    case XML_SCHEMAS_QNAME:
	    case XML_SCHEMAS_NOTATION:
		cur = xmlSchemaDupVal(val);]==] [==[	    case XML_SCHEMAS_HEXBINARY:]==] [==[	    case XML_SCHEMAS_QNAME:
	    case XML_SCHEMAS_NOTATION:
                cur = qoreXmlQNameValue(val->value.qname.uri, val->value.qname.name,
                                        val->type == XML_SCHEMAS_NOTATION);
                if (cur == NULL) {
                    goto error;
                }
                break;
]==])
            string(REPLACE [==[if (val->value.str != NULL)
		    cur->value.str = xmlStrdup(BAD_CAST val->value.str);]==] [==[if (val->value.str != NULL) {
                    cur->value.str = xmlStrdup(BAD_CAST val->value.str);
                    if (cur->value.str == NULL) {
                        xmlFree(cur);
                        goto error;
                    }
                }]==] _source "${_source}")
            string(REPLACE [==[if (val->value.hex.str != NULL)
		    cur->value.hex.str = xmlStrdup(BAD_CAST val->value.hex.str);]==] [==[if (val->value.hex.str != NULL) {
                    cur->value.hex.str = xmlStrdup(BAD_CAST val->value.hex.str);
                    if (cur->value.hex.str == NULL) {
                        xmlFree(cur);
                        goto error;
                    }
                }]==] _source "${_source}")
            string(REPLACE [==[if (val->value.base64.str != NULL)
		    cur->value.base64.str =
                    xmlStrdup(BAD_CAST val->value.base64.str);]==] [==[if (val->value.base64.str != NULL) {
                    cur->value.base64.str = xmlStrdup(BAD_CAST val->value.base64.str);
                    if (cur->value.base64.str == NULL) {
                        xmlFree(cur);
                        goto error;
                    }
                }]==] _source "${_source}")
            string(REPLACE [==[if (val->value.decimal.str != NULL)
                    cur->value.decimal.str = xmlStrdup(BAD_CAST val->value.decimal.str);]==] [==[if (val->value.decimal.str != NULL) {
                    cur->value.decimal.str = xmlStrdup(BAD_CAST val->value.decimal.str);
                    if (cur->value.decimal.str == NULL) {
                        xmlFree(cur);
                        goto error;
                    }
                }]==] _source "${_source}")
        else()
            string(REPLACE [==[    xmlSchemaPtr schema;        /* The schema in use */
    xmlDocPtr doc;]==] [==[    xmlSchemaPtr schema;        /* The schema in use */
    xmlNodePtr defaultNamespaceNode; /* Scoped declaration namespace bindings. */
    xmlDocPtr doc;]==] _source "${_source}")
            file(READ "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/libxml2-default-namespace.inc" _namespace)
            _qore_xml_default_block([==[static const xmlChar *
xmlSchemaLookupNamespace(]==] [==[/*
* This one works on the schema of the validation context.]==] "${_owned}\n${_namespace}\n")
            _qore_xml_default_block([==[static int
xmlSchemaValidateNotation(]==] [==[static int
xmlSchemaVAddNodeQName(]==] [==[static int
xmlSchemaValidateNotation(xmlSchemaValidCtxtPtr vctxt, xmlSchemaPtr schema,
                          xmlNodePtr node, const xmlChar *value,
                          xmlSchemaValPtr *val, int valNeeded)
{
    if (schema == NULL) {
        return -1;
    }
    return qoreXmlValidateScopedQName(vctxt, node, schema, value, val, valNeeded, 1);
}

]==])
            _qore_xml_default_block([==[static int
xmlSchemaValidateQName(]==] [==[/* Identity-only payloads;]==] [==[static int
xmlSchemaValidateQName(xmlSchemaValidCtxtPtr vctxt, const xmlChar *value,
                       xmlSchemaValPtr *val, int valNeeded, int fireErrors)
{
    int ret = qoreXmlValidateScopedQName(vctxt, NULL, NULL, value, val, valNeeded, 0);
    if (ret > 0) {
        ret = XML_SCHEMAV_CVC_DATATYPE_VALID_1_2_1;
        if (fireErrors) {
            xmlSchemaSimpleTypeErr(ACTXT_CAST vctxt, ret, NULL, value,
                xmlSchemaGetBuiltInType(XML_SCHEMAS_QNAME), 1);
        }
    }
    return ret;
}

]==])
            _qore_xml_default_block([==[static int
xmlSchemaVExpandQName(]==] [==[static int
xmlSchemaProcessXSIType(]==] [==[static int
xmlSchemaVExpandQName(xmlSchemaValidCtxtPtr vctxt, const xmlChar *value,
                      const xmlChar **nsName, const xmlChar **localName)
{
    xmlChar *prefix = NULL, *local = NULL;
    const xmlChar *uri = NULL, *name = NULL, *namespaceName = NULL;
    int ret;
    if (nsName == NULL || localName == NULL) {
        return -1;
    }
    *nsName = NULL;
    *localName = NULL;
    ret = qoreXmlQNameParts(value, &prefix, &local);
    if (ret == 0) {
        ret = qoreXmlLookupNamespace(vctxt, NULL, prefix, &uri);
    }
    if (ret == 0 && prefix != NULL && uri == NULL) {
        ret = 1;
    }
    if (ret == 0) {
        name = xmlDictLookup(vctxt->dict, local, -1);
        if (name == NULL) {
            ret = -1;
        } else if (uri != NULL) {
            namespaceName = xmlDictLookup(vctxt->dict, uri, -1);
            if (namespaceName == NULL) {
                ret = -1;
            }
        }
    }
    xmlFree(prefix);
    xmlFree(local);
    if (ret == 0) {
        *localName = name;
        *nsName = namespaceName;
    } else if (ret > 0) {
        xmlSchemaSimpleTypeErr(ACTXT_CAST vctxt,
            XML_SCHEMAV_CVC_DATATYPE_VALID_1_2_1, NULL, value,
            xmlSchemaGetBuiltInType(XML_SCHEMAS_QNAME), 1);
    }
    return ret;
}

]==])
            file(READ "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/libxml2-element-default.inc" _default)
            string(REPLACE [==[static int
xmlSchemaValidatorPopElem(]==] "${_default}\nstatic int
xmlSchemaValidatorPopElem(" _source "${_source}")
            string(REPLACE [==[	/*
	* NOTE: 'local' above means types acquired by xsi:type.
	* NOTE: Although the *canonical* value is stated, it is not
	* relevant if canonical or not. Additionally XML Schema 1.1
	* will removed this requirement as well.
	*/
	if (inode->flags & XML_SCHEMA_ELEM_INFO_LOCAL_TYPE) {

	    ret = xmlSchemaCheckCOSValidDefault(vctxt,
		inode->decl->value, &(inode->val));
	    if (ret != 0) {
		if (ret < 0) {
		    VERROR_INT("xmlSchemaValidatorPopElem",
			"calling xmlSchemaCheckCOSValidDefault()");
		    goto internal_error;
		}
		goto end_elem;
	    }
	    /*
	    * Stop here, to avoid redundant validation of the value
	    * (see following).
	    */
	    goto default_psvi;
	}
	/*
	* cvc-elt (3.3.4) : 5.1.2
	* The element information item with the canonical lexical
	* representation of the {value constraint} value used as its
	* `normalized value` must be `valid` with respect to the
	* `actual type definition` as defined by Element Locally Valid (Type)
	* ($3.3.4).
	*/
	if (WXS_IS_SIMPLE(inode->typeDef)) {
	    ret = xmlSchemaVCheckINodeDataType(vctxt,
		inode, inode->typeDef, inode->decl->value);
	} else if (WXS_HAS_SIMPLE_CONTENT(inode->typeDef)) {
	    ret = xmlSchemaVCheckINodeDataType(vctxt,
		inode, inode->typeDef->contentTypeDef,
		inode->decl->value);
	}
	if (ret != 0) {
	    if (ret < 0) {
		VERROR_INT("xmlSchemaValidatorPopElem",
		    "calling xmlSchemaVCheckCVCSimpleType()");
		goto internal_error;
	    }
	    goto end_elem;
	}

default_psvi:]==] [==[        ret = qoreXmlValidateElementDefault(vctxt);
        if (ret != 0) {
            if (ret < 0) {
                VERROR_INT("xmlSchemaValidatorPopElem", "validating canonical element default");
                goto internal_error;
            }
            goto end_elem;
        }
]==] _source "${_source}")
        endif()
        string(SHA256 _hash "${_source}")
        if(NOT _hash STREQUAL _fixed_hash)
            message(FATAL_ERROR "Pinned libxml2 element default fix did not match ${_filename}: ${_hash}")
        endif()
        file(MAKE_DIRECTORY "${binary_dir}/qore-element-default-fix")
        set(_replacement "${binary_dir}/qore-element-default-fix/${_filename}")
        file(WRITE "${_replacement}.tmp" "${_source}")
        configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
        list(REMOVE_ITEM _sources "${_input}")
        list(APPEND _sources "${_replacement}")
        set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
        message(STATUS "XML module: applied canonical libxml2 element defaults to ${_filename}")
    endforeach()
endfunction()
