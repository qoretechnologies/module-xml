# P7-09 SOAP one-way acknowledgments and protocol faults

Copyright (C) 2026 Qore Technologies, s.r.o.

## Root causes and implemented behavior

SoapBinding rejected any response Body value before checking for a protocol Fault
when the operation had no application output message. Valid infrastructure faults
therefore raised SOAP-DESERIALIZATION-ERROR instead of the established
SOAP-SERVER-FAULT-RESPONSE. Fault recognition/decoding now precedes the output-message
check and application SOAP encoding. The existing exception contents are preserved.
Direct retained XML response calls use the same fault path before enforcing their
requirement for declared application output parts.

The same check treated an empty hash as unexpected output. A whitespace-only Body
produced that hash while a syntactically empty Body produced NOTHING. Native
one-way decoding now accepts both empty forms, returns the existing header value
or NOTHING, and still rejects actual unexpected application children.

SoapHandler previously returned an empty 200 result, which the general-purpose
HttpServer intentionally rewrites to 204. SOAP handlers now explicitly return an
empty 202 acknowledgment for one-way operations in both versions. SOAP 1.2 requires
202 when no response envelope is provided; WS-I Basic Profile 1.2 lists 202 as a
preferred SOAP 1.1 one-way status. This is the selected protocol acknowledgment,
not an HTTP transport override or a Qore change. HTTP WSDL bindings are unaffected.
Processing failures still return a SOAP fault with its required error status.

## Normative basis and public contract

[WS-I Basic Profile 1.2 section 4.7.8](https://docs.oasis-open.org/ws-brsp/BasicProfile/v1.2/BasicProfile-v1.2.html)
and [Basic Profile 2.0 section 4.7.8](https://docs.oasis-open.org/ws-brsp/BasicProfile/v2.0/BasicProfile-v2.0.html)
R2714 permit an envelope on one-way responses, including infrastructure faults.
R2727 distinguishes successful transmission from application validation/processing.
[SOAP 1.2 Part 2 Table 19](https://www.w3.org/TR/soap12-part2/#http-respbindprocess)
specifies the empty-response status. W3C assertions `x2-http-respbindprocess-reshdr`
and `x2-http-reqbindwaitstate-trans` are relevant; full protocol assertion acceptance
is still open.

SoapClient processes optional response envelopes with its configured SOAP node,
including acknowledgment header processors and unknown mandatory-header rejection.
An empty one-way acknowledgment returns NOTHING, including with xml_values selected.
Its HTTP information and SOAP processing metadata remain available to the caller.
A successful HTTP result is not an application-delivery guarantee. Direct
`deserializeXmlResponse()` has no application parts to return without an output
declaration: it reports protocol faults, but still rejects a nonfault empty envelope
under its existing retained-parts contract.

## Independent validation

The independent Python server covers exact empty 200, 202 and 204 responses, optional
SOAP envelopes on 200/202, faults on error statuses, known/unknown mandatory response
headers and invalid application/fault Bodies. Each failure is followed by an empty
successful acknowledgment on the same client. An external peer is necessary to emit
an exact empty 200 because Qore HttpServer's documented general behavior converts it
to 204; that behavior is not bypassed in the Qore loopback tests.

Python clients verify real one-way handlers in source/saved-object/saved-data and
native/retained modes. Success has status 202, zero body bytes, Content-Length 0 and
no Content-Type. Failures validate against unchanged pinned W3C SOAP schemas and
expanded QName codes. Unknown mandatory request headers do not invoke the callback;
application errors do, and a subsequent successful call verifies recovery. Queue
counts, READY/STOP handshakes and bounded I/O provide deterministic teardown.

All **31 affected Qore suites pass: 394 cases / 22,871 assertions**. Ten focused
SOAP suites also pass compiled: **35 cases / 11,908 assertions**. The new one-way
suite passes **3 cases / 783 assertions**, covering source/saved service graphs,
both SOAP versions, direct/native/retained fault handling, generated faults, version
negotiation, whitespace-only Bodies, acknowledgments, header capabilities and recovery.

Ten independent Python gates pass. The new two-test gate checks **228 HTTP exchanges**:
180 external-server/client exchanges and 48 external-client/handler exchanges. It
verifies exact 200/202/204 acknowledgments, optional envelope/header processing,
protocol errors, empty handler bodies with no Content-Type, fault QName identities
against pinned schemas, and callback counts before deterministic shutdown.
All 16 corpus commands meet their recorded outcomes; all six semantic reports match
P7-08 except for the WSDL source digest. Installed Qore is `9d8ce440b`.
Documentation and five-file astparser checks pass without warnings/errors.

Audit: **18 Pass / 44 N/A / zero Fail**. No C++ changes; Valgrind is not required.

P7 continues with remaining action/media/method rules, transport interruption and
complete applicable assertion accounting, followed by P8–P9. No Qore mutation,
installation, push or CI trigger.
