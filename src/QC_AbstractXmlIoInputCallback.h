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
        // input_stream should be nullptr on destruction; log if not
        if (input_stream) {
            printd(0, "AbstractXmlIoInputCallback::~AbstractXmlIoInputCallback() WARNING: input_stream not closed\n");
        }
        // remove the weak reference
        self->tDeref();
    }

    // libxml2 I/O callback: can we provide the requested resource; 1 = true, 0 = false
    DLLLOCAL int match(const char* filename) {
        // validate preconditions with proper error handling
        if (!filename || !filename[0]) {
            printd(0, "AbstractXmlIoInputCallback::match() ERROR: null or empty filename\n");
            return 0;
        }
        if (input_stream) {
            printd(0, "AbstractXmlIoInputCallback::match() ERROR: input_stream already set\n");
            return 0;
        }
        if (!xsink) {
            printd(0, "AbstractXmlIoInputCallback::match() ERROR: no exception context\n");
            return 0;
        }

        // Check filesystem security before allowing access to external resources
        QoreSandboxManager* sm = runtime_get_sandbox_manager();
        if (sm && !sm->checkFilesystemAccess(filename, QSEC_READ, xsink)) {
            // Filesystem access denied - return 0 to indicate we can't provide this resource
            // Exception is already raised in xsink
            return 0;
        }

        // unhandled exceptions will appear on stdout
        ReferenceHolder<QoreListNode> args(new QoreListNode(autoTypeInfo), xsink);
        args->push(new QoreStringNode(filename), xsink);
        if (*xsink) {
            return 0;
        }
        ValueHolder bufHolder(self->evalMethod("open", *args, xsink), xsink);
        //printd(5, "AbstractXmlIoInputCallback::match() '%s': %d\n", filename, (int)(bool)bufHolder);
        if (!bufHolder)
            return 0;
        input_stream = bufHolder.release().get<QoreObject>();
        return 1;
    }

    // libxml2 I/O callback: open the requested resource; returns nullptr on error
    DLLLOCAL void* open(const char* filename) {
        if (!input_stream) {
            printd(0, "AbstractXmlIoInputCallback::open() ERROR: input_stream not set\n");
            return nullptr;
        }
        return input_stream;
    }

    // libxml2 I/O callback: read the requested resource; returns the number of bytes read or -1 in case of error
    DLLLOCAL int read(void* context, char* buffer, int len) {
        // validate preconditions with proper error handling
        if (!input_stream) {
            printd(0, "AbstractXmlIoInputCallback::read() ERROR: input_stream not set\n");
            return -1;
        }
        if (context != input_stream) {
            printd(0, "AbstractXmlIoInputCallback::read() ERROR: context mismatch\n");
            return -1;
        }
        if (len <= 0) {
            printd(0, "AbstractXmlIoInputCallback::read() ERROR: invalid len %d\n", len);
            return -1;
        }
        if (!buffer) {
            printd(0, "AbstractXmlIoInputCallback::read() ERROR: null buffer\n");
            return -1;
        }
        if (!xsink) {
            printd(0, "AbstractXmlIoInputCallback::read() ERROR: no exception context\n");
            return -1;
        }

        // unhandled exceptions will appear on stdout
        ReferenceHolder<QoreListNode> args(new QoreListNode(autoTypeInfo), xsink);
        args->push(len, xsink);
        if (*xsink) {
            return -1;
        }
        ValueHolder bufHolder(input_stream->evalMethod("read", *args, xsink), xsink);
        if (!bufHolder) {
            printd(5, "AbstractXmlIoInputCallback::read() %d failed (err: %d)\n", len, *xsink ? 1 : 0);
            return *xsink ? -1 : 0;
        }
        const BinaryNode* b = bufHolder->get<const BinaryNode>();
        if (b->size() > (size_t)len) {
            printd(0, "AbstractXmlIoInputCallback::read() ERROR: read size %zu > requested %d\n", b->size(), len);
            return -1;
        }
        memcpy(buffer, b->getPtr(), b->size());
        printd(5, "AbstractXmlIoInputCallback::read() %d succeeded: %d\n", len, (int)b->size());
        return (int)b->size();
    }

    // libxml2 I/O callback: close the requested resource
    DLLLOCAL int close(void* context) {
        if (!input_stream) {
            printd(0, "AbstractXmlIoInputCallback::close() WARNING: input_stream already null\n");
            return 0;
        }
        if (context != input_stream) {
            printd(0, "AbstractXmlIoInputCallback::close() ERROR: context mismatch\n");
            return -1;
        }
        if (!xsink) {
            printd(0, "AbstractXmlIoInputCallback::close() ERROR: no exception context\n");
            // Still try to clean up
            input_stream = nullptr;
            return -1;
        }

        input_stream->deref(xsink);
        input_stream = nullptr;
        return 0;
    }

    // set exception context
    DLLLOCAL void setExceptionContext(ExceptionSink* xs) {
        if (xsink && xs != xsink) {
            printd(0, "AbstractXmlIoInputCallback::setExceptionContext() WARNING: overwriting existing context\n");
        }
        xsink = xs;
    }

    // clear exception context
    DLLLOCAL void clearExceptionContext() {
        if (!xsink) {
            printd(0, "AbstractXmlIoInputCallback::clearExceptionContext() WARNING: context already null\n");
        }
        xsink = nullptr;
    }

protected:
    QoreObject* self;
    QoreObject* input_stream = nullptr;
    // current exception context
    ExceptionSink* xsink = nullptr;
};

#endif
