# P5-19e native annotation grammar

Copyright (C) 2026 Qore Technologies, s.r.o.

Based on `6dfcc3b`, this increment fixes two independent libxml2 defects in
`xmlSchemaParseAnnotation`: a local-name check rejected legal foreign `lang`
attributes, and documentation omitted `source` URI validation. The correction
uses expanded names and the existing checked attribute validator. It does not
load annotation resources or alter arbitrary annotation payloads.
See [implemented design](../../design/native-schema-annotations.md) and
[XSD 1.0 §3.13.2–3](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cAnnotations).

The authored [117-schema matrix](fixtures/annotations.json) contains 54 valid
and 63 invalid cases, independently checked with pinned Xerces-J 2.12.2. All
three native APIs agree; the Qore regression has 415 assertions and verifies
that validation does not alter the input document. Schema, notation and facet
placements exercise identical annotation rules. URI/language boundaries,
foreign attributes, schema-qualified attributes, invalid content and arbitrary
mixed payloads are covered. No validator disagreement is hidden.

Acceptance: 20 affected Qore suites, all 66 dependency-provider tests and three
Python supplements pass. The new behavioral probe triggers AUTO fallback and
SYSTEM rejection on an otherwise repaired library with only the annotation
bugs retained. Corrected sources reconfigure without timestamp changes. Existing
allocation-failure regression tests pass. The focused direct-ELF Valgrind run
with signals and PCRE2 JIT disabled has zero errors and zero lost memory.
Debug build and native documentation are clean. All four corpus reports are
byte-identical to P5-19d, retaining all previous classified failures.

The [inventory](P5-19e-validation.json) records commands, input/log hashes and
results; [full audit](audits/P5-19e-native-annotations.md) covers all 62 items:
18 Pass, 44 N/A, zero Fail. Artifacts are under
`/tmp/wsdl-p5-19e-schema-annotations/`; provider builds are under
`/tmp/qore-xml-libxml2-test-ocahwgys/`.

The installed Qore library still matches the frozen verified `8c0c22c15` runtime.
Main Qore remains read-only. No installation or push. Unrelated
`test/cmake/__pycache__/` is excluded. The independently reproduced
[WSDL annotation/ID grammar gap](p5-wsdl-annotation-finding.md) is the next P5
increment, followed by key/unique/keyref and complete typed accounting. P6–P9,
including Python CI wiring and supported-environment acceptance, remain open.
