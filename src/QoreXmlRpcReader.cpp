/* -*- indent-tabs-mode: nil -*- */
/*
    QoreXmlRpcReader.cpp

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
#include "QoreXmlRpcReader.h"

#include "ql_xml.h"

#include <cerrno>
#include <climits>

static int xmlrpc_do_empty_value(Qore::Xml::intern::XmlRpcValue *v, const char *name, int depth, ExceptionSink *xsink) {
    if (!strcmp(name, "string")) {
        v->set(null_string());
    } else if (!strcmp(name, "i4") || !strcmp(name, "int") || !strcmp(name, "ex:i1") || !strcmp(name, "ex:i2") ||
               !strcmp(name, "ex:i8")) {
        v->set(0ll);
    } else if (!strcmp(name, "boolean")) {
        v->set(false);
    } else if (!strcmp(name, "struct")) {
        v->set(new QoreHashNode(autoTypeInfo));
    } else if (!strcmp(name, "array")) {
        v->set(new QoreListNode(autoTypeInfo));
    } else if (!strcmp(name, "double") || !strcmp(name, "ex:float")) {
        v->set(0.0f);
    } else if (!strcmp(name, "dateTime.iso8601") || !strcmp(name, "ex:dateTime")) {
        v->set(zero_date());
    } else if (!strcmp(name, "base64")) {
        v->set(new BinaryNode);
    } else if (!strcmp(name, "ex:nil")) {
        v->set(reinterpret_cast<AbstractQoreNode *>(0));
    } else {
        xsink->raiseException("PARSE-XMLRPC-ERROR", "unknown XML-RPC type '%s' at level %d", name, depth);
        return -1;
    }
    return 0;
}

int QoreXmlRpcReader::getStruct(Qore::Xml::intern::XmlRpcValue *v, const QoreEncoding *data_ccsid,
                                ExceptionSink *xsink) {
    int nt;

    QoreHashNode *h = new QoreHashNode(autoTypeInfo);
    v->set(h);

    while (true) {
        if ((nt = readXmlRpcNode(xsink)) == -1) {
            return -1;
        }

        if (nt == XML_READER_TYPE_END_ELEMENT) {
            break;
        }

        if (nt != XML_READER_TYPE_ELEMENT) {
            xsink->raiseException("PARSE-XMLRPC-ERROR",
                                  "error parsing XML string, expecting 'member' element (got type %d)", nt);
            return -1;
        }

        // check for 'member' element
        if (checkXmlRpcMemberName("member", xsink)) {
            return -1;
        }

        // get member name
        if (readXmlRpc(xsink)) {
            return -1;
        }

        if ((nt = nodeTypeSkipWhitespace()) != XML_READER_TYPE_ELEMENT) {
            xsink->raiseException("PARSE-XMLRPC-ERROR", "error parsing XML string, expecting struct 'name'");
            return -1;
        }

        // check for 'name' element
        if (checkXmlRpcMemberName("name", xsink)) {
            return -1;
        }

        ReferenceHolder<QoreStringNode> member(new QoreStringNode(QCS_UTF8), xsink);
        if (!isEmptyElement()) {
            if (read(xsink) != 1) {
                return -1;
            }
            member = readCharacterData(xsink);
            if (!member) {
                return -1;
            }
            if (nodeType() != XML_READER_TYPE_END_ELEMENT || checkXmlRpcMemberName("name", xsink, true)) {
                if (!*xsink) {
                    xsink->raiseException("PARSE-XMLRPC-ERROR", "struct names require character data only");
                }
                return -1;
            }
        }

        // get value
        if (readXmlRpc(xsink)) {
            return -1;
        }

        if ((nt = readXmlRpcNode(xsink)) == -1) {
            return -1;
        }
        if (nt != XML_READER_TYPE_ELEMENT) {
            xsink->raiseException("PARSE-XMLRPC-ERROR",
                                  "error parsing XML string, expecting struct 'value' for key '%s'", member->c_str());
            return -1;
        }

        v->setReference(&h->getKeyValueReference(member->c_str()));
        if (getValue(v, data_ccsid, xsink)) {
            return -1;
        }

        if ((nt = readXmlRpcNode(xsink)) == -1) {
            return -1;
        }
        if (nt != XML_READER_TYPE_END_ELEMENT) {
            // printd(5, "QoreXmlRpcReader::getStruct() error nt: %d\n", nt);
            xsink->raiseException("PARSE-XMLRPC-ERROR", "error parsing XML string, expecting member close element");
            return -1;
        }
        // printd(5, "QoreXmlRpcReader::getStruct() close /member: %s\n", (char*)constName());

        if (readXmlRpc(xsink)) {
            return -1;
        }
    }
    return 0;
}

int QoreXmlRpcReader::getParams(Qore::Xml::intern::XmlRpcValue *v, const QoreEncoding *data_ccsid,
                                ExceptionSink *xsink) {
    int nt;
    int index = 0;

    QoreListNode *l = new QoreListNode(autoTypeInfo);
    v->set(l);

    int array_depth = depth();

    while (true) {
        // expecting param open element
        if ((nt = readXmlRpcNode(xsink)) == -1) {
            return -1;
        }

        // printd(5, "getParams() nt: %d name: %s\n", nt, constName());

        // if higher-level "params" element closed, then return
        if (nt == XML_READER_TYPE_END_ELEMENT) {
            return 0;
        }

        if (nt != XML_READER_TYPE_ELEMENT) {
            xsink->raiseException("PARSE-XMLRPC-ERROR", "error parsing XML string, expecting 'param' open element");
            return -1;
        }

        if (checkXmlRpcMemberName("param", xsink)) {
            return -1;
        }

        v->setReference(&l->getEntryReference(index++));

        // get next value tag or param close tag
        if (readXmlRpc(xsink)) {
            return -1;
        }

        int value_depth = depth();
        // if param was not an empty node
        if (value_depth > array_depth) {
            if ((nt = readXmlRpcNode(xsink)) == -1) {
                return -1;
            }

            // if we got a "value" element
            if (nt == XML_READER_TYPE_ELEMENT) {
                if (getValue(v, data_ccsid, xsink)) {
                    return -1;
                }

                if ((nt = nodeTypeSkipWhitespace()) != XML_READER_TYPE_END_ELEMENT) {
                    xsink->raiseException("PARSE-XMLRPC-ERROR",
                                          "extra data in params, expecting param close tag (got node type %s instead)",
                                          get_xml_node_type_name(nt));
                    return -1;
                }

                if (checkXmlRpcMemberName("param", xsink, true)) {
                    return -1;
                }
            } else if (nt != XML_READER_TYPE_END_ELEMENT) {
                xsink->raiseException("PARSE-XMLRPC-ERROR", "extra data in params, expecting value element");
                return -1;
            }
            // just read a param close tag, position reader at next element
            if (readXmlRpc(xsink)) {
                return -1;
            }
        }
    }
    return 0;
}

QoreStringNode *QoreXmlRpcReader::readCharacterData(ExceptionSink *xsink) {
    ReferenceHolder<QoreStringNode> text(new QoreStringNode(QCS_UTF8), xsink);
    while (true) {
        int nt = nodeType();
        if (nt == XML_READER_TYPE_ELEMENT || nt == XML_READER_TYPE_END_ELEMENT) {
            return text.release();
        }
        if (nt == XML_READER_TYPE_TEXT || nt == XML_READER_TYPE_CDATA || nt == XML_READER_TYPE_WHITESPACE ||
            nt == XML_READER_TYPE_SIGNIFICANT_WHITESPACE) {
            const char *value = constValue();
            if (value) {
                text->concat(value);
            }
        } else if (nt != XML_READER_TYPE_COMMENT && nt != XML_READER_TYPE_PROCESSING_INSTRUCTION) {
            xsink->raiseException("PARSE-XMLRPC-ERROR", "unexpected XML-RPC character data node %d", nt);
            return nullptr;
        }
        // Every reader advance checks cancellation and retains parser errors.
        if (read(xsink) != 1) {
            if (!*xsink) {
                xsink->raiseException("PARSE-XMLRPC-ERROR", "unterminated XML-RPC character data");
            }
            return nullptr;
        }
    }
}

int QoreXmlRpcReader::getString(Qore::Xml::intern::XmlRpcValue *v, const QoreEncoding *data_ccsid,
                                ExceptionSink *xsink) {
    ReferenceHolder<QoreStringNode> text(readCharacterData(xsink), xsink);
    if (!text) {
        return -1;
    }
    if (nodeType() != XML_READER_TYPE_END_ELEMENT) {
        xsink->raiseException("PARSE-XMLRPC-ERROR", "XML-RPC strings require character data only");
        return -1;
    }
    QoreStringNode *converted = data_ccsid == QCS_UTF8 ? text.release() : text->convertEncoding(data_ccsid, xsink);
    if (!converted) {
        return -1;
    }
    v->set(converted);
    return 0;
}
int QoreXmlRpcReader::getBoolean(Qore::Xml::intern::XmlRpcValue *v, ExceptionSink* xsink) {
   int nt;

   if ((nt = readXmlRpcNode(xsink)) == -1)
      return -1;

   if (nt == XML_READER_TYPE_TEXT) {
      const char* str = constValue();
      if (str) {
         //printd(5, "** got boolean '%s'\n", str);
         char* endptr = nullptr;
         long long val = strtoll(str, &endptr, 10);
         // Skip trailing whitespace
         while (endptr && *endptr && isspace(*endptr)) {
            ++endptr;
         }
         // For boolean, we're lenient - just check if it parsed anything
         v->set(val ? true : false);
      }

      if (readXmlRpc(xsink))
         return -1;

      if ((nt = readXmlRpcNode(xsink)) == -1)
         return -1;
   }
   else
      v->set(false);

   if (nt != XML_READER_TYPE_END_ELEMENT) {
      xsink->raiseException("PARSE-XMLRPC-ERROR", "extra information in boolean (%d)", nt);
      return -1;
   }
   return 0;
}

int QoreXmlRpcReader::getInt(Qore::Xml::intern::XmlRpcValue *v, ExceptionSink* xsink) {
   int nt;

   if ((nt = readXmlRpcNode(xsink)) == -1)
      return -1;

   if (nt == XML_READER_TYPE_TEXT) {
      const char* str = constValue();
      if (str) {
         printd(5, "** getInt() str='%s' len=%d\n", str, (int)strlen(str));
         // note that we can parse 64-bit integers here, which is not conformant to the standard
         char* endptr = nullptr;
         errno = 0;
         long long val = strtoll(str, &endptr, 10);
         if (errno == ERANGE) {
            xsink->raiseException("PARSE-XMLRPC-ERROR", "integer value '%s' is out of range", str);
            return -1;
         }
         if (endptr == str || (endptr && *endptr != '\0')) {
            // Allow trailing whitespace
            while (endptr && *endptr && isspace(*endptr)) {
               ++endptr;
            }
            if (endptr && *endptr != '\0') {
               xsink->raiseException("PARSE-XMLRPC-ERROR", "invalid integer value '%s'", str);
               return -1;
            }
         }
         v->set(val);
      }

      if (readXmlRpc(xsink))
         return -1;

      if ((nt = readXmlRpcNode(xsink)) == -1)
         return -1;
   }
   else
      v->set(0ll);

   if (nt != XML_READER_TYPE_END_ELEMENT) {
      xsink->raiseException("PARSE-XMLRPC-ERROR", "extra information in int (%d)", nt);
      return -1;
   }
   return 0;
}

int QoreXmlRpcReader::getDouble(Qore::Xml::intern::XmlRpcValue *v, ExceptionSink* xsink) {
   int nt;

   if ((nt = readXmlRpcNode(xsink)) == -1)
      return -1;

   if (nt == XML_READER_TYPE_TEXT) {
      const char* str = constValue();
      if (str) {
         //printd(5, "** got float '%s'\n", str);
         v->set(q_strtod(str));
      }

      // advance to next position
      if (readXmlRpc(xsink))
         return -1;

      if ((nt = readXmlRpcNode(xsink)) == -1)
         return -1;
   }
   else
      v->set(0.0f);

   if (nt != XML_READER_TYPE_END_ELEMENT) {
      xsink->raiseException("PARSE-XMLRPC-ERROR", "extra information in float (%d)", nt);
      return -1;
   }
   return 0;
}

int QoreXmlRpcReader::getDate(Qore::Xml::intern::XmlRpcValue *v, ExceptionSink* xsink) {
   int nt;

   if ((nt = readXmlRpcNode(xsink)) == -1)
      return -1;

   if (nt == XML_READER_TYPE_TEXT) {
      const char* str = constValue();
      //printd(5, "QoreXmlRpcReader::getDate() str: %p (%s)\n", str, str ? str : "(null)");
      if (str)
         v->set(new DateTimeNode(str));

      // advance to next position
      if (readXmlRpc(xsink))
         return -1;

      if ((nt = readXmlRpcNode(xsink)) == -1)
         return -1;
   }
   else
      v->set(zero_date());

   if (nt != XML_READER_TYPE_END_ELEMENT) {
      xsink->raiseException("PARSE-XMLRPC-ERROR", "extra information in date (%d)", nt);
      return -1;
   }
   return 0;
}

int QoreXmlRpcReader::getBase64(Qore::Xml::intern::XmlRpcValue *v, ExceptionSink* xsink) {
   int nt;

   if ((nt = readXmlRpcNode(xsink)) == -1)
      return -1;

   if (nt == XML_READER_TYPE_TEXT) {
      const char* str = constValue();
      if (str) {
         //printd(5, "** got base64 '%s'\n", str);
         BinaryNode* b = parseBase64(str, strlen(str), xsink);
         if (!b)
            return -1;

         v->set(b);
      }

      // advance to next position
      if (readXmlRpc(xsink))
         return -1;

      if ((nt = readXmlRpcNode(xsink)) == -1)
         return -1;
   }
   else
      v->set(new BinaryNode);

   if (nt != XML_READER_TYPE_END_ELEMENT) {
      xsink->raiseException("PARSE-XMLRPC-ERROR", "extra information in base64 (%d)", nt);
      return -1;
   }
   return 0;
}

int QoreXmlRpcReader::getArray(Qore::Xml::intern::XmlRpcValue *v, const QoreEncoding *data_ccsid,
                               ExceptionSink *xsink) {
    QoreListNode *list = new QoreListNode(autoTypeInfo);
    v->set(list);
    if (nodeType() != XML_READER_TYPE_ELEMENT || checkXmlRpcMemberName("data", xsink)) {
        if (!*xsink) {
            xsink->raiseException("PARSE-XMLRPC-ERROR", "expecting array data element");
        }
        return -1;
    }
    bool empty = isEmptyElement();
    if (readXmlRpc(xsink)) {
        return -1;
    }
    if (!empty) {
        size_t index = 0;
        while (nodeType() != XML_READER_TYPE_END_ELEMENT) {
            // getValue() advances through cancellation-aware reader calls.
            v->setReference(&list->getEntryReference(index++));
            if (getValue(v, data_ccsid, xsink)) {
                return -1;
            }
        }
        if (checkXmlRpcMemberName("data", xsink, true) || readXmlRpc(xsink)) {
            return -1;
        }
    }
    if (nodeType() != XML_READER_TYPE_END_ELEMENT || checkXmlRpcMemberName("array", xsink, true)) {
        if (!*xsink) {
            xsink->raiseException("PARSE-XMLRPC-ERROR", "expecting array close element");
        }
        return -1;
    }
    return 0;
}

int QoreXmlRpcReader::getValue(Qore::Xml::intern::XmlRpcValue *v, const QoreEncoding *data_ccsid,
                               ExceptionSink *xsink) {
    if (nodeType() != XML_READER_TYPE_ELEMENT || checkXmlRpcMemberName("value", xsink)) {
        if (!*xsink) {
            xsink->raiseException("PARSE-XMLRPC-ERROR", "expecting value element");
        }
        return -1;
    }
    if (isEmptyElement()) {
        v->set(QoreValue());
        return readXmlRpc(xsink);
    }
    // Whitespace is data until a typed child proves that it is formatting.
    if (read(xsink) != 1) {
        return -1;
    }
    if (nodeType() == XML_READER_TYPE_END_ELEMENT) {
        v->set(QoreValue());
    } else if (getValueData(v, data_ccsid, true, xsink)) {
        return -1;
    }
    if (nodeType() != XML_READER_TYPE_END_ELEMENT || checkXmlRpcMemberName("value", xsink, true)) {
        if (!*xsink) {
            xsink->raiseException("PARSE-XMLRPC-ERROR", "expecting value close element");
        }
        return -1;
    }
    return readXmlRpc(xsink);
}

int QoreXmlRpcReader::getValueData(Qore::Xml::intern::XmlRpcValue *v, const QoreEncoding *data_ccsid, bool read_next,
                                   ExceptionSink *xsink) {
    int nt = nodeType();
    if (nt == -1) {
        xsink->raiseException("PARSE-XMLRPC-ERROR", "error parsing XML string");
        return -1;
    }

    // printd(5, "QoreXmlRpcReader::getValueData() DEBUG nt: %d read_next: %d\n", nt, read_next);

    if (nt != XML_READER_TYPE_ELEMENT && nt != XML_READER_TYPE_END_ELEMENT) {
        ReferenceHolder<QoreStringNode> text(readCharacterData(xsink), xsink);
        if (!text) {
            return -1;
        }
        if (nodeType() == XML_READER_TYPE_END_ELEMENT) {
            QoreStringNode *converted =
                data_ccsid == QCS_UTF8 ? text.release() : text->convertEncoding(data_ccsid, xsink);
            if (!converted) {
                return -1;
            }
            v->set(converted);
            // The collector is already on </value>; the containing parser consumes it.
            return 0;
        }
        for (size_t i = 0; i < text->size(); ++i) {
            if (!(i % 100) && qore_check_cancel(xsink, "XML-RPC value whitespace")) {
                return -1;
            }
            char c = text->c_str()[i];
            if (c != ' ' && c != '\t' && c != '\r' && c != '\n') {
                xsink->raiseException("PARSE-XMLRPC-ERROR", "character data before an XML-RPC typed value");
                return -1;
            }
        }
        nt = nodeType();
    }

    if (nt == XML_READER_TYPE_ELEMENT) {
        int depth = QoreXmlReader::depth();

        const char *current_name = constName();
        if (!current_name) {
            xsink->raiseException("PARSE-XMLRPC-ERROR", "expecting type name at level %d", depth);
            return -1;
        }
        QoreString type_name(current_name, QCS_UTF8);
        const char *name = type_name.c_str();
        if (isEmptyElement()) {
            int rc = xmlrpc_do_empty_value(v, name, depth, xsink);
            return !rc && read_next ? readXmlRpc(xsink) : rc;
        }
        int rc = !strcmp(name, "string") ? read(xsink) : readSkipWhitespace(xsink);
        if (rc != 1) {
            if (!*xsink) {
                xsink->raiseException("PARSE-XMLRPC-ERROR", "unterminated XML-RPC typed value");
            }
            return -1;
        }
        if (depth == QoreXmlReader::depth()) {
            if (nodeType() != XML_READER_TYPE_END_ELEMENT || checkXmlRpcMemberName(name, xsink, true)) {
                if (!*xsink) {
                    xsink->raiseException("PARSE-XMLRPC-ERROR", "expecting typed value close element");
                }
                return -1;
            }
            int rc = xmlrpc_do_empty_value(v, name, depth, xsink);
            return !rc && read_next ? readXmlRpc(xsink) : rc;
        }

        if (!strcmp(name, "string")) {
            if (getString(v, data_ccsid, xsink)) {
                return -1;
            }
        } else if (!strcmp(name, "i4") || !strcmp(name, "int") || !strcmp(name, "ex:i1") || !strcmp(name, "ex:i2") ||
                   !strcmp(name, "ex:i8")) {
            if (getInt(v, xsink)) {
                return -1;
            }
        } else if (!strcmp(name, "boolean")) {
            if (getBoolean(v, xsink)) {
                return -1;
            }
        } else if (!strcmp(name, "struct")) {
            if (getStruct(v, data_ccsid, xsink)) {
                return -1;
            }
        } else if (!strcmp(name, "array")) {
            if (getArray(v, data_ccsid, xsink)) {
                return -1;
            }
        } else if (!strcmp(name, "double") || !strcmp(name, "ex:float")) {
            if (getDouble(v, xsink)) {
                return -1;
            }
        } else if (!strcmp(name, "dateTime.iso8601") || !strcmp(name, "ex:dateTime")) {
            if (getDate(v, xsink)) {
                return -1;
            }
        } else if (!strcmp(name, "base64")) {
            if (getBase64(v, xsink)) {
                return -1;
            }
        } else {
            xsink->raiseException("PARSE-XMLRPC-ERROR", "unknown XML-RPC type '%s' at level %d", name, depth);
            return -1;
        }

        // printd(5, "getValueData() finished parsing type '%s' element depth: %d\n", name, depth);
        if (xsink->isEvent()) {
            return -1;
        }
    } else {
        xsink->raiseException("PARSE-XMLRPC-ERROR",
                              "unable to parse XML-RPC string; expecting element node, got type %d instead", nt);
        return -1;
    }

    return read_next ? readXmlRpc(xsink) : 0;
}
