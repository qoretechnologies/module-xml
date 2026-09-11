# Substitution members in child particles

Copyright (C) 2026 Qore Technologies, s.r.o.

An element particle admits the concrete declarations returned by
`XsdElement::getInstanceDeclarations()`. A local declaration admits itself; a
global declaration or reference admits its resolved substitution group.
`getInstanceDeclaration(expanded_name)` selects the validating declaration.
`getDeclaration()` exposes the canonical declaration behind a reference.
Affiliation, derivation and blocking follow the
[element substitution design](wsdl-element-substitution.md).

The structural matcher compiles each admitted expanded name as a finite
alternative at the same particle position. The whole alternative receives the
particle's occurrence range, so different members share the limit. Attribution
returns the original particle position; conversion then uses the selected name
to retrieve the actual member. Shared group definitions retain their caller
continuations. Empty groups contribute an empty language, while optional
occurrences can still contribute no children.

An all group indexes each admitted name to its original slot. Presence and
requiredness are counted by slot identity, preventing two alternate members
from filling one slot twice. Samples reserve the remaining required slots and
choose a permitted declaration for each selected slot. Occurrence ranges are
computed for individual names over the complete language: a required slot with
two members gives each name a minimum of zero, but the matcher still requires
one member in total.

After memberships are published, schema construction checks every named group
and every reachable complex type, including anonymous and recursive types.
Unique attribution uses expanded member names, including their namespaces when
checking wildcard overlap. Element Declarations Consistent merges explicit
declarations with implicit member declarations. Canonical declaration identity
allows repeated references to the same global declaration with an anonymous
type. Distinct declarations of the same expanded name must share a named type.
Incremental additions recheck existing models; errors and cancellation restore
the old registry and membership maps. Traversal state is local to each call.
Concurrent readers use the immutable schema graph after construction. Schema
additions require exclusive access; they must not run alongside readers.

Native fields use a local member name when unique and an expanded name when
names collide. Each selected member's type, nillability and value checks govern
conversion. Field presence selects a substitution member even when its value
is `NOTHING`; an absent key omits it. Decoding consequently does not prepopulate
an unused head field. This preserves empty member occurrences without adding
an extra head when the record is serialized again. Ordinary fields retain their
existing omission behavior. Retained `XsdXmlValue` values preserve exact child
order and the distinction between empty and explicitly nil XML.

Single-part SOAP calls accept these fields both inside an explicit part wrapper
and as a flattened record. Field extraction uses the same active declarations
and aliases as conversion, retaining the existing reservations for other parts
and headers. An empty record for an emptiable particle retains its enclosing
message element.

Provider fields use the same concrete declarations and occurrence ranges as
conversion. Complete native providers validate the containing particle;
individual field metadata alone cannot express coupled occurrence constraints.
Samples select member names before requesting their declaration-specific values.
When alternatives include a declaration with a concrete type, samples prefer it
to a declaration whose abstract type would require a separate `xsi:type` choice.
This preference leaves every permitted name available to the matcher.
Native records retain order within each field; use `XsdXmlValue` to retain
interleaving between different member names.

For example, an order can accept an integer quantity in place of its abstract
decimal head:

```qore
XsdSchema schema("<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
    "<xs:element name='item' type='xs:decimal' abstract='true'/>"
    "<xs:element name='quantity' type='xs:int' substitutionGroup='item'/>"
    "<xs:element name='order'><xs:complexType><xs:sequence>"
    "<xs:element ref='item' maxOccurs='2'/></xs:sequence></xs:complexType></xs:element>"
    "</xs:schema>");
XsdXmlValue order = schema.serializeXmlValue("", "order", {"quantity": 17});
@assert(index(order.getXml(), "<quantity>17</quantity>") >= 0);
@assert(schema.getXmlDataProviderType("", "order").acceptsValue(order).getXml() == order.getXml());
```

The relevant rules are XSD 1.0 Structures
[model group constraints and validation](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#Model_Groups)
and [particle validation](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-particle).
See the [regressions and independent evidence](../test/wsdl-interop/substitution-particles-evidence.md).
