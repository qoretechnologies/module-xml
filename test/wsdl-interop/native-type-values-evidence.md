# P5-04 portable native type capture

Copyright (C) 2026 Qore Technologies, s.r.o.

The original `TypeSubstitutionUsingXsiType` corpus input is independently valid.
Its second `part` selects `Part2`, extending `Part` with a `description` child.
Before this change, native decoding returned both fields but discarded the
selected type. Re-encoding that value against declared `Part` failed on the
extra child. The reduction and historical diagnostic are
`/tmp/wsdl-p5-04-before.qr` and `/tmp/wsdl-p5-04-before.log`.

The explicit `preserve_types` option retains the resolved type's expanded QName
with its native value. The receiving schema resolves that name and repeats all
selection and value checks. The existing component wrapper still uses component
identity. The [implemented contract](../../design/wsdl-native-type-values.md)
documents defaults, schema reconstruction, header shapes, low-level map scopes
and an executed invoice example. XSD 1.0
[Element Locally Valid](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-elt)
requires the resolved selected definition to validate the instance;
[QName identity](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#QName)
is an expanded name, independent of prefix spelling. The native wrapper is a
Qore API choice for preserving that information.

The independent matrix adds a derived child-content example to the 104 P5-03
instance selection cases: 63 valid and 42 invalid cases. Both pinned validators
(lxml 6.1.1/libxml2 2.12.10 and Xerces-J 2.12.2) compile the original schemas and
agree with their expected input verdicts. There is no disagreement in this matrix.
Both actual SOAP bindings, both directions and original/reconstructed receiving
services produce 840 rows. Each saved value is reconstructed independently.
Invalid rows require both decoding and explicit-wrapper serialization errors;
336 rows reject with the intended error categories. All 1008 reconstructed and
explicit-wrapper outputs independently validate. Separate assertions require
exact native values and expanded envelope, payload and selected type names.
Missing, duplicate, extra or out-of-order worker rows fail.

The Qore suite checks malformed, extra-field and nested wrappers; unknown and
wrong-namespace selections; receiver derivation, block and facet changes;
canonical builtin versus custom conversion identity; same-type normalization;
list, union, repeated, nil and unqualified values; independent data/type QNames;
capture and map restoration after exceptions; cancellation and concurrent callers.
Its document and RPC cases check selected root arguments, both message directions
and both bindings. Header cases preserve selected body/header boundaries.
Twenty-four HTTP calls exercise SoapClient and SoapHandler choices independently,
including saved callback/results and unchanged defaults. Invalid or conflicting
representation options fail before I/O or registration. These tests use listener
readiness and bounded queue/counter completion, without sleeps or polling.

The original W3C example was additionally replayed with explicit capture in
`/tmp/wsdl-p5-04-w3c.py` and `/tmp/wsdl-p5-04-w3c.qr`. Original WSDL, inline schema
and message digests are checked against `adjudication-report.json`. The SOAP 1.2
description changes only the binding extension namespace, then asserts that
the selected binding is SOAP 1.2. Original bytes remain untouched. Eight
binding/direction/schema-copy rows independently validate both original payloads
and 24 native/retained outputs. They require the two part numbers `p1` and `p2`,
the second part's `extended part` description and its expanded `Part2` selection.
The saved native values are reconstructed before reserialization.

Development tests exposed boundary defects fixed in this increment: a whole
root type wrapper was not consumed as a single argument, and legacy header
flattening merged header fields into the wrapper. Explicit wrapper recognition
and retaining its body part-name key fix those causes without altering default
native projection. The audit also found that interpreting wrappers in the common
scalar serializer let attribute values produce element type metadata. The parent
source rejects those values. Wrapper interpretation now has a separate WSDL
type-part entry point; element conversion handles its own boundary. Negative
regressions reject wrappers in attributes and complex simple-content text, both
for QName and component selections, including identity. A separate temporary-service test exposed existing weak
operation dependencies; its committed-source reduction and P6 ownership are
recorded in [the lifetime finding](p6-operation-lifetime-finding.md).

The separate full diagnostic corpus continues to use the default projection.
Its remaining native type-loss failures therefore remain visible; opting in to
capture is reported separately and does not rewrite historical/default results.
Provider integration, substitution groups and element final, wildcard/mixed/
generic content, complete nil/default/fixed and document identity remain P5 work.
P6-P9 binding, protocol, attachment, environment and CI acceptance remain open.
