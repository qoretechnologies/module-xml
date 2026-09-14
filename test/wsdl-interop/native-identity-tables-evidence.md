# P5-20g native identity table evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

This independent native prerequisite repairs three libxml2 table-merging defects
found while implementing P5-20f WSDL instance tuples. It implements
[XSD 1.0 Structures §3.11.5](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#sic-identity-constraint),
without a new interpretation or a public representation change.

## Root causes

The old `xmlSchemaBubbleIDCNodeTables()` appended a child's distinct entry only
when the receiving table still contained an older entry. Earlier sibling
conflicts could empty that table, silently losing a later distinct key.
`xmlSchemaIDCFillNodeTables()` also treated local entries as ordinary inherited
conflicts rather than giving them precedence. Finally, bubbling copied a child's
rejected-entry list to its parent, although those entries were absent from the
child's normative table. They could incorrectly conflict with another branch.

The correction retains distinct entries in empty receiving tables, gives local
entries precedence, and limits conflict markers to their receiving element.
Ancestor/descendant selector overlap needs no added node identifier: local
precedence retains the shared node, and sibling subtrees are disjoint. The
[implemented design](../../design/native-identity-tables.md) includes examples
and ownership/complexity details.

## Normative and independent tests

Eight independently authored schemas and 54 documents cover forward references,
missing fields/tables, sibling order, three siblings, nested and recursive
scopes, local precedence, overlapping selectors, composite integer/string keys
and defaults. The 38 valid and 16 invalid expectations remain separate from
oracle outcomes. The original native library rejects 12 valid documents; the
correction passes every expected DOM and streaming verdict. Public Qore reader,
parser and DOM tests pass 179 assertions and verify unchanged document content.
The configure probe additionally verifies reuse after rejected documents.

Pinned Xerces-J 2.12.2 agrees on 32 documents. Twenty-one differences arise from
its sibling-store representation: `ValueStoreCache.initValueStoresFor()` reuses
and clears a store indexed by constraint and depth; `transplant()` publishes that
same object, and `startElement()` shallow-copies the map. A later sibling can
therefore replace values already retained for an earlier sibling. Merging also
stores values without selected-node identity, preventing the required conflict
removal. Reversed order and composite derivatives retain these failures as
explicit expectations rather than changing normative validity.

One additional composite missing-field case has no qualified keyref tuple.
Xerces `KeyRefValueStore.endDocumentFragment()` reports `KeyRefOutOfScope` when
no key table exists before checking whether any complete reference needs it.
XSD 1.0 §3.11.4 clause 4.3 quantifies over qualified references, so this document
is valid. Source locations: `XMLSchemaValidator.java` lines 4247-4264 and
4356-4485; source archive SHA-256
`3c531edfc074e3e0885e5d4a777a9e7317e108028be50ef6e893a5a9cf3e12c2`.
[Original source archive](https://repo.maven.apache.org/maven2/xerces/xercesImpl/2.12.2/xercesImpl-2.12.2-sources.jar).

## Ownership, complexity and configuration

Fourteen private merge scenarios exercise all 14 allocation positions with
single and persistent failures, recovery and exact live-allocation accounting.
They include adding a new value before and after removing a conflicting old
entry. Deterministic comparison counters check 128 and 1,024 entries: a sole
child table needs zero value comparisons, and local targets merged against one
inherited entry need exactly one comparison per target. This caught and removed
an unnecessary quadratic path in the first prototype.

Native document and allocation Valgrind runs free every allocation with zero
errors. The Qore matrix has zero memory errors or lost bytes; only runtime-global
reachable allocations remain. Signals and PCRE2 JIT are disabled for that run.
The complete 76-test provider suite passed the first revision; six affected
checks passed after the comparison-bound correction. Final allocation checks
also cover two added ordering branches, and two source/distribution tests verify
missing, duplicate and unknown source rejection and packaged patch inputs.

The final affected gate passes 56 Qore suites, 24,871 assertions. All four corpus
commands complete successfully; comparison with P5-20c changes only the Qore
runtime version metadata. Existing diagnostic compatibility failures remain
visible. Survey unit tests pass all 17 cases with the explicit local runtime and
module environment. The initial launch without that environment failed to load
the required local native APIs; its log is retained separately. The vanished
previous extraction was replaced from the verified pinned archive. Native docs
build without warnings or errors.

The runtime is a frozen copy of the separately prebuilt Release Qore and its
reflection/core modules, with exact hashes and the concurrent worktree type fix
recorded. It verifies the optional-softlist core correction, but does not imply
that correction is installed or committed. Main Qore was not modified, built,
installed or pushed by this task.

See [validation inventory](P5-20g-validation.json) and
[full audit](audits/P5-20g-native-identity-tables.md). Reproducible scripts and raw
logs are under `/tmp/wsdl-p5-20g-native-identity-tables/`. WSDL tuple validation,
complete P5 typed accounting and P6-P9 are still outstanding. The separate
[skipped-subtree decision](skipped-subtree-interpretation.md) is approved.
