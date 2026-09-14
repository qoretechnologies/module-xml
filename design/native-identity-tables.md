# Native identity constraint tables

Copyright (C) 2026 Qore Technologies, s.r.o.

Native XSD validation assembles key and unique tables according to
[XSD 1.0 Structures §3.11.5](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#sic-identity-constraint).
A receiving element inherits its children's surviving entries. Equal key tuples
associated with distinct nodes in different children are excluded at that
receiving element. A locally selected entry takes precedence over inherited
entries with the same tuple. Rejected child entries are absent; their conflict
markers do not propagate to an ancestor.

For example, three sibling batches contributing keys `[1]`, `[1]`, and `[2]`
leave key `2` available to a reference on their parent. Key `1` is ambiguous
there. If that parent also contributes a locally selected key `1`, its local
entry resolves a reference from an ancestor. If a child's two descendant
batches conflict on key `1`, that child contributes no entry for `1`; another
child's unambiguous key `1` can still be referenced above both children.

The private libxml2 implementation separates inherited candidates from local
entries. Child tables already contain unique tuples, so a merge compares each
incoming entry only with the entries and conflicts present before that child's
merge. Newly appended entries stay outside the old-entry prefix. This avoids
quadratic self-comparison when a large table propagates through an otherwise
empty ancestor. Existing cross-table value comparisons retain their original
value-space semantics and worst-case product cost. Local targets use the same
principle; an empty receiving table retains the existing ownership transfer.

Bindings own pointer arrays and conflict lists; keys and selected nodes remain
owned by the validation context. A new binding is published before fallible
array growth. Conflict-list insertion completes before an inherited entry is
removed. Allocation failures report through the active validation context and
leave all partial storage reachable by normal cleanup. No node identity or
public structure layout is added: sibling subtrees are disjoint, and local
precedence also handles an ancestor selector selecting the same actual node.

CMake tests installed libraries with positive and negative DOM/reader controls,
including context reuse. `AUTO` chooses the private corrected dependency on a
failed probe; `SYSTEM` rejects it. Distribution backports that pass remain
usable regardless of version text. The bundled correction consumes and produces
exact source hashes after the earlier nil-identity correction, writes only to
the build tree, and preserves original dependency sources and notices.

Run `qore -b --enable-debug test/xml-identity-tables.qtest` for the 54-document
parser/reader/DOM matrix. The independent diagnostic test is
`python3 -B test/wsdl-interop/test_identity_tables.py -v`; it explicitly retains
known Xerces differences. `test/cmake/libxml2_identity_tables_allocation.c`
checks single and persistent allocation failures, recovery, and deterministic
comparison bounds at 128 and 1,024 entries. See the
[validation evidence](../test/wsdl-interop/native-identity-tables-evidence.md).
