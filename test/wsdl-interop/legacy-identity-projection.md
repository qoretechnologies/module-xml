# Approved legacy anySimpleType identity projection

Copyright (C) 2026 Qore Technologies, s.r.o.

Approved on 2026-09-15: preserve the existing `preserve_types=False` scalar
mapping, and reject serialization when its type projection violates identity
constraints. Use native type retention or complete XML carriers for lossless
forwarding when identity depends on explicit type distinctions. This decision
is independent of the approved nil and skipped-subtree interpretations.

For example, two `anySimpleType` elements constrained by `unique` may contain
an explicit integer `1` and an explicit string `1`. Their input identity values
are distinct. Legacy decoding yields `{a: 1, b: "1"}`, but its existing serializer
emits both as untyped text. Instance validation must reject the duplicate string
identities. Changing legacy scalar inference is a separate compatibility change.

The P5-20f prototype explicitly asserts this one expected legacy rejection in
its 165-case matrix (2,667 assertions), separately from native/XML lossless paths
(191 assertions). Those paths exercise source/saved schemas and ordinary,
saved and soft native providers. The rejection is not counted as a lossless
round-trip. Original diagnostic failure logs remain unchanged.

The prototype and typed accounting are retained in
`/tmp/wsdl-p5-20f-identity-tuples/`. This decision approves the policy; repository
WSDL instance tuple implementation and its remaining consumer, cancellation,
performance and final P5 acceptance checks are still in progress.
