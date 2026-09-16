# Copyright (C) 2026 Qore Technologies, s.r.o.
# Fix URI identity, XSD anyURI mapping and XML Base at their native boundaries.
# xmlschemas.c already contains the checksum-verified QName fixes.
# Compile checked build-tree copies; keep the original source/archive immutable.
function(qore_xml_fix_libxml2_uris source_dir binary_dir)
    get_target_property(_sources LibXml2 SOURCES)
    foreach(_filename IN ITEMS uri.c tree.c xmlschemas.c)
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
            message(FATAL_ERROR "Cannot locate libxml2 ${_filename} for URI fixes")
        endif()
        if(IS_ABSOLUTE "${_input}")
            set(_path "${_input}")
        else()
            set(_path "${source_dir}/${_input}")
        endif()
        file(SHA256 "${_path}" _hash)
        file(READ "${_path}" _source)
        if(_filename STREQUAL "uri.c")
            set(_original_hash 16cc4794868487cb3dac76faffef603163f8d8472508735df7b5a4cf0a4c4e44)
            set(_fixed_hash 206c64120b0da3b64daf1f1aa8fc93f36d92bc0ad2c9f35e06bb7044ade4b07d)
            string(REPLACE [==[#include <string.h>

#include <libxml/xmlmemory.h>
#include <libxml/uri.h>
#include <libxml/xmlerror.h>

#include "private/error.h"
#include "private/memory.h"
]==]
                [==[#include <string.h>

#include <libxml/xmlmemory.h>
#include <libxml/uri.h>

XML_HIDDEN int
xmlBuildLEIRISafe(const xmlChar *URI, const xmlChar *base, xmlChar **valPtr);
#include <libxml/xmlerror.h>

#include "private/error.h"
#include "private/memory.h"
]==] _source "${_source}")
            string(REPLACE [==[#define XML_URI_ALLOW_UCSCHAR   4

static int
xmlIsUnreserved(xmlURIPtr uri, const char *cur) {
    if (uri == NULL)
        return(0);

    if (ISA_STRICTLY_UNRESERVED(cur))
        return(1);

]==]
                [==[#define XML_URI_ALLOW_UCSCHAR   4

static int
xmlIsUnreserved(xmlURIPtr uri, const char *cur) {
    if ((uri == NULL) || (*cur == 0)) {
        return(0);
    }

    if (ISA_STRICTLY_UNRESERVED(cur))
        return(1);

]==] _source "${_source}")
            string(REPLACE [==[    }
    return(0);
}

/**
 * Parse an URI based on RFC 3986
 *
 * URI-reference = [ absoluteURI | relativeURI ] [ "\#" fragment ]
]==]
                [==[    }
    return(0);
}

static int
xmlParseURIWithFlags(const char *str, xmlURI **uriOut, int flags) {
    xmlURIPtr uri;
    int ret;

    if (uriOut == NULL) {
        return(1);
    }
    *uriOut = NULL;
    if (str == NULL) {
        return(1);
    }

    uri = xmlCreateURI();
    if (uri == NULL) {
        return(-1);
    }

    uri->cleanup = flags;
    ret = xmlParse3986URIReference(uri, str);
    if (ret) {
        xmlFreeURI(uri);
        return(ret);
    }

    *uriOut = uri;
    return(0);
}

/**
 * Parse an URI based on RFC 3986
 *
 * URI-reference = [ absoluteURI | relativeURI ] [ "\#" fragment ]
]==] _source "${_source}")
            string(REPLACE [==[ * or -1 if a memory allocation failed.
 */
int
xmlParseURISafe(const char *str, xmlURI **uriOut) {
    xmlURIPtr uri;
    int ret;

    if (uriOut == NULL)
        return(1);
    *uriOut = NULL;
    if (str == NULL)
	return(1);

    uri = xmlCreateURI();
    if (uri == NULL)
        return(-1);

    ret = xmlParse3986URIReference(uri, str);
    if (ret) {
        xmlFreeURI(uri);
        return(ret);
    }

    *uriOut = uri;
    return(0);
}

/**
 * Parse an URI based on RFC 3986
]==]
                [==[ * or -1 if a memory allocation failed.
 */
int
xmlParseURISafe(const char *str, xmlURI **uriOut) {
    return(xmlParseURIWithFlags(str, uriOut, 0));
}

/**
 * Parse an URI based on RFC 3986
]==] _source "${_source}")
            string(REPLACE [==[                temp = xmlSaveUriRealloc(ret, &max);
                if (temp == NULL) goto mem_error;
                ret = temp;
	    }
	    if (IS_RESERVED(*(p)) || IS_UNRESERVED(*(p)))
		ret[len++] = *p++;
	    else {
		int val = *(unsigned char *)p++;
		int hi = val / 0x10, lo = val % 0x10;
		ret[len++] = '%';
		ret[len++] = hi + (hi > 9? 'A'-10 : '0');
]==]
                [==[                temp = xmlSaveUriRealloc(ret, &max);
                if (temp == NULL) goto mem_error;
                ret = temp;
	    }
	    if ((uri->cleanup & XML_URI_NO_UNESCAPE) || IS_RESERVED(*(p)) || IS_UNRESERVED(*(p))) {
		ret[len++] = *p++;
	    } else {
		int val = *(unsigned char *)p++;
		int hi = val / 0x10, lo = val % 0x10;
		ret[len++] = '%';
		ret[len++] = hi + (hi > 9? 'A'-10 : '0');
]==] _source "${_source}")
            string(REPLACE [==[                        temp = xmlSaveUriRealloc(ret, &max);
                        if (temp == NULL) goto mem_error;
                        ret = temp;
		    }
		    if ((IS_UNRESERVED(*(p))) ||
			((*(p) == ';')) || ((*(p) == ':')) ||
			((*(p) == '&')) || ((*(p) == '=')) ||
			((*(p) == '+')) || ((*(p) == '$')) ||
			((*(p) == ',')))
			ret[len++] = *p++;
		    else {
			int val = *(unsigned char *)p++;
			int hi = val / 0x10, lo = val % 0x10;
			ret[len++] = '%';
			ret[len++] = hi + (hi > 9? 'A'-10 : '0');
]==]
                [==[                        temp = xmlSaveUriRealloc(ret, &max);
                        if (temp == NULL) goto mem_error;
                        ret = temp;
		    }
		    if ((uri->cleanup & XML_URI_NO_UNESCAPE) || (IS_UNRESERVED(*(p))) ||
			((*(p) == ';')) || ((*(p) == ':')) ||
			((*(p) == '&')) || ((*(p) == '=')) ||
			((*(p) == '+')) || ((*(p) == '$')) ||
			((*(p) == ','))) {
			ret[len++] = *p++;
		    } else {
			int val = *(unsigned char *)p++;
			int hi = val / 0x10, lo = val % 0x10;
			ret[len++] = '%';
			ret[len++] = hi + (hi > 9? 'A'-10 : '0');
]==] _source "${_source}")
            string(REPLACE [==[                    temp = xmlSaveUriRealloc(ret, &max);
                    if (temp == NULL) goto mem_error;
                    ret = temp;
		}
		if ((IS_UNRESERVED(*(p))) ||
                    ((*(p) == '$')) || ((*(p) == ',')) || ((*(p) == ';')) ||
                    ((*(p) == ':')) || ((*(p) == '@')) || ((*(p) == '&')) ||
                    ((*(p) == '=')) || ((*(p) == '+')))
		    ret[len++] = *p++;
		else {
		    int val = *(unsigned char *)p++;
		    int hi = val / 0x10, lo = val % 0x10;
		    ret[len++] = '%';
		    ret[len++] = hi + (hi > 9? 'A'-10 : '0');
]==]
                [==[                    temp = xmlSaveUriRealloc(ret, &max);
                    if (temp == NULL) goto mem_error;
                    ret = temp;
		}
		if ((uri->cleanup & XML_URI_NO_UNESCAPE) || (IS_UNRESERVED(*(p))) ||
                    ((*(p) == '$')) || ((*(p) == ',')) || ((*(p) == ';')) ||
                    ((*(p) == ':')) || ((*(p) == '@')) || ((*(p) == '&')) ||
                    ((*(p) == '=')) || ((*(p) == '+'))) {
		    ret[len++] = *p++;
		} else {
		    int val = *(unsigned char *)p++;
		    int hi = val / 0x10, lo = val % 0x10;
		    ret[len++] = '%';
		    ret[len++] = hi + (hi > 9? 'A'-10 : '0');
]==] _source "${_source}")
            string(REPLACE [==[                    temp = xmlSaveUriRealloc(ret, &max);
                    if (temp == NULL) goto mem_error;
                    ret = temp;
		}
		if ((IS_UNRESERVED(*(p))) || ((*(p) == '/')) ||
                    ((*(p) == ';')) || ((*(p) == '@')) || ((*(p) == '&')) ||
	            ((*(p) == '=')) || ((*(p) == '+')) || ((*(p) == '$')) ||
	            ((*(p) == ',')))
		    ret[len++] = *p++;
		else {
		    int val = *(unsigned char *)p++;
		    int hi = val / 0x10, lo = val % 0x10;
		    ret[len++] = '%';
		    ret[len++] = hi + (hi > 9? 'A'-10 : '0');
]==]
                [==[                    temp = xmlSaveUriRealloc(ret, &max);
                    if (temp == NULL) goto mem_error;
                    ret = temp;
		}
		if ((uri->cleanup & XML_URI_NO_UNESCAPE) || (IS_UNRESERVED(*(p))) || ((*(p) == '/')) ||
                    ((*(p) == ';')) || ((*(p) == '@')) || ((*(p) == '&')) ||
	            ((*(p) == '=')) || ((*(p) == '+')) || ((*(p) == '$')) ||
	            ((*(p) == ','))) {
		    ret[len++] = *p++;
		} else {
		    int val = *(unsigned char *)p++;
		    int hi = val / 0x10, lo = val % 0x10;
		    ret[len++] = '%';
		    ret[len++] = hi + (hi > 9? 'A'-10 : '0');
]==] _source "${_source}")
            string(REPLACE [==[                    temp = xmlSaveUriRealloc(ret, &max);
                    if (temp == NULL) goto mem_error;
                    ret = temp;
		}
		if ((IS_UNRESERVED(*(p))) || (IS_RESERVED(*(p))))
		    ret[len++] = *p++;
		else {
		    int val = *(unsigned char *)p++;
		    int hi = val / 0x10, lo = val % 0x10;
		    ret[len++] = '%';
		    ret[len++] = hi + (hi > 9? 'A'-10 : '0');
]==]
                [==[                    temp = xmlSaveUriRealloc(ret, &max);
                    if (temp == NULL) goto mem_error;
                    ret = temp;
		}
		if ((uri->cleanup & XML_URI_NO_UNESCAPE) || (IS_UNRESERVED(*(p))) || (IS_RESERVED(*(p)))) {
		    ret[len++] = *p++;
		} else {
		    int val = *(unsigned char *)p++;
		    int hi = val / 0x10, lo = val % 0x10;
		    ret[len++] = '%';
		    ret[len++] = hi + (hi > 9? 'A'-10 : '0');
]==] _source "${_source}")
            string(REPLACE [==[                temp = xmlSaveUriRealloc(ret, &max);
                if (temp == NULL) goto mem_error;
                ret = temp;
	    }
	    if ((IS_UNRESERVED(*(p))) || (IS_RESERVED(*(p))))
		ret[len++] = *p++;
	    else {
		int val = *(unsigned char *)p++;
		int hi = val / 0x10, lo = val % 0x10;
		ret[len++] = '%';
		ret[len++] = hi + (hi > 9? 'A'-10 : '0');
]==]
                [==[                temp = xmlSaveUriRealloc(ret, &max);
                if (temp == NULL) goto mem_error;
                ret = temp;
	    }
	    if ((uri->cleanup & XML_URI_NO_UNESCAPE) || (IS_UNRESERVED(*(p))) || (IS_RESERVED(*(p)))) {
		ret[len++] = *p++;
	    } else {
		int val = *(unsigned char *)p++;
		int hi = val / 0x10, lo = val % 0x10;
		ret[len++] = '%';
		ret[len++] = hi + (hi > 9? 'A'-10 : '0');
]==] _source "${_source}")
            string(REPLACE [==[                    if (cur[2] == 0)
                        break;
                    cur += 3;
                    continue;
                } else if (out[0] == '/') {
                    /* Ignore extraneous ".." in absolute paths */
                    if (cur[2] == 0)
                        break;
                    cur += 3;
]==]
                [==[                    if (cur[2] == 0)
                        break;
                    cur += 3;
                    continue;
                } else if (path[0] == '/') {
                    /* Ignore extraneous ".." in absolute paths */
                    if (cur[2] == 0)
                        break;
                    cur += 3;
]==] _source "${_source}")
            string(REPLACE [==[    xmlFree(ref);
    return(ret);
}

/**
 * Computes he final URI of the reference done by checking that
 * the given URI is valid, and building the final URI using the
 * base URI. This is processed according to section 5.2 of the
 * RFC 2396
 *
 * 5.2. Resolving Relative References to Absolute Form
 *
 * @since 2.13.0
 *
 * @param URI  the URI instance found in the document
 * @param base  the base value
 * @param valPtr  pointer to result URI
 * @returns 0 on success, -1 if a memory allocation failed or an error
 * code if URI or base are invalid.
 */
int
xmlBuildURISafe(const xmlChar *URI, const xmlChar *base, xmlChar **valPtr) {
    xmlChar *val = NULL;
    int ret, len, indx, cur, out;
    xmlURIPtr ref = NULL;
    xmlURIPtr bas = NULL;
]==]
                [==[    xmlFree(ref);
    return(ret);
}

/* RFC 3986 section 5.2.4. Work in place, preserving empty path segments and
 * percent escapes. Each byte is copied or removed at most once. */
static void
xmlRemoveURIDotSegments(char *path) {
    char *read = path, *write = path;

    if (path == NULL) {
        return;
    }
    while (*read != 0) {
        if (strncmp(read, "../", 3) == 0) {
            read += 3;
        } else if (strncmp(read, "./", 2) == 0) {
            read += 2;
        } else if (strncmp(read, "/./", 3) == 0) {
            read += 2;
        } else if (strcmp(read, "/.") == 0) {
            *write++ = '/';
            break;
        } else if ((strncmp(read, "/../", 4) == 0) || (strcmp(read, "/..") == 0)) {
            read += 3;
            while ((write > path) && (write[-1] != '/')) {
                --write;
            }
            if (write > path) {
                --write;
            }
            if (*read == 0) {
                *write++ = '/';
                break;
            }
        } else if ((strcmp(read, ".") == 0) || (strcmp(read, "..") == 0)) {
            break;
        } else {
            if (*read == '/') {
                *write++ = *read++;
            }
            while ((*read != 0) && (*read != '/')) {
                *write++ = *read++;
            }
        }
    }
    *write = 0;
}

static int
xmlBuildURIInternal(const xmlChar *URI, const xmlChar *base, xmlChar **valPtr, int flags) {
    xmlChar *val = NULL;
    int ret, len, indx, cur, out;
    xmlURIPtr ref = NULL;
    xmlURIPtr bas = NULL;
]==] _source "${_source}")
            string(REPLACE [==[     *    NOTE that a completely empty URI is treated by modern browsers
     *    as a reference to "." rather than as a synonym for the current
     *    URI.  Should we do that here?
     */
    if (URI[0] != 0)
        ret = xmlParseURISafe((const char *) URI, &ref);
    else
        ret = 0;
    if (ret != 0)
	goto done;
    if ((ref != NULL) && (ref->scheme != NULL)) {
	/*
	 * The URI is absolute don't modify.
	 */
	val = xmlStrdup(URI);
        if (val == NULL)
            ret = -1;
	goto done;
    }
]==]
                [==[     *    NOTE that a completely empty URI is treated by modern browsers
     *    as a reference to "." rather than as a synonym for the current
     *    URI.  Should we do that here?
     */
    if (URI[0] != 0) {
        ret = xmlParseURIWithFlags((const char *) URI, &ref, flags);
    } else {
        ret = 0;
    }
    if (ret != 0)
	goto done;
    if ((ref != NULL) && (ref->scheme != NULL)) {
	/*
	 * The URI is absolute don't modify.
	 */
	xmlRemoveURIDotSegments(ref->path);
	val = xmlSaveUri(ref);
        if (val == NULL)
            ret = -1;
	goto done;
    }
]==] _source "${_source}")
            string(REPLACE [==[        }
    }
#endif

    ret = xmlParseURISafe((const char *) base, &bas);
    if (ret < 0)
        goto done;
    if (ret != 0) {
	if (ref) {
]==]
                [==[        }
    }
#endif

    ret = xmlParseURIWithFlags((const char *) base, &bas, flags);
    if (ret < 0)
        goto done;
    if (ret != 0) {
	if (ref) {
]==] _source "${_source}")
            string(REPLACE [==[    ret = -1;
    res = xmlCreateURI();
    if (res == NULL)
	goto done;
    if ((ref->scheme == NULL) && (ref->path == NULL) &&
	((ref->authority == NULL) && (ref->server == NULL) &&
         (ref->port == PORT_EMPTY))) {
	if (bas->scheme != NULL) {
]==]
                [==[    ret = -1;
    res = xmlCreateURI();
    if (res == NULL)
	goto done;
    res->cleanup = flags;
    if ((ref->scheme == NULL) && (ref->path == NULL) &&
	((ref->authority == NULL) && (ref->server == NULL) &&
         (ref->port == PORT_EMPTY))) {
	if (bas->scheme != NULL) {
]==] _source "${_source}")
            string(REPLACE [==[
    /*
     * Steps c) to h) are really path normalization steps
     */
    xmlNormalizeURIPath(res->path);

step_7:

    /*
     * 7) The resulting URI components, including any inherited from the
     *    base URI, are recombined to give the absolute form of the URI
]==]
                [==[
    /*
     * Steps c) to h) are really path normalization steps
     */
step_7:
    xmlRemoveURIDotSegments(res->path);

    /*
     * 7) The resulting URI components, including any inherited from the
     *    base URI, are recombined to give the absolute form of the URI
]==] _source "${_source}")
            string(REPLACE [==[    if (res != NULL)
	xmlFreeURI(res);
    *valPtr = val;
    return(ret);
}

/**
 * Computes he final URI of the reference done by checking that
]==]
                [==[    if (res != NULL)
	xmlFreeURI(res);
    *valPtr = val;
    return(ret);
}

/**
 * Computes he final URI of the reference done by checking that
 * the given URI is valid, and building the final URI using the
 * base URI. This is processed according to section 5.2 of the
 * RFC 2396
 *
 * 5.2. Resolving Relative References to Absolute Form
 *
 * @since 2.13.0
 *
 * @param URI  the URI instance found in the document
 * @param base  the base value
 * @param valPtr  pointer to result URI
 * @returns 0 on success, -1 if a memory allocation failed or an error
 * code if URI or base are invalid.
 */
int
xmlBuildURISafe(const xmlChar *URI, const xmlChar *base, xmlChar **valPtr) {
    return(xmlBuildURIInternal(URI, base, valPtr, XML_URI_NO_UNESCAPE));
}

/* XML Base accessors return unescaped LEIRIs. Use the existing extended URI
 * parser without decoding existing percent escapes or rewriting source text. */
XML_HIDDEN int
xmlBuildLEIRISafe(const xmlChar *URI, const xmlChar *base, xmlChar **valPtr) {
    return(xmlBuildURIInternal(URI, base, valPtr,
                              XML_URI_NO_UNESCAPE | XML_URI_ALLOW_UCSCHAR));
}

/**
 * Computes he final URI of the reference done by checking that
]==] _source "${_source}")
        elseif(_filename STREQUAL "tree.c")
            set(_original_hash 2045cf4d1a93bd5d2e9b2781ed92a748e146e30c2919f59fb3ea1845f5795dea)
            set(_fixed_hash 342056b51113f7ea6ef022e36a224cd49eaf0a7e16b2e8c74645632773813a87)
            string(REPLACE [==[#include "private/io.h"
#include "private/parser.h"
#include "private/tree.h"

#ifndef SIZE_MAX
  #define SIZE_MAX ((size_t) -1)
]==]
                [==[#include "private/io.h"
#include "private/parser.h"
#include "private/tree.h"

XML_HIDDEN int
xmlBuildLEIRISafe(const xmlChar *URI, const xmlChar *base, xmlChar **valPtr);

#ifndef SIZE_MAX
  #define SIZE_MAX ((size_t) -1)
]==] _source "${_source}")
            string(REPLACE [==[            }
	    if (base != NULL) {
		if (ret != NULL) {
		    res = xmlBuildURISafe(ret, base, &newbase);
                    xmlFree(ret);
                    xmlFree(base);
                    if (res != 0)
]==]
                [==[            }
	    if (base != NULL) {
		if (ret != NULL) {
		    res = xmlBuildLEIRISafe(ret, base, &newbase);
                    xmlFree(ret);
                    xmlFree(base);
                    if (res != 0)
]==] _source "${_source}")
            string(REPLACE [==[            if (ret == NULL)
                return(-1);
        } else {
            res = xmlBuildURISafe(ret, doc->URL, &newbase);
            xmlFree(ret);
            if (res != 0)
                return(res);
]==]
                [==[            if (ret == NULL)
                return(-1);
        } else {
            res = xmlBuildLEIRISafe(ret, doc->URL, &newbase);
            xmlFree(ret);
            if (res != 0)
                return(res);
]==] _source "${_source}")
        elseif(_filename STREQUAL "xmlschemas.c")
            set(_original_hash 99eeb19c5c78c3407af28efc22752ae8c5e581ef74a5c09807ab3fcf37277650)
            set(_fixed_hash 62def2d85880e32e6a69b810302f301190c4a9a5581437447d10dff7fc626e31)
            string(REPLACE [==[}


static const xmlChar *
xmlSchemaBuildAbsoluteURI(xmlDictPtr dict, const xmlChar* location,
			  xmlNodePtr ctxtNode,
]==]
                [==[}


/* XSD anyURI references use the XLink escaping procedure before resolution.
 * Preserve existing percent escapes and URI delimiters, and leave source text intact. */
static xmlChar *
xmlSchemaResolveAnyURI(const xmlChar *location, const xmlChar *base)
{
    const xmlChar *reserved = BAD_CAST ":/?#[]@!$&()*+,;='%";
    xmlChar *escapedLocation, *escapedBase = NULL, *result;
    xmlChar *normalized, *write;
    const xmlChar *read;
    int space = 0;

    normalized = xmlStrdup(location);
    if (normalized == NULL) {
        return(NULL);
    }
    write = normalized;
    for (read = normalized; *read != 0; ++read) {
        if (IS_BLANK_CH(*read)) {
            space = write != normalized;
        } else {
            if (space) {
                *write++ = ' ';
                space = 0;
            }
            *write++ = *read;
        }
    }
    *write = 0;
    escapedLocation = xmlURIEscapeStr(normalized, reserved);
    xmlFree(normalized);
    if (escapedLocation == NULL) {
        return(NULL);
    }
    if (base != NULL) {
        escapedBase = xmlStrstr(base, BAD_CAST "://")
            ? xmlURIEscapeStr(base, reserved) : xmlStrdup(base);
        if (escapedBase == NULL) {
            xmlFree(escapedLocation);
            return(NULL);
        }
    }
    result = xmlBuildURI(escapedLocation, escapedBase);
    xmlFree(escapedLocation);
    xmlFree(escapedBase);
    return(result);
}

static const xmlChar *
xmlSchemaBuildAbsoluteURI(xmlDictPtr dict, const xmlChar* location,
			  xmlNodePtr ctxtNode,
]==] _source "${_source}")
            string(REPLACE [==[
	    base = xmlNodeGetBase(ctxtNode->doc, ctxtNode);
	    if (base == NULL) {
		URI = xmlBuildURI(location, ctxtNode->doc->URL);
	    } else {
		URI = xmlBuildURI(location, base);
		xmlFree(base);
	    }
	} else if (baseURI != NULL) {
	    URI = xmlBuildURI(location, baseURI);
	} else {
	    return(location);
	}
	if (URI != NULL) {
	    ret = xmlDictLookup(dict, URI, -1);
]==]
                [==[
	    base = xmlNodeGetBase(ctxtNode->doc, ctxtNode);
	    if (base == NULL) {
		URI = xmlSchemaResolveAnyURI(location, ctxtNode->doc->URL);
	    } else {
		URI = xmlSchemaResolveAnyURI(location, base);
		xmlFree(base);
	    }
	} else if (baseURI != NULL) {
	    URI = xmlSchemaResolveAnyURI(location, baseURI);
	} else {
	    URI = xmlSchemaResolveAnyURI(location, NULL);
	}
	if (URI != NULL) {
	    ret = xmlDictLookup(dict, URI, -1);
]==] _source "${_source}")
            string(REPLACE [==[	    goto exit_error;
	base = xmlNodeGetBase(node->doc, node);
	if (base == NULL) {
	    uri = xmlBuildURI(*schemaLocation, node->doc->URL);
	} else {
	    uri = xmlBuildURI(*schemaLocation, base);
	    xmlFree(base);
	}
	if (uri == NULL) {
]==]
                [==[	    goto exit_error;
	base = xmlNodeGetBase(node->doc, node);
	if (base == NULL) {
	    uri = xmlSchemaResolveAnyURI(*schemaLocation, node->doc->URL);
	} else {
	    uri = xmlSchemaResolveAnyURI(*schemaLocation, base);
	    xmlFree(base);
	}
	if (uri == NULL) {
]==] _source "${_source}")
            string(REPLACE [==[        (vctxt->parserCtxt != NULL) &&
        (vctxt->parserCtxt->input != NULL))
        baseURI = BAD_CAST vctxt->parserCtxt->input->filename;
    location = xmlSchemaBuildAbsoluteURI(pctxt->dict,
        location, node, baseURI);
    /*
]==]
                [==[        (vctxt->parserCtxt != NULL) &&
        (vctxt->parserCtxt->input != NULL))
        baseURI = BAD_CAST vctxt->parserCtxt->input->filename;
    /* SAX plugs such as XmlReader provide their source URI through a
     * locator instead of vctxt->parserCtxt. */
    if ((node == NULL) && (baseURI == NULL) && (vctxt->locFunc != NULL)) {
        const char *filename = NULL;
        unsigned long line = 0;
        if (vctxt->locFunc(vctxt->locCtxt, &filename, &line) == 0) {
            baseURI = BAD_CAST filename;
        }
    }
    location = xmlSchemaBuildAbsoluteURI(pctxt->dict,
        location, node, baseURI);
    /*
]==] _source "${_source}")
            string(REPLACE [==[    int ret = 0;
    xmlSchemaAttrInfoPtr iattr;

    /*
    * Parse the value; we will assume an even number of values
    * to be given (this is how Xerces and XSV work).
    *
    * URGENT TODO: !! This needs to work for both
    * @noNamespaceSchemaLocation AND @schemaLocation on the same
    * element !!
    */
    iattr = xmlSchemaGetMetaAttrInfo(vctxt,
	XML_SCHEMA_ATTR_INFO_META_XSI_SCHEMA_LOC);
    if (iattr == NULL)
	iattr = xmlSchemaGetMetaAttrInfo(vctxt,
	XML_SCHEMA_ATTR_INFO_META_XSI_NO_NS_SCHEMA_LOC);
    if (iattr == NULL)
	return (0);
    cur = iattr->value;
    do {
	/*
]==]
                [==[    int ret = 0;
    xmlSchemaAttrInfoPtr iattr;

    /* noNamespaceSchemaLocation is one anyURI, not a whitespace list.
     * Process it independently so both XSI location attributes can contribute. */
    iattr = xmlSchemaGetMetaAttrInfo(vctxt,
        XML_SCHEMA_ATTR_INFO_META_XSI_NO_NS_SCHEMA_LOC);
    if (iattr != NULL) {
        ret = xmlSchemaAssembleByLocation(vctxt, vctxt->schema,
            iattr->node, NULL, iattr->value);
        if (ret != 0) {
            return(ret);
        }
    }
    iattr = xmlSchemaGetMetaAttrInfo(vctxt,
        XML_SCHEMA_ATTR_INFO_META_XSI_SCHEMA_LOC);
    if (iattr == NULL) {
        return(ret);
    }
    cur = iattr->value;
    do {
	/*
]==] _source "${_source}")
        endif()
        if(_hash STREQUAL _fixed_hash)
            continue()
        endif()
        if(NOT _hash STREQUAL _original_hash)
            message(FATAL_ERROR "Unexpected libxml2 ${_filename}; cannot apply URI fixes")
        endif()
        string(SHA256 _result_hash "${_source}")
        if(NOT _result_hash STREQUAL _fixed_hash)
            message(FATAL_ERROR "Pinned libxml2 URI fixes did not match ${_filename}")
        endif()
        file(MAKE_DIRECTORY "${binary_dir}/qore-uri-fix")
        set(_replacement "${binary_dir}/qore-uri-fix/${_filename}")
        file(WRITE "${_replacement}.tmp" "${_source}")
        configure_file("${_replacement}.tmp" "${_replacement}" COPYONLY)
        list(FIND _sources "${_input}" _index)
        list(REMOVE_AT _sources ${_index})
        list(APPEND _sources "${_replacement}")
        message(STATUS "XML module: applied libxml2 URI fixes to ${_filename} in the build tree")
    endforeach()
    set_property(TARGET LibXml2 PROPERTY SOURCES "${_sources}")
endfunction()
