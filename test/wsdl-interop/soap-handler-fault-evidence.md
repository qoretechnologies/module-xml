# P7-07 SOAP handler fault boundaries

Copyright (C) 2026 Qore Technologies, s.r.o.

## Root causes and implemented behavior

Registered header processors run before Body routing and conversion. Their declared
header-fault exceptions previously entered the generic parse-error path, losing the
header declaration and value. The handler now retains the exception while resolving
only the operation identity, verifies the binding version, and uses shared declared
fault serialization without Body conversion or application dispatch. Unknown targeted
mandatory headers still fail preflight before any header processor runs.

Unexpected application, header processor and output serialization exceptions previously
used the generic Client/Sender default, incorrectly attributing server processing
failures to the request. They now produce Server/Receiver and HTTP 500. Input conversion
and routing failures retain Client/Sender; SOAP 1.2 uses HTTP 400 for Sender and HTTP
500 for Receiver, MustUnderstand and VersionMismatch. SOAP 1.1 faults use HTTP 500.
A declared body fault named SOAP-HEADER-FAULT retains its existing precedence; header
processors explicitly select header-fault metadata. Invalid declarations and fault
serialization failures are server-side errors. Error hooks retain operation context.

THREAD-CANCELLED and PROGRAM-INTERRUPTED now escape all handler fault-translation
boundaries with their original exception data. Direct public-handler tests verify
this independently for header processors and application callbacks.

Audit reproductions also exposed diagnostic formatting failures: a missing or non-string
description could cause a secondary overload exception, while XML-invalid control
characters produced malformed fault XML. Diagnostic values are now formatted explicitly;
valid Unicode is preserved and unrepresentable characters become visible Unicode escapes.
The existing client suite expected HTTP 400 for its injected application exception;
it now checks HTTP 500 and Receiver. Its identity assertion for fault readiness was
replaced with an actual fault exchange, including exact reason text.

## Normative basis and independent evidence

[SOAP 1.1 section 4.4.1](https://www.w3.org/TR/2000/NOTE-SOAP-20000508/#_Toc478383510)
and [SOAP 1.2 section 5.4.6](https://www.w3.org/TR/soap12-part1/#faultcodes)
distinguish request defects from processing failures. HTTP mapping follows
[SOAP 1.1 section 6.2](https://www.w3.org/TR/2000/NOTE-SOAP-20000508/#_Toc478383529)
and [SOAP 1.2 Part 2 Table 20](https://www.w3.org/TR/soap12-part2/#tabresstatereccodes).
The W3C assertion `x2-http-respbindprocess-fltmap` supplies the SOAP 1.2 mapping
requirement. This increment does not claim full profile/assertion acceptance.

The Python peer sends requests using an independent HTTP client to real Qore handlers,
checks output against the pinned W3C schemas and resolves QName identities with lxml.
Each negative exchange is followed by a successful call on the same connection. Server
queues prove mandatory-header priority and absence of Body callbacks after header or
input-conversion failures. READY/STOP handshakes and bounded I/O provide deterministic
teardown without readiness sleeps or polling.

All **29 affected Qore suites pass: 388 cases / 19,256 assertions**. Eight focused
SOAP suites also pass compiled: **29 cases / 8,293 assertions**. The new handler
suite passes **5 cases / 1,174 assertions**, including both SOAP versions, source and
saved service graphs, native and retained values, action/body routing, fault recovery,
cancellation, and missing/structured/XML-invalid exception diagnostics.

Eight independent Python gates pass. The new gate checks **576 HTTP exchanges**
against unchanged pinned SOAP schemas, independently checking QName fault identities,
status codes, declared header/detail placement, preflight priority and callback counts.
All 16 corpus commands meet their recorded outcomes; all six reports exactly match
P7-06. Installed Qore is `9d8ce440b`, including the verified strict URI fix.
Documentation and four-file astparser checks pass without warnings/errors.

Audit: **18 Pass / 44 N/A / zero Fail**. No C++ changes; Valgrind is not required.

P7 continues with action/media/HTTP requirements and complete applicable assertion
accounting, followed by P8–P9. No Qore mutation, installation, push or CI trigger.
