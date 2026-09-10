# Exact particle attribution evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

XSD 1.0 [section 3.8.6](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-nonambig)
requires a unique particle position for the current element name, using preceding
input and without inspecting later elements or element values. The requirement
applies to every present model group. It permits different repetition boundaries
when those boundaries identify the same declaration position.

The implementation uses the weak-determinism conditions in
[Chen and Lu (2012)](https://lcs.ios.ac.cn/~chm/papers/dlt2012.pdf), sections 3, 4
and 6, with the exact flexibility calculation reproduced as Algorithm 3 in
[Groz and Maneth (2017)](https://www.pure.ed.ac.uk/ws/portalfiles/portal/32885322/jcss2017_3.pdf).
The latter's example 3.13 distinguishes `(b? a{2,3}){2,2} b` (deterministic)
from `(b? a{2,3}){3,3} b` (ambiguous). For the latter, after six `a` elements the
next `b` may be the first position in a third repetition or the final position
after three two-`a` repetitions. The two-iteration language cannot reach that
conflict. The tests independently enumerate all finite marked words for these
principles; they do not use the production threshold algorithm as an oracle.

`test_particle_ambiguity.py` generates exactly 300 finite schema expressions with
seed 4103. Its language-size budget is applied while constructing each expression;
every emitted case and every word of its finite language is checked. For each
prefix, the oracle records the selected declaration position. Repetitions reuse
that position; separate syntactic children have separate positions. Each present
model group also receives its own component check. The fixed result is 242 valid
and 58 ambiguous schemas, tested in 600 actual SOAP binding descriptions and
2,536 construction/bound-part rows. Invalid schemas must raise `WSDL-ERROR` before
operation use. Accepted originals and Serializable reconstructions check each
bound request/response root.

A separate 12-schema matrix uses pinned lxml 6.1.1/libxml2 2.12.10 and Xerces-J
2.12.2. Exact finite boundaries, competing choices, optional boundaries, weak
repetition boundaries, wildcard namespace intersections, empty components and
the two-versus-three example have normative expectations. The following independent
disagreements are asserted explicitly; all other verdicts must agree.

| Validator | Case | Expected | Actual | Root cause |
| --- | --- | --- | --- | --- |
| libxml2 | exact-boundary (`a{2,2} a`) | valid | rejected | The automaton determinism check compares transitions without the counter conditions that make their uses disjoint. |
| libxml2 | choice-duplicate | rejected | valid | Equal same-target transitions are coalesced without declaration-position identity. |
| libxml2 | empty-language-component | rejected | valid | The ambiguous nested choice has the same transition-identity loss; its component constraint remains applicable inside an empty language. |
| libxml2 | nested-count-2 | valid | rejected | Counter-insensitive transition analysis loses the exact outer iteration boundary. |
| Xerces | nested-count-2 | valid | rejected | UPA construction changes inner `2..3` to `1..2`, which introduces a conflict absent from the original language. |

The libxml2 source points are `xmlSchemaBuildContentModel()` in `xmlschemas.c`,
`xmlFAComputesDeterminism()` / `xmlFARecurseDeterminism()` and `xmlFAEqualAtoms()`
in `xmlregexp.c`. The equality check compares token strings, not schema positions;
the recursive conflict check follows count transitions without counter feasibility.
The pinned Xerces source is [the 2.12.2 source archive](https://repo.maven.apache.org/maven2/xerces/xercesImpl/2.12.2/xercesImpl-2.12.2-sources.jar):
`CMBuilder.buildSyntaxTree(particle, true)` reduces variable counts above one to
`1..2` and fixed counts above one to `2..2`, before DFA attribution checking.
The published counterexample shows why the original counts matter.

The private libxml2 2.15.4 provider reproduces all four native schema disagreements.
[P4-native-attribution-diagnostics.json](P4-native-attribution-diagnostics.json)
records its exact binary/schema hashes and outcomes. These are failing native
requirements owned by the next P4 native attribution increment. They are not
counted as native passes or suppressed. WSDL's new component check has the correct
results; native schema construction/validation still needs its own repair before
P4 acceptance. Independent validator binaries and upstream schemas are unchanged.

The focused Qore suite covers 80/81-digit adjacent thresholds, shared group
contexts, wildcard/element namespace collisions, all-group rules, empty and absent
terms, graph reconstruction, cancellation/reuse, deterministic concurrent calls,
1,000 alternatives and a compact graph representing more than one billion
expanded positions. A recovery regression exposed validation after legacy field
mutation; validation now precedes that mutation, and rejected schema additions
preserve the existing requiredness and subsequent use of shared declarations.
