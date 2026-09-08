/* -*- indent-tabs-mode: nil -*- */
/*
    QoreXmlReader.cpp

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

#include <qore/Qore.h>
#include "QoreXmlReader.h"
#include "QoreXmlRpcReader.h"

#include <memory>

static bool keys_are_equal(const char* name, const char* key) {
    size_t length = strlen(name);
    return !strncmp(name, key, length) && (!key[length] || key[length] == '^');
}

// Return an owning slot for the next child, retaining the public repeated-key convention.
static QoreValue* xml_element_slot(QoreHashNode* h, const char* name, bool preserve_order,
        std::unordered_map<std::string, size_t>& suffixes, ExceptionSink* xsink) {
    if (!h->existsKey(name)) {
        return &h->getKeyValueReference(name);
    }
    const char* key = name;
    if (preserve_order) {
        key = h->getLastKey();
        if (!keys_are_equal(name, key)) {
            // XML names cannot contain '^'; one counter per name assigns the
            // next unused suffix without rescanning all previous occurrences.
            QoreString unique;
            unique.sprintf("%s^%zu", name, ++suffixes[name]);
            assert(!h->existsKey(unique.c_str()));
            return &h->getKeyValueReference(unique.c_str());
        }
    }
    QoreValue& value = h->getKeyValueReference(key);
    QoreListNode* list = value.getType() == NT_LIST ? value.get<QoreListNode>() : nullptr;
    if (!list) {
        ReferenceHolder<QoreListNode> holder(new QoreListNode(autoTypeInfo), xsink);
        holder->push(value.refSelf(), xsink);
        if (*xsink) {
            return nullptr;
        }
        list = holder.release();
        discard(value.assign(list), xsink);
    }
    return &list->getEntryReference(list->size());
}

QoreValue* Qore::Xml::intern::xml_stack::getElementSlot(QoreHashNode* h, const char* name, ExceptionSink* xsink) {
    return xml_element_slot(h, name, tail->preserve_order, tail->suffixes, xsink);
}

int Qore::Xml::intern::xml_node::finish(ExceptionSink* xsink) {
    if (!elements || character_content || preserve_space || !vcount) {
        return 0;
    }
    assert(node.getType() == NT_HASH);
    QoreHashNode* h = node.get<QoreHashNode>();
    for (int i = 0; i < vcount; ++i) {
        if (!(i % 100) && qore_check_cancel(xsink, "XML whitespace parsing")) {
            return -1;
        }
        QoreString key;
        if (i) {
            key.sprintf("^value%d^", i);
        } else {
            key.concat("^value^");
        }
        h->takeKeyValue(key.c_str()).discard(nullptr);
    }
    if (!preserve_order) {
        return 0;
    }
    // Removing indentation can make equal child names adjacent. Reapply the same
    // grouping used during parsing, including intervening comments and attributes.
    ReferenceHolder<QoreHashNode> result(new QoreHashNode(autoTypeInfo), xsink);
    std::unordered_map<std::string, size_t> grouped_suffixes;
    ConstHashIterator entry(h);
    while (entry.next()) {
        if (qore_check_cancel(xsink, "XML whitespace parsing")) {
            return -1;
        }
        const char* key = entry.getKey();
        if (*key == '^') {
            result->setKeyValue(key, entry.get().refSelf(), xsink);
            if (*xsink) {
                return -1;
            }
            continue;
        }
        const char* suffix = strchr(key, '^');
        QoreString name(key, suffix ? suffix - key : strlen(key), QCS_UTF8);
        auto add = [&](QoreValue value) -> int {
            QoreValue* slot = xml_element_slot(*result, name.c_str(), true, grouped_suffixes, xsink);
            if (!slot) {
                return -1;
            }
            *slot = value.refSelf();
            return 0;
        };
        QoreValue value = entry.get();
        if (value.getType() == NT_LIST) {
            ConstListIterator items(value.get<QoreListNode>());
            while (items.next()) {
                if (qore_check_cancel(xsink, "XML whitespace parsing") || add(items.getValue())) {
                    return -1;
                }
            }
        } else if (add(value)) {
            return -1;
        }
    }
    discard(node.assign(result.release()), xsink);
    return 0;
}

void QoreXmlReader::processOpts(const QoreHashNode* opts, ExceptionSink* xsink) {
    assert(reader);
    if (!opts)
        return;

    ConstHashIterator i(opts);
    while (i.next()) {
        const char* key = i.getKey();
        if (!strcmp(key, "xsd")) {
            QoreValue n = i.get();
            if (n.getType() != NT_STRING) {
                xsink->raiseException("XMLREADER-XSD-ERROR", "expecting type 'string' with option 'xsd'; got type '%s' instead", n.getTypeName());
                return;
            }

            // set xml_input_io first
            XmlIoInputCallbackHelper xicbh(opts, xsink);
            if (*xsink)
                return;

#ifdef HAVE_XMLTEXTREADERSETSCHEMA
            QoreStringValueHelper xsd(n);
            std::unique_ptr<QoreXmlSchemaContext> schema(new QoreXmlSchemaContext(**xsd, xsink));
            if (*xsink)
                return;

            int rc = setSchema(schema->getSchema());
            if (rc < 0) {
                xsink->raiseException("XSD-VALIDATION-ERROR", "XML schema could not be validated");
                return;
            }

            val = schema.release();
            //printd(5, "QoreXmlReader::processOpts() set schema %p\n", val);
            continue;
#else
            xsink->raiseException("MISSING-FEATURE-ERROR", "the libxml2 version used to compile the xml module did not support the xmlTextReaderSetSchema() function, XSD validation is not available; for maximum portability, use the constant Option::HAVE_PARSEXMLWITHSCHEMA to check if this function is implemented before using XSD validation functionality");
            return;
#endif
        }

        // ignore options already processed
        if (!strcmp(key, "encoding") || !strcmp(key, "xml_parse_options") || !strcmp(key, "xml_input_io"))
            continue;

        xsink->raiseException("XML-READER-ERROR", "unsupported option '%s'", key);
        return;
    }
}

QoreHashNode* QoreXmlReader::parseXmlData(const QoreEncoding* data_ccsid, int pflags, ExceptionSink* xsink) {
    if (read(xsink) != 1)
        return 0;

    QoreValue rv = getXmlData(xsink, data_ccsid, pflags, depth());

    if (!rv) {
        if (!*xsink)
            xsink->raiseExceptionArg("PARSE-XML-EXCEPTION", xml ? new QoreStringNode(*xml) : 0, "parse error parsing XML string");
        return 0;
    }
    assert(rv.getType() == NT_HASH);

    return rv.get<QoreHashNode>();
}

QoreValue QoreXmlReader::getXmlData(ExceptionSink* xsink, const QoreEncoding* data_ccsid, int pflags, int min_depth) {
    Qore::Xml::intern::xml_stack xstack(pflags);
    // A reader may start inside an existing document, below the declaration.
    xstack.setPreserveSpace(xmlNodeGetSpacePreserve(xmlTextReaderCurrentNode(reader)) == 1);

    QORE_TRACE("getXMLData()");
    //printd(5, "QoreXmlReader::getXmlData() enc: %s flags: %d md: %d\n", data_ccsid->getCode(), pflags, min_depth);
    int rc = 1;

    while (rc == 1) {
        int nt = nodeType();
        // get node name
        const char* name = constName();
        if (!name)
            name = "--";
        else if (pflags & XPF_STRIP_NS_PREFIXES) {
            const char* p = strchr(name, ':');
            if (p)
                name = p + 1;
        }

        if (nt == -1) // ERROR
            break;

        if (nt == XML_READER_TYPE_ELEMENT) {
            int depth = QoreXmlReader::depth();
            if (xstack.checkDepth(depth, xsink)) {
                return QoreValue();
            }
            xstack.setElements();

            QoreValue n = xstack.getValue();
            // if there is no node pointer, then make a hash
            if (n.isNothing()) {
                QoreHashNode* h = new QoreHashNode(autoTypeInfo);
                xstack.setNode(h);
                xstack.push(h->getKeyValueReference(name), depth);
            }
            else { // node ptr already exists
                QoreHashNode* h = n.getType() == NT_HASH ? n.get<QoreHashNode>() : nullptr;
                if (!h) {
                    h = new QoreHashNode(autoTypeInfo);
                    xstack.setNode(h);
                    h->setKeyValue("^value^", n, xsink);
                    xstack.incValueCount();
                    xstack.push(h->getKeyValueReference(name), depth);
                }
                else {
                    QoreValue* slot = xstack.getElementSlot(h, name, xsink);
                    if (!slot) {
                        return QoreValue();
                    }
                    xstack.push(*slot, depth);
                }
            }
            // add attributes to structure if possible
            if (hasAttributes()) {
                ReferenceHolder<QoreHashNode> h(new QoreHashNode(autoTypeInfo), xsink);
                while (moveToNextAttribute(xsink) == 1) {
                    const char* aname = constName();
                    QoreStringNode* value = getValue(data_ccsid, xsink);
                    if (!value)
                        return QoreValue();
                    if (!strcmp(aname, "xml:space")) {
                        xstack.setPreserveSpace(!strcmp(constValue(), "preserve"));
                    }
                    h->setKeyValue(aname, value, xsink);
                }
                if (*xsink)
                    return QoreValue();

                // make new new a hash and assign "^attributes^" key
                QoreHashNode* nv = new QoreHashNode(autoTypeInfo);
                nv->setKeyValue("^attributes^", h.release(), xsink);
                xstack.setNode(nv);
            }
            //printd(5, "%s: type: %d, hasValue: %d, empty: %d, depth: %d\n", name, nt, xmlTextReaderHasValue(reader), xmlTextReaderIsEmptyElement(reader), depth);
        }
        else if (nt == XML_READER_TYPE_TEXT || ((nt == XML_READER_TYPE_SIGNIFICANT_WHITESPACE
                || nt == XML_READER_TYPE_WHITESPACE) && QoreXmlReader::depth() > 0)) {
            int depth = QoreXmlReader::depth();
            if (xstack.checkDepth(depth, xsink)) {
                return QoreValue();
            }
            if (nt == XML_READER_TYPE_TEXT) {
                xstack.setCharacterContent();
            }

            const char* str = constValue();
            if (str) {
                QoreStringNodeHolder val(getValue(data_ccsid, xsink));
                if (!val)
                    return QoreValue();

                QoreValue n = xstack.getValue();
                if (!n.isNothing()) {
                    QoreHashNode* h = n.getType() == NT_HASH ? n.get<QoreHashNode>() : nullptr;
                    if (h) {
                        if (!xstack.getValueCount())
                            h->setKeyValue("^value^", val.release(), xsink);
                        else {
                            QoreString kstr;
                            kstr.sprintf("^value%d^", xstack.getValueCount());
                            h->setKeyValue(kstr.getBuffer(), val.release(), xsink);
                        }
                    }
                    else { // convert value to hash and save value node
                        h = new QoreHashNode(autoTypeInfo);
                        xstack.setNode(h);
                        h->setKeyValue("^value^", n, xsink);
                        xstack.incValueCount();

                        QoreString kstr;
                        kstr.sprintf("^value%d^", 1);
                        h->setKeyValue(kstr.getBuffer(), val.release(), xsink);
                    }
                    xstack.incValueCount();
                }
                else
                xstack.setNode(val.release());
            }
        }
        else if (nt == XML_READER_TYPE_CDATA) {
            int depth = QoreXmlReader::depth();
            if (xstack.checkDepth(depth, xsink)) {
                return QoreValue();
            }
            xstack.setCharacterContent();

            const char* str = constValue();
            if (str) {
                QoreStringNode* val = getValue(data_ccsid, xsink);
                if (!val)
                    return QoreValue();

                QoreValue n = xstack.getValue();
                if (n.getType() == NT_HASH) {
                    QoreHashNode* h = n.get<QoreHashNode>();
                    if (!xstack.getCDataCount())
                        h->setKeyValue("^cdata^", val, xsink);
                    else {
                        QoreString kstr;
                        kstr.sprintf("^cdata%d^", xstack.getCDataCount());
                        h->setKeyValue(kstr.getBuffer(), val, xsink);
                    }
                }
                else { // convert value to hash and save value node
                    QoreHashNode* h = new QoreHashNode(autoTypeInfo);
                    xstack.setNode(h);
                    if (!n.isNothing()) {
                        h->setKeyValue("^value^", n, xsink);
                        xstack.incValueCount();
                    }

                    h->setKeyValue("^cdata^", val, xsink);
                }
                xstack.incCDataCount();
            }
        } else if (nt == XML_READER_TYPE_COMMENT && (pflags & XPF_ADD_COMMENTS)) {
            int depth = QoreXmlReader::depth();
            if (xstack.checkDepth(depth, xsink)) {
                return QoreValue();
            }

            const char* str = constValue();
            if (str) {
                QoreStringNode* val = getValue(data_ccsid, xsink);
                if (!val)
                    return QoreValue();

                QoreValue n = xstack.getValue();
                if (n.getType() == NT_HASH) {
                    QoreHashNode* h = n.get<QoreHashNode>();
                    if (!xstack.getCommentCount())
                        h->setKeyValue("^comment^", val, xsink);
                    else {
                        QoreString kstr;
                        kstr.sprintf("^comment%d^", xstack.getCommentCount());
                        h->setKeyValue(kstr.getBuffer(), val, xsink);
                    }
                }
                else { // convert value to hash and save value node
                    QoreHashNode* h = new QoreHashNode(autoTypeInfo);
                    xstack.setNode(h);
                    if (!n.isNothing()) {
                        h->setKeyValue("^value^", n, xsink);
                        xstack.incValueCount();
                    }

                    h->setKeyValue("^comment^", val, xsink);
                }
                xstack.incCommentCount();
            }
        }
        rc = read(xsink);

        if (min_depth > 0 && QoreXmlReader::depth() < min_depth) {
            rc = 0;
            break;
        }
    }
    return rc ? QoreValue() : xstack.takeValue(xsink);
}
