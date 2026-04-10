/* -*- mode: c++; indent-tabs-mode: nil -*- */
/*
 QoreXmlDoc.h

 Qore Programming Language

 Copyright 2003 - 2010 David Nichols

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

#ifndef _QORE_QOREXMLDOC_H

#define _QORE_QOREXMLDOC_H

#if (defined _WIN32 || defined __WIN32__) && ! defined __CYGWIN__
#define LIBXML_STATIC 1
#endif

#include <libxml/parser.h>
#include <libxml/HTMLparser.h>

#define XML_PARSE_NOBLANKS 0

// There hardcoded node size limits since libxml2 2.7.3. The XML_PARSE_HUGE
// switches off those limits and restores unlimited size behavior like before.
#if LIBXML_VERSION >= 20703
#define QORE_XML_PARSER_OPTIONS_ADDONS | XML_PARSE_HUGE
#else
#define QORE_XML_PARSER_OPTIONS_ADDONS
#endif

#ifdef DEBUG
#define QORE_XML_PARSER_OPTIONS XML_PARSE_NOBLANKS QORE_XML_PARSER_OPTIONS_ADDONS
#else
#define QORE_XML_PARSER_OPTIONS XML_PARSE_NOERROR | XML_PARSE_NOWARNING | XML_PARSE_NOBLANKS QORE_XML_PARSER_OPTIONS_ADDONS
#endif

// HTML parser options for lenient real-world HTML parsing.
//
// HTML_PARSE_RECOVER: keep parsing on errors (essential for malformed HTML5)
// HTML_PARSE_NOERROR / NOWARNING: silence libxml2's stderr noise (the
// caller wants the DOM, not parser diagnostics)
// HTML_PARSE_NOBLANKS: drop ignorable whitespace text nodes
// HTML_PARSE_NONET: never fetch external entities (security — prevents
// SSRF via DTD/external resource loading during parsing)
#define QORE_HTML_PARSER_OPTIONS \
    (HTML_PARSE_RECOVER | HTML_PARSE_NOERROR | HTML_PARSE_NOWARNING \
     | HTML_PARSE_NOBLANKS | HTML_PARSE_NONET)

DLLLOCAL QoreStringNode *doString(xmlChar *str);
class QoreXmlNodeData;
class QoreXmlDocData;
DLLLOCAL QoreXmlNodeData *doNode(xmlNodePtr p, QoreXmlDocData *doc);

// Tag types for QoreXmlDoc constructor overloads.  Used so the HTML parsing
// path can be selected at the type level rather than via a runtime bool flag.
struct QoreXmlDocHtmlTag {};
constexpr QoreXmlDocHtmlTag QoreXmlDocHtml{};

class QoreXmlDoc {
private:
   DLLLOCAL void init(const char *buf, int size, const char *encoding = 0) {
      ptr = xmlReadMemory(buf, size, 0, encoding, QORE_XML_PARSER_OPTIONS);
   }

   // Lenient HTML parser path (libxml2 htmlReadMemory).  Tolerates
   // real-world malformed HTML5; suitable for crawler / scraper use cases
   // where the input may not be valid XHTML.
   DLLLOCAL void initHtml(const char *buf, int size, const char *encoding = 0) {
      ptr = htmlReadMemory(buf, size, 0, encoding, QORE_HTML_PARSER_OPTIONS);
   }

protected:
   xmlDocPtr ptr;

public:
   DLLLOCAL QoreXmlDoc(const char *buf, int size) {
      init(buf, size);
   }
   DLLLOCAL QoreXmlDoc(const QoreString &xml) {
      init(xml.getBuffer(), xml.strlen(), xml.getEncoding()->getCode());
   }
   DLLLOCAL QoreXmlDoc(const QoreString *xml) {
      init(xml->getBuffer(), xml->strlen(), xml->getEncoding()->getCode());
   }
   // HTML constructor — tag-dispatched to avoid colliding with the XML overloads
   DLLLOCAL QoreXmlDoc(const QoreString& html, QoreXmlDocHtmlTag,
           const char* encoding = 0) {
      initHtml(html.getBuffer(), html.strlen(),
               encoding ? encoding : html.getEncoding()->getCode());
   }
   DLLLOCAL QoreXmlDoc(const QoreXmlDoc &orig) {
      ptr = orig.ptr ? xmlCopyDoc(orig.ptr, 1) : 0;
   }
   DLLLOCAL ~QoreXmlDoc() {
      if (ptr) {
         xmlFreeDoc(ptr);
      }
   }
   DLLLOCAL bool isValid() const {
      return ptr;
   }
   DLLLOCAL const char *getVersion() const {
      return ptr ? (const char *)ptr->version : 0;
   }
   DLLLOCAL xmlDocPtr getDocPtr() const {
      return ptr;
   }
   DLLLOCAL QoreStringNode *toString(ExceptionSink *xsink) {
      xmlChar *x;
      int len;
      xmlDocDumpMemory(ptr, &x, &len);
      if (!x) {
         xsink->raiseException("XML-DOC-TOSTRING-ERROR", "an error occured converting the XmlDoc object to an XML string");
         return 0;
      }
      QoreStringNode *rv = new QoreStringNode((const char *)x, QCS_UTF8);
      xmlFree(x);
      return rv;
   }

   DLLLOCAL int validateRelaxNG(const char *rng, int size, ExceptionSink *xsink);
   DLLLOCAL int validateSchema(const QoreString& xsd, ExceptionSink *xsink);
   DLLLOCAL int validateDtd(const QoreString& dtd, ExceptionSink* xsink);
};

#endif
