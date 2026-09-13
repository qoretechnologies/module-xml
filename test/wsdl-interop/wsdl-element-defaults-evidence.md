# WSDL canonical empty-element default evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

P5-18j builds on native prerequisite `3767c18`. The approved interpretation is
recorded in [the decision](default-identity-investigation.md); the
[implemented design](../../design/wsdl-element-defaults.md) documents the public
carrier, namespace boundaries and legacy/opt-in behavior.

## Root causes and corrections

The WSDL decoder sent an empty element directly to the selected type converter,
without applying its declaration's canonical constraint. This rejected 66 valid
inputs in the initial 200-document reduction. Applying a default also requires
separating declaration QName scope from instance attribute scope; replacing the
entire instance namespace context would reinterpret valid attributes.

`XsdDefaultValue` retains the empty occurrence and its complete converted value
when preservation is explicitly enabled. This is necessary for fixed unions:
canonical boolean text `true` assessed as an actual string cannot subsequently
be written as explicit text and still compare equal to the declaration's boolean
fixed value. Checked serialization instead emits the empty occurrence with its
actual type and validated attributes. Ordinary decoding remains the default.

The integration regressions found and fixed two issues before acceptance:
ordered mixed text must not be reduced to its first scoped fragment, and the
new provider wrapper must preserve existing names/base types/tags. The fixed
provider malformed-state test locates the nested constrained provider rather
than assuming it remains the outermost serialized object. Saved `NOTHING`
carrier values account for Serializable's omission of absent-valued members.

## Reproducible coverage

- `test/wsdl-element-defaults.qtest`: 11 cases, 1,077 assertions. Actual-type
  source/canonical restrictions for ten atomic families; empty/comment/CDATA,
  absent/nil/whitespace distinctions; fixed union string/QName identities;
  declaration and attribute QName scopes; lists, empty lists/strings and anyType;
  mixed/simple content attributes and required particles; defaulted IDREF closure;
  saved carriers/providers, variants, malformed metadata and cancellation recovery.
- `test/wsdl-element-defaults-http.qtest`: 100 assertions through real SOAP 1.1
  and SOAP 1.2 bindings, saved request/response providers, live clients/handlers,
  ordinary SoapDataProvider requests, malformed request rejection and recovery.
  SoapDataProvider keeps its existing ordinary request/legacy response API;
  SoapClient and handler tests exercise explicit preserved selected-type values.
- `test/wsdl-interop/test_wsdl_element_defaults.py`: 40 schemas, 200 documents,
  3,200 binding records across both versions, directions, decoding modes and
  original/reconstructed services. The 1,760 emitted payloads are checked with
  pinned Xerces 2.12.2. All 120 expected output disagreements derive from the
  previously documented time/date canonicalization defects; legacy explicit
  default text is independently assessed as written. The original fixture and
  native verdicts remain unchanged. Repeated output variants are counted as
  distinct consumer checks, not as additional source documents.

## Acceptance

All 165 Qore suites and 18 supplemental runs pass without warnings or errors.
Both new suites pass all four forced execution modes and compiled WSDL; the
independent binding matrix passes with source and compiled WSDL. The existing
fixed-value suite passes 177 assertions. WSDL AOT compilation and both affected
Doxygen targets pass. No C++ changed, so this increment requires no additional
Valgrind; P5-18i retains its four clean native runs.

The Qore gate's broad hash manifest included the supplemental Python matrix,
whose calendar-oracle expectations were corrected while the Qore suites ran.
Every executed Qore input remained unchanged. Final Python sources were frozen
and verified in the separate supplemental run; the inventory records the exact
changed hash rather than claiming the entire broad manifest stayed unchanged.

Both-version surveys and strict coverage retain every parent validity count,
failure, stage and scope record in legacy and preservation modes. Four
GlobalElementDefault message payloads per mode change as intended: legacy mode
materializes `theDefaultValue`, while preservation mode emits an empty-element
tag for its carrier. Every other case field matches P5-18i exactly. This is not
complete WSDL/SOAP conformance: remaining typed accounting, NOTATION and
key/unique/keyref are P5 work; P6–P9 remain required.

See [inventory](P5-18j-validation.json) and
[all 62 audit results](audits/P5-18j-wsdl-element-defaults.md): 20 Pass, 42 N/A,
zero Fail. Reproducible raw logs and manifests are under
`/tmp/wsdl-p5-18j-wsdl-element-defaults/final/`. Tests use local Debug XML and
frozen fixed Qore `8c0c22c15`, verified to match the installed ELF/library.
No main-Qore mutation, installation or push. Qore suites join the existing CI
qtest discovery; mandatory Python/environment coverage remains a P9 deliverable.

The independently reproduced [NOTATION gap](p5-wsdl-notation-finding.md) is the
next required implementation increment, not an unsupported-scope designation.
