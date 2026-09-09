/* -*- mode: c++; indent-tabs-mode: nil -*- */
/*
    QC_AbstractXmlIoInputCallback.h

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

#ifndef _QORE_QC_ABSTRACTXMLIOINPUTCALLBACK_H

#define _QORE_QC_ABSTRACTXMLIOINPUTCALLBACK_H

#include "qore-xml-module.h"
#include "ql_xml.h"

#include <qore/InputStream.h>
#include <qore/QoreSandboxManager.h>

DLLEXPORT extern qore_classid_t CID_ABSTRACTXMLIOINPUTCALLBACK;
DLLLOCAL QoreClass *initAbstractXmlIoInputCallbackClass(QoreNamespace& ns);

class AbstractXmlIoInputCallback : public AbstractPrivateData {
public:
    DLLLOCAL AbstractXmlIoInputCallback(QoreObject* self) : self(self) {
        // make a weak reference to the object
        self->tRef();
    }

    DLLLOCAL virtual ~AbstractXmlIoInputCallback() {
        self->tDeref();
    }

    // Each resource owns its stream; the callback itself has no mutable parser state.
    DLLLOCAL QoreObject* open(const char* filename, ExceptionSink* xsink) {
        ReferenceHolder<QoreListNode> args(new QoreListNode(autoTypeInfo), xsink);
        args->push(new QoreStringNode(filename), xsink);
        if (*xsink) {
            return nullptr;
        }
        ValueHolder result(self->evalMethod("open", *args, xsink), xsink);
        if (*xsink || !result) {
            return nullptr;
        }
        return result.release().get<QoreObject>();
    }

protected:
    QoreObject* self;

};

#endif
