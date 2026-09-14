# Native nil identity values

Copyright (C) 2026 Qore Technologies, s.r.o.

The approved nil-as-missing interpretation excludes incomplete unique/keyref
value tuples from comparison. XML nodes and their nil markers remain intact.
See the [decision and oracle evidence](../test/wsdl-interop/nil-identity-interpretation.md).
The existing simple-content requirement, selected-node cardinality and XSD1.0
key nillable-declaration restriction remain enforced.

For example, two products with `<supplierCode xsi:nil="true"/>` do not supply
duplicate supplier codes, and a nil reference requires no matching supplier.
Two `<supplierCode/>` elements of string type supply two empty-string values
and can violate uniqueness. A single product with two selected supplierCode
children violates field cardinality even if both children are nil.

## Representation and lifecycle

A matched nil field uses the existing owned identity key object with its value
pointer set to NULL. An absent field has no key object. This distinguishes
absence of a value from absence of a selected node without sentinel addresses,
new public types or shared state. The nil flag is considered only for element
nodes, because attribute node flags occupy a different domain.

Field matching and cardinality checks operate on the key pointer, so a second
selected nil or valued node is rejected. Tuple qualification checks both the
key pointer and its value pointer. Incomplete tuples leave through the normal
selector cleanup path before hashing, comparison or keyref-table publication.
Multiple constraints selecting one nil node share its context-owned key object,
as they already do for valued nodes. No nil value reaches the value comparator.

Allocation uses the existing sequence/key/context ownership. Failed sequence
or key allocation now reports the memory error on the actual validation context;
the old branches incorrectly passed NULL. Failure while storing a newly allocated
key releases it; the unfinished sequence remains available for normal cleanup.
The direct fault harness exercises all four allocation positions, both one-shot
and persistent failure, with successful recovery and complete release.

## Configuration and verification

The guarded private dependency correction follows the key nillable fix and
verifies exact input/output hashes. Configure tests repeated nil unique values,
nil keyrefs, real duplicate/unresolved values, missing fields and multi-node
fields through DOM and reader APIs with context reuse. AUTO selects the fixed
private library when necessary; SYSTEM rejects a dependency with other behavior.
The source archive is unchanged and reconfiguration preserves output timestamps.

The148-case fixture matrix runs through native reader, parser and DOM APIs,
with exact rejection categories and unchanged DOM content. Pinned Xerces results
are recorded separately for the29 documented differences. The original historical
W3C fixture is retained unchanged; its typed derivative is explicitly identified.
Native and Qore Valgrind tests and allocation recovery cover ownership.
See [acceptance evidence](../test/wsdl-interop/native-nil-identities-evidence.md).
