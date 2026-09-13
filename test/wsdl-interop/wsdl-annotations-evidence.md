# WSDL schema annotation acceptance (P5-19f)

Copyright (C) 2026 Qore Technologies, s.r.o.

Based on `9ed2230`, this increment adds ordered annotation grammar and declaration
ID checks before component grouping. It fixes heterogeneous repeated-child
containers and complex-type documentation extraction, preserving mixed text order
and accepting empty documentation. The native `normalize_xsd_uri()` API provides
XSD URI assessment without dereferencing or changing URI value identity.
See [implemented design](../../design/wsdl-schema-annotations.md),
[root cause](p5-wsdl-annotation-finding.md), [inventory](P5-19f-validation.json)
and [all 62 audit checks](audits/P5-19f-wsdl-annotations.md).

The shared 117-schema matrix includes 54 valid and 63 invalid schemas and agrees
with pinned Xerces. WSDL tests cover independent document ID scope, imports,
chameleon includes, failed additions, cancellation, event-barrier concurrency,
saved schemas/providers, both decoding modes and actual SOAP binding contracts.
Twenty-two additional complex schemas test empty, attributed, repeated, mixed,
CDATA and Unicode documentation on original and reconstructed schemas.

Final validation:

- 55 affected Qore suites pass without warnings/errors, plus `xsd-compliance.qtest`.
  A preceding broad 172-suite run passed before the final documentation followup;
  it is not represented as a full final-revision run.
- The annotation suite passes 1,362 assertions in AST, IR, JIT and tiered modes.
  URI tests pass 35 assertions in each mode. Four Python supplements pass,
  including survey tests and independent annotation/NOTATION validation.
- Actual annotated SOAP 1.1/1.2 HTTP contracts pass 440 assertions through
  original/saved services and both client/server directions.
- Direct-ELF Valgrind on the final annotation suite and unchanged native URI API
  reports zero errors and zero definitely, indirectly or possibly lost bytes.
  URI has 117,500 reachable bytes; annotation has 139,032 reachable bytes.
- Local Debug native build, module/WSDL documentation and metadata targets pass.
  Existing native allocation tests include anyURI computed-value allocation;
  all 66 provider checks passed in the immediately preceding native increment.
- Both-version diagnostic surveys and strict selected coverage in both decoding
  modes have exactly the parent's results; only the WSDL source hash changes.
  Exit success does not imply complete corpus conformance.

Commands, source/fixture/report/log SHA-256 values and individual results are in
the inventory. Artifacts: `/tmp/wsdl-p5-19f-wsdl-annotations/`, with the final
revision under `final/`. Tests use the fixed frozen Qore ELF and library under
`/tmp/wsdl-p5-17b-identities/final/runtime`, `-b --enable-debug`, and local
`QORE_MODULE_DIR=build-debug:qlib`. Ordinary runs retain PCRE2 JIT; Valgrind uses
`QORE_PCRE2_NO_JIT=1`. Installed Qore library SHA-256 matches the frozen library.
The main Qore checkout remains clean and read-only; no installation or push.

The independent [scalar URI/language gap](p5-wsdl-uri-language-finding.md) is the
next P5 increment. Key/unique/keyref and complete typed-preservation accounting
remain open, including 24 recorded NOTATION identity/legacy-projection failures
and 48 classified default-context oracle disagreements. P6-P9, including Python
CI wiring, remain required. No question is pending.
