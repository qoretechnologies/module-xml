/* -*- mode: c++; indent-tabs-mode: nil -*- */
/*
    QoreXmlRpcReader.h

    Qore Programming Language

    Copyright (C) 2003 - 2026 Qore Technologies, s.r.o.

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

#ifndef _QORE_QOREXMLRPCREADER_H
#define _QORE_QOREXMLRPCREADER_H

#include "QoreXmlReader.h"

#include <unordered_map>

namespace Qore {
namespace Xml {
namespace intern { // make classes local
    class XmlRpcValue {
    private:
        QoreValue val;
        QoreValue* vp = nullptr;
        bool is_set = false;

    public:
        DLLLOCAL XmlRpcValue() {
        }

        DLLLOCAL ~XmlRpcValue() {
            val.discard(0);
        }

        DLLLOCAL QoreValue getValue() {
            QoreValue rv;
            rv.swap(val);
            return rv;
        }

        DLLLOCAL void set(QoreValue v) {
            if (is_set) {
                *vp = v;
            } else {
                discard(val.assign(v), 0);
            }
        }

        DLLLOCAL void setReference(QoreValue* v) {
            vp = v;
            if (!is_set) {
                is_set = true;
            }
        }
    };

    class xml_node {
    public:
        QoreValue& node;
        xml_node* next = nullptr;
        int depth;
        int vcount = 0;
        int cdcount = 0;
        int commentcount = 0;
        bool elements = false;
        bool character_content = false;
        bool preserve_space = false;
        bool preserve_order = false;
        std::unordered_map<std::string, size_t> suffixes;

        DLLLOCAL xml_node(QoreValue& n, int d) : node(n), depth(d) {
        }

        // Keep scalar and mixed-content whitespace. Only discard formatting in
        // element-only content, after all children have been read.
        DLLLOCAL int finish(ExceptionSink* xsink);

    };

    class xml_stack {
    private:
        xml_node* tail = nullptr;
        QoreValue val;

    public:
        DLLLOCAL xml_stack(int pflags) {
            push(val, -1);
            tail->preserve_order = pflags & XPF_PRESERVE_ORDER;
        }

        DLLLOCAL ~xml_stack() {
            val.discard(nullptr);

            while (tail) {
                //printd(5, "xml_stack::~xml_stack(): deleting: %p (%d), next: %p\n", tail, tail->depth, tail->next);
                xml_node* n = tail->next;
                delete tail;
                tail = n;
            }
        }

        DLLLOCAL int checkDepth(int depth, ExceptionSink* xsink) {
            size_t count = 0;
            while (tail && depth && tail->depth >= depth) {
                if (!(count++ % 100) && qore_check_cancel(xsink, "XML parsing")) {
                    return -1;
                }
                if (tail->finish(xsink)) {
                    return -1;
                }
                //printd(5, "xml_stack::checkDepth(%d): deleting: %p (%d), new tail: %p\n", depth, tail, tail->depth, tail->next);
                xml_node* n = tail->next;
                delete tail;
                tail = n;
            }
            return 0;
        }

        DLLLOCAL void push(QoreValue& node, int depth) {
            xml_node* sn = new xml_node(node, depth);
            sn->next = tail;
            sn->preserve_space = tail && tail->preserve_space;
            sn->preserve_order = tail && tail->preserve_order;
            tail = sn;
        }
        DLLLOCAL QoreValue* getElementSlot(QoreHashNode* h, const char* name, ExceptionSink* xsink);
        DLLLOCAL QoreValue getValue() {
            return tail->node;
        }
        DLLLOCAL void setNode(QoreValue n) {
            tail->node = n;
        }
        DLLLOCAL QoreValue takeValue(ExceptionSink* xsink) {
            size_t count = 0;
            for (xml_node* current = tail; current; current = current->next) {
                if (!(count++ % 100) && qore_check_cancel(xsink, "XML parsing")) {
                    return QoreValue();
                }
                if (current->finish(xsink)) {
                    return QoreValue();
                }
            }
            QoreValue rv = val;
            val = QoreValue();
            return rv;
        }
        DLLLOCAL void setElements() {
            tail->elements = true;
        }
        DLLLOCAL void setCharacterContent() {
            tail->character_content = true;
        }
        DLLLOCAL void setPreserveSpace(bool preserve) {
            tail->preserve_space = preserve;
        }
        DLLLOCAL int getValueCount() const {
            return tail->vcount;
        }
        DLLLOCAL void incValueCount() {
            tail->vcount++;
        }
        DLLLOCAL int getCDataCount() const {
            return tail->cdcount;
        }
        DLLLOCAL void incCDataCount() {
            tail->cdcount++;
        }
        DLLLOCAL int getCommentCount() const {
            return tail->commentcount;
        }
        DLLLOCAL void incCommentCount() {
            tail->commentcount++;
        }
    };
}
}
}

class QoreXmlRpcReader : public QoreXmlReader {
public:
    DLLLOCAL QoreXmlRpcReader(const QoreString* n_xml, int options, ExceptionSink* xsink) : QoreXmlReader(n_xml, options, xsink) {
    }

    DLLLOCAL int readXmlRpc(ExceptionSink* xsink) {
        return readSkipWhitespace(xsink) != 1;
    }

    DLLLOCAL int readXmlRpc(const char* info, ExceptionSink* xsink) {
        return readSkipWhitespace(info, xsink) != 1;
    }

    DLLLOCAL int readXmlRpcNode(ExceptionSink* xsink) {
        int nt = nodeTypeSkipWhitespace();
        if (nt == -1 && !*xsink)
            xsink->raiseException("PARSE-XMLRPC-ERROR", "error parsing XML string");
        return nt;
    }

    DLLLOCAL int checkXmlRpcMemberName(const char* member, ExceptionSink* xsink, bool close = false) {
        const char* name = (const char*)xmlTextReaderConstName(reader);
        if (!name) {
            xsink->raiseExceptionArg("PARSE-XMLRPC-ERROR", xml ? new QoreStringNode(*xml) : 0, "expecting %selement '%s', got NOTHING", close ? "closing " : "", member);
            return -1;
        }

        if (strcmp(name, member)) {
            xsink->raiseExceptionArg("PARSE-XMLRPC-ERROR", xml ? new QoreStringNode(*xml) : 0, "expecting %selement '%s', got '%s'", close ? "closing " : "", member, name);
            return -1;
        }
        return 0;
    }

    DLLLOCAL int getArray(Qore::Xml::intern::XmlRpcValue *v, const QoreEncoding* data_ccsid, ExceptionSink* xsink);
    DLLLOCAL int getStruct(Qore::Xml::intern::XmlRpcValue *v, const QoreEncoding* data_ccsid, ExceptionSink* xsink);
    DLLLOCAL int getString(Qore::Xml::intern::XmlRpcValue *v, const QoreEncoding* data_ccsid, ExceptionSink* xsink);
    DLLLOCAL int getBoolean(Qore::Xml::intern::XmlRpcValue *v, ExceptionSink* xsink);
    DLLLOCAL int getInt(Qore::Xml::intern::XmlRpcValue *v, ExceptionSink* xsink);
    DLLLOCAL int getDouble(Qore::Xml::intern::XmlRpcValue *v, ExceptionSink* xsink);
    DLLLOCAL int getDate(Qore::Xml::intern::XmlRpcValue *v, ExceptionSink* xsink);
    DLLLOCAL int getBase64(Qore::Xml::intern::XmlRpcValue *v, ExceptionSink* xsink);
    DLLLOCAL int getValueData(Qore::Xml::intern::XmlRpcValue *v, const QoreEncoding* data_ccsid, bool read_next, ExceptionSink* xsink);
    DLLLOCAL int getParams(Qore::Xml::intern::XmlRpcValue *v, const QoreEncoding* data_ccsid, ExceptionSink* xsink);
};

#endif
