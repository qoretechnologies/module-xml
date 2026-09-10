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
@assert(invoice.getParticle().matchesElementNames(("{}number", "{}card")));
@assert(!invoice.getParticle().matchesElementNames(("{}card", "{}number")));
```

Run `qore -b --enable-debug test/wsdl-particle-model.qtest` and
`python3 test/wsdl-interop/test_particle_model.py -v` with local modules selected.
The independent matrix inspects actual SOAP 1.1/1.2 bound parts in both directions.
See [occurrence evidence](../test/wsdl-interop/particle-counts-evidence.md) for
native validation and the independent validator disagreements.

## Recognition of ordered child names

`matchesElementNames()` accepts expanded child names in document order and returns
whether the complete sequence belongs to the particle's language. It checks whole
sequence/choice/group counts, finite count gaps, nullable repetition, all-group
permutations and wildcard namespace admission. It rejects malformed expanded names
with `XSD-PARTICLE-ERROR`, and unresolved/cyclic groups or invalid XSD 1.0 all
placement with `WSDL-ERROR`. It does not perform element value, nil, dynamic-type,
wildcard declaration or schema ambiguity validation. Message conversion still has
its separate field adapters until the P4 integration is complete.

Element wildcards now retain their resolved namespace and processing constraints.
`getWildcard()` exposes the existing `XsdAttributeWildcardInfo` representation;
element and attribute wildcards share that namespace algebra. This captures
`##targetNamespace` in the declaring schema, independently of later bindings.
Serializable restoration validates the wildcard's presence, constraint and
processing mode. Shared graph references survive reconstruction.

Compilation builds a postorder graph without expanding occurrence values or named
group definitions. It preserves the distinction between an empty language and an
empty sequence: a required empty choice cannot match any input. A zero-count child
declaration contributes no component, including no epsilon alternative to a choice.
An empty sequence inside a choice is a real alternative that accepts empty input.

The structural regex matcher has a typed token-predicate entry point. Particle
matching supplies expanded names directly, so the number of distinct schema names
is not limited by an artificial character encoding. Ordinary zero/one/unbounded
repetition uses the existing Thompson state-set matcher when the compiled graph
is a tree. Shared group graphs use memoized node/start endpoint sets, preserving
each caller's continuation; a shared Thompson fragment would conflate them.

General finite counts use the existing endpoint matcher. Input length bounds
every iteration count before integer conversion. Nullable terms can pad minimum
counts without advancing input; positive-progress endpoint sets still preserve
exact attainable counts and their gaps. All groups use a direct name-set check,
with each required member present once, each optional member at most once, and
whole-group optionality applied only to the empty input.

For `m` grammar nodes/edges and `n` input names, compilation requires `O(m)` storage.
Ordinary state-set recognition is polynomial in `m` and `n`, caching only transitions
encountered by the input. General counted matching stores at most `O(m n²)` endpoints;
`O(m n⁴)` is a conservative upper bound for its joins and count frontiers. QName
comparison adds the cost of the name strings. These are input-dependent polynomial
bounds, with no exponential backtracking or expansion of declared numeric values.
All mutable match state is local to a call, and Qore cancellation checks remain
active in the loops. Tests cover 10,000 names, 1,000 declaration positions,
80 nested exact repetitions and a shared group DAG whose expanded size is 32,768.

Run `qore -b --enable-debug test/wsdl-particle-matching.qtest` and
`python3 test/wsdl-interop/test_particle_matching.py -v` with local modules selected.
The [matching evidence](../test/wsdl-interop/particle-matching-evidence.md) records
the independent empty-choice and zero-count validator differences.
