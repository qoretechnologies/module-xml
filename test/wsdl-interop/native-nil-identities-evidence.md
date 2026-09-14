# P5-20e native nil identity evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

The user approved nil-as-missing on2026-09-14 and explicitly confirmed “count it
as missing”. The question is resolved. See the
[interpretation record](nil-identity-interpretation.md) for the precise scope,
W3C references, corrected historical evidence and independent oracle findings.

## Implementation and coverage

The native matcher previously rejected nil fields because it required a
precomputed value before recording a field match. It now records an owned
value-less key for a selected nil node, so cardinality still rejects a second
node. Tuple qualification excludes such missing values before comparison or
keyref publication. Simple-content typing, invalid nil content, empty-string
values and XSD1.0 key declaration restrictions remain enforced. See
[implemented design](../../design/native-nil-identities.md).

The148 schema/document pairs comprise96 valid and52 invalid instances.
The native reader, parser and DOM suite passes497 assertions. Coverage includes
simple/complex content, composite references, missing/one/multiple fields,
nil before/after values, duplicate values, defaults, empty strings, attributes
on nil owners, shared constraints and XPath unions. DOM content is unchanged.
Pinned Xerces agrees on119 cases;27 nil-keyref null-tuple differences and2
same-node union double-counting defects are independently documented. Oracle
outcomes and expected module behavior remain separate, explicit assertions.

The original W3C idF018 schema and instance bytes, including CRLF endings, remain
unchanged. It is invalid because its untyped uid declaration supplies an
inadmissible anyType field. A separately identified derivative adds only the
anySimpleType declaration from WG2219; its instance is unchanged and valid.
This corrects the preliminary claim that the original historical expectation
established duplicate-nil behavior.

## Allocation and provider selection

The new nil path uses existing sequence/key ownership and normal cleanup.
Two allocation branches previously reported errors with a NULL validation
context; they now report through the active context. The direct harness fails
each of four allocation positions, both once and persistently, verifies the
memory-error category and cleanup, and succeeds on the subsequent recovery.
Native Valgrind frees all361 allocations with zero errors. The complete Qore
matrix under Valgrind has zero errors/lost bytes and117,480 runtime-global
reachable bytes, with signals and PCRE2 JIT disabled.

The ten-case configure probe checks DOM and reader behavior with context reuse.
A real system fixture containing every prior fix fails nil identity semantics;
AUTO chooses the corrected private dependency, SYSTEM rejects the failed probe,
and a fully fixed shared fixture remains usable. Reconfiguration is idempotent,
source-distribution inputs are registered, and all74 provider tests pass.

## Acceptance scope

The isolated validation snapshot overlays only this native increment on
committed43c9923 and uses the local Debug XML binary with the frozen runtime.
Its54 affected Qore suites pass. All four corpus commands pass and their
reports are exactly unchanged from the prior committed-WSDL results: legacy
and native preservation modes remain separate, both SOAP versions are assessed,
and existing diagnostic failures remain visible. Survey unit tests and native
documentation builds pass without warnings/errors.

The full62-item audit has18 Pass,44 N/A and zero Fail. See
[P5-20e-validation.json](P5-20e-validation.json) for source/runtime/fixture hashes,
results, guide hashes and exact commands, and
[full audit](audits/P5-20e-native-nil-identities.md). Artifacts and reproducible
scripts are in `/tmp/wsdl-p5-20e-nil-identities/`; `native-snapshot/` holds the
independent committed-source input and `final/` holds its gate/corpus results.

P5-20c WSDL components remain uncommitted pending the separate Qore serialization
source-lifetime fix. The installed runtime has not changed and no Qore source
was modified here. WSDL scoped tuples must use this approved interpretation;
that work, complete typed accounting and P6-P9 remain outstanding.
