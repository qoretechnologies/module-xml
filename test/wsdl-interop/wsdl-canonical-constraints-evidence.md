# P5-18b WSDL canonical numeric declarations

Copyright (C) 2026 Qore Technologies, s.r.o.

WSDL previously validated only a declaration's original spelling. XSD 1.0
[e-props-correct.2](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#e-props-correct)
and [a-props-correct.2](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#a-props-correct)
also require canonical validity. P5-18a corrected native schema construction;
this increment applies the numeric/boolean checks to WSDL after type resolution.

The selected atomic/list/union identities supply canonical spellings without
losing arbitrary-precision digits or the declaration's namespace context. A
second conversion verifies validity but never replaces the first computed value.
For a union of boolean-pattern-`1` and string, canonical `true` can select string;
the declaration still retains its original boolean identity and lexical `1`.
See the [implemented design](../../design/wsdl-canonical-constraints.md).

Acceptance on installed Qore `8c0c22c150c6e51ed09976ca99d74041ec074620`, frozen
under `/tmp/wsdl-p5-17b-identities/final/runtime`, with local Debug XML and WSDL:

- All 152 Qore suites pass, with complete summaries and no warnings or errors.
- The new unit suite passes four cases and 1,646 assertions; the real HTTP suite
  passes one case and 88 assertions. It exercises SoapClient, SoapHandler,
  SoapDataProvider, saved schemas/providers, both preservation policies, invalid
  requests and responses, omitted attributes and deterministic server shutdown.
- All 16 supplements pass: both suites in forced AST/IR/JIT/tiered modes and
  AOT, independent source/AOT matrices, 17 survey tests, native value-space,
  selected-union identity and native numeric declaration matrices. Compilation
  thresholds are one, with synchronous JIT compilation enabled.
- All 396 declaration schemas (202 valid, 194 invalid) agree with pinned
  Xerces-J 2.12.2. The independent WSDL worker emits exactly 2,804 records:
  1,188 construction checks and 1,616 request/response payloads across actual
  SOAP 1.1/1.2 bindings and original/saved services. Payload values and expanded
  QName identities match the source independently; Xerces validates every output.
- Scope restoration and unpublished constraint values survive conversion errors,
  program interruption and thread cancellation during canonical assessment.
- Both full corpus surveys and strict coverage reports equal P5-18a at every
  case and stage. Native mode still has 2,096 assessed valid directions; legacy
  mode has 2,092 and four tracked failures. Neither existing later-phase failures
  nor unassessed typed-preservation records are reclassified as passing.
- The affected WSDL AOT module and WSDL/native API documentation build cleanly.

Commands are in the [interop README](README.md#wsdl-canonical-numeric-declarations-p5-18b).
Logs, exact commands, source hashes and corpus comparisons are inventoried in
[P5-18b-validation.json](P5-18b-validation.json); raw evidence is under
`/tmp/wsdl-p5-18b-declarations/`. The [full audit](audits/P5-18b-wsdl-canonical-constraints.md)
records all 62 checks: 15 Pass, 47 N/A, zero Fail.

This increment changes Qore source only; it needs no additional native Valgrind
run and makes no main-Qore change, installation or push. Empty-element default
projection, float/calendar/binary canonical spellings, key/unique/keyref, complete
typed-preservation accounting and P6–P9 remain required work. The instance PSVI
[investigation](default-identity-investigation.md) is not resolved by declaration
validation.
