# Copyright (C) 2026 Qore Technologies, s.r.o.
# Apply XSD 1.0 builtin instance attributes and selected identity value variety.
set(_qore_xml_instance_identities_dir "${CMAKE_CURRENT_LIST_DIR}")
function(qore_xml_fix_libxml2_instance_identities source_dir binary_dir)
    get_target_property(_sources LibXml2 SOURCES)
    set(_input "")
    foreach(_entry IN LISTS _sources)
        get_filename_component(_name "${_entry}" NAME)
        if(_name STREQUAL "xmlschemas.c")
            if(_input)
                message(FATAL_ERROR "Duplicate libxml2 xmlschemas.c target source")
            endif()
            set(_input "${_entry}")
        endif()
    endforeach()
    if(NOT _input)
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemas.c for instance attribute and list identity")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "d87f077caf371594f5f1ad8fa4fc327190c6e31acba04cd328f789540e8c1a1e")
        qore_xml_fix_libxml2_instance_identity_values("${source_dir}" "${binary_dir}")
        return()
    endif()
    if(NOT _hash STREQUAL "c41bfe71ac77dfc5b7ac5d363181d34e4d7a5f10026554860e19d0f9a143f8fd")
        message(FATAL_ERROR "Unexpected libxml2 xmlschemas.c; cannot apply instance attribute and list identity")
    endif()
    file(READ "${_path}" _source)
    set(_implementation "${_qore_xml_instance_identities_dir}/libxml2-instance-identities.inc")
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${_implementation}")
    file(READ "${_implementation}" _instance_attributes)
    string(REPLACE "static int\nxmlSchemaVAttributesSimple("
        "${_instance_attributes}\nstatic int\nxmlSchemaVAttributesSimple(" _source "${_source}")
    string(REPLACE [==[struct _xmlSchemaPSVIIDCKey {
    xmlSchemaTypePtr type;
    xmlSchemaValPtr val;
};

/**
]==] [==[struct _xmlSchemaPSVIIDCKey {
    xmlSchemaTypePtr type;
    xmlSchemaValPtr val;
    int nil; /* An empty list is a value; nil is not. */
    int list; /* The selected variety, including union member selection. */
};

/**
]==] _source "${_source}")
    string(REPLACE [==[#define XML_SCHEMA_ELEM_INFO_LOCAL_TYPE        (1<<3)

#define XML_SCHEMA_NODE_INFO_VALUE_NEEDED      (1<<4)
#define XML_SCHEMA_ELEM_INFO_EMPTY             (1<<5)
#define XML_SCHEMA_ELEM_INFO_HAS_CONTENT       (1<<6)

]==] [==[#define XML_SCHEMA_ELEM_INFO_LOCAL_TYPE        (1<<3)

#define XML_SCHEMA_NODE_INFO_VALUE_NEEDED      (1<<4)
#define XML_SCHEMA_NODE_INFO_LIST_VALUE        (1<<11)
#define XML_SCHEMA_ELEM_INFO_EMPTY             (1<<5)
#define XML_SCHEMA_ELEM_INFO_HAS_CONTENT       (1<<6)

]==] _source "${_source}")
    string(REPLACE [==[    xmlSchemaValidityWarningFunc warning; /* the callback in case of warning */
    xmlStructuredErrorFunc serror;

    xmlSchemaPtr schema;        /* The schema in use */
    xmlNodePtr defaultNamespaceNode; /* Scoped declaration namespace bindings. */
    xmlDocPtr doc;
]==] [==[    xmlSchemaValidityWarningFunc warning; /* the callback in case of warning */
    xmlStructuredErrorFunc serror;

    xmlSchemaType xsiLocationType; /* Stable anonymous list type for IDC keys. */
    xmlSchemaPtr schema;        /* The schema in use */
    xmlNodePtr defaultNamespaceNode; /* Scoped declaration namespace bindings. */
    xmlDocPtr doc;
]==] _source "${_source}")
    string(REPLACE [==[ * @returns 0 if the value could be built and -1 in case of
 *         API errors or if the value type is not supported yet.
 */
static int
xmlSchemaGetCanonValueWhtspExt_1(xmlSchemaValPtr val,
			         xmlSchemaWhitespaceValueType ws,
			         xmlChar **retValue,
				 int for_hash)
{
    int list;
    xmlSchemaValType valType;
    const xmlChar *value, *value2 = NULL;


    if ((retValue == NULL) || (val == NULL))
	return (-1);
    list = xmlSchemaValueGetNext(val) ? 1 : 0;
    *retValue = NULL;
    do {
	value = NULL;
	valType = xmlSchemaGetValType(val);
	switch (valType) {
	    case XML_SCHEMAS_STRING:
	    case XML_SCHEMAS_NORMSTRING:
	    case XML_SCHEMAS_ANYSIMPLETYPE:
		value = xmlSchemaValueGetAsString(val);
		if (value != NULL) {
		    if (ws == XML_SCHEMA_WHITESPACE_COLLAPSE)
			value2 = xmlSchemaCollapseString(value);
		    else if (ws == XML_SCHEMA_WHITESPACE_REPLACE)
			value2 = xmlSchemaWhiteSpaceReplace(value);
		    if (value2 != NULL)
			value = value2;
		}
		break;
	    default:
		if (xmlSchemaGetCanonValue(val, &value2) == -1) {
		    if (value2 != NULL)
			xmlFree((xmlChar *) value2);
		    goto internal_error;
		}
		if (for_hash && valType == XML_SCHEMAS_DECIMAL) {
		    /* We can mostly use the canonical value for hashing,
		       except in the case of decimal.  There the canonical
		       representation requires a trailing '.0' even for
		       non-fractional numbers, but for the derived integer
		       types it forbids any decimal point.  Nevertheless they
		       compare equal if the value is equal.  We need to generate
		       the same hash value for this to work, and it's easiest
		       to just cut off the useless '.0' suffix for the
		       decimal type.  */
		    int len = xmlStrlen(value2);
		    if (len > 2 && value2[len-1] == '0' && value2[len-2] == '.')
		      ((xmlChar*)value2)[len-2] = 0;
		}
		value = value2;
	}
	if (*retValue == NULL)
	    if (value == NULL) {
		if (! list)
		    *retValue = xmlStrdup(BAD_CAST "");
	    } else
		*retValue = xmlStrdup(value);
	else if (value != NULL) {
	    /* List. */
	    *retValue = xmlStrcat((xmlChar *) *retValue, BAD_CAST " ");
	    *retValue = xmlStrcat((xmlChar *) *retValue, value);
	}
	FREE_AND_NULL(value2)
	val = xmlSchemaValueGetNext(val);
    } while (val != NULL);

    return (0);
internal_error:
    if (*retValue != NULL)
	xmlFree((xmlChar *) (*retValue));
    if (value2 != NULL)
	xmlFree((xmlChar *) value2);
    return (-1);
}

static int
]==] [==[ * @returns 0 if the value could be built and -1 in case of
 *         API errors or if the value type is not supported yet.
 */
/* Copyright (C) 2026 Qore Technologies, s.r.o. */
static int
qoreXmlIdentityAppendText(xmlBufPtr buffer, const xmlChar *value,
        xmlSchemaWhitespaceValueType whitespace)
{
    const xmlChar *cursor = value;
    int pending = 0, written = 0;
    if (value == NULL) {
        return 0;
    }
    if (whitespace != XML_SCHEMA_WHITESPACE_COLLAPSE &&
            whitespace != XML_SCHEMA_WHITESPACE_REPLACE) {
        return xmlBufCat(buffer, value);
    }
    while (*cursor != 0) {
        const xmlChar *start = cursor;
        if (IS_BLANK_CH(*cursor)) {
            if (whitespace == XML_SCHEMA_WHITESPACE_REPLACE) {
                if (xmlBufAdd(buffer, BAD_CAST " ", 1) < 0) {
                    return -1;
                }
            } else if (written) {
                pending = 1;
            }
            cursor++;
            continue;
        }
        while (*cursor != 0 && !IS_BLANK_CH(*cursor)) {
            cursor++;
        }
        if ((pending && xmlBufAdd(buffer, BAD_CAST " ", 1) < 0) ||
                xmlBufAdd(buffer, start, cursor - start) < 0) {
            return -1;
        }
        pending = 0;
        written = 1;
    }
    return 0;
}

static int
xmlSchemaGetCanonValueWhtspExt_1(xmlSchemaValPtr val,
        xmlSchemaWhitespaceValueType ws, xmlChar **retValue, int for_hash)
{
    xmlBufPtr buffer;
    xmlChar *owned = NULL;
    int first = 1;
    if (retValue == NULL || val == NULL) {
        return -1;
    }
    *retValue = NULL;
    buffer = xmlBufCreate(50);
    if (buffer == NULL) {
        return -1;
    }
    do {
        const xmlChar *value;
        xmlSchemaValType type = xmlSchemaGetValType(val);
        if (type == XML_SCHEMAS_STRING || type == XML_SCHEMAS_NORMSTRING ||
                type == XML_SCHEMAS_ANYSIMPLETYPE) {
            value = xmlSchemaValueGetAsString(val);
        } else {
            if (xmlSchemaGetCanonValue(val, (const xmlChar **)&owned) < 0 || owned == NULL) {
                goto error;
            }
            if (for_hash && type == XML_SCHEMAS_DECIMAL) {
                int length = xmlStrlen(owned);
                if (length > 2 && owned[length - 1] == '0' && owned[length - 2] == '.') {
                    owned[length - 2] = 0;
                }
            }
            value = owned;
        }
        if ((!first && xmlBufAdd(buffer, BAD_CAST " ", 1) < 0) ||
                qoreXmlIdentityAppendText(buffer, value,
                    owned == NULL ? ws : XML_SCHEMA_WHITESPACE_PRESERVE) < 0) {
            goto error;
        }
        xmlFree(owned);
        owned = NULL;
        first = 0;
        val = xmlSchemaValueGetNext(val);
    } while (val != NULL);
    *retValue = xmlBufDetach(buffer);
    xmlBufFree(buffer);
    return *retValue == NULL ? -1 : 0;
error:
    xmlFree(owned);
    xmlBufFree(buffer);
    return -1;
}

static int
]==] _source "${_source}")
    string(REPLACE [==[    return (resolved);
}

static const xmlChar *
xmlSchemaFormatIDCKeySequence_1(xmlSchemaValidCtxtPtr vctxt,
				xmlChar **buf,
				xmlSchemaPSVIIDCKeyPtr *seq,
				int count, int for_hash)
{
    int i, res;
    xmlChar *value = NULL;

    *buf = xmlStrdup(BAD_CAST "[");
    for (i = 0; i < count; i++) {
	*buf = xmlStrcat(*buf, BAD_CAST "'");
	if (!for_hash)
	    res = xmlSchemaGetCanonValueWhtspExt(seq[i]->val,
		    xmlSchemaGetWhiteSpaceFacetValue(seq[i]->type),
		    &value);
	else {
	    res = xmlSchemaGetCanonValueHash(seq[i]->val, &value);
	}
	if (res == 0)
	    *buf = xmlStrcat(*buf, BAD_CAST value);
	else {
	    VERROR_INT("xmlSchemaFormatIDCKeySequence",
		"failed to compute a canonical value");
	    *buf = xmlStrcat(*buf, BAD_CAST "???");
	}
	if (i < count -1)
	    *buf = xmlStrcat(*buf, BAD_CAST "', ");
	else
	    *buf = xmlStrcat(*buf, BAD_CAST "'");
	if (value != NULL) {
	    xmlFree(value);
	    value = NULL;
	}
    }
    *buf = xmlStrcat(*buf, BAD_CAST "]");

    return (BAD_CAST *buf);
}

static const xmlChar *
]==] [==[    return (resolved);
}

/* Copyright (C) 2026 Qore Technologies, s.r.o. */
static const xmlChar *
xmlSchemaFormatIDCKeySequence_1(xmlSchemaValidCtxtPtr vctxt, xmlChar **buf,
        xmlSchemaPSVIIDCKeyPtr *seq, int count, int for_hash)
{
    xmlBufPtr buffer = xmlBufCreate(50);
    xmlChar *value = NULL;
    int i;
    *buf = NULL;
    if (buffer == NULL || xmlBufAdd(buffer, BAD_CAST "[", 1) < 0) {
        goto error;
    }
    for (i = 0; i < count; i++) {
        if ((i != 0 && xmlBufAdd(buffer, BAD_CAST ", ", 2) < 0) ||
                xmlBufAdd(buffer, BAD_CAST "'", 1) < 0) {
            goto error;
        }
        if (seq[i]->val != NULL) {
            int result = for_hash ? xmlSchemaGetCanonValueHash(seq[i]->val, &value)
                : xmlSchemaGetCanonValueWhtspExt(seq[i]->val,
                    xmlSchemaGetWhiteSpaceFacetValue(seq[i]->type), &value);
            if (result < 0 || value == NULL || xmlBufCat(buffer, value) < 0) {
                goto error;
            }
            xmlFree(value);
            value = NULL;
        } else if (!seq[i]->list) {
            goto error;
        }
        if (xmlBufAdd(buffer, BAD_CAST "'", 1) < 0) {
            goto error;
        }
    }
    if (xmlBufAdd(buffer, BAD_CAST "]", 1) < 0) {
        goto error;
    }
    *buf = xmlBufDetach(buffer);
    xmlBufFree(buffer);
    if (*buf == NULL) {
        xmlSchemaVErrMemory(vctxt);
    }
    return *buf;
error:
    xmlFree(value);
    xmlBufFree(buffer);
    xmlSchemaVErrMemory(vctxt);
    return NULL;
}

static const xmlChar *
]==] _source "${_source}")
    string(REPLACE [==[ * @param depth  depth
 * @returns 0 on success and -1 on internal errors.
 */
static int
xmlSchemaXPathProcessHistory(xmlSchemaValidCtxtPtr vctxt,
			     int depth)
]==] [==[ * @param depth  depth
 * @returns 0 on success and -1 on internal errors.
 */
static int
xmlSchemaIDCEqualKeys(xmlSchemaPSVIIDCKeyPtr a, xmlSchemaPSVIIDCKeyPtr b)
{
    if (a->list != b->list) {
        return 0;
    }
    return xmlSchemaAreValuesEqual(a->val, b->val);
}

static int
xmlSchemaXPathProcessHistory(xmlSchemaValidCtxtPtr vctxt,
			     int depth)
]==] _source "${_source}")
    string(REPLACE [==[		goto deregister_check;
	    }

	    if ((key == NULL) && (vctxt->inode->val == NULL) && !nil) {
		/*
		* Failed to provide the normalized value; maybe
		* the value was invalid.
]==] [==[		goto deregister_check;
	    }

	    if ((key == NULL) && (vctxt->inode->val == NULL) && !nil
                    && !WXS_IS_LIST(simpleType)
                    && !(vctxt->inode->flags & XML_SCHEMA_NODE_INFO_LIST_VALUE)) {
		/*
		* Failed to provide the normalized value; maybe
		* the value was invalid.
]==] _source "${_source}")
    string(REPLACE [==[		    * Consume the compiled value.
		    */
		    key->type = simpleType;
                    key->val = nil ? NULL : vctxt->inode->val;
                    if (!nil) {
                        vctxt->inode->val = NULL;
]==] [==[		    * Consume the compiled value.
		    */
		    key->type = simpleType;
                    key->nil = nil;
                    key->list = WXS_IS_LIST(simpleType) ||
                        (vctxt->inode->flags & XML_SCHEMA_NODE_INFO_LIST_VALUE);
                    key->val = nil ? NULL : vctxt->inode->val;
                    if (!nil) {
                        vctxt->inode->val = NULL;
]==] _source "${_source}")
    string(REPLACE [==[	    }

	    for (i = 0; i < nbKeys; i++) {
                if (((*keySeq)[i] == NULL) || ((*keySeq)[i]->val == NULL)) {
		    /*
		    * Not qualified, if any field is absent or nil.
		    */
]==] [==[	    }

	    for (i = 0; i < nbKeys; i++) {
                if (((*keySeq)[i] == NULL) || (*keySeq)[i]->nil) {
		    /*
		    * Not qualified, if any field is absent or nil.
		    */
]==] _source "${_source}")
    string(REPLACE [==[		    for (j = 0; j < nbKeys; j++) {
			ckey = (*keySeq)[j];
			bkey = bkeySeq[j];
			res = xmlSchemaAreValuesEqual(ckey->val, bkey->val);
			if (res == -1) {
			    return (-1);
			} else if (res == 0) {
]==] [==[		    for (j = 0; j < nbKeys; j++) {
			ckey = (*keySeq)[j];
			bkey = bkeySeq[j];
			res = xmlSchemaIDCEqualKeys(ckey, bkey);
			if (res == -1) {
			    return (-1);
			} else if (res == 0) {
]==] _source "${_source}")
    string(REPLACE [==[{
    int i;
    for (i = 0; i < count; i++) {
        int ret = xmlSchemaAreValuesEqual(a->keys[i]->val, b->keys[i]->val);
        if (ret != 1) {
            return ret;
        }
]==] [==[{
    int i;
    for (i = 0; i < count; i++) {
        int ret = xmlSchemaIDCEqualKeys(a->keys[i], b->keys[i]);
        if (ret != 1) {
            return ret;
        }
]==] _source "${_source}")
    string(REPLACE [==[		    for (;e; e = e->next) {
			keys = bind->nodeTable[e->index]->keys;
			for (k = 0; k < nbFields; k++) {
			    res = xmlSchemaAreValuesEqual(keys[k]->val,
							  refKeys[k]->val);
			    if (res == 0)
			        break;
			    else if (res == -1) {
]==] [==[		    for (;e; e = e->next) {
			keys = bind->nodeTable[e->index]->keys;
			for (k = 0; k < nbFields; k++) {
			    res = xmlSchemaIDCEqualKeys(keys[k], refKeys[k]);
			    if (res == 0)
			        break;
			    else if (res == -1) {
]==] _source "${_source}")
    string(REPLACE [==[			    keys = ((xmlSchemaPSVIIDCNodePtr)
				bind->dupls->items[j])->keys;
			    for (k = 0; k < nbFields; k++) {
				res = xmlSchemaAreValuesEqual(keys[k]->val,
				    refKeys[k]->val);
				if (res == 0)
				    break;
				else if (res == -1) {
]==] [==[			    keys = ((xmlSchemaPSVIIDCNodePtr)
				bind->dupls->items[j])->keys;
			    for (k = 0; k < nbFields; k++) {
				res = xmlSchemaIDCEqualKeys(keys[k], refKeys[k]);
				if (res == 0)
				    break;
				else if (res == -1) {
]==] _source "${_source}")
    string(REPLACE [==[			     xmlSchemaValPtr *retVal,
			     int fireErrors,
			     int normalize,
			     int isNormalized)
{
    int ret = 0, valNeeded = (retVal) ? 1 : 0;
    xmlSchemaValPtr val = NULL;
    /* xmlSchemaWhitespaceValueType ws; */
    xmlChar *normValue = NULL;

#define NORMALIZE(atype) \
    if ((! isNormalized) && \
]==] [==[			     xmlSchemaValPtr *retVal,
			     int fireErrors,
			     int normalize,
			     int isNormalized, int *listValue)
{
    int ret = 0, valNeeded = (retVal) ? 1 : 0;
    xmlSchemaValPtr val = NULL;
    /* xmlSchemaWhitespaceValueType ws; */
    xmlChar *normValue = NULL;
    if (listValue != NULL) {
        *listValue = WXS_IS_LIST(type) != 0;
    }

#define NORMALIZE(atype) \
    if ((! isNormalized) && \
]==] _source "${_source}")
    string(REPLACE [==[
	    if (valNeeded)
		ret = xmlSchemaVCheckCVCDataType(actxt, node, itemType,
		    tmpValue, &curVal, fireErrors, 0, 1);
	    else
		ret = xmlSchemaVCheckCVCDataType(actxt, node, itemType,
		    tmpValue, NULL, fireErrors, 0, 1);
	    FREE_AND_NULL(tmpValue);
	    if (curVal != NULL) {
		/*
]==] [==[
	    if (valNeeded)
		ret = xmlSchemaVCheckCVCDataType(actxt, node, itemType,
		    tmpValue, &curVal, fireErrors, 0, 1, NULL);
	    else
		ret = xmlSchemaVCheckCVCDataType(actxt, node, itemType,
		    tmpValue, NULL, fireErrors, 0, 1, NULL);
	    FREE_AND_NULL(tmpValue);
	    if (curVal != NULL) {
		/*
]==] _source "${_source}")
    string(REPLACE [==[	while (memberLink != NULL) {
	    if (valNeeded)
		ret = xmlSchemaVCheckCVCDataType(actxt, node,
		    memberLink->type, value, &val, 0, 1, 0);
	    else
		ret = xmlSchemaVCheckCVCDataType(actxt, node,
		    memberLink->type, value, NULL, 0, 1, 0);
	    if (ret <= 0)
		break;
	    memberLink = memberLink->next;
]==] [==[	while (memberLink != NULL) {
	    if (valNeeded)
		ret = xmlSchemaVCheckCVCDataType(actxt, node,
		    memberLink->type, value, &val, 0, 1, 0, listValue);
	    else
		ret = xmlSchemaVCheckCVCDataType(actxt, node,
		    memberLink->type, value, NULL, 0, 1, 0, listValue);
	    if (ret <= 0)
		break;
	    memberLink = memberLink->next;
]==] _source "${_source}")
    string(REPLACE [==[                             int isNormalized)
{
    xmlSchemaValPtr val = NULL, item;
    int ret;

    if ((actxt->type != XML_SCHEMA_CTXT_VALIDATOR) ||
        (!xmlSchemaTypeHasEntity(type))) {
        return(xmlSchemaVCheckCVCDataType(actxt, node, type, value, retVal,
            fireErrors, normalize, isNormalized));
    }
    if ((retVal != NULL) && (*retVal != NULL)) {
        xmlSchemaFreeValue(*retVal);
        *retVal = NULL;
    }
    ret = xmlSchemaVCheckCVCDataType(actxt, node, type, value, &val,
        fireErrors, normalize, isNormalized);
    for (item = val; (ret == 0) && (item != NULL);
         item = xmlSchemaValueGetNext(item)) {
        if (xmlSchemaGetValType(item) == XML_SCHEMAS_ENTITY) {
]==] [==[                             int isNormalized)
{
    xmlSchemaValPtr val = NULL, item;
    int ret, listValue = 0;
    xmlSchemaNodeInfoPtr capture = NULL;
    if (actxt->type == XML_SCHEMA_CTXT_VALIDATOR) {
        xmlSchemaValidCtxtPtr vctxt = (xmlSchemaValidCtxtPtr) actxt;
        if (vctxt->inode != NULL && retVal == &vctxt->inode->val) {
            capture = vctxt->inode;
            capture->flags &= ~XML_SCHEMA_NODE_INFO_LIST_VALUE;
        }
    }

    if ((actxt->type != XML_SCHEMA_CTXT_VALIDATOR) ||
        (!xmlSchemaTypeHasEntity(type))) {
        ret = xmlSchemaVCheckCVCDataType(actxt, node, type, value, retVal,
            fireErrors, normalize, isNormalized, &listValue);
        if (ret == 0 && listValue && capture != NULL) {
            capture->flags |= XML_SCHEMA_NODE_INFO_LIST_VALUE;
        }
        return ret;
    }
    if ((retVal != NULL) && (*retVal != NULL)) {
        xmlSchemaFreeValue(*retVal);
        *retVal = NULL;
    }
    ret = xmlSchemaVCheckCVCDataType(actxt, node, type, value, &val,
        fireErrors, normalize, isNormalized, &listValue);
    for (item = val; (ret == 0) && (item != NULL);
         item = xmlSchemaValueGetNext(item)) {
        if (xmlSchemaGetValType(item) == XML_SCHEMAS_ENTITY) {
]==] _source "${_source}")
    string(REPLACE [==[        *retVal = val;
    } else {
        xmlSchemaFreeValue(val);
    }
    return(ret);
}
]==] [==[        *retVal = val;
    } else {
        xmlSchemaFreeValue(val);
    }
    if (ret == 0 && listValue && capture != NULL) {
        capture->flags |= XML_SCHEMA_NODE_INFO_LIST_VALUE;
    }
    return(ret);
}
]==] _source "${_source}")
    string(REPLACE [==[		* IDCs will consume the precomputed default value,
		* so we need to clone it.
		*/
		if (iattr->val == NULL) {
		    VERROR_INT("xmlSchemaVAttributesComplex",
			"default/fixed value on an attribute use was "
			"not precomputed");
		    goto internal_error;
		}
		iattr->val = xmlSchemaCopyValue(iattr->val);
		if (iattr->val == NULL) {
		    VERROR_INT("xmlSchemaVAttributesComplex",
			"calling xmlSchemaCopyValue()");
		    goto internal_error;
		}
	    }
	    /*
	    * PSVI: Add the default attribute to the current element.
]==] [==[		* IDCs will consume the precomputed default value,
		* so we need to clone it.
		*/
                if (xpathRes) {
                    xmlNodePtr previous = vctxt->defaultNamespaceNode;
                    /* The current value is borrowed from the schema. */
                    iattr->val = NULL;
                    vctxt->defaultNamespaceNode = iattr->use->defValue != NULL
                        ? iattr->use->node : iattr->decl->node;
                    res = xmlSchemaVCheckCVCSimpleType(ACTXT_CAST vctxt, NULL,
                        iattr->typeDef, iattr->value, &iattr->val, 1, 1, 0);
                    vctxt->defaultNamespaceNode = previous;
                    if (res != 0) {
                        goto internal_error;
                    }
                } else {
                    if (iattr->val == NULL) {
                        VERROR_INT("xmlSchemaVAttributesComplex",
                            "default/fixed attribute value was not precomputed");
                        goto internal_error;
                    }
                    iattr->val = xmlSchemaCopyValue(iattr->val);
                    if (iattr->val == NULL) {
                        VERROR_INT("xmlSchemaVAttributesComplex", "copying a default attribute value");
                        goto internal_error;
                    }
                }
	    }
	    /*
	    * PSVI: Add the default attribute to the current element.
]==] _source "${_source}")
    string(REPLACE [==[		"calling xmlSchemaXPathEvaluate()");
	    goto internal_error;
	}
    }
    /*
    * Validate attributes.
]==] [==[		"calling xmlSchemaXPathEvaluate()");
	    goto internal_error;
	}
    }
    /* Built-in instance attributes are assessed for both content varieties. */
    if (xmlSchemaVInstanceAttributes(vctxt) < 0) {
        goto internal_error;
    }
    /*
    * Validate attributes.
]==] _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "d87f077caf371594f5f1ad8fa4fc327190c6e31acba04cd328f789540e8c1a1e")
        message(FATAL_ERROR "Pinned libxml2 instance attribute and list identity fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-instance-identity-fix")
    set(_replacement "${binary_dir}/qore-instance-identity-fix/xmlschemas.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    qore_xml_fix_libxml2_instance_identity_values("${source_dir}" "${binary_dir}")
    message(STATUS "XML module: applied libxml2 instance attribute and list identity assessment in the build tree")
endfunction()

# Preserve expanded names and allocation failures in the shared value formatter.
function(qore_xml_fix_libxml2_instance_identity_values source_dir binary_dir)
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
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemastypes.c for identity value formatting")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "68dda4b794ceb9bd8819c6158f1917b062b021f9017ab4bcb11a6b3886040d97")
        return()
    endif()
    if(NOT _hash STREQUAL "2abe89c92ecc1219e6174237f9239fc088e6aa4e916c52869c52ae7ecf592bef")
        message(FATAL_ERROR "Unexpected libxml2 xmlschemastypes.c; cannot apply identity value formatting")
    endif()
    file(READ "${_path}" _source)
    string(REPLACE [==[	case XML_SCHEMAS_QNAME:
	    /* TODO: Unclear in XML Schema 1.0. */
	    if (val->value.qname.uri == NULL) {
		*retValue = BAD_CAST xmlStrdup(BAD_CAST val->value.qname.name);
		return (0);
	    } else {
		*retValue = BAD_CAST xmlStrdup(BAD_CAST "{");
		*retValue = BAD_CAST xmlStrcat((xmlChar *) (*retValue),
		    BAD_CAST val->value.qname.uri);
		*retValue = BAD_CAST xmlStrcat((xmlChar *) (*retValue),
		    BAD_CAST "}");
		*retValue = BAD_CAST xmlStrcat((xmlChar *) (*retValue),
		    BAD_CAST val->value.qname.uri);
	    }
	    break;
]==] [==[        case XML_SCHEMAS_QNAME:
        case XML_SCHEMAS_NOTATION: {
            xmlBufPtr buffer;
            if (val->value.qname.name == NULL) {
                return -1;
            }
            buffer = xmlBufCreate(64);
            if (buffer == NULL) {
                return -1;
            }
            if (val->value.qname.uri != NULL) {
                if (xmlBufAdd(buffer, BAD_CAST "{", 1) != 0 ||
                        xmlBufCat(buffer, val->value.qname.uri) != 0 ||
                        xmlBufAdd(buffer, BAD_CAST "}", 1) != 0) {
                    xmlBufFree(buffer);
                    return -1;
                }
            }
            if (xmlBufCat(buffer, val->value.qname.name) != 0) {
                xmlBufFree(buffer);
                return -1;
            }
            *retValue = xmlBufDetach(buffer);
            xmlBufFree(buffer);
            return *retValue == NULL ? -1 : 0;
        }
]==] _source "${_source}")
    string(REPLACE "\tcase XML_SCHEMAS_NOTATION: /* Unclear */\n" "" _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "68dda4b794ceb9bd8819c6158f1917b062b021f9017ab4bcb11a6b3886040d97")
        message(FATAL_ERROR "Pinned libxml2 identity value formatter fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-instance-identity-fix")
    set(_replacement "${binary_dir}/qore-instance-identity-fix/xmlschemastypes.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
endfunction()
