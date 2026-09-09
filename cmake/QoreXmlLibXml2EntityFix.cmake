# Copyright (C) 2026 Qore Technologies, s.r.o.
# Restore XSD ENTITY document context, computed values and built-in list facets.
# Apply after the QName and URI fixes; preserve pinned/offline upstream sources.
function(qore_xml_fix_libxml2_entities source_dir binary_dir)
    get_target_property(_sources LibXml2 SOURCES)
    foreach(_filename IN ITEMS xmlschemas.c xmlschemastypes.c)
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
            message(FATAL_ERROR "Cannot locate libxml2 ${_filename} for ENTITY fixes")
        endif()
        if(IS_ABSOLUTE "${_input}")
            set(_path "${_input}")
        else()
            set(_path "${source_dir}/${_input}")
        endif()
        file(SHA256 "${_path}" _hash)
        file(READ "${_path}" _source)
        if(_filename STREQUAL "xmlschemas.c")
            set(_original_hash 62def2d85880e32e6a69b810302f301190c4a9a5581437447d10dff7fc626e31)
            set(_fixed_hash 955e8848f6446219f5b1546993ab55b27ed2512828c0cea5d6e30b6da1f3a105)
            string(REPLACE [==[    xmlSchemaValidityErrorFunc error;   /* the callback in case of errors */
    xmlSchemaValidityWarningFunc warning; /* the callback in case of warning */
    xmlStructuredErrorFunc serror;

    xmlSchemaPtr schema;        /* The schema in use */
    xmlDocPtr doc;
    xmlParserInputBufferPtr input;
    xmlCharEncoding enc;
    xmlSAXHandlerPtr sax;
    xmlParserCtxtPtr parserCtxt;
    void *user_data; /* TODO: What is this for? */
    char *filename;
]==]
                [==[    xmlSchemaValidityErrorFunc error;   /* the callback in case of errors */
    xmlSchemaValidityWarningFunc warning; /* the callback in case of warning */
    xmlStructuredErrorFunc serror;

    xmlSchemaPtr schema;        /* The schema in use */
    xmlDocPtr doc;
    /* First general-entity declarations in the current SAX document. */
    xmlHashTablePtr entities;
    xmlParserInputBufferPtr input;
    xmlCharEncoding enc;
    xmlSAXHandlerPtr sax;
    xmlParserCtxtPtr parserCtxt;
    void *user_data; /* TODO: What is this for? */
    char *filename;
]==] _source "${_source}")
            string(REPLACE [==[	if (res == 1)
	    xmlSchemaDeriveFacetErr(pctxt, fmaxlen, bfmaxlen, -1, 1, 1);
	if ((res != 0) && (bfmaxlen->fixed)) {
	    FACET_RESTR_FIXED_ERR(fmaxlen)
	}
    }
    /*
    * SCC "length and minLength or maxLength"
    */
    if (! flength)
	flength = bflength;
    if (flength) {
]==]
                [==[	if (res == 1)
	    xmlSchemaDeriveFacetErr(pctxt, fmaxlen, bfmaxlen, -1, 1, 1);
	if ((res != 0) && (bfmaxlen->fixed)) {
	    FACET_RESTR_FIXED_ERR(fmaxlen)
	}
    }
    /* XSD 1.0 Part 2 section 4.3.2.4 applies to the effective facets,
     * including a minimum or maximum inherited from the base type. */
    {
        xmlSchemaFacetPtr minimum = fminlen != NULL ? fminlen : bfminlen;
        xmlSchemaFacetPtr maximum = fmaxlen != NULL ? fmaxlen : bfmaxlen;
        if ((minimum != NULL) && (maximum != NULL)) {
            res = xmlSchemaCompareValues(minimum->val, maximum->val);
            if (res == -2) {
                goto internal_error;
            }
            if (res == 1) {
                xmlSchemaDeriveFacetErr(pctxt, minimum, maximum, -1, 1, 0);
            }
        }
    }
    /*
    * SCC "length and minLength or maxLength"
    */
    if (! flength)
	flength = bflength;
    if (flength) {
]==] _source "${_source}")
            string(REPLACE [==[    xmlSchemaTypePtr tmpType;
    xmlSchemaFacetLinkPtr facetLink;
    xmlSchemaFacetPtr facet;
    unsigned long len = 0;
    xmlSchemaWhitespaceValueType ws;

    /*
    * In Libxml2, derived built-in types have currently no explicit facets.
    */
    if (type->type == XML_SCHEMA_TYPE_BASIC)
	return (0);

    /*
    * NOTE: Do not jump away, if the facetSet of the given type is
    * empty: until now, "pattern" and "enumeration" facets of the
    * *base types* need to be checked as well.
    */
]==]
                [==[    xmlSchemaTypePtr tmpType;
    xmlSchemaFacetLinkPtr facetLink;
    xmlSchemaFacetPtr facet;
    unsigned long len = 0;
    xmlSchemaWhitespaceValueType ws;

    /* Built-in list types carry the explicit minLength=1 facet. */
    if ((type->type == XML_SCHEMA_TYPE_BASIC) && (!WXS_IS_LIST(type))) {
        return (0);
    }

    /*
    * NOTE: Do not jump away, if the facetSet of the given type is
    * empty: until now, "pattern" and "enumeration" facets of the
    * *base types* need to be checked as well.
    */
]==] _source "${_source}")
            string(REPLACE [==[		BAD_CAST local);
    } else
	xmlFree(local);
    return (0);
}

/*
* cvc-simple-type
*/
static int
xmlSchemaVCheckCVCSimpleType(xmlSchemaAbstractCtxtPtr actxt,
			     xmlNodePtr node,
			     xmlSchemaTypePtr type,
			     const xmlChar *value,
			     xmlSchemaValPtr *retVal,
			     int fireErrors,
			     int normalize,
]==]
                [==[		BAD_CAST local);
    } else
	xmlFree(local);
    return (0);
}

/* Identity-only payloads; the validation context owns the table and names. */
static int xmlSchemaParsedEntity;
static int xmlSchemaUnparsedEntity;

/* Datatype conversion also runs while compiling facets and defaults. Only
 * instance validation checks the containing document's unparsed entities
 * (XSD 1.0 Part 1, String Valid, clauses 2.1 and 2.2). */
static int
xmlSchemaValidateEntity(const xmlChar *value, xmlSchemaValPtr *val,
                       int valNeeded)
{
    const xmlChar *start = value, *end;
    xmlChar *name;
    int ret;

    while (IS_BLANK_CH(*start)) {
        start++;
    }
    end = start;
    while ((*end != 0) && (!IS_BLANK_CH(*end))) {
        end++;
    }
    name = xmlStrndup(start, end - start);
    if (name == NULL) {
        return(-1);
    }
    while (IS_BLANK_CH(*end)) {
        end++;
    }
    ret = (*end != 0) ? 1 : xmlValidateNCName(name, 0);
    if ((ret == 0) && valNeeded) {
        *val = xmlSchemaNewStringValue(XML_SCHEMAS_ENTITY, name);
        if (*val == NULL) {
            ret = -1;
        } else {
            name = NULL;
        }
    }
    xmlFree(name);
    return(ret);
}

/* Datatype and facet validation; document constraints run in the wrapper. */
static int
xmlSchemaVCheckCVCDataType(xmlSchemaAbstractCtxtPtr actxt,
			     xmlNodePtr node,
			     xmlSchemaTypePtr type,
			     const xmlChar *value,
			     xmlSchemaValPtr *retVal,
			     int fireErrors,
			     int normalize,
]==] _source "${_source}")
            string(REPLACE [==[	/*
	* NOTATIONs need to be processed here, since they need
	* to lookup in the hashtable of NOTATION declarations of the schema.
	*/
	if (actxt->type == XML_SCHEMA_CTXT_VALIDATOR) {
	    switch (biType->builtInType) {
		case XML_SCHEMAS_NOTATION:
		    ret = xmlSchemaValidateNotation(
			(xmlSchemaValidCtxtPtr) actxt,
			((xmlSchemaValidCtxtPtr) actxt)->schema,
			NULL, value, &val, valNeeded);
		    break;
]==]
                [==[	/*
	* NOTATIONs need to be processed here, since they need
	* to lookup in the hashtable of NOTATION declarations of the schema.
	*/
	if (actxt->type == XML_SCHEMA_CTXT_VALIDATOR) {
	    switch (biType->builtInType) {
                case XML_SCHEMAS_ENTITY:
                    ret = xmlSchemaValidateEntity(value, &val, valNeeded);
                    break;
		case XML_SCHEMAS_NOTATION:
		    ret = xmlSchemaValidateNotation(
			(xmlSchemaValidCtxtPtr) actxt,
			((xmlSchemaValidCtxtPtr) actxt)->schema,
			NULL, value, &val, valNeeded);
		    break;
]==] _source "${_source}")
            string(REPLACE [==[			ret = xmlSchemaValPredefTypeNodeNoNorm(biType,
			    value, NULL, node);
		    break;
	    }
	} else if (actxt->type == XML_SCHEMA_CTXT_PARSER) {
	    switch (biType->builtInType) {
		case XML_SCHEMAS_NOTATION:
		    ret = xmlSchemaValidateNotation(NULL,
			((xmlSchemaParserCtxtPtr) actxt)->schema, node,
			value, &val, valNeeded);
		    break;
		default:
]==]
                [==[			ret = xmlSchemaValPredefTypeNodeNoNorm(biType,
			    value, NULL, node);
		    break;
	    }
	} else if (actxt->type == XML_SCHEMA_CTXT_PARSER) {
	    switch (biType->builtInType) {
                case XML_SCHEMAS_ENTITY:
                    ret = xmlSchemaValidateEntity(value, &val, valNeeded);
                    break;
		case XML_SCHEMAS_NOTATION:
		    ret = xmlSchemaValidateNotation(NULL,
			((xmlSchemaParserCtxtPtr) actxt)->schema, node,
			value, &val, valNeeded);
		    break;
		default:
]==] _source "${_source}")
            string(REPLACE [==[	    if (end == cur)
		break;
	    tmpValue = xmlStrndup(cur, end - cur);
	    len++;

	    if (valNeeded)
		ret = xmlSchemaVCheckCVCSimpleType(actxt, node, itemType,
		    tmpValue, &curVal, fireErrors, 0, 1);
	    else
		ret = xmlSchemaVCheckCVCSimpleType(actxt, node, itemType,
		    tmpValue, NULL, fireErrors, 0, 1);
	    FREE_AND_NULL(tmpValue);
	    if (curVal != NULL) {
		/*
		* Add to list of computed values.
		*/
]==]
                [==[	    if (end == cur)
		break;
	    tmpValue = xmlStrndup(cur, end - cur);
	    len++;

	    if (valNeeded)
		ret = xmlSchemaVCheckCVCDataType(actxt, node, itemType,
		    tmpValue, &curVal, fireErrors, 0, 1);
	    else
		ret = xmlSchemaVCheckCVCDataType(actxt, node, itemType,
		    tmpValue, NULL, fireErrors, 0, 1);
	    FREE_AND_NULL(tmpValue);
	    if (curVal != NULL) {
		/*
		* Add to list of computed values.
		*/
]==] _source "${_source}")
            string(REPLACE [==[	* cannot store the whitespace information with the value
	* itself; otherwise a later value-comparison would be
	* not possible.
	*/
	while (memberLink != NULL) {
	    if (valNeeded)
		ret = xmlSchemaVCheckCVCSimpleType(actxt, node,
		    memberLink->type, value, &val, 0, 1, 0);
	    else
		ret = xmlSchemaVCheckCVCSimpleType(actxt, node,
		    memberLink->type, value, NULL, 0, 1, 0);
	    if (ret <= 0)
		break;
	    memberLink = memberLink->next;
	}
	if (ret != 0) {
]==]
                [==[	* cannot store the whitespace information with the value
	* itself; otherwise a later value-comparison would be
	* not possible.
	*/
	while (memberLink != NULL) {
	    if (valNeeded)
		ret = xmlSchemaVCheckCVCDataType(actxt, node,
		    memberLink->type, value, &val, 0, 1, 0);
	    else
		ret = xmlSchemaVCheckCVCDataType(actxt, node,
		    memberLink->type, value, NULL, 0, 1, 0);
	    if (ret <= 0)
		break;
	    memberLink = memberLink->next;
	}
	if (ret != 0) {
]==] _source "${_source}")
            string(REPLACE [==[internal_error:
    if (normValue != NULL)
	xmlFree(normValue);
    if (val != NULL)
	xmlSchemaFreeValue(val);
    return (-1);
}

static int
xmlSchemaVExpandQName(xmlSchemaValidCtxtPtr vctxt,
			   const xmlChar *value,
			   const xmlChar **nsName,
]==]
                [==[internal_error:
    if (normValue != NULL)
	xmlFree(normValue);
    if (val != NULL)
	xmlSchemaFreeValue(val);
    return (-1);
}

/* Union member lists have already been flattened by schema construction.
 * List items may themselves be unions, but cannot contain list members. */
static int
xmlSchemaTypeHasEntity(xmlSchemaTypePtr type)
{
    if (WXS_IS_LIST(type)) {
        return(xmlSchemaTypeHasEntity(WXS_LIST_ITEMTYPE(type)));
    }
    if (WXS_IS_UNION(type)) {
        xmlSchemaTypeLinkPtr member = xmlSchemaGetUnionSimpleTypeMemberTypes(type);
        while (member != NULL) {
            if (xmlSchemaTypeHasEntity(member->type)) {
                return(1);
            }
            member = member->next;
        }
        return(0);
    }
    while ((type != NULL) && (type->type != XML_SCHEMA_TYPE_BASIC)) {
        type = type->baseType;
    }
    return((type != NULL) && (type->builtInType == XML_SCHEMAS_ENTITY));
}

/* XSD 1.0 Part 2 section 2.5.1.3 chooses the first matching datatype;
 * String Valid subsequently checks the selected ENTITY values. An undeclared
 * entity must not change that choice to a later string member. */
static int
xmlSchemaVCheckCVCSimpleType(xmlSchemaAbstractCtxtPtr actxt,
                             xmlNodePtr node,
                             xmlSchemaTypePtr type,
                             const xmlChar *value,
                             xmlSchemaValPtr *retVal,
                             int fireErrors,
                             int normalize,
                             int isNormalized)
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
            const xmlChar *name = xmlSchemaValueGetAsString(item);
            xmlSchemaValidCtxtPtr vctxt = (xmlSchemaValidCtxtPtr) actxt;
            xmlDocPtr doc = (node != NULL) ? node->doc : vctxt->doc;
            if (doc != NULL) {
                xmlEntityPtr entity = xmlGetDocEntity(doc, name);
                ret = (entity == NULL) ||
                    (entity->etype != XML_EXTERNAL_GENERAL_UNPARSED_ENTITY);
            } else {
                ret = xmlHashLookup(vctxt->entities, name) != &xmlSchemaUnparsedEntity;
            }
            if (ret > 0) {
                ret = XML_SCHEMAV_CVC_DATATYPE_VALID_1_2_1;
                if (fireErrors) {
                    xmlSchemaCustomErr(actxt, ret, node,
                        WXS_BASIC_CAST xmlSchemaGetBuiltInType(XML_SCHEMAS_ENTITY),
                        "The ENTITY value '%s' does not name an unparsed entity "
                        "in the containing document", name, NULL);
                }
            } else if ((node != NULL) && (node->type == XML_ATTRIBUTE_NODE) &&
                       WXS_IS_ATOMIC(type)) {
                ((xmlAttrPtr) node)->atype = XML_ATTRIBUTE_ENTITY;
            }
        }
    }
    if ((ret == 0) && (retVal != NULL)) {
        *retVal = val;
    } else {
        xmlSchemaFreeValue(val);
    }
    return(ret);
}

static int
xmlSchemaVExpandQName(xmlSchemaValidCtxtPtr vctxt,
			   const xmlChar *value,
			   const xmlChar **nsName,
]==] _source "${_source}")
            string(REPLACE [==[    *   Might be problematic if one reuses the context
    *   and assumes that the options remain the same.
    */
    vctxt->flags = 0;
    vctxt->validationRoot = NULL;
    vctxt->doc = NULL;
#ifdef LIBXML_READER_ENABLED
    vctxt->reader = NULL;
#endif
    vctxt->hasKeyrefs = 0;

    if (vctxt->value != NULL) {
]==]
                [==[    *   Might be problematic if one reuses the context
    *   and assumes that the options remain the same.
    */
    vctxt->flags = 0;
    vctxt->validationRoot = NULL;
    vctxt->doc = NULL;
    xmlHashFree(vctxt->entities, NULL);
    vctxt->entities = NULL;
#ifdef LIBXML_READER_ENABLED
    vctxt->reader = NULL;
#endif
    vctxt->hasKeyrefs = 0;

    if (vctxt->value != NULL) {
]==] _source "${_source}")
            string(REPLACE [==[ */
void
xmlSchemaFreeValidCtxt(xmlSchemaValidCtxt *ctxt)
{
    if (ctxt == NULL)
        return;
    if (ctxt->value != NULL)
        xmlSchemaFreeValue(ctxt->value);
    if (ctxt->pctxt != NULL)
	xmlSchemaFreeParserCtxt(ctxt->pctxt);
    if (ctxt->idcNodes != NULL) {
	int i;
]==]
                [==[ */
void
xmlSchemaFreeValidCtxt(xmlSchemaValidCtxt *ctxt)
{
    if (ctxt == NULL)
        return;
    xmlHashFree(ctxt->entities, NULL);
    if (ctxt->value != NULL)
        xmlSchemaFreeValue(ctxt->value);
    if (ctxt->pctxt != NULL)
	xmlSchemaFreeParserCtxt(ctxt->pctxt);
    if (ctxt->idcNodes != NULL) {
	int i;
]==] _source "${_source}")
            string(REPLACE [==[        (ctxt->user_sax->getParameterEntity != NULL))
	return(ctxt->user_sax->getParameterEntity(ctxt->user_data, name));
    return(NULL);
}


static void
entityDeclSplit(void *ctx, const xmlChar *name, int type,
          const xmlChar *publicId, const xmlChar *systemId, xmlChar *content)
{
    xmlSchemaSAXPlugPtr ctxt = (xmlSchemaSAXPlugPtr) ctx;
    if ((ctxt != NULL) && (ctxt->user_sax != NULL) &&
        (ctxt->user_sax->entityDecl != NULL))
	ctxt->user_sax->entityDecl(ctxt->user_data, name, type, publicId,
	                           systemId, content);
}

]==]
                [==[        (ctxt->user_sax->getParameterEntity != NULL))
	return(ctxt->user_sax->getParameterEntity(ctxt->user_data, name));
    return(NULL);
}


/* Preserve the first binding (XML 1.0 section 4.2), including a parsed
 * declaration that prevents a later unparsed declaration from replacing it.
 * Parameter entities belong to a separate namespace. */
static void
xmlSchemaSAXRecordEntity(xmlSchemaValidCtxtPtr ctxt, const xmlChar *name,
                         int type)
{
    void *kind;

    if ((type != XML_INTERNAL_GENERAL_ENTITY) &&
        (type != XML_EXTERNAL_GENERAL_PARSED_ENTITY) &&
        (type != XML_EXTERNAL_GENERAL_UNPARSED_ENTITY)) {
        return;
    }
    if (ctxt->entities == NULL) {
        ctxt->entities = xmlHashCreate(0);
        if (ctxt->entities == NULL) {
            xmlSchemaVErrMemory(ctxt);
            return;
        }
    }
    if (xmlHashLookup(ctxt->entities, name) != NULL) {
        return;
    }
    kind = (type == XML_EXTERNAL_GENERAL_UNPARSED_ENTITY) ?
        &xmlSchemaUnparsedEntity : &xmlSchemaParsedEntity;
    if (xmlHashAddEntry(ctxt->entities, name, kind) < 0) {
        xmlSchemaVErrMemory(ctxt);
    }
}

static void
xmlSchemaSAXEntityDecl(void *ctx, const xmlChar *name, int type,
                       const xmlChar *publicId ATTRIBUTE_UNUSED,
                       const xmlChar *systemId ATTRIBUTE_UNUSED,
                       xmlChar *content ATTRIBUTE_UNUSED)
{
    xmlSchemaSAXRecordEntity((xmlSchemaValidCtxtPtr) ctx, name, type);
}

static void
xmlSchemaSAXUnparsedEntityDecl(void *ctx, const xmlChar *name,
                       const xmlChar *publicId ATTRIBUTE_UNUSED,
                       const xmlChar *systemId ATTRIBUTE_UNUSED,
                       const xmlChar *notationName ATTRIBUTE_UNUSED)
{
    xmlSchemaSAXRecordEntity((xmlSchemaValidCtxtPtr) ctx, name,
        XML_EXTERNAL_GENERAL_UNPARSED_ENTITY);
}

static void
entityDeclSplit(void *ctx, const xmlChar *name, int type,
          const xmlChar *publicId, const xmlChar *systemId, xmlChar *content)
{
    xmlSchemaSAXPlugPtr ctxt = (xmlSchemaSAXPlugPtr) ctx;
    if ((ctxt != NULL) && (ctxt->ctxt != NULL)) {
        xmlSchemaSAXRecordEntity(ctxt->ctxt, name, type);
    }
    if ((ctxt != NULL) && (ctxt->user_sax != NULL) &&
        (ctxt->user_sax->entityDecl != NULL))
	ctxt->user_sax->entityDecl(ctxt->user_data, name, type, publicId,
	                           systemId, content);
}

]==] _source "${_source}")
            string(REPLACE [==[static void
unparsedEntityDeclSplit(void *ctx, const xmlChar *name,
		   const xmlChar *publicId, const xmlChar *systemId,
		   const xmlChar *notationName)
{
    xmlSchemaSAXPlugPtr ctxt = (xmlSchemaSAXPlugPtr) ctx;
    if ((ctxt != NULL) && (ctxt->user_sax != NULL) &&
        (ctxt->user_sax->unparsedEntityDecl != NULL))
	ctxt->user_sax->unparsedEntityDecl(ctxt->user_data, name, publicId,
	                                   systemId, notationName);
}

]==]
                [==[static void
unparsedEntityDeclSplit(void *ctx, const xmlChar *name,
		   const xmlChar *publicId, const xmlChar *systemId,
		   const xmlChar *notationName)
{
    xmlSchemaSAXPlugPtr ctxt = (xmlSchemaSAXPlugPtr) ctx;
    if ((ctxt != NULL) && (ctxt->ctxt != NULL)) {
        xmlSchemaSAXRecordEntity(ctxt->ctxt, name,
            XML_EXTERNAL_GENERAL_UNPARSED_ENTITY);
    }
    if ((ctxt != NULL) && (ctxt->user_sax != NULL) &&
        (ctxt->user_sax->unparsedEntityDecl != NULL))
	ctxt->user_sax->unparsedEntityDecl(ctxt->user_data, name, publicId,
	                                   systemId, notationName);
}

]==] _source "${_source}")
            string(REPLACE [==[	 */
	ret->schemas_sax.ignorableWhitespace = xmlSchemaSAXHandleText;
	ret->schemas_sax.characters = xmlSchemaSAXHandleText;

	ret->schemas_sax.cdataBlock = xmlSchemaSAXHandleCDataSection;
	ret->schemas_sax.reference = xmlSchemaSAXHandleReference;

	ret->user_data = ctxt;
	*user_data = ctxt;
    } else {
       /*
        * for each callback unused by Schemas initialize it to the Split
]==]
                [==[	 */
	ret->schemas_sax.ignorableWhitespace = xmlSchemaSAXHandleText;
	ret->schemas_sax.characters = xmlSchemaSAXHandleText;

	ret->schemas_sax.cdataBlock = xmlSchemaSAXHandleCDataSection;
	ret->schemas_sax.reference = xmlSchemaSAXHandleReference;
        ret->schemas_sax.entityDecl = xmlSchemaSAXEntityDecl;
        ret->schemas_sax.unparsedEntityDecl = xmlSchemaSAXUnparsedEntityDecl;

	ret->user_data = ctxt;
	*user_data = ctxt;
    } else {
       /*
        * for each callback unused by Schemas initialize it to the Split
]==] _source "${_source}")
            string(REPLACE [==[        if (old_sax->hasExternalSubset != NULL)
            ret->schemas_sax.hasExternalSubset = hasExternalSubsetSplit;
        if (old_sax->resolveEntity != NULL)
            ret->schemas_sax.resolveEntity = resolveEntitySplit;
        if (old_sax->getEntity != NULL)
            ret->schemas_sax.getEntity = getEntitySplit;
        if (old_sax->entityDecl != NULL)
            ret->schemas_sax.entityDecl = entityDeclSplit;
        if (old_sax->notationDecl != NULL)
            ret->schemas_sax.notationDecl = notationDeclSplit;
        if (old_sax->attributeDecl != NULL)
            ret->schemas_sax.attributeDecl = attributeDeclSplit;
        if (old_sax->elementDecl != NULL)
            ret->schemas_sax.elementDecl = elementDeclSplit;
        if (old_sax->unparsedEntityDecl != NULL)
            ret->schemas_sax.unparsedEntityDecl = unparsedEntityDeclSplit;
        if (old_sax->setDocumentLocator != NULL)
            ret->schemas_sax.setDocumentLocator = setDocumentLocatorSplit;
        if (old_sax->startDocument != NULL)
            ret->schemas_sax.startDocument = startDocumentSplit;
        if (old_sax->endDocument != NULL)
            ret->schemas_sax.endDocument = endDocumentSplit;
]==]
                [==[        if (old_sax->hasExternalSubset != NULL)
            ret->schemas_sax.hasExternalSubset = hasExternalSubsetSplit;
        if (old_sax->resolveEntity != NULL)
            ret->schemas_sax.resolveEntity = resolveEntitySplit;
        if (old_sax->getEntity != NULL)
            ret->schemas_sax.getEntity = getEntitySplit;
        ret->schemas_sax.entityDecl = entityDeclSplit;
        if (old_sax->notationDecl != NULL)
            ret->schemas_sax.notationDecl = notationDeclSplit;
        if (old_sax->attributeDecl != NULL)
            ret->schemas_sax.attributeDecl = attributeDeclSplit;
        if (old_sax->elementDecl != NULL)
            ret->schemas_sax.elementDecl = elementDeclSplit;
        ret->schemas_sax.unparsedEntityDecl = unparsedEntityDeclSplit;
        if (old_sax->setDocumentLocator != NULL)
            ret->schemas_sax.setDocumentLocator = setDocumentLocatorSplit;
        if (old_sax->startDocument != NULL)
            ret->schemas_sax.startDocument = startDocumentSplit;
        if (old_sax->endDocument != NULL)
            ret->schemas_sax.endDocument = endDocumentSplit;
]==] _source "${_source}")
        elseif(_filename STREQUAL "xmlschemastypes.c")
            set(_original_hash 714fdfd7fdde878bea05d970cb1035ba3ca8d305d0cee55c87806a5917b07f30)
            set(_fixed_hash 6c8d53841944eff6e81c63dbd3059a0f27abb3bdd114e4aa04f56e1b69f6d2bd)
            string(REPLACE [==[	    break;
	case XML_SCHEMAS_IDREFS:
	case XML_SCHEMAS_NMTOKENS:
	case XML_SCHEMAS_ENTITIES:
	    ret->flags |= XML_SCHEMAS_TYPE_VARIETY_LIST;
	    ret->facets = xmlSchemaNewMinLengthFacet(1);
	    ret->flags |= XML_SCHEMAS_TYPE_HAS_FACETS;
	    break;
	default:
	    ret->flags |= XML_SCHEMAS_TYPE_VARIETY_ATOMIC;
	    break;
    }
]==]
                [==[	    break;
	case XML_SCHEMAS_IDREFS:
	case XML_SCHEMAS_NMTOKENS:
	case XML_SCHEMAS_ENTITIES:
	    ret->flags |= XML_SCHEMAS_TYPE_VARIETY_LIST;
	    ret->facets = xmlSchemaNewMinLengthFacet(1);
            if (ret->facets == NULL) {
                xmlSchemaFreeType(ret);
                return(NULL);
            }
            ret->facetSet = xmlMalloc(sizeof(xmlSchemaFacetLink));
            if (ret->facetSet == NULL) {
                xmlSchemaFreeType(ret);
                return(NULL);
            }
            ret->facetSet->facet = ret->facets;
            ret->facetSet->next = NULL;
	    ret->flags |= XML_SCHEMAS_TYPE_HAS_FACETS;
	    break;
	default:
	    ret->flags |= XML_SCHEMAS_TYPE_VARIETY_ATOMIC;
	    break;
    }
]==] _source "${_source}")
            string(REPLACE [==[	return (0);
    return (val->value.b);
}

/**
 * Allocate a new simple type value. The type can be
 * of XML_SCHEMAS_STRING.
 * WARNING: This one is intended to be expanded for other
 * string based types. We need this for anySimpleType as well.
 * The given value is consumed and freed with the struct.
 *
 * @param type  the value type
 * @param value  the value
]==]
                [==[	return (0);
    return (val->value.b);
}

/**
 * Allocate a new simple type value. The type can be
 * of XML_SCHEMAS_STRING or XML_SCHEMAS_ENTITY.
 * WARNING: This one is intended to be expanded for other
 * string based types. We need this for anySimpleType as well.
 * The given value is consumed and freed with the struct.
 *
 * @param type  the value type
 * @param value  the value
]==] _source "${_source}")
            string(REPLACE [==[xmlSchemaVal *
xmlSchemaNewStringValue(xmlSchemaValType type,
			const xmlChar *value)
{
    xmlSchemaValPtr val;

    if (type != XML_SCHEMAS_STRING)
	return(NULL);
    val = (xmlSchemaValPtr) xmlMalloc(sizeof(xmlSchemaVal));
    if (val == NULL) {
	return(NULL);
    }
    memset(val, 0, sizeof(xmlSchemaVal));
    val->type = type;
]==]
                [==[xmlSchemaVal *
xmlSchemaNewStringValue(xmlSchemaValType type,
			const xmlChar *value)
{
    xmlSchemaValPtr val;

    if ((type != XML_SCHEMAS_STRING) && (type != XML_SCHEMAS_ENTITY)) {
        return(NULL);
    }
    val = (xmlSchemaValPtr) xmlMalloc(sizeof(xmlSchemaVal));
    if (val == NULL) {
	return(NULL);
    }
    memset(val, 0, sizeof(xmlSchemaVal));
    val->type = type;
]==] _source "${_source}")
            string(REPLACE [==[                    if ((ent == NULL) ||
                        (ent->etype !=
                         XML_EXTERNAL_GENERAL_UNPARSED_ENTITY))
                        ret = 4;
                }
                if ((ret == 0) && (val != NULL)) {
                    /* TODO */
                }
                if ((ret == 0) && (node != NULL) &&
                    (node->type == XML_ATTRIBUTE_NODE)) {
                    xmlAttrPtr attr = (xmlAttrPtr) node;

                    attr->atype = XML_ATTRIBUTE_ENTITY;
]==]
                [==[                    if ((ent == NULL) ||
                        (ent->etype !=
                         XML_EXTERNAL_GENERAL_UNPARSED_ENTITY))
                        ret = 4;
                }
                if ((ret == 0) && (val != NULL)) {
                    const xmlChar *start = value, *end;
                    while (IS_BLANK_CH(*start)) {
                        start++;
                    }
                    end = start;
                    while ((*end != 0) && (!IS_BLANK_CH(*end))) {
                        end++;
                    }
                    v = xmlSchemaNewValue(XML_SCHEMAS_ENTITY);
                    if (v == NULL) {
                        goto error;
                    }
                    v->value.str = xmlStrndup(start, end - start);
                    if (v->value.str == NULL) {
                        xmlSchemaFreeValue(v);
                        goto error;
                    }
                    *val = v;
                }
                if ((ret == 0) && (node != NULL) &&
                    (node->type == XML_ATTRIBUTE_NODE)) {
                    xmlAttrPtr attr = (xmlAttrPtr) node;

                    attr->atype = XML_ATTRIBUTE_ENTITY;
]==] _source "${_source}")
        endif()
        if(_hash STREQUAL _fixed_hash)
            continue()
        endif()
        if(NOT _hash STREQUAL _original_hash)
            message(FATAL_ERROR "Unexpected libxml2 ${_filename}; cannot apply the ENTITY fix")
        endif()
        string(SHA256 _result_hash "${_source}")
        if(NOT _result_hash STREQUAL _fixed_hash)
            message(FATAL_ERROR "Pinned libxml2 ENTITY fix did not match ${_filename}")
        endif()
        file(MAKE_DIRECTORY "${binary_dir}/qore-entity-fix")
        set(_replacement "${binary_dir}/qore-entity-fix/${_filename}")
        file(WRITE "${_replacement}.tmp" "${_source}")
        configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
        list(REMOVE_ITEM _sources "${_input}")
        list(APPEND _sources "${_replacement}")
        message(STATUS "XML module: applied libxml2 ENTITY fix to ${_filename} in the build tree")
    endforeach()
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    target_include_directories(LibXml2 PRIVATE "${source_dir}")
endfunction()
