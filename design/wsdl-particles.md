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
invoice.getParticle().validateDeterminism();
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

## Unique particle attribution

Schema construction checks ordered particle attribution after declaration/group
resolution and base-type composition, before legacy field adapters can change
shared occurrence metadata. Unused named group definitions are checked too.
`XsdParticle::validateDeterminism()` applies the same check to a detached or
reconstructed graph. An ambiguity raises `WSDL-ERROR`. `XsdElement::getNamespaceUri()`
returns the namespace of the actual element name, including unqualified local
forms and resolved global references. Element and wildcard overlap uses this
identity and the resolved wildcard namespace algebra.

The check implements weak determinism: the current expanded name and preceding
input must determine a unique declaration position. Different decompositions into
repetition iterations are allowed if they identify the same declaration. For
example, nested counts around one `a` position remain deterministic, while an
optional `a` followed by another `a` position is ambiguous. An exact two-count
`a` followed by another `a` position is deterministic. No lookahead into later
names, values or attributes resolves a conflict.

The implementation combines Chen and Lu's weak-determinism conditions with the
count-flexibility calculation described by Kilpeläinen and reproduced as Algorithm
3 in Groz and Maneth. First-name sets are independent of repetition context.
Follow-last membership and ambiguity are monotone in the inherited maximum count
`N`: each becomes true at one rational threshold, or never. A graph node stores
those thresholds, its nullability, its flexibility ratio and the two ambiguity
thresholds for continuing/noncontinuing contexts. Named references reuse this
summary, so different call paths do not expand shared definitions.

A repetition scales descendant thresholds by its maximum. A nonnullable sibling
resets the corresponding inherited count to one. Choice merges thresholds by their
minimum; sequence applies the published cross-boundary conditions. For a fixed
repeat maximum `n` whose child's flexibility ratio is `p/q > 1`, its own flexible
threshold is `p / ((p-q)n)`. A variable range is flexible unconditionally. Nullable
counted children normalize their minimum to zero for the analysis only; declaration
counts remain unchanged. Optional one-count terms introduce no repetition edge.
The threshold calculation uses exact decimal integer products and comparisons;
there is no floating-point rounding or expansion of numeric counts.

Empty languages and epsilon are distinct. Zero-count declarations contribute no
component and their absent child graph is not traversed by the compiled program.
Every present model group must itself satisfy the component constraints, including
one inside a surrounding empty language. An empty parent therefore cannot hide an
ambiguous nested group. Construction-time QName/type consistency remains a
separate prerequisite.

For `m` graph nodes/edges and `p` distinct terminal predicates, summaries need
`O(mp)` entries; wildcard intersection caching needs at most `O(p²)` entries.
`O(mp²)` predicate/set work is a conservative bound, with exact integer arithmetic
adding its digit-dependent cost. Rational numerator/denominator lengths grow with
count digits along graph paths, not with expanded occurrence values. Ordinary
name intersections use hash lookups over the smaller set, and flat choices update
accumulated sets in place. Tests include 1,000 alternatives and a shared DAG whose
expanded declaration count exceeds one billion. All mutable analysis state belongs
to the call; concurrent calls and cancellation/reuse are tested.

The WSDL particle checks cover element names and wildcard namespace admission.
Implicit substitution-member admission is coupled to the separate substitution
resolution requirements. These checks do not replace native libxml2 schema
validation; its independent attribution defects are tracked with the interoperability
evidence. Ordered SOAP message conversion and field/sample integration remain
separate requirements in the execution plan.

References:

- [Chen and Lu, Checking Determinism of Regular Expressions with Counting (2012)](https://lcs.ios.ac.cn/~chm/papers/dlt2012.pdf), sections 3, 4 and 6.
- [Groz and Maneth, Efficient Testing and Matching of Deterministic Regular Expressions (2017)](https://www.pure.ed.ac.uk/ws/portalfiles/portal/32885322/jcss2017_3.pdf), section 3.4 and Algorithm 3.
- [XSD 1.0 model-group component constraints](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-nonambig).

## Declaration attribution for ordered values

`attributeElementNames()` returns one terminal `XsdParticle` per input child in
document order. An accepted empty input returns an empty list; rejection returns
`NOTHING`. Complete schema attribution validation before using this projection.
The returned objects retain the selected declaration's identity, including two
distinct declarations with the same expanded name at a fixed count boundary.
Repeated group uses can share their terminal declaration object while keeping
their caller's continuation separate.

For example, conversion can select the invoice number and payment declarations:

```qore
list<XsdParticle> positions = invoice.getParticle().attributeElementNames(("{}number", "{}card"));
@assert(positions[0] === content[0]);
@assert(positions[1] === content[1].getChildren()[0]);
```

Ordinary zero/one/unbounded models use the existing Thompson automaton. Each
reachable state retains one predecessor trace for the consumed prefix; epsilon
closures are cached per consuming state. An accepting trace is reconstructed
iteratively after the last token. At most `O(m n)` trace records and `O(m²)` cached
closure entries are retained for `m` states and `n` names; transition work is at
most `O(m² n)`. No future-name lookahead changes the schema attribution rule.

General finite counts and shared group graphs reuse the memoized endpoint
matcher. Sequence/repetition frontiers record predecessor offsets, reconstruct
one accepted decomposition, and then visit its child spans iteratively. Nullable
terms use only positive-progress repetitions; empty spans need no terminal trace.
Thus a shared empty graph is not expanded just to reconstruct empty iterations.
The recognition bounds above also bound endpoint reconstruction; predecessor
frontiers add at most quadratic input storage per active reconstruction, with no
exponential retry or numeric-count expansion. All call state is private, and Qore
cancellation remains active.

The projection identifies declarations and wildcard namespace predicates. It does
not itself convert values or enforce nil, dynamic types or wildcard processing.
Those consumers use their own validation. The runtime field/sample integration
remains separately tracked in the P4 execution record.

Run `qore -b --enable-debug test/wsdl-particle-attribution.qtest` and
`python3 test/wsdl-interop/test_particle_value_attribution.py -v`. The latter
compares original and reconstructed graphs against complete marked languages and
negative mutations, checking every returned declaration position rather than
only whether the input was accepted.
