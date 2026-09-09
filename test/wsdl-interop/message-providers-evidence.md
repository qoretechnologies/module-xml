# Complete message provider evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

The P3-42 increment makes complete native message providers check supplied part
instances after their normal field conversion. The public contract and example
are in [the implemented design](../../design/wsdl-message-providers.md).

## Reductions and root causes

The scalar reduction `/tmp/wsdl-p3-42-preflight.qr` found ten false acceptances
across original/reconstructed providers: lexical ENTITY values passed the generic
HashDataType but failed their SOAP instance conversion. The new suite against
committed parent `a6bb218` reproduces seven failing cases and two passing cases:
`/tmp/wsdl-p3-42-before-unit.log`, with the immutable parent source and test in
`/tmp/wsdl-p3-42-before`.

Retaining the schema context also exposed a component-serialization defect.
The generic serializer cannot resolve the private recursive
`list<hash<XsdEmptiabilityInfo>>` type. Groups and complex types now serialize an
ordinary-container representation and restore the private type explicitly.
The final tests retain shared declarations and reject malformed metadata.
The serialization hooks read live members rather than reserializing the hook's
already encoded member references.

An initial field projection attempted to call isMandatory() after its field had
been removed. Current checks follow the retained fields, including optional
projections. Direct adapter construction now creates the same fields as the
message factory.

The optional-group reduction also confirms the already assigned P4 occurrence
failure: an absent optional group still requires its flattened child. It is
preserved in `/tmp/wsdl-p3-42-optional-group-reduction.qtest` and
`/tmp/wsdl-p3-42-optional-group-reduction.log`. This increment tests group metadata
independently and does not claim group occurrence conformance.

## Verification

All Qore commands use `/tmp/wsdl-core-date-env.sh`, `qore -b --enable-debug`,
local WSDL/xml and the frozen Debug core/DataProvider. The final new suite passes
nine cases and 226 assertions in AST, IR, JIT and tiered modes. Logs are
`/tmp/wsdl-p3-42-mode-<mode>.log`.

The regression gate passes 93 suites. The final tested suite union contains
957 cases and 36,372 reported assertions. The initial gate ran the new suite
with 219 assertions; the final seven malformed-metadata assertions were then
added and passed in all four modes. The unchanged 92 suite results plus the
updated new suite are recorded in `/tmp/wsdl-p3-42-final-verification.json`.
Original gate output remains `/tmp/wsdl-p3-42-final-gate.log` and
`/tmp/wsdl-p3-42-final-xml-gate.json`.

The unchanged independent ENTITY matrix passes both methods in 137.108 seconds:

| Coverage | Results |
| --- | --- |
| Actual SOAP contracts | 72, across 12 datatypes, three layouts and both bindings |
| Outbound consumer/sample outcomes | 2,880 |
| Independently valid emitted documents | 888 |
| Inbound/consumer outcomes | 9,216 |
| Independent inbound document verdicts | 7,392: 6,528 valid and 864 invalid |
| Total document verdicts | 8,280 |

Every schema, row identity, repeated occurrence, exact value and reachable stage
remains required. The final matrix log is `/tmp/wsdl-p3-42-entity-final.log`.
`/tmp/wsdl-p3-42-entity-artifacts` retains 84 files; all 72 WSDL byte sequences
match P3-41. Inventory `/tmp/wsdl-p3-42-fixtures.json` has SHA-256
`0730f28d29206e2021a6cae0f3b0e12a1890a648fb9312735a5b9c6b42384d98`.

The both-version survey and strict report have identical outcomes to P3-41:
all 2,411 raw rows and all 293 coverage cases compare equal. The strict selection
has no failure; the broader report retains 144 failure signatures. The only
report change is the WSDL source hash. See `/tmp/wsdl-p3-42-comparison.json`.
Fifteen survey test methods pass. The fourteen coverage methods retain exactly
the two previously tracked P6-selected-binding-version failures for SOAP 1.1
request/response envelopes. No skips or expected-failure annotations were added.

The catalog example and Doxygen docs-module build pass without warnings or
errors. No C++ changed. Debug native xml still has SHA-256
`95ed6b98adc9c3171883c2c5d8e848431d1bf1720961faca8502ca54466e5824`;
no new Valgrind run is required. The main Qore checkout remains clean develop
at `4e049e0d8`.

Final WSDL source SHA-256: `d59400ff0a83278d26e3d820e8a235c4d44fdf75c3a9919507ef5cc51c74f20f`.
See [the complete 62-check audit](audits/P3-42-message-providers.md).
Native sample generation is still the next P3 increment. P3's remaining scalar
work and P4-P9 acceptance remain open; these results do not close the full plan.
