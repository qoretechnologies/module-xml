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

The repository matrix `test/wsdl-identity-tuples.qtest` explicitly asserts this
one expected legacy rejection, separately from the 191 assertions in
`test/wsdl-identity-lossless-paths.qtest`. Those lossless paths exercise source/
saved schemas and ordinary, saved and soft native providers. The rejection is
not counted as a lossless round-trip. Original diagnostic failure logs remain
unchanged in `/tmp/wsdl-p5-20f-identity-tuples/`.

Scoped tuples are now integrated in WSDL; their acceptance is tracked as P5-20j.
Complete P5 typed/infoset accounting remains separate. See the
[implemented design](../../design/wsdl-identity-tuples.md).


The instance-attribute matrix additionally records two legacy `anyType` cases
where empty untyped rows become strings and output inference adds duplicate
`xsi:type` values. The previous committed WSDL emitted invalid XML for those
rows. Tuple validation now rejects that projected document. Native preservation
mode retains XML-data hashes and keeps the type attribute absent; XML carriers
also forward the original valid document. This preserves the existing legacy
inference contract and does not count those two rejections as lossless success.
