# Detached schema namespace ownership

Copyright (C) 2026 Qore Technologies, s.r.o.

`XsdAbstractType` stored its namespace registry as a weak reference in both
constructors. `XsdSchema::addSchemaString()` and external schema parsing create
temporary registries and restore the caller's registry when they finish. A
returned type could therefore survive its registry. Raw serialization and
namespace lookup then raised `OBJECT-ALREADY-DELETED`, including while the
containing schema still existed after an incremental addition.

The fix replaces those two weak stores with owned references. Namespace maps
and XML conversion rules are unchanged. Existing `Serializable` indexing and
Qore cycle collection preserve and release the builtin-cache cycle; no manual
cycle breaking or duplicate namespace cache is introduced. This repairs the
public component lifetime contract rather than changing an XSD validity rule.

The final regression suite has 13 cases and 105 assertions. Against the exact
previous WSDL source from `d5985db`, 12 cases fail: deleted registries or premature
destructor notifications establish the cause. The exception-cleanup case also
passes before the fix because its registry remains in local scope until unwind.
With the fix, all cases pass. Baseline and final logs are
`/tmp/wsdl-p3-32-namespace-ownership-final-baseline.log` and
`/tmp/wsdl-p3-32-namespace-ownership-final.log`.

Tests cover direct and cached builtins; standalone restricted types; elements
and attributes with provider/value constraints; distinct same-name types in
sibling namespaces; nested import/chameleon include scopes; failed additions
and retry; binary and raw indexed reconstruction; two QName enumeration
spellings with different identities; serialization failure; constructor failure;
exception and program interruption cleanup; and four concurrent independent
copies coordinated through bounded queues. Eight destructor-counted cache
cycles verify retention while a caller owns a type and release afterward.
The test-only namespace subclass contains a nonserializable Counter, so its
serialization failure also checks that failed traversal preserves live ownership.

The existing independent declaration/value/list/union and provider matrices
exercise both actual SOAP bindings and directions. The broad survey and strict
adjudicated report retain all failures assigned to later phases. Final gate
counts, exact hashes, Valgrind results and the full audit are recorded in
[EXECUTION.md](EXECUTION.md). No native XML or Qore change is part of this
increment. Ordinary QName instance namespace conversion remains the next P3 work.
