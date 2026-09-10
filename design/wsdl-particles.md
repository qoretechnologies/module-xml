# Ordered schema particle construction

Copyright (C) 2026 Qore Technologies, s.r.o.

`XsdComplexType::getParticle()` and `XsdGroup::getParticle()` expose the ordered
declaration graph constructed by WSDL. A node retains its `XsdParticleKind`, its
own minimum and maximum occurrence values, and its direct children in schema
order. An element node references the same `XsdElement` object used by the
schema's field metadata and late type resolver. Distinct declaration positions
remain distinct even when their expanded element names agree.

Occurrence getters return canonical decimal strings. `NOTHING` is the unbounded
maximum. Parsing collapses XML whitespace, accepts optional plus signs and
negative zero, rejects other negative values and malformed lexical forms, and
compares the complete integers before accepting a range. Counts do not allocate
or expand repeated declarations. Legacy field projections can have inherited
occurrence adjustments; use the particle getters for the declaration's range.

The XML source adapter requests preserved order from the native parser, retaining
ordered keys within XSD sequence, choice and all declarations. Other schema and
WSDL containers keep their grouped interfaces. Declaration enumeration precedes
namespace stripping, so aliases on either side of another term cannot regroup
positions. Empty adjacent and nonadjacent compositors remain explicit nodes.
Original source bytes remain available for schema validation and reconstruction.

A group reference retains its expanded name and a link to the checked named
definition. Multiple references share that definition without expanding it.
Existing undefined-reference, declaration-consistency and group-cycle checks run
before construction completes. Group resolution also detects a cycle in a child
graph. Extension creates a synthetic one-occurrence sequence with the base first
and extension second; restriction retains its own declaration. Declared legacy
SOAP array sequences use the same element construction path.

The graph is Serializable, including shared element and group identities. Member
restoration validates term types, canonical counts, ranges and field consistency.
Tests reconstruct complete schemas and detached types. Complete schema additions
and group resolution before sharing a graph between threads. Child lists use
copy-on-write semantics; internal finalization mutates links during construction.
Failed parsing restores namespace/finalization scopes and permits subsequent use.

Storage is proportional to the source declarations and reference edges, independent
of numeric occurrence values. Source conversion appends grouped children directly;
it does not repeatedly copy the accumulated list. Graph traversal visits declaration
positions without occurrence expansion. XML parser depth limits still apply;
the regression suite exercises 1,000 sibling positions and 80 nested sequences.
Qore loop cancellation remains active. The public model describes construction;
the runtime field adapters are covered separately by the pending P4 matching and
serialization criteria in [the execution plan](../test/wsdl-interop/PLAN.md).

For example, an invoice must retain the payment choice after its number:

```qore
XsdSchema schema("<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
    "<xs:complexType name='Invoice'><xs:sequence><xs:element name='number' type='xs:string'/>"
    "<xs:choice><xs:element name='card' type='xs:string'/><xs:element name='transfer' type='xs:string'/>"
    "</xs:choice></xs:sequence></xs:complexType></xs:schema>");
XsdComplexType invoice = cast<XsdComplexType>(schema.findType("Invoice"));
list<XsdParticle> content = invoice.getParticle().getChildren();
@assert(content[0].getElement().name == "number");
@assert(content[1].getKind() == XsdParticleKind::Choice);
```

Run `qore -b --enable-debug test/wsdl-particle-model.qtest` and
`python3 test/wsdl-interop/test_particle_model.py -v` with local modules selected.
The independent matrix inspects actual SOAP 1.1/1.2 bound parts in both directions.
See [occurrence evidence](../test/wsdl-interop/particle-counts-evidence.md) for
native validation and the independent validator disagreements.
