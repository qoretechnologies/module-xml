# P7-13 SOAP 1.2 response retrieval

Copyright (C) 2026 Qore Technologies, s.r.o.

## Implemented contract

[SOAP 1.2 Part 2 section 6.3](https://www.w3.org/TR/soap12-part2/#soapresmep)
defines an envelope-free request followed by a SOAP response. Sections
[7.3](https://www.w3.org/TR/soap12-part2/#http-mep) and
[7.4](https://www.w3.org/TR/soap12-part2/#http-features) include GET retrieval in
the HTTP binding. This increment implements that path with explicit client and
handler APIs rather than inferring a safe retrieval from an ordinary operation.
It supplies executable GET evidence for W3C assertion IDs
`x2-bindformdesc2-reqsttr`, `x2-bindformdesc2-ressttr`,
`x2-webmethodstatemachine-compat`, `x2-http-suptransmep-uris`,
`x2-http-suptfeatures-webmethod`, and `x2-http-suptfeatures-methrest`.

`getSoapResponse()` selects the configured binding's output/fault codec and resolves
a resource URI through core request-local HTTP support. It reuses response media,
charset, version, mandatory-header and fault processing. It rejects request-only
options and explicit entity/SOAPAction headers; native and legacy entity defaults
are suppressed without mutation. SOAP 1.1, HTTP and output-less bindings reject.

`addSoapResponseResource()` registers an exact GET resource relative to the mount.
Its typed provider receives context without SOAP request decoding. Existing output
serialization, declared fault mapping and generic Receiver errors apply. GET bodies
reject before callbacks; ordinary POST and GET ?wsdl remain usable. GET routes share
the existing method registry and participate in Allow and service removal. Duplicate
static routes reject; overlaps with HTTP templates reject during dispatch in either
registration order. Callbacks run outside registry locks and can remove themselves.

The new root-route test exposed a collision-check defect also present in HTTP route
registration: a missing match's NOTHING path compared equal to the empty root key.
Both paths now require an existing matching object before comparing its path. Tests
register root resources after other routes and verify real duplicate rejection.

## Executable coverage

- `test/soap-response.qtest`: options, entity headers, versions/bindings/output,
  operations, path validation, canonical duplicate detection, root/HTTP collisions,
  template overlaps in both orders, removal, declared faults and invalid output.
- `test_soap_response.py`: independent raw HTTP peers in both directions; empty GET
  wire requests, headers, native/retained output, source/object/data graphs, media,
  unknown mandatory headers, version errors, HTTP errors, faults on 200/400/500,
  recovery, query/IRI/escaped paths, request-local defaults, cross-origin credentials,
  redirects, subsequent POST, mounted resources, GET bodies, Allow and WSDL retrieval.
  Generated SOAP responses/faults validate against the pinned W3C SOAP 1.2 schema.
- `test_soap_transport.py::test_get_response_interruption_and_recovery`: EOF before
  headers, partial status, short length/chunk bodies, event-triggered cancellation
  in both framings, peer EOF, no premature header callbacks and same-client recovery.
  The existing 432 POST/client/handler exchanges remain mandatory.

Reproduction commands use `QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug`
for Qore tests and `python3 -B test/wsdl-interop/test_soap_response.py -v` plus the
transport gate. Compiled checks build all three qmods with `qcc -m -o`, remove the
source-prepend directives in temporary test copies, select the qmods with
QORE_MODULE_DIR and preserve original fixture directories. Logs and runners are in
`/tmp/xml-soap-response-get/accept/`; exact commands and digests are committed in
[P7-13-validation.json](P7-13-validation.json).

Forty affected Qore suites pass: **468 cases / 27,612 assertions**. The new unit
suite passes **4 cases / 156 assertions**. All sixteen independent Python gates pass,
including **336 new HTTP exchanges** and **72 new GET interruption/cancellation
exchanges**. The full transport matrix now covers 504 exchanges. Freshly compiled
WSDL, SoapClient and SoapHandler pass four focused Qore suites (39 cases / 604
assertions), the full new GET matrix and the complete transport matrix.

All 16 corpus commands meet their recorded outcomes; all six semantic reports are
unchanged from P7-11 except for the Qore runtime identifier. The known legacy
projection-loss gate retains its expected exit 1. Documentation and all six changed
Qore files pass documentation/AST checks without warnings or errors. Installed Qore
is `25346118e`. Audit: **19 Pass / 43 N/A / zero Fail**. No C++ change; no Valgrind needed.

The full standards assertion ledger remains open; this is not P7 acceptance or a
claim of complete WS-I/SOAP conformance. P8–P9 follow. No Qore edits, installation,
push or CI trigger. Durable design: [SOAP processing](../../design/soap-envelope-processing.md).
Audit: [all 62 checks](audits/P7-13-soap-response.md).

The next P7 assertion review reproduced buffered-upload/early-response deadlock in
core HTTPClient, independently of XML. The core-only and ordinary SOAP reproducers,
positive raw-socket control and source-level root cause are handed off at
`/tmp/qore-httpclient-buffered-duplex/README.md`. The buffered HTTP/1.1 path sends the
whole request before starting response reads; the existing full-duplex branch is
limited to chunked streaming sends. This remains an open P7 dependency, not an
accepted result or an XML workaround.
