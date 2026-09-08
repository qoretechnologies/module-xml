# Union and XML whitespace evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

XSD 1.0 Part 2 [whiteSpace, section 4.3.6](https://www.w3.org/TR/xmlschema-2/#rf-whiteSpace)
delegates union normalization to the successfully validating member. A union with
a leading string member preserves its input; token members collapse XML whitespace.
The union's [permitted facets](https://www.w3.org/TR/xmlschema-2/#union-datatypes)
are pattern and enumeration, excluding ordered bounds, lengths, digit facets and
whiteSpace declarations. Qore now rejects the remaining ordered-bound declarations.
Comment wrappers survive union scalar serialization without changing the input.

The P3-10 preflight's 24 apparent input mismatches included eight inputs for which
Xerces's union-pattern normalization disagrees with this normative rule. Those
eight were provisional oracle comparisons, not confirmed Qore defects. The
remaining 16 input mismatches, eight invalid serialized outputs and primitive
union value/enum/pattern/provider requirements remain required P3 work. The two
accepted invalid ordered-bound contracts are fixed here. Original preflight
artifacts and the P3-10 record are retained; this adjudication corrects their
interpretation rather than altering that historical evidence.

Xerces-J 2.12.2 source assigns `WS_COLLAPSE` to unions; `getActualValue()` calls
`normalize()` before testing the type's patterns. The normalization method bypasses
that collapse when no pattern exists, explaining why an unpatterned string union
preserves the value but its own pattern does not. A restriction with pattern
`A B` on a string/int union wrongly accepts ` A  B ` and `A\tB`. A patterned string
member rejects them. Libxml2 and Qore reject both forms in both placements.

Source artifact:
[xercesImpl-2.12.2-sources.jar](https://repo.maven.apache.org/maven2/xerces/xercesImpl/2.12.2/xercesImpl-2.12.2-sources.jar),
SHA-256 `3c531edfc074e3e0885e5d4a777a9e7317e108028be50ef6e893a5a9cf3e12c2`.
The entry `org/apache/xerces/impl/dv/xs/XSSimpleTypeDecl.java` has SHA-256
`1f81a456d6b9dcbde0627fbeb51beb1381f2e166230a4530f2711c20c227d9f4`;
relevant lines are 458–464, 1821–1843 and 2023–2042. Research copies are under
`/tmp/wsdl-p3-11-*`; executable tests use the existing pinned offline oracle jar.
The authored pattern matrix identifies exactly 24 Xerces document disagreements
across atomic/attributed/repeated values, both bindings and both directions.
No Qore rejection, serialization or exact-value assertion is waived.

The whitespace tests also exposed native XML data loss. XML 1.0
[line-ending handling, section 2.11](https://www.w3.org/TR/REC-xml/#sec-line-ends)
normalizes literal CR before the application receives text; serialization now
uses references for CR in text and between CDATA sections. Pretty-printing no
longer adds text around CDATA or inside preserved-space content. The reader
previously skipped significant-whitespace nodes before learning whether they were
scalar values. It now retains scalar/mixed text and performs the documented
child-only indentation projection after reading the complete element. Inherited
[xml:space, section 2.10](https://www.w3.org/TR/REC-xml/#sec-white-space) is honored.
Regrouping after omitted indentation retains existing ordered-array conventions
and uses per-name counters to avoid quadratic suffix searches.

Tests: `../xml-whitespace.qtest`, `../wsdl-union-whitespace.qtest` and
`test_union_whitespace.py`. Native cases cover encodings, CDATA, formatting,
comments, repeated/mixed/empty values, subtree readers, inherited/default space
policies, invalid data, cancellation and cleanup. The SOAP matrix includes
string, restricted string, boolean, integer, list and nested union members,
original/reconstructed contracts/providers, attributed/repeated values and
examples. The declaration matrix rejects 24 schemas and 48 real SOAP contracts
with the intended error category using both independent schema compilers.

Preserving `xml:space` also requires the schema/protocol consumer to distinguish
XML formatting from scalar text. `XsdScalarTextHelper::elementContent()` removes
only XML whitespace from the temporary element-only validation view and rejects
non-whitespace/non-string fragments with `SOAP-DESERIALIZATION-ERROR`. It is used
for nonmixed complex particles, SOAP Body/Header and the RPC wrapper. Original
retained XML remains unchanged. The existing independent XML-context test checks
80 documents and ancestor context in both bindings and directions.

`test_soap_container_whitespace.py` checks document and multi-parameter RPC
containers, exact scalar CR/TAB/LF values, marker values and negative Body/Header/
RPC-wrapper text (including NBSP). Its two explicitly named P6 requirements retain
additional independent failures, without skips or expected-failure decorators:

- Explicitly selected single body parts can serialize a scalar round-trip result
  without a Body; the getter expects part-keyed input although deserialization
  returned an unwrapped scalar. With a declared header, document messages exhibit
  this missing-body result as well.
- RPC deserialization iterates every message part instead of the selected body
  parts, requiring a declared Context header again as an RPC body parameter.
- A single RPC parameter deserializes to an unwrapped scalar, while
  `serializeRpcValue()` requires `reference<hash<auto>>`, yielding `RUNTIME-TYPE-ERROR`.

The old HEAD WSDL and old native module reproduce the header/body failures:
`/tmp/wsdl-p3-11-container-baseline-rows.json` and
`/tmp/wsdl-p3-11-container-rows.json` have the same 16 affected message/stage pairs.
The baseline worker and WSDL are under `/tmp/wsdl-p3-11-container-baseline`.
These are P6 binding selection/part representation requirements, not regressions
introduced by native whitespace handling. They remain failing tests until P6.

The local Qore-authored `test/test.wsdl` i4452 fixture previously supplied string
and CDATA values to a nonmixed wildcard type. XSD 1.0 Part 1
[section 3.4.4, clauses 2.3–2.4](https://www.w3.org/TR/xmlschema-1/#cvc-complex-type)
requires `mixed="true"` for those character values. Its declaration now states
that intended content model; the values are unchanged. The committed independent
fixture test checks both the old nonmixed and corrected mixed declarations with
text, CDATA and child-element inputs using libxml2 and Xerces (six documents).
No upstream W3C/CXF fixture was altered. The local fixture SHA-256 changes from
`126b4e18b3d839bc73195acec0b585d8bd1317567d917d8b0655d619546d52cc` to
`e5372621234b027f112780ccde21365d6baf09fdc359f8d4da841a2131d7d8f5`.
The existing SOAP suite passes with that valid declaration.

The single-parameter RPC reproduction was also rerun with the old WSDL/native
module. `/tmp/wsdl-p3-11-scalar-rpc-baseline-rows.json` records the same eight
valid-input serialization failures. Its additional acceptance of invalid RPC
container text is corrected by the current element-content boundary validation.
