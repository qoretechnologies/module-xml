# P7-06 SOAP fault data and generation

Copyright (C) 2026 Qore Technologies, s.r.o.

## Implemented behavior

`WSDLLib::getSOAPFaultInfo()` exposes scoped QName codes/subcodes, ordered reasons
with explicit language, actor/node/role references, optional detail and headers,
SOAP 1.1 extensions and original envelope XML. It validates protocol grammar while
leaving application schema selection to the existing declared fault consumers.
Ordinary response exceptions retain their existing contract.

Trailing `SoapFaultOptions` on fault/headerfault serializers select protocol fields
for generic, declared and header faults. Version-incompatible fields reject.
Schema detail/header processing remains in the binding. Generated QName fields
receive local namespace bindings, avoiding envelope/schema prefix collisions.
Original message forwarding uses retained envelope XML; generated prefixes may vary.

## Requirements and audit findings

Primary requirements: [SOAP 1.1 section 4.4](https://www.w3.org/TR/2000/NOTE-SOAP-20000508/#_Toc478383507),
[SOAP 1.2 section 5.4](https://www.w3.org/TR/soap12-part1/#soapfault), and
[SOAP 1.2 encodingStyle placement](https://www.w3.org/TR/soap12-part1/#soapencattr).
Field representation covers the `x1-soapfault-*`, `x1-faultcodeelement-prop`,
`x1-faultvalueelement-prop`, `x1-faultsubcodeelement-prop`,
`x1-faultsubvalueelem-prop`, `x1-faultstringelement-prop`,
`x1-reasontextelement-prop`, `x1-faultactorelement-prop`,
`x1-faultroleelement-prop` and `x1-faultdetailelement-prop` shapes in the
[W3C assertion collection](https://www.w3.org/TR/soap12-testcollection/).
This increment does not claim complete protocol/profile assertion acceptance.

The previous generator exposed only its fixed Client/Sender code and one reason.
Native exceptions also projected QName and XML information. Explicit typed metadata
and generation options now cover these protocol fields without changing decoding
defaults. Tests retain lexical XML and context separately from normalized URI values.

The audit found a shared-validator defect: SOAP 1.2 encodingStyle was rejected on
Detail but accepted on Fault and its other protocol fields. The checker stopped at
container-specific attribute rules. The corrected traversal checks Fault, Code,
Value, nested Subcode, Reason, Text, Node and Role. Application detail entries still
accept encodingStyle; an application attribute with the same local name remains
independent. Fourteen explicit cases agree with the pinned normative schema.
The schema's Detail wildcard excludes unqualified attributes, so that existing
rejection is retained. No normative schema was modified.

Negative generation tests also check XML-invalid reason characters, including NUL,
for a protocol serialization error before XML generation. Version negotiation tests
verify the SOAP 1.1 VersionMismatch exception to an expected SOAP 1.2 response.
Options and caller XML are unchanged after success and failure.

## Independent validation

The new peer checks all five SOAP 1.2 top-level codes and SOAP 1.1 Client/Server
codes, source/saved-object/saved-data services and generic/declared/header faults.
It verifies original generated XML with the pinned W3C schemas and explicit QName,
reason, language, URI, detail and header assertions. For SOAP 1.1 only, a separate
schema-validation copy omits faultstring xml:lang because
[WS-I R1016](https://docs.oasis-open.org/ws-brsp/BasicProfile/v1.2/BasicProfile-v1.2.html#SOAPFaults)
requires its acceptance despite omission in the old SOAP 1.1 schema. The original
attribute and text are independently verified and transmitted unchanged.

A Python HTTP peer sends generated and attribute-placement cases to source/saved
Qore clients in native and retained modes. The returned typed metadata is compared
against Python/lxml QName resolution and field extraction, not Qore-generated
expectations. Case uniqueness, count and all requests/replies are checked.

All **28 affected Qore suites pass: 383 cases / 18,078 assertions**. Seven focused
SOAP suites also pass compiled: **24 cases / 7,119 assertions**. The new fault-data
suite passes **6 cases / 936 assertions**, covering protocol fields, original XML,
source/saved service graphs, typed serialization, negative recovery and 64 subcodes.

Seven independent Python gates pass. The new three-test gate checks **63 generated
fault variants**, **14 attribute-placement cases** and **462 HTTP exchanges** against
pinned schemas and an independent namespace-aware decoder. The existing fault gate
adds 720 exchanges. All 16 corpus commands meet their recorded outcomes; six semantic
reports match P7-05 except for the WSDL source digest and Qore revision. The final
checks use installed Qore `9d8ce440b`, which includes the verified strict URI fix. Documentation and four-file
astparser checks pass without warnings/errors.

Audit: **18 Pass / 44 N/A / zero Fail**. No C++ changes; Valgrind is not required.

P7 continues with declared faults from header processors, application/protocol fault
status mapping, remaining HTTP/action/media requirements and complete assertion
accounting. P8–P9 remain open. No Qore mutation, installation, push or CI trigger.
