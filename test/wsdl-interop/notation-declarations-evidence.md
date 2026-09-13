# WSDL notation declaration evidence (P5-19b)

Copyright (C) 2026 Qore Technologies, s.r.o.

The WSDL schema model previously recognized `notation` as a top-level schema child
but discarded its declarations. This increment retains their expanded names and
public/system identifiers through the existing composition and reconstruction
paths. It provides the declaration table required by NOTATION value conversion.

`XsdNotationInfo`, `XsdNotationRegistry` and `Namespaces::getNotation()` provide
validated, typed declaration metadata. Names and IDs use NCName validation after
whitespace collapse; at least one public/system identifier must be present, and
empty strings remain distinct from absent identifiers. Public identifiers follow
the schema token rule, including strings outside the DTD PubidLiteral grammar.
Unknown unqualified/schema-namespace attributes and duplicate expanded names
reject. Foreign attributes and an optional direct annotation remain legal.

Imported and chameleon declarations share the completed registry before type
resolution. Failed additions restore it through previously retained contexts,
including when a newly retrieved include was processed before the failure.
Saved schemas reconstruct from sources; detached namespace contexts retain the
table directly. Corrupt saved maps, mismatched keys and malformed fields reject
with `DESERIALIZATION-ERROR`. Returned hashes cannot mutate stored declarations.

The requirements and implementation are described in the
[durable design](../../design/wsdl-notation-declarations.md).

Acceptance on the installed/frozen fixed Qore `8c0c22c15`, local WSDL and Debug XML:

- All 167 Qore regression suites pass with debugging enabled.
- The new suite passes 391 assertions across 10 cases, including saved schemas,
  namespace copies, duplicates, imports/includes, rollback, concurrent independent
  schema copies, cancellation/retry and both SOAP binding descriptions.
- The independent 54-schema matrix checks native and WSDL outcomes, six original/
  saved/context metadata paths per valid schema, exact rejection categories and
  pinned Xerces 2.12.2. All verdicts agree; no cases are skipped.
- Eight supplements pass: AST/IR/JIT/tiered execution and four Python suites
  (notation declarations, survey, QName declarations and native NOTATION).
- Both-version diagnostic surveys and strict coverage in legacy/native modes retain
  exactly the parent's results. Only the WSDL source hash changes in the reports.
  Existing assigned failures stay visible; a successful survey is not complete
  SOAP conformance.
- Native and WSDL documentation plus WSDL metadata generation complete without
  warnings. No native code changed, so no additional Valgrind run is required.
- Every applicable item in the full 62-item audit passes; see the
  [audit](audits/P5-19b-notation-declarations.md) and [inventory](P5-19b-validation.json).

Commands, frozen hashes and logs are retained under
`/tmp/wsdl-p5-19b-notation-declarations/final/`. The JSON inventory records the
verified final inputs and results. No installation, push or main-Qore mutation.

This is declaration storage acceptance. NOTATION value conversion, its distinct
primitive identity, enumeration-derived type uses, defaults/fixed, list/union and
provider/HTTP integration remain the required next P5 increment. Key/unique/keyref
and complete typed-preservation accounting also remain open before P6.
