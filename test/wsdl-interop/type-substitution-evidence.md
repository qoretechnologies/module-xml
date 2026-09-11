# P5-03 instance type derivation and controls

Copyright (C) 2026 Qore Technologies, s.r.o.

The parent implementation (`460349d`) checked only component identity or an
immediate complex extension. It did not retain effective instance `block` or
`abstract` controls. The four-case reproducer in `/tmp/wsdl-p5-03-reduce.qr`
recorded a rejected transitive extension, an accepted blocked extension and
accepted abstract element/type instances in `/tmp/wsdl-p5-03-before.log`.

## Requirements and implementation

XSD 1.0 Structures [Type Derivation OK (Complex)](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-ct-derived-ok)
and [Type Derivation OK (Simple)](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-st-derived-ok)
define identity and ancestry checks with a fixed exclusion set. Simple derivation
also considers actual union members. [Element Locally Valid](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-elt)
requires a resolved instance QName and a compatible selected type. Complex
selections combine element and declared-type exclusions. An intermediate
ancestor's block does not change that set. Abstract selected types cannot validate
an instance; an abstract element requires a different member declaration.

Source parsing now retains applicable defaults and explicit overrides, including
empty overrides. References copy global declaration properties. The shared
selection helper consumes only the checked type annotation in a private working
value; direct type APIs and retained XML validation use the same checks.
The [implemented design](../../design/wsdl-type-substitution.md) documents the
graph traversal, namespace ownership and public metadata.

Traversal review found two avoidable costs: duplicate edges allocated duplicate
pending pairs, and unrelated simple chains repeatedly scanned the same base
chain. Pairs are now deduplicated on enqueue, and base union lookup caches all
visited restrictions, including an absent union. Regressions exercise 1000-step
complex and unrelated simple chains, 10000 repeated member references, a shared
40-level union graph and a defensively mutated cycle. These are correctness and
termination tests in a Debug runtime, not performance benchmarks.

## Independent and integration evidence

`test_type_substitution.py` generates 104 schema/type cases: 62 valid and 42
invalid instance selections. Original schemas compile in both pinned independent
validators (lxml 6.1.1 with libxml2 2.12.10, and Xerces-J 2.12.2). Both agree with
the expected input verdicts; there is no oracle disagreement in this matrix.
This increment does not change the module's private libxml2 dependency.

Each case uses actual SOAP 1.1 and SOAP 1.2 bindings, original and serialized
service objects, and requests and responses. The resulting 832 worker rows
require 336 rejections in each conversion path, with exact serialization or
deserialization error categories. All 992 valid native-wrapper and retained-XML
outputs independently validate. Assertions check expanded envelope, payload and
type names and exact native values. Native output must include `xsi:type` when
the selected type differs from its declaration; retained XML keeps an explicit
annotation even for identity. Missing, duplicate and extra worker rows fail.

The executable Qore suite covers declaration syntax, imports, copies, default
restoration after errors, direct APIs, optional absent abstract references,
anonymous selected components, legacy adapter metadata and synchronized shared
schema consumers. An executed invoice example checks an exact large decimal
with an explicitly selected restricted type.

## Development findings retained as diagnostics

The first broad run exposed five failures. Their causes and repairs were:

- Non-hash native objects reached metadata access before normal value validation.
  The selection helper now guards that access; binary and QName negative tests
  retain their intended error categories.
- Detached union probes omitted the namespace used by the emitted type QName's
  value. A boolean member could consequently change from `true` to `1`. The
  probe now carries both attribute-name and QName-value namespaces from its
  originating serializer.
- IEEE and array test callers passed detached fragments without their actual
  enclosing namespace context. Those fixtures now supply the output registry's
  bindings, and a negative IEEE case requires unbound wire prefixes to reject.
  Production namespace inheritance still has its documented attribute-name
  scope; no guessed wire-prefix fallback was added.

The first matrix expected an extra WSDL part wrapper in native results. The
documented single-part projection omits that wrapper, so the test was corrected
to assert the established shape. Earlier malformed test-call references were
replaced with closures. These diagnostic runs are not counted as passes.

## Remaining plan ownership

This increment completes instance derivation and block/abstract controls.
Substitution-group membership and element final exclusions, complete native
selected-type retention, wildcard/mixed/generic content, nil/default/fixed and
document identity constraints remain P5 work. The existing flat native return
shape is unchanged; retained XML preserves the original type annotation.
The current corpus continues to report remaining failures. P6-P9 retain their
full binding, protocol, attachment, environment and CI requirements.
