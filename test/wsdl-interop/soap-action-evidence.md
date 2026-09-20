# P7-10 SOAP request action transport and dispatch

Copyright (C) 2026 Qore Technologies, s.r.o.

## Root causes and implemented behavior

The handler compared raw SOAPAction headers with unquoted WSDL values. Ordinary
single-operation requests masked the error through Body dispatch; two empty-body
operations on the same route exposed a quoted-action failure. Action lookup also
preceded multipart normalization, and SOAP 1.2 incorrectly fell back to SOAPAction.

The serializer emitted bare SOAP 1.1 actions, copied the SOAPAction header into SOAP
1.2 requests, and copied request actions to responses. It now quotes SOAP 1.1 request
headers, uses only SOAP 1.2 root media parameters, and omits request actions on responses.
Explicit empty per-call overrides continue to suppress the action. URI grammar uses
Qore RFC 3986 ASCII validation; SOAP 1.1 references may be empty/relative, while a
present SOAP 1.2 action must be nonempty and absolute. Returned actions preserve their
original URI spelling; quote decoding is shared with the MIME parser.

Handler action lookup now follows MIME root normalization and envelope validation.
The normalized action is available as cx.soap_action to header and body processors.
The handler rejects malformed actions, ambiguous empty Bodies, unknown operation
roots and disagreement with a selected nonempty WSDL action before the body callback.
SOAP 1.2 ignores legacy SOAPAction, including malformed values. HTTP WSDL routing
retains its own method/path and MIME rules.

Moving lookup exposed a version-negotiation dependency: unsupported envelope namespaces
could fail before the handler knew the selected route's expected version. The handler
now derives an unambiguous version from the registered route independently of actions;
this preserves version-mismatch fault/Upgrade metadata without selecting an operation
from an unvalidated envelope. Mixed-version routes do not invent a single expected version.

## Standards and independent source adjudication

[WS-I Basic Profile 1.2 R2744/R2745](https://docs.oasis-open.org/ws-brsp/BasicProfile/v1.2/BasicProfile-v1.2.html)
cover quoted SOAP 1.1 actions and their empty default. Receiver acceptance of legacy
unquoted URI references does not change the quoted output contract.
[SOAP 1.2 Part 2 section 6.5.3](https://www.w3.org/TR/soap12-part2/#soapfeatureaction)
requires nonempty absolute action URIs and exposure of the received value.
[Basic Profile 2.0 R2744, R2757/R2758 and R2760/R2761](https://docs.oasis-open.org/ws-brsp/BasicProfile/v2.0/BasicProfile-v2.0.html)
cover binding identity, optional action presence and independence from SOAPAction.
An invalid supplied URI or conflicting binding value is distinct from mere presence
or absence. Missing actions remain valid when Body/route dispatch is unambiguous.

The pinned CXF hello_world_soap12.wsdl and historical sayHi capture contain the relative
value sayHiAction. They remain unchanged and are mandatory negative controls for
serialization and HTTP reception. The separately named absolute-action derivative
changes only that value to urn:cxf:sayHiAction and adds a 2026 modification notice.
Both hashes and the exact transform are recorded in cxf-derived/soap12-action.json;
the peer test reconstructs the bytes. Positive replay, coverage and generated/live
CXF SOAP 1.2 bindings explicitly select that derivative. Original source/capture
failures remain visible; no production validation exception was added.

The full regression gate also exposed a P7 node-serialization regression: URL-loaded
WebService graphs retain their SoapClient, which now owns a processing node. The
node lacked Serializable, breaking an existing saved-document test. It now saves
immutable configuration, validates it on restore and rebuilds the transient role
lookup. Default/role-only configurations survive object and data graph round trips.
Missing/invalid configuration rejects. Nodes with nonserializable callbacks raise
the normal serialization error and retain their original working capabilities.

The audit also reproduced an older saved-client failure: without the newly added
node member, the first call failed with a runtime type error. SoapClient now restores
the constructor's default ultimate-receiver node when the saved field is absent,
and validates any supplied saved node before assigning members. Current object/data
and legacy saved clients perform real calls in both versions and value modes;
invalid/intermediary saved nodes reject, and invalid per-call options cannot corrupt
subsequent successful calls. The complete native gate was rerun after this audit fix.

## Validation

Tests cover absent/empty/quoted/legacy actions, surrounding HTTP whitespace, quoted
pairs, exact case and percent spelling, relative SOAP 1.1 references, malformed URI
and header syntax, duplicate MIME parameters, plain/multipart/XOP roots, conflicting
legacy SOAP 1.2 headers, ambiguous empty Bodies, action/body mismatch, recovery and
callback counts. Outgoing wire headers and generated response envelopes are checked
independently with Python HTTP peers and unchanged pinned W3C schemas. Existing
fixtures that depended on nonconforming action output now check the protocol's
actual representation. Eighteen owned synthetic Qore fixtures, header-parts.wsdl
and the independent ID-binding peer now use explicit urn: actions where they also
exercise SOAP 1.2. SOAP 1.1 relative-reference tests remain positive coverage.
The attachment-part suite now checks that response root media omits the request action.
The complete suite was rerun after both serialization fixes; the changed shared header-parts fixture also
has a separate successful soap.qtest rerun, and the changed independent peer has
its Python gate rerun. Client overrides remain covered against an external endpoint.

All **216 Qore suites pass: 3,307 cases / 152,066 assertions**.
Eleven focused SOAP suites also pass compiled: **39 cases / 13,352 assertions**.
The new action suite passes **4 cases / 1,444 assertions** across source/saved service
graphs, native/retained values, raw headers, root media parameters and failure recovery.

All twelve independent Python gates pass. The new two-test gate checks **396 HTTP
exchanges**: 48 external-server/client exchanges and 348 external-client/handler
exchanges. The pinned CXF 4.1.3 gate passes with seven tests, including the explicit
absolute-action derivative and unchanged-source negative controls. All 16 corpus
commands meet their recorded outcomes; all six semantic reports match P7-09 except
for the WSDL source digest. Installed Qore is `9d8ce440b`.
Documentation and thirty-one-file astparser checks pass without warnings/errors.

Audit: **18 Pass / 44 N/A / zero Fail**. No C++ changes; Valgrind is not required.

P7 continues with remaining media/method rules, transport interruption and complete
applicable assertion accounting, followed by P8–P9. No Qore edits or installation,
push or CI trigger.
