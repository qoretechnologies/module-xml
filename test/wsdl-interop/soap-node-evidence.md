# P7-03 explicit SOAP nodes — validation

Copyright (C) 2026 Qore Technologies, s.r.o.

The node-processing increment is accepted after verifying the installed Qore strict URI fix.

## Implemented behavior

`SoapProcessingNode` uses immutable typed configuration and a typed callback registry keyed by
expanded header names. WSDL declarations do not imply application understanding. Role targeting
and mandatory preflight finish before callbacks. Known targeted optional headers are processed;
unknown optional and untargeted headers are not. Results keep every original XML block and its
outcome. Ultimate receivers get an application envelope containing only targeted headers.
Intermediaries get a forwarding envelope according to the protocol version's relay rules, with
stable XML Base, namespaces, lexical content, order and body values. Adjacent same-name occurrences
are filtered individually, including occurrence lists used by the ordered XML parser.

SoapClient constructor and per-call node options apply to responses. SoapHandler's optional fifth
constructor argument applies to requests. Both require ultimate receivers. Both retain typed
processing metadata independently of the decoded body/header values. Untargeted bound headers
never enter application schema decoding. Native HTTP contexts are copied into explicit typed
containers before storing typed results; this respects legacy untyped-container assignment rules.
The application XML passes through the established SOAP parser to preserve comment projection and
XOP handling. Unknown mandatory request headers produce correctly scoped MustUnderstand faults;
SOAP 1.2 NotUnderstood headers carry expanded-name QName metadata. Response roles resolve against
the final HTTP response URL after redirects, including inherited XML Base.

The audit also corrected SOAP fault recognition: an application element named `Fault`
was previously mistaken for a protocol fault after namespace projection. The decoder now
checks the actual envelope-qualified name first. `soap-fault-identity.qtest` passes
3 cases / 210 assertions across both versions, saved services, native/retained values,
aliases, empty data, foreign namespaces and 12 live client/handler exchanges. Genuine
SOAP faults retain their existing exception category.

## Requirements and independent evidence

Primary requirements are SOAP 1.1 sections 4.2.2–4.2.3 and SOAP 1.2 Part 1 sections 2.2–2.7,
5.2.2–5.2.4, 5.4.8 and 6:

- https://www.w3.org/TR/2000/NOTE-SOAP-20000508/
- https://www.w3.org/TR/soap12-part1/
- https://www.w3.org/TR/soap12-testcollection/

The W3C collection's T12/T13, T15–T17 and T21/T22 scenarios correspond to ultimate/next/custom
role targeting, unknown mandatory faults, untargeted forwarding and successful known-header/body
processing. Tests here are authored semantic equivalents, not copied W3C fixture bytes.
URI grammar and ASCII URI policy are enforced by Qore; inherited XML Base IRIs are mapped to URIs.

- `soap-node.qtest`: role/capability/mandatory/relay matrix for both versions and ultimate/intermediary
  roles; preflight and failure recovery; ordered forwarding and XML context; namespace scope,
  configuration errors, immutable configuration and concurrent calls.
- `soap-node-http.qtest`: actual clients/handlers, source/saved/data services, native and retained XML,
  preflight fault priority, original typed context, per-call capabilities, recovery, and adjacent
  bound headers targeted at different nodes. **176 HTTP exchanges.**
- `test_soap_node.py`: **96 HTTP exchanges against pinned Apache CXF 4.1.3**, matching ultimate-receiver
  mandatory/role decisions; **240 external-client/Qore-handler exchanges**, checking faults against
  the existing exact pinned W3C envelope schemas; **12 redirect/final-response HTTP exchanges**,
  checking response base URI and role selection. Total **348 independent HTTP exchanges**. The
  standalone intermediary matrix inspects forwarding with lxml and processes each forwarded result
  at a second node.
- The CXF dependency hashes are verified against the existing manifest before compilation. Java
  compiles with all warnings enabled and warnings as errors. Expected CXF fault warnings are
  suppressed at its logger; assertions inspect status, fault QName and response body independently.
- The legacy WCF golden message is unchanged. Its handler test now requires a concrete MustUnderstand
  rejection and both unknown WS-Addressing expanded names instead of accepting any success or error.

No C++, Qore mutation, installation, push or CI trigger belongs to this increment. P7 complete fault
semantics and HTTP/action rules remain open, followed by P8–P9. The node callback exception contract
propagates callback errors; additional declared/header-fault mapping belongs to the remaining fault
integration review. XML/JMS transport scope remains the approved metadata/rejection-only contract.

## Validation result

All **25 affected Qore suites pass: 373 cases / 15,340 assertions**. The four new
SOAP suites also pass compiled: **14 cases / 4,381 assertions**. The strict-URI
suite passes all **3 cases / 75 assertions**, including forbidden ASCII, malformed
authorities and percent triplets, non-ASCII role rejection, encoded identities,
relative references, and IRI XML Base mapping. The installed Qore runtime is
`489ff7802dc35af2dea70540abfbca8501834d6c`; the standalone native reproducer also
rejects every originally reported malformed reference. SOAP role validation uses
`RESOLVE_URL_ASCII`, with no local character scan or URI grammar implementation.

Five independent Python gates plus the affected HTTP request-URL helper gate pass.
The new independent node gate passes 4 tests and 348 HTTP exchanges. All 16 corpus
commands meet their recorded outcomes; six semantic reports match P7-02 apart from
the WSDL source digest and installed Qore revision, including the preserved ordinary legacy limitations.
Documentation and eleven-file astparser checks are clean.

The completed audit accounts for all 62 checks: **18 Pass / 44 N/A / zero Fail**.
This increment is accepted; P7 fault and HTTP/action work and P8–P9 remain open.
