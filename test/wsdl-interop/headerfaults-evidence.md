# Declared SOAP fault values (P6-20/P6-21)

Copyright (C) 2026 Qore Technologies, s.r.o.

This increment implements declared headerfault values and explicit consumption.
P6–P9 remain open.

The implementation compiles headerfault descriptions in their own namespace
scope and owns their messages independently of the original service. Explicit
operation APIs select input/output declarations and serialize a fault value in
Header with a generic Fault in Body. Native and retained-XML decode APIs consume
selected headerfault values. SoapHandler callbacks can use SOAP_HEADER_FAULT;
ordinary declared faults retain precedence and SoapClient retains its existing
SOAP-SERVER-FAULT-RESPONSE contract.

Tests cover both SOAP versions, document/RPC, literal/encoded, imported and saved
operations, ambiguity, source errors, namespace scope, wire placement, nil values,
subtype capture, lexical retention and live client/server exchange. The existing
component-reference fixture now uses a qualified literal element for its
headerfault; invalid reference assertions are retained and saved descriptor
identity is checked. The pinned WSDL4J observer independently reads nested fault
metadata in both SOAP versions. Full envelope/encoding conformance remains P7/P8.

## Explicit body fault values

WSOperation::deserializeFault() selects a named fault's own single-part schema.
WSOperation::deserializeXmlFault() retains a literal detail element after schema
validation. SOAP envelope extraction is shared with headerfault decoding. Names,
use and namespaces come from the selected binding; normal output data and fault
reason strings do not select the detail schema. Tests cover independently
authored envelopes, imported/saved operation handles, schema identity checks,
substitution roots, nil values, native subtype capture, lexical forwarding and
ordinary SOAP client exception compatibility.

## Validation

The combined body/header gate on the fixed runtime passes 26 suites / 505 cases /
10,221 reported assertions, including all 8 headerfault cases / 601 assertions
and all 8 body-fault cases / 210 assertions. Doxygen and astparser pass.
All 16 corpus commands meet expected outcomes. All six semantic reports match
P6-19 apart from version metadata, including the expected legacy projection
losses. The coverage and survey tools pass 17 and 19 tests respectively.
Audit: 18 Pass / 44 N/A / zero Fail. No C++ changes were made in this increment.

The full legacy worker initially reached its fixed 60-second deadline twice
under concurrent local builds. With user approval, both corpus tools now accept
a bounded --worker-timeout option (1–3600 seconds, default 60). The final run
uses 180 seconds and retains every case and assertion. Tests cover API/CLI input
validation, deadline propagation, and cleanup after timeout/cancellation.
Report artifacts and semantic comparisons, rather than exit status alone,
establish the final corpus result.

## Runtime dependency

These gates use the locally installed Qore forward typed-container fix. The
standalone Qore graph reproducer now preserves the child's shared self-reference.
The runtime reports build hash e07631a9951073dcede030fa7b7bc564f540fdda; the installed
serialization patch was concurrent uncommitted Qore work during validation, so
the manifest also fingerprints its source. No Qore source was changed or
committed by this XML increment. The root-cause handoff remains at
`/tmp/qore-serializable-forward-typed-list/README.md`.

See [validation](P6-20-validation.json),
[audit](audits/P6-20-headerfaults.md), and
[durable header design](../../design/wsdl-soap-header-values.md).
