# P7-08 SOAP HTTP fault identity and charset boundaries

Copyright (C) 2026 Qore Technologies, s.r.o.

## Root causes and implemented behavior

SoapClient recognized HTTP error faults with a regex on the response body. Valid
UTF-16 faults and faults with whitespace before the closing-tag delimiter did not
match. Comments, CDATA and unrelated application names could match accidentally.
The client now normalizes MIME/charset data and recognizes the matching expanded
SOAP Envelope/Body/Fault names. The parsed response is reused for normal protocol
validation and header processing. Nonadjacent repeated Body elements are recognized
so malformed envelopes containing a fault reach the grammar validator.

This applies to the existing HTTP 400 and 500-series SOAP error paths. Application
Fault names, comments, CDATA, header-local Fault elements, wrong namespaces and
non-SOAP bodies retain the original HTTP exception. Other statuses, such as 404,
retain their HTTP error even when their body resembles a SOAP fault. Malformed
SOAP error documents report their XML/protocol error; fault grammar remains fully
validated. HTTP WSDL bindings retain their independent behavior.

Removing the regex exposed a second XML-side defect: after SoapProcessingNode
produced UTF-8 XML, client and handler reparsed it using the original wire charset.
Both now explicitly label the generated XML as UTF-8 for the internal reparse,
while preserving original transport metadata and attachment entities. Exact accented
values verify both the initial wire decoding and subsequent header-processing path.
No Qore change or charset fallback is used.

## Normative basis and tests

[XML end-tag grammar](https://www.w3.org/TR/xml/#NT-ETag) permits whitespace before
the closing delimiter. SOAP element identity follows expanded XML names under
[SOAP 1.2 Part 1 section 5](https://www.w3.org/TR/soap12-part1/#soapenv) and
[SOAP 1.1 section 4](https://www.w3.org/TR/2000/NOTE-SOAP-20000508/#_Toc478383494).
The HTTP fault paths follow [SOAP 1.2 Part 2 section 7.5.1](https://www.w3.org/TR/soap12-part2/#http-reqbindwaitstate)
and SOAP 1.1 section 6.2. The wire/document charset distinction follows
[RFC 7303](https://www.rfc-editor.org/rfc/rfc7303#section-3.1).
W3C assertions `x1-reltoxml-lexicalform`, `x1-soapfault-prop` and
`x2-http-reqbindwaitstate-trans` are relevant to this increment; complete assertion
acceptance is still open.

The independent Python server sends fault and success variants in UTF-8, UTF-16,
UTF-16LE, UTF-16BE and ISO-8859-1. Prefix aliases and legal closing-tag whitespace
are separately validated against unchanged pinned W3C SOAP schemas. The Qore client
peer reports exact accented values and retains the original status for transport
errors. Every XML error case is followed by a successful call on the same client.
Independent Python clients also send five encodings to real source/saved Qore handlers,
verify the generated envelope schema and exact application value, and check callback
counts through the existing READY/STOP peer protocol. All I/O has bounded deadlines;
there are no readiness sleeps or polling loops.

All **30 affected Qore suites pass: 391 cases / 22,088 assertions**. Nine focused
SOAP suites also pass compiled: **32 cases / 11,125 assertions**. The new HTTP fault
suite passes **3 cases / 2,832 assertions**, covering both SOAP versions, source and
saved service graphs, native/retained values, five encodings, fault identity, HTTP
status boundaries, malformed documents and recovery after failures.

Nine independent Python gates pass. The new three-test gate checks **1,806 HTTP
exchanges**: 1,440 encoded fault/success exchanges, 336 transport-error/document
checks, and 30 external-client/handler encoding checks. Generated fixtures validate
against unchanged pinned SOAP schemas and exact Unicode value assertions.
All 16 corpus commands meet their recorded outcomes; all six reports exactly match
P7-07. Installed Qore is `9d8ce440b`, including the verified strict URI fix.
Documentation and four-file astparser checks pass without warnings/errors.

Audit: **18 Pass / 44 N/A / zero Fail**. No C++ changes; Valgrind is not required.

P7 continues with action/media/HTTP requirements, one-way/empty responses, transport
interruption and complete applicable assertion accounting, followed by P8–P9.
No Qore mutation, installation, push or CI trigger.
