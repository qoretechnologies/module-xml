/*
  Qore xml module

  Copyright (C) 2010 - 2026 Qore Technologies, s.r.o.

  This library is free software; you can redistribute it and/or
  modify it under the terms of the GNU Lesser General Public
  License as published by the Free Software Foundation; either
  version 2.1 of the License, or (at your option) any later version.

  This library is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
  Lesser General Public License for more details.

  You should have received a copy of the GNU Lesser General Public
  License along with this library; if not, write to the Free Software
  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
*/

#include "qore-xml-module.h"

#include "QC_XmlRpcClient.h"
#include "QC_XmlNode.h"
#include "QC_XmlDoc.h"
#include "QC_XmlNode.h"
#include "QC_XmlReader.h"
#include "QC_SaxIterator.h"
#include "QC_AbstractXmlIoInputCallback.h"

#include "ql_xml.h"

#include <libxml/xmlversion.h>
#include <libxml/uri.h>
#include <libxml/parserInternals.h>
#include <openssl/ssl.h>
#include <qore/QoreHttpClientObject.h>
#ifdef LIBXML_FTP_ENABLED
#include <qore/QoreFtpClient.h>
#endif
#include <memory>
#include <algorithm>

#include <stdarg.h>

static void xml_module_init(QoreModuleInitContext& ctx, ExceptionSink& xsink);
static void xml_module_ns_init(QoreNamespace* rns, QoreNamespace* qns, ExceptionSink& xsink);
static void xml_module_delete();

DLLLOCAL void init_option_constants(QoreNamespace& ns);

// module declaration for Qore 0.9.5+
extern "C" DLLEXPORT void xml_qore_module_desc(QoreModuleInfo& mod_info) {
    mod_info.name = "xml";
    mod_info.version = PACKAGE_VERSION;
    mod_info.desc = "xml module";
    mod_info.author = "David Nichols";
    mod_info.url = "http://qore.org";
    mod_info.api_major = QORE_MODULE_API_MAJOR;
    mod_info.api_minor = QORE_MODULE_API_MINOR;
    mod_info.init = xml_module_init;
    mod_info.ns_init = xml_module_ns_init;
    mod_info.del = xml_module_delete;
    mod_info.license = QL_MIT;
    mod_info.license_str = "MIT";
}

thread_local AbstractXmlIoInputCallback* xml_io_callback = nullptr;

QoreNamespace XNS("Qore::Xml");

static void qoreXmlGenericErrorFunc(QoreString *err, const char *msg, ...) {
   va_list args;
   va_start(args, msg);
   err->clear();
   err->vsprintf(msg, args);
   va_end(args);
}

// ignore errors after initialization
static void qoreXmlIgnoreErrorFunc(QoreString *err, const char *msg, ...) {
}

#ifdef HAVE_XMLTEXTREADERSETSCHEMA
thread_local ExceptionSink* qore_xml_schema_resource_xsink = nullptr;

// A non-null failed resource prevents libxml2 from falling through to an unchecked
// default loader. Each successful callback resource owns its stream independently.
class QoreXmlSchemaResource {
public:
    explicit QoreXmlSchemaResource(ExceptionSink* xsink) : xsink(xsink), stream(nullptr, xsink), body(xsink) {
    }

    // True means this resource handles the URI (including a reported failure).
    // False delegates an authorized file to libxml2, preserving compressed-file support.
    bool open(const char* location) {
        resolved_location = location;
        if (*xsink || qore_check_cancel(xsink, "XML schema resource loading")) {
            return true;
        }
        if (xml_io_callback) {
            stream = xml_io_callback->open(location, xsink);
            if (*xsink || stream) {
                return true;
            }
        }
        bool http = !xmlStrncasecmp(BAD_CAST location, BAD_CAST "http://", 7)
            || !xmlStrncasecmp(BAD_CAST location, BAD_CAST "https://", 8);
#ifdef LIBXML_FTP_ENABLED
        bool ftp = !xmlStrncasecmp(BAD_CAST location, BAD_CAST "ftp://", 6);
#else
        bool ftp = false;
#endif
        if (http || ftp) {
            if (getProgram() && (getProgram()->getParseOptions() & PO_NO_NETWORK)) {
                xsink->raiseException("ILLEGAL-NETWORK-ACCESS", "loading an XSD resource is not allowed "
                    "when PO_NO_NETWORK is set");
                return true;
            }
            if (http) {
                QoreHttpClientObject client;
                client.setSslVerifyMode(SSL_VERIFY_PEER);
                client.setEncodingPassthru(true);
                if (client.setURL(location, xsink)) {
                    return true;
                }
                ReferenceHolder<QoreHashNode> info(new QoreHashNode(autoTypeInfo), xsink);
                body = client.get(nullptr, nullptr, *info, xsink);
                if (*xsink) {
                    return true;
                }
                // Redirects establish the document base URI used by relative imports.
                for (int index = 1; ; ++index) {
                    QoreString key;
                    key.sprintf("redirect-%d", index);
                    QoreValue value = info->getKeyValue(key.c_str());
                    if (value.isNothing()) {
                        break;
                    }
                    const QoreStringNode* redirect = value.get<const QoreStringNode>();
                    xmlChar* resolved = xmlBuildURI(BAD_CAST redirect->c_str(), BAD_CAST resolved_location.c_str());
                    if (!resolved) {
                        xsink->raiseException("XSD-SYNTAX-ERROR", "could not resolve a schema redirect URI");
                        return true;
                    }
                    ON_BLOCK_EXIT(xmlFree, resolved);
                    resolved_location = reinterpret_cast<const char*>(resolved);
                }
            }
#ifdef LIBXML_FTP_ENABLED
            else {
                QoreString url(location, QCS_UTF8);
                xmlURIPtr uri = xmlParseURI(location);
                if (!uri) {
                    xsink->raiseException("XSD-SYNTAX-ERROR", "invalid FTP schema URI");
                    return true;
                }
                ON_BLOCK_EXIT(xmlFreeURI, uri);
                QoreFtpClient client(&url, xsink);
                if (!*xsink && !client.connect(xsink)) {
                    body = client.getAsBinary(uri->path ? uri->path : "/", xsink);
                }
            }
#endif
            return true;
        }
        if (getProgram() && (getProgram()->getParseOptions() & PO_NO_FILESYSTEM)) {
            xsink->raiseException("ILLEGAL-FILESYSTEM-ACCESS", "loading an XSD resource is not allowed "
                "when PO_NO_FILESYSTEM is set");
            return true;
        }
        // Match libxml2's file URI conversion before checking the actual filesystem path.
        const char* escaped = nullptr;
        if (!xmlStrncasecmp(BAD_CAST location, BAD_CAST "file://localhost/", 17)) {
            escaped = location + 16;
        } else if (!xmlStrncasecmp(BAD_CAST location, BAD_CAST "file:///", 8)) {
            escaped = location + 7;
        } else if (!xmlStrncasecmp(BAD_CAST location, BAD_CAST "file:/", 6)) {
            escaped = location + 5;
        }
#ifdef _WIN32
        if (escaped) {
            ++escaped;
        }
#endif
        char* path = escaped ? xmlURIUnescapeString(escaped, 0, nullptr) : nullptr;
        ON_BLOCK_EXIT(xmlFree, path);
        if (escaped && !path) {
            xsink->raiseException("XSD-SYNTAX-ERROR", "could not decode an XSD resource file URI");
            return true;
        }
        QoreSandboxManagerHelper manager(QoreSandboxManagerHelper::Policy);
        return manager && !manager->checkFilesystemAccess(path ? path : location, QSEC_READ, xsink);
    }

    const char* getLocation() const {
        return resolved_location.c_str();
    }

    static bool isNetworkLocation(const char* location) {
        if (!location) {
            return false;
        }
        return !xmlStrncasecmp(BAD_CAST location, BAD_CAST "http://", 7)
            || !xmlStrncasecmp(BAD_CAST location, BAD_CAST "https://", 8)
#ifdef LIBXML_FTP_ENABLED
            || !xmlStrncasecmp(BAD_CAST location, BAD_CAST "ftp://", 6)
#endif
            ;
    }

    int read(char* buffer, int length) {
        if (*xsink || qore_check_cancel(xsink, "XML schema resource reading")) {
            return -1;
        }
        if (length <= 0) {
            return 0;
        }
        if (stream) {
            ReferenceHolder<QoreListNode> args(new QoreListNode(autoTypeInfo), xsink);
            args->push(length, xsink);
            if (*xsink) {
                return -1;
            }
            ValueHolder chunk(stream->evalMethod("read", *args, xsink), xsink);
            if (*xsink || qore_check_cancel(xsink, "XML schema resource reading")) {
                return -1;
            }
            if (!chunk) {
                return 0;
            }
            const BinaryNode* binary = chunk->get<const BinaryNode>();
            if (binary->size() > static_cast<size_t>(length)) {
                xsink->raiseException("XML-INPUT-STREAM-ERROR", "schema input stream returned more bytes than requested");
                return -1;
            }
            memcpy(buffer, binary->getPtr(), binary->size());
            return static_cast<int>(binary->size());
        }
        const char* data = nullptr;
        size_t size = 0;
        if (body->getType() == NT_BINARY) {
            const BinaryNode* binary = body->get<const BinaryNode>();
            data = static_cast<const char*>(binary->getPtr());
            size = binary->size();
        } else if (body->getType() == NT_STRING) {
            const QoreStringNode* string = body->get<const QoreStringNode>();
            data = string->c_str();
            size = string->size();
        }
        size_t count = std::min(static_cast<size_t>(length), size - offset);
        if (count) {
            memcpy(buffer, data + offset, count);
            offset += count;
        }
        return static_cast<int>(count);
    }

private:
    ExceptionSink* xsink;
    ReferenceHolder<QoreObject> stream;
    ValueHolder body;
    size_t offset = 0;
    std::string resolved_location;
};
#endif

static int qoreXmlInputMatchCallback(const char* filename) {
#ifdef HAVE_XMLTEXTREADERSETSCHEMA
    return filename && qore_xml_schema_resource_xsink ? 1 : 0;
#else
    return 0;
#endif
}

static void* qoreXmlInputOpenCallback(const char* filename) {
#ifdef HAVE_XMLTEXTREADERSETSCHEMA
    std::unique_ptr<QoreXmlSchemaResource> resource(new QoreXmlSchemaResource(qore_xml_schema_resource_xsink));
    return resource->open(filename) ? resource.release() : nullptr;
#else
    return nullptr;
#endif
}

static int qoreXmlInputReadCallback(void* context, char* buffer, int len) {
#ifdef HAVE_XMLTEXTREADERSETSCHEMA
    return static_cast<QoreXmlSchemaResource*>(context)->read(buffer, len);
#else
    return -1;
#endif
}

static int qoreXmlInputCloseCallback(void* context) {
#ifdef HAVE_XMLTEXTREADERSETSCHEMA
    delete static_cast<QoreXmlSchemaResource*>(context);
#endif
    return 0;
}


#ifdef HAVE_XMLTEXTREADERSETSCHEMA
#if LIBXML_VERSION >= 21400
xmlParserErrors qoreXmlSchemaResourceLoader(void* context, const char* url, const char* public_id,
        xmlResourceType type, xmlParserInputFlags flags, xmlParserInput** output) {
    if (!QoreXmlSchemaResource::isNetworkLocation(url)) {
        return xmlNewInputFromUrl(url, flags, output);
    }
    auto* xsink = static_cast<ExceptionSink*>(context);
    std::unique_ptr<QoreXmlSchemaResource> resource(new QoreXmlSchemaResource(xsink));
    [[maybe_unused]] const bool handled = resource->open(url);
    assert(handled);
    if (*xsink) {
        *output = nullptr;
        return XML_IO_LOAD_ERROR;
    }
    // xmlNewInputFromIO takes ownership, including on allocation failure.
    std::string location(resource->getLocation());
    *output = xmlNewInputFromIO(location.c_str(), qoreXmlInputReadCallback,
        qoreXmlInputCloseCallback, resource.release(), flags);
    return *output ? XML_ERR_OK : XML_ERR_NO_MEMORY;
}
#else
static xmlExternalEntityLoader qore_xml_previous_loader = nullptr;

static xmlParserInput* qoreXmlSchemaEntityLoader(const char* url, const char* public_id, xmlParserCtxt* parser) {
    if (!qore_xml_schema_resource_xsink || !QoreXmlSchemaResource::isNetworkLocation(url)) {
        return qore_xml_previous_loader(url, public_id, parser);
    }
    auto* xsink = qore_xml_schema_resource_xsink;
    std::unique_ptr<QoreXmlSchemaResource> resource(new QoreXmlSchemaResource(xsink));
    [[maybe_unused]] const bool handled = resource->open(url);
    assert(handled);
    if (*xsink) {
        return nullptr;
    }
    std::string location(resource->getLocation());
    xmlParserInputBuffer* buffer = xmlParserInputBufferCreateIO(qoreXmlInputReadCallback,
        qoreXmlInputCloseCallback, resource.get(), XML_CHAR_ENCODING_NONE);
    if (!buffer) {
        xsink->raiseException("XSD-SYNTAX-ERROR", "could not allocate a schema input buffer");
        return nullptr;
    }
    resource.release();
    xmlParserInput* input = xmlNewIOInputStream(parser, buffer, XML_CHAR_ENCODING_NONE);
    if (!input) {
        // Before 2.14, ownership transfers only after input allocation succeeds.
        xmlFreeParserInputBuffer(buffer);
        xsink->raiseException("XSD-SYNTAX-ERROR", "could not allocate a schema parser input");
        return nullptr;
    }
    input->filename = reinterpret_cast<const char*>(xmlStrdup(BAD_CAST location.c_str()));
    if (!input->filename) {
        xmlFreeInputStream(input);
        xsink->raiseException("XSD-SYNTAX-ERROR", "could not allocate a schema document URI");
        return nullptr;
    }
    return input;
}
#endif
#endif

static void xml_module_init(QoreModuleInitContext& ctx, ExceptionSink& xsink) {
    QoreString err;

    // set our generic error handler to catch initialization errors
    xmlSetGenericErrorFunc((void*)&err, (xmlGenericErrorFunc)qoreXmlGenericErrorFunc);

    // initialize libxml2 library
    LIBXML_TEST_VERSION

    if (err.strlen()) {
        xsink.raiseException("MODULE-INIT-ERROR", new QoreStringNode(err));
        return;
    }

    {
        // register input callbacks
        int rc = xmlRegisterInputCallbacks(qoreXmlInputMatchCallback,
            (xmlInputOpenCallback)qoreXmlInputOpenCallback,
            (xmlInputReadCallback)qoreXmlInputReadCallback,
            (xmlInputCloseCallback)qoreXmlInputCloseCallback);
        if (rc == -1) {
            xsink.raiseException("MODULE-INIT-ERROR", new QoreStringNodeMaker("error registering input callback; xmlRegisterInputCallbacks() returned %d; cannot initialize the libxml2 module", rc));
            return;
        }
    }

#if defined(HAVE_XMLTEXTREADERSETSCHEMA) && LIBXML_VERSION < 21400
    // Older libxml2 lacks per-schema resource loaders. Delegate all loads outside
    // the thread-local schema scope to the previously registered entity loader.
    qore_xml_previous_loader = xmlGetExternalEntityLoader();
    xmlSetExternalEntityLoader(qoreXmlSchemaEntityLoader);
#endif

    // ignore errors after initialization
    xmlSetGenericErrorFunc((void*)&err, (xmlGenericErrorFunc)qoreXmlIgnoreErrorFunc);

    XNS.addSystemClass(initXmlNodeClass(XNS));
    XNS.addSystemClass(initXmlDocClass(XNS));
    XNS.addSystemClass(initXmlReaderClass(XNS));
    XNS.addSystemClass(initSaxIteratorClass(XNS));
    XNS.addSystemClass(initFileSaxIteratorClass(XNS));
    XNS.addSystemClass(initInputStreamSaxIteratorClass(XNS));
    XNS.addSystemClass(initAbstractXmlIoInputCallbackClass(XNS));

    XNS.addSystemClass(initXmlRpcClientClass(XNS));

    init_xml_constants(XNS);

    // set up Option namespace for XML options
    QoreNamespace *option = new QoreNamespace("Option");

    init_option_constants(*option);

    XNS.addInitialNamespace(option);

    init_xml_functions(XNS);
}

static void xml_module_ns_init(QoreNamespace* rns, QoreNamespace* qns, ExceptionSink& xsink) {
   qns->addNamespace(XNS.copy());
}

void xml_module_delete() {
   // cleanup libxml2 library
   xmlCleanupParser();
}
