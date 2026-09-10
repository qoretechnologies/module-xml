# Native schema position evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

The P4-03 schema matrix exposed a native duplicate-choice false acceptance.
`xmlFAEqualAtoms()` compared token strings without source positions;
`xmlFAComputesDeterminism()` then coalesced equal transitions with the same target.
An element declaration pointer is insufficient: two references to one global
element or two uses of a shared group still represent distinct particle positions.
[XSD 1.0 unique particle attribution](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-nonambig)
requires those uses to be distinguishable from the preceding input and current name.

The checked private-dependency correction retains `(parent use, particle address)`
identity independently of callback declarations. A first implementation assigned an
identity per emission; review found that libxml2 emits some counted source positions
more than once. The final map reuses their identity. Tests cover unbounded groups
with minimum two and nested repeated single positions, as well as ambiguous choices,
local/global declarations, shared groups, substitution collisions, all members and
wildcard namespace alternatives. Both DOM and XmlReader paths check schema error
categories, preserved content values, invalid integer rejection and recovery. The
final focused suite has six cases and 93 assertions and passes all four modes.

The 12-schema native recheck is preserved in
[P4-04-native-attribution.json](P4-04-native-attribution.json). The duplicate-choice
case now rejects correctly. Three failures remain, assigned to the next P4 native
counted-attribution/component increment: exact-boundary and nested-count-2 are
still falsely rejected because automaton conflict analysis ignores counter
feasibility; empty-language-component is still falsely accepted. Additional source
inspection refines the earlier explanation of the latter: after an empty choice,
its sibling's states become unreachable and are removed before the final automaton
check. Preserving transition identity alone cannot enforce that nested component's
constraint. The original four-failure record is retained as historical evidence;
none of these three remaining failures is counted as a passing native requirement.
The independent lxml and Xerces binaries and their expected discrepancy lists are
unchanged.

CMake's nine-case identity probe rejects incomplete system backports and accepts a
complete backport even when it advertises an older release number. The private
static build uses the same probe. The 26 provider/source-distribution tests cover
AUTO/SYSTEM/BUNDLED selection, offline sources, cross-build verification, unchanged
source hashes, stable reconfiguration, installation ownership and unexpected-source
rejection. The private allocation fixture exercises all 327 allocation failure
points, map growth and re-entry without allocation, then verifies clean reuse and
zero live allocations. It is compiled as an internal libxml2 fixture; its internal
automata API use is not an application API recommendation.

Valgrind runs the focused identity and existing occurrence suites with Qore signals
disabled, debugging enabled, and the previously authorized PCRE2 JIT test switch.
There are zero memory errors, zero definite/indirect/possible losses and no
suppressions. LLVM and the dynamic loader retain 116,230 reachable bytes in 46
blocks; these are reachable process-lifetime allocations, not lost allocations.
An initial run classified reachable allocations as errors; its full stacks remain
in the local log. The known isolated core DWARF diagnostic remains P9-owned.
The standalone allocation fixture is also checked under Valgrind, without Qore or
LLVM runtime allocations. Full results, exact binaries and source hashes are in
[P4-04-validation.json](P4-04-validation.json).
