# Native instance attributes and identity value varieties

Copyright (C) 2026 Qore Technologies, s.r.o.

Native XSD validation includes the four built-in instance attributes in identity
fields. Their types are defined by [XSD 1.0 Structures §3.2.7](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#Built-in_Attribute_Declarations):
`xsi:type` is a QName, `xsi:nil` is a boolean, `xsi:schemaLocation` is a list of
URIs, and `xsi:noNamespaceSchemaLocation` is a URI. Admission of these attributes
is independent of ordinary attribute uses and the owner's simple or complex
content. Their lexical forms are checked even without an identity constraint.
The existing skipped-element-subtree rule still applies.

Only attributes actually present contribute nodes. An element's selected type
does not invent an `xsi:type` attribute, and a non-nil element does not invent
`xsi:nil="false"`. QName prefixes compare by expanded name; `false` and `0` are
the same boolean. A field such as `@*` selecting both `xsi:type` and `xsi:nil`
is invalid because a field may select at most one node. This follows
[XSD 1.0 Structures §3.11.4](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-identity-constraint).

Identity keys retain the selected list or atomic variety, including union
member selection. A one-item list containing `urn:product` differs from the
atomic URI `urn:product`. An empty list is a qualified value and compares equal
to another empty list. Nil remains a missing value under the approved nil rule;
its node still participates in field cardinality checks. Key fields retain the
restriction against nillable element declarations.

For example, an import document can use `@xsi:type` as a discriminator in a
composite key. Two prefix aliases for the same type identify the same value.
A defaulted QName-list attribute uses its schema declaration's namespace
bindings, even when the instance reuses that prefix for another namespace.
Matched default attributes are assessed in that declaration scope to retain
the selected union variety; their schema-owned compiled values are never freed
by instance validation.

The private dependency keeps the anonymous schema-location list type in the
validation context, which outlives all keys borrowing its type pointer. Nil and
list variety are separate private key fields. The conversion helper returns
selected variety through recursive union trials without changing schema type
objects. All mutable assessment state belongs to one validation context.
No public API or public structure layout changes.

Canonical value and key formatting use owned, growable buffers. Every append
and detach is checked; failures free partial storage and report through the
validation context. Whitespace rules, decimal hash equivalence, tuple order,
and tuple delimiters are retained. QName and NOTATION text includes both the
namespace and local name, correcting the earlier duplicated or missing namespace
components. Invalid attribute values discard their XPath match history before
stream-state cleanup, so rejected documents retain no orphaned field states.
Formatting appends text in one pass
instead of repeatedly scanning and copying a growing string. Native dependency
loops retain the module's existing callback and cancellation boundaries.

CMake's behavioral probe includes positive and negative DOM/reader checks and
context reuse. `AUTO` falls back to the pinned private dependency when the probe
fails, `SYSTEM` rejects an affected library, and passing distribution backports
remain usable. The bundled patch checks exact input and output source hashes,
changes only the build tree, and preserves dependency notices.

The public regression is `test/xml-instance-identities.qtest`; the independent
reference check is `test/wsdl-interop/test_instance_identities.py`. Allocation
failure tests instrument a separate test translation unit and cover single and
persistent failures followed by recovery. No fault hook enters the production
library. The tests reset libxml2's independently owned last-error record before
comparing allocation counts. See the [validation evidence](../test/wsdl-interop/native-instance-identities-evidence.md).
