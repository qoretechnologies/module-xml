# P7-11 SOAP HTTP media and method boundaries

Copyright (C) 2026 Qore Technologies, s.r.o.

## Root causes

Unsupported SOAP media previously fell through generic MIME payload conversion and
failed as SOAP envelopes, producing SOAP faults instead of transport errors. Invalid
Content-Type syntax failed before the handler knew its SOAP version. Unsupported
HTTP methods fell through to 501. application/soap+xml accepted SOAP 1.1 envelopes.

SOAP adapters now explicitly request SOAP transport/root validation during MIME
normalization. Generic XML and opaque WSDL HTTP MIME uses retain their own contracts.
The handler distinguishes malformed metadata (plain HTTP 400), unsupported media or
charset (plain HTTP 415), and recognized-envelope processing failures (SOAP faults).
Expected-envelope version negotiation precedes the final RFC 3902 media identity
check. Header callbacks do not run for rejected media. Charset support uses Qore's
documented conversion-stream constructor, not a module-owned charset registry;
unsupported conversion is distinguished from core system errors carrying errno.

Unsupported methods on registered resources return 405 with Allow computed from
applicable SOAP and WSDL HTTP routes. Read locks protect method discovery; discovery
never invokes a callback. GET ?wsdl still serves the description. Explicit GET and
POST HTTP bindings remain functional, individually and on the same resource.

Client response media is checked before header callbacks. The public envelope check
can use the same response-version-negotiation mode as SoapProcessingNode, preserving
SOAP 1.1 VersionMismatch responses to SOAP 1.2 calls. Empty one-way acknowledgments
require no XML media. Non-SOAP HTTP error responses preserve their original exception.

The charset negative matrix found a separate error-path defect: logging an invalidly
encoded request body could itself fail conversion, replacing the protocol error with
an HTML 500 and closing the connection. The handler now logs byte count and original
exception strings without interpreting body bytes. Unsupported charset labels reject
in preflight; malformed bytes in a supported encoding retain their SOAP error.

The standards audit then reproduced a SOAP processing-order defect: complete
envelope validation checked malformed Body content/fault grammar before testing
unknown targeted mandatory headers. The direct node and both HTTP adapters now
perform structure/version preflight with Body checks deferred, reject unknown
mandatory capabilities, then perform full Body/fault validation before any processor
callback. Direct envelope validation remains complete by default. Missing capability
produces MustUnderstand even with a malformed Fault or non-element Body content;
optional/untargeted headers do not suppress those Body errors. Both receiver roles,
saved node graphs, handler requests and client HTTP 200/500 responses are covered.

## Requirements and validation scope

[SOAP 1.2 Part 1 section 2.6](https://www.w3.org/TR/soap12-part1/#procsoapmsgs)
requires mandatory-header handling before Body-content faults (W3C assertion
`x1-procsoapmsgs-steps`).
[SOAP 1.2 Part 2 section 7.5.2.1](https://www.w3.org/TR/soap12-part2/#http-initstate)
separates HTTP initialization errors from faults after SOAP reception.
[WS-I Basic Profile 1.2 R1113–R1115](https://docs.oasis-open.org/ws-brsp/BasicProfile/v1.2/BasicProfile-v1.2.html)
specifies the corresponding preferred HTTP 400/405/415 behavior.
[RFC 3902](https://www.rfc-editor.org/rfc/rfc3902.html) reserves application/soap+xml
for SOAP 1.2. Generic XML representations remain supported under SOAP 1.2 Part 2
section 7.1.4; arbitrary application XML media types are not advertised.

Tests cover plain, multipart and XOP roots; absent/unsupported/malformed media;
unknown/empty/conflicting charsets; UTF-8/UTF-16 and malformed encoded bytes; media/
envelope version identity; response-version negotiation; HEAD and other unsupported
methods; exact Allow values; GET ?wsdl; single/mixed HTTP routes; header callback
isolation; and successful calls following every rejected representation. Python checks
wire status/headers independently and validates generated SOAP faults against the
unchanged pinned W3C schemas. Existing envelope, fault, action, one-way, WSDL HTTP,
attachment and live CXF gates remain mandatory.

The **217-suite broad Qore gate passes: 3,309 cases / 152,203 assertions**.
The standards audit then fixed mandatory-header precedence. On that final source,
**35 affected Qore suites pass: 411 cases / 24,802 assertions**.
Thirteen focused SOAP suites also pass compiled: **43 cases / 13,735 assertions**.
The new media/transport suite passes **2 cases / 137 assertions**; mandatory-header
priority passes **2 cases / 246 assertions**.

All fourteen independent Python gates pass on the final source. The new media gate
covers **1,167 HTTP exchanges**; the priority gate adds **192 exchanges** (72 handler,
120 client). Tests check statuses, media/Allow headers, WSDL retrieval, HTTP routes,
invalid bytes, callback counts and recovery across source/object/data service graphs
and native/retained values. All 16 corpus commands meet their recorded outcomes;
all six semantic reports match P7-10 except for the WSDL source digest. Installed
Qore is `9d8ce440b`. Documentation and seven-file AST checks pass without warnings/errors.

Audit: **18 Pass / 44 N/A / zero Fail**. No C++ changes; Valgrind is not required.

P7 remains open for transport interruption, full applicable assertion accounting,
and review of SOAP 1.2 SOAP-response GET MEP applicability/API. This increment's 405
behavior describes WSDL SOAP invocation routes; it does not claim complete SOAP 1.2
HTTP binding or WS-I profile conformance. P8–P9 remain subsequent phases. No Qore
edits, installation, push or CI trigger.
