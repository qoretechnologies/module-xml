/* Copyright (C) 2026 Qore Technologies, s.r.o.
   SPDX-License-Identifier: LGPL-2.1-or-later */

#ifndef QORE_XML_XSD_FLOAT_H
#define QORE_XML_XSD_FLOAT_H

#include <qore/Qore.h>

// Validate XML lexical input and round directly to the requested IEEE format.
// The returned double contains the exact binary32 result when double_precision is false.
DLLLOCAL double qore_xml_convert_xsd_float(QoreValue value, bool double_precision, ExceptionSink* xsink);

#endif
