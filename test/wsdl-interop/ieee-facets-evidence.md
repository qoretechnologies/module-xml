# IEEE facet interoperability evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

`test_ieee_facets.py` uses authored schemas with actual SOAP 1.1/1.2 bindings
and distinct request/response wrappers. Original W3C fixtures are unchanged.
Atomic values, attributes/simple content and repeated elements are exercised
through schema operations, detached element/message providers, Serializable
copies and generated examples. Lists and unions have separate matrices.

| Matrix | Contracts | Inputs: valid / invalid | Outputs | Provider results |
| --- | ---: | ---: | ---: | ---: |
| IEEE atomic facets | 192 | 840 / 1452 | 840 | 13760 |
| IEEE list enumeration | 12 | 72 / 96 | 72 | 992 |
| Float/double union identity | 24 | 216 / 168 | 216 | 2240 |
| Total | 228 | 1128 / 1716 | 1128 | 16992 |

Provider results comprise 7,648 valid outputs (including 1,632 examples),
9,152 invalid-value rejections and 192 expected `XSD-SAMPLE-ERROR` results for
empty NaN-exclusive types. Every rejection asserts its exception category.
The independent validators inspect 11,640 original/output documents with
Xerces-J 2.12.2 and 11,480 with lxml 6.1.1/libxml2 2.12.10. The remaining 160
libxml2 document checks are unreachable because it rejects three valid schemas,
as explained below. They still require Xerces and normative value checks.

Seven methods cover these binding matrices and construct 1,128 singleton/empty IEEE intervals
by walking encoded float/double values. These include both signs, zero,
subnormal/normal transitions, powers of two, finite maxima and infinities,
plus seeded ordinary values (`0xFACEE2026 + wide`). Original/reconstructed
schemas produce exactly the adjacent target value in 564 nonempty intervals
and reject generation in 564 empty intervals. This independently checks
2,256 schema variants and the corresponding reconstructed providers.

An eighth method compiles 20 valid/invalid atomic and simple-content schemas
through 40 actual SOAP binding contracts, checking fixed digit counts independently
of builtin ranges. Both validators check the schemas and 20 valid documents.

## Root causes in WSDL

Restrictions formerly used decimal-text/native arithmetic that did not apply
the target float rounding before every comparison. For float `minExclusive=1`,
serialization admitted `1.00000001` although decoding rejected it after
rounding. Conversely, `maxInclusive=1` rejected that valid spelling during
serialization. NaN could pass a numeric lower bound, and equivalent float
enumeration spellings failed to match. Shared IEEE comparison now handles
both directions and provider paths consistently.

The example helper's enumeration branch omitted float from the types whose
candidate is checked by `getSampleValue()`. Enumeration `1` combined with
pattern `001[.]00e0` therefore emitted an invalid example. Float now follows
the same validated pattern-candidate path as other completed scalar types.

Enabling float list metadata exposed an inconsistent builtin/provider pair:
metadata changed from integer to float could retain its integer provider.
Known numeric provider identities are now checked during construction and
reconstruction. The old negative test remains a negative test.

Review also caught a regression in the new shared fixed-value comparator:
ordinary native-float display formatting made decimal values
`1.234567891234567` and `1.234567891234568` compare equal. The comparator now
uses the existing lossless decimal lexical conversion. Dedicated positive
and negative tests exercise schema, wire and reconstructed provider paths.
A second audit correction keeps fixed digit counts in their own count space:
`totalDigits=300` is valid on a byte type, and `fractionDigits=0` is valid on a
negativeInteger type. Comparing those limits as instance values wrongly rejected
valid repeated fixed facets. Count comparison now uses `XsdFacetCountHelper`.

## Independent validator disagreements

The normative baseline is [XSD 1.0 Part 2, float/double](https://www.w3.org/TR/xmlschema-2/#float),
[primitive equality](https://www.w3.org/TR/xmlschema-2/#dt-equal) and
[exclusive bound derivation](https://www.w3.org/TR/xmlschema-2/#rf-minExclusive).
NaN identifies itself but is incomparable with every other value; float and
double remain distinct primitive families in unions. The tests compute
target rounding with integer rational arithmetic, independently of Qore,
libc and MPFR. Invalid lexical forms are covered by the preceding
[scalar matrix](ieee-scalars-evidence.md).

`xmlSchemaCompareFloats()` in pinned libxml2 2.15.4
`xmlschemastypes.c` (around line 4796) returns 1 for NaN versus an ordinary
value, and -1 for the reverse. The bound checks in
`xmlSchemaValidateFacetInternal()` (around lines 5506–5534) use that ordering
without an incomparable-value guard. Thus `minInclusive=0` and
`minExclusive=0` wrongly admit NaN; `maxInclusive=NaN` and
`maxExclusive=NaN` wrongly admit ordinary values. The private 2.15.4 native
`XmlReader` reproduces all four cases for both float and double. The lxml
2.12.10 matrix reproduces **372 false positives**, including inherited
enumeration and fixed lower-bound variants.

Every false positive must be rejected by Xerces and the independent partial
ordering predicate, and must be accepted by the predicate with precisely
libxml2's NaN-as-largest comparison substituted. Other differences fail the
test. No production validation is weakened and no source document is changed.

The three `float-repeated-exclusive` schemas repeat `minExclusive=1` as
`minExclusive=1.00000001`; both values round to binary32 1. XSD permits that
same exclusive endpoint in a derivation. libxml2 instead checks it as an
instance of the base, rejecting it as insufficiently greater than 1. This is
the previously adjudicated [repeated-endpoint compiler defect](facet-declarations-adjudication.md),
now exercised with target-rounded IEEE spellings. Xerces accepts the original
schemas, and every reachable document retains its independent value assertion.

## Corpus promotion and regression scope

The strict selection adds Float/Double Attribute, Element, EnumerationType
and SimpleTypePattern: 97 selected WSDLs and 828 message directions pass.
`ieee_reference.py` shares the already-tested rational conversion with the
coverage driver; mutated schema-valid values, precision changes, NaN and
native zero-sign loss are explicitly tested. The original corpus resolves
24 tracked failures: eight each for the float/double pattern families and
four each for their enumeration families. No new corpus failures appear;
196 broader failures remain assigned to their unfinished phases.

The Qore suite `test/wsdl-ieee-facets.qtest` passes 13 cases / 4,837 assertions.
It covers rounded/NaN bounds, fixed/inherited declarations, patterns,
provider precision metadata, fixed attributes, atomic choice updates, lists,
unions, examples and the decimal fixed-value regression. It passes in AST,
IR, JIT, tiered and AOT execution. The affected 66-suite matrix and the
executed design example pass (66 suites / 761 cases / 20,957 assertions). This increment does not close the remaining
P3 date, binary and contextual scalar work, or later binding/protocol phases.
