# Copyright (C) 2026 Qore Technologies, s.r.o.
# Validate document ID/IDREF bindings after actual datatype selection.
function(qore_xml_fix_libxml2_id_bindings source_dir binary_dir)
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
        message(FATAL_ERROR "Cannot locate libxml2 xmlschemas.c for document ID/IDREF bindings")
    endif()
    if(IS_ABSOLUTE "${_input}")
        set(_path "${_input}")
    else()
        set(_path "${source_dir}/${_input}")
    endif()
    file(SHA256 "${_path}" _hash)
    if(_hash STREQUAL "600f8d93bc1c8baf799e7de148e07ac3cda456b472d14b485498e20d8fd77583")
        return()
    endif()
    if(NOT _hash STREQUAL "239c8ec7758547ff172911da21e345bdcc948eacd5142e6f556292d95cf7556c")
        message(FATAL_ERROR "Unexpected libxml2 xmlschemas.c; cannot apply document ID/IDREF bindings")
    endif()
    file(READ "${_path}" _source)
    string(REPLACE [==[    int appliedXPath; /* Indicates that an XPath has been applied. */]==] [==[    int appliedXPath; /* Indicates that an XPath has been applied. */
    unsigned long identityNumber;]==] _source "${_source}")
    string(REPLACE [==[    xmlHashTablePtr entities;]==] [==[    xmlHashTablePtr entities;
    xmlHashTablePtr idBindings;
    unsigned long nextIdentityNumber;]==] _source "${_source}")
    string(REPLACE [==[    info->depth = vctxt->depth;]==] [==[    info->depth = vctxt->depth;
    if (vctxt->nextIdentityNumber == ULONG_MAX) {
        VERROR_INT("xmlSchemaGetFreshElemInfo", "element identity counter exhausted");
        return(NULL);
    }
    info->identityNumber = ++vctxt->nextIdentityNumber;]==] _source "${_source}")
    string(REPLACE [==[static int
xmlSchemaVExpandQName(]==] [==[/* XSD 1.0 3.3.4/3.15.5: bind IDs to elements in the validation scope.
 * An ID attribute identifies its owner; an ID-valued child identifies its
 * parent. A monotonically assigned number also works with recycled SAX nodes.
 * Datatype trials never modify this table. Only the selected computed values
 * of assessed occurrences are recorded, including defaulted attributes. */
static int
xmlSchemaTypeHasIdentity(xmlSchemaTypePtr type)
{
    if (type == NULL) {
        return(0);
    }
    if (WXS_IS_COMPLEX(type) && WXS_HAS_SIMPLE_CONTENT(type)) {
        return(xmlSchemaTypeHasIdentity(type->contentTypeDef));
    }
    if (WXS_IS_LIST(type)) {
        return(xmlSchemaTypeHasIdentity(WXS_LIST_ITEMTYPE(type)));
    }
    if (WXS_IS_UNION(type)) {
        xmlSchemaTypeLinkPtr member = xmlSchemaGetUnionSimpleTypeMemberTypes(type);
        while (member != NULL) {
            if (xmlSchemaTypeHasIdentity(member->type)) {
                return(1);
            }
            member = member->next;
        }
        return(0);
    }
    while ((type != NULL) && (type->type != XML_SCHEMA_TYPE_BASIC)) {
        type = type->baseType;
    }
    return((type != NULL) && ((type->builtInType == XML_SCHEMAS_ID) ||
        (type->builtInType == XML_SCHEMAS_IDREF)));
}

typedef struct {
    unsigned long owner;
    int multiple;
} xmlSchemaIdBinding;

static void
xmlSchemaFreeIdBinding(void *payload, const xmlChar *name ATTRIBUTE_UNUSED)
{
    xmlFree(payload);
}

static int
xmlSchemaRecordIdValues(xmlSchemaValidCtxtPtr vctxt, xmlSchemaValPtr val,
                       unsigned long owner, xmlNodePtr node)
{
    xmlSchemaValPtr item;
    for (item = val; item != NULL; item = xmlSchemaValueGetNext(item)) {
        xmlSchemaValType type = xmlSchemaGetValType(item);
        const xmlChar *name;
        xmlSchemaIdBinding *binding;
        if ((type != XML_SCHEMAS_ID) && (type != XML_SCHEMAS_IDREF)) {
            continue;
        }
        name = xmlSchemaValueGetAsString(item);
        if (vctxt->idBindings == NULL) {
            vctxt->idBindings = xmlHashCreate(0);
            if (vctxt->idBindings == NULL) {
                goto memory_error;
            }
        }
        binding = xmlHashLookup(vctxt->idBindings, name);
        if (binding == NULL) {
            binding = xmlMalloc(sizeof(*binding));
            if (binding == NULL) {
                goto memory_error;
            }
            binding->owner = 0;
            binding->multiple = 0;
            if (xmlHashAddEntry(vctxt->idBindings, name, binding) != 0) {
                xmlFree(binding);
                goto memory_error;
            }
        }
        if ((type == XML_SCHEMAS_ID) && (owner != 0)) {
            if (binding->owner == 0) {
                binding->owner = owner;
            } else if (binding->owner != owner) {
                binding->multiple = 1;
            }
        }
        /* Preserve DOM ID lookup only after the chosen value has passed its
         * facets. Existing DOM bindings outside this validation scope do not
         * participate in cvc-id assessment. SAX/reader values need no DOM. */
        if ((node != NULL) && (node->type == XML_ATTRIBUTE_NODE)) {
            xmlAttrPtr attr = (xmlAttrPtr) node;
            if (type == XML_SCHEMAS_ID) {
                if ((attr->atype != XML_ATTRIBUTE_ID) &&
                    (xmlAddIDSafe(attr, name) < 0)) {
                    goto memory_error;
                }
            } else {
                if (xmlAddRef(NULL, node->doc, name, attr) == NULL) {
                    goto memory_error;
                }
                /* The schema validator checks lists item by item; retain its
                 * existing DOM marker for each selected IDREF item. */
                attr->atype = XML_ATTRIBUTE_IDREF;
            }
        }
    }
    return(0);
memory_error:
    xmlSchemaVErrMemory(vctxt);
    return(-1);
}

static void
xmlSchemaCheckIdBinding(void *payload, void *data, const xmlChar *name)
{
    xmlSchemaIdBinding *binding = payload;
    xmlSchemaValidCtxtPtr vctxt = data;
    if (vctxt->err == XML_ERR_NO_MEMORY || vctxt->err < 0) {
        return;
    }
    if (binding->owner == 0) {
        xmlSchemaErr3(ACTXT_CAST vctxt, XML_SCHEMAV_CVC_IDC, NULL,
            "ID/IDREF value '%s' has no ID binding in the validation root "
            "(cvc-id.1)\n", name, NULL, NULL);
    } else if (binding->multiple) {
        xmlSchemaErr3(ACTXT_CAST vctxt, XML_SCHEMAV_CVC_IDC, NULL,
            "ID value '%s' identifies more than one element in the validation "
            "root (cvc-id.2)\n", name, NULL, NULL);
    }
}

static int
xmlSchemaVExpandQName(]==] _source "${_source}")
    string(REPLACE [==[		case XML_SCHEMAS_QNAME:
		    ret = xmlSchemaValidateQName]==] [==[                case XML_SCHEMAS_ID:
                case XML_SCHEMAS_IDREF:
                case XML_SCHEMAS_IDREFS:
                    ret = xmlSchemaValPredefTypeNodeNoNorm(biType, value,
                        valNeeded ? &val : NULL, NULL);
                    break;
		case XML_SCHEMAS_QNAME:
		    ret = xmlSchemaValidateQName]==] _source "${_source}")
    string(REPLACE [==[    if ((inode->flags & XML_SCHEMA_NODE_INFO_VALUE_NEEDED) ||
        (inode->decl != NULL && (inode->decl->flags & XML_SCHEMAS_ELEM_FIXED))) {]==] [==[    if ((inode->flags & XML_SCHEMA_NODE_INFO_VALUE_NEEDED) ||
        xmlSchemaTypeHasIdentity(type) ||
        (inode->decl != NULL && (inode->decl->flags & XML_SCHEMAS_ELEM_FIXED))) {]==] _source "${_source}")
    string(REPLACE [==[	    if ((xpathRes) || (defAttrOwnerElem)) {]==] [==[	    if ((xpathRes) || (defAttrOwnerElem) || xmlSchemaTypeHasIdentity(iattr->typeDef)) {]==] _source "${_source}")
    string(REPLACE [==[	if (xpathRes || fixed) {]==] [==[	if (xpathRes || fixed || xmlSchemaTypeHasIdentity(iattr->typeDef)) {]==] _source "${_source}")
    string(REPLACE [==[eval_idcs:
	/*]==] [==[eval_idcs:
        if (((iattr->state == XML_SCHEMAS_ATTR_ASSESSED) ||
             (iattr->state == XML_SCHEMAS_ATTR_DEFAULT)) &&
            (xmlSchemaRecordIdValues(vctxt, iattr->val,
                vctxt->elemInfos[vctxt->depth]->identityNumber, iattr->node) < 0)) {
            goto internal_error;
        }
	/*]==] _source "${_source}")
    string(REPLACE [==[end_elem:
    if (vctxt->depth < 0) {]==] [==[end_elem:
    if ((ret == 0) && (vctxt->depth >= 0) && (inode->val != NULL) &&
        (xmlSchemaRecordIdValues(vctxt, inode->val,
            vctxt->depth > 0 ? vctxt->elemInfos[vctxt->depth - 1]->identityNumber : 0,
            NULL) < 0)) {
        goto internal_error;
    }
    if (vctxt->depth == 0) {
        xmlHashScan(vctxt->idBindings, xmlSchemaCheckIdBinding, vctxt);
    }
    if (vctxt->depth < 0) {]==] _source "${_source}")
    string(REPLACE [==[    xmlHashFree(vctxt->entities, NULL);
    vctxt->entities = NULL;]==] [==[    xmlHashFree(vctxt->entities, NULL);
    vctxt->entities = NULL;
    xmlHashFree(vctxt->idBindings, xmlSchemaFreeIdBinding);
    vctxt->idBindings = NULL;
    vctxt->nextIdentityNumber = 0;]==] _source "${_source}")
    string(REPLACE [==[    /*
    * VAL TODO: 7 If the element information item is the `validation root`, it must be
    * `valid` per Validation Root Valid (ID/IDREF) ($3.3.4).
    */
]==] [==[]==] _source "${_source}")
    string(SHA256 _hash "${_source}")
    if(NOT _hash STREQUAL "600f8d93bc1c8baf799e7de148e07ac3cda456b472d14b485498e20d8fd77583")
        message(FATAL_ERROR "Pinned libxml2 document ID/IDREF bindings fix did not match")
    endif()
    file(MAKE_DIRECTORY "${binary_dir}/qore-id-binding-fix")
    set(_replacement "${binary_dir}/qore-id-binding-fix/xmlschemas.c")
    file(WRITE "${_replacement}.tmp" "${_source}")
    configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
    list(REMOVE_ITEM _sources "${_input}")
    list(APPEND _sources "${_replacement}")
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
    message(STATUS "XML module: applied libxml2 document ID/IDREF bindings in the build tree")
endfunction()
