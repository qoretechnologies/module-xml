# Ordered particle recognition evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

XSD 1.0 Part 1 section 3.8.4 defines sequence/choice/all languages. A choice must
select an actual child particle; a required choice with no particles accepts no
sequence, including the empty sequence. Empty sequence/all groups admit empty
input. Sections 3.3.2 and 3.8.2 omit zero-count declarations from the parent model
entirely. Section 3.9.4 applies occurrence bounds to complete partitions of a group.
These rules are the expected language, independent of validator agreement.

- [Model group validation rules](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-model-group)
- [Particle validation rules](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-particle)
- [All-group constraints](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-all-limited)

`test_particle_matching.py` checks 11 schema families: repeated sequences and
choices, nested optional groups, exact finite gaps, nullable counts, shared group
references, all permutations, zero-count choice members, empty choices, optional
empty choices and epsilon alternatives. Positive strings and deterministic
insert/delete mutations are compared with independent Python regular-language
expressions and both pinned XML validators. Worker rows cover both actual SOAP
bindings, each bound request/response root, and original/reconstructed schemas.
The fixed inventory is 270 documents, 22 binding contracts and 2,160 worker rows.
These rows inspect particle recognition on bound parts; they do not claim completed
message serialization or scalar conversion integration.

The independent lxml 6.1.1/libxml2 2.12.10 falsely accepts exactly two documents for
the zero-count choice member: empty content and the forbidden element. Its local
zero-count declaration enters the automaton as both an optional and a consuming
alternative. This is the same root cause fixed in the private 2.15.4 fallback by
P4-01, and the original independent validator is unchanged.

Pinned Xerces-J 2.12.2 falsely accepts exactly the empty document for a required
empty choice. `CMBuilder.buildSyntaxTree()` returns no node for the empty choice;
`getContentModel()` substitutes its empty content model. That loses the distinction
between an empty choice and an empty sequence required by section 3.8.4. Source
inspection used the [pinned Xerces source archive](https://repo.maven.apache.org/maven2/xerces/xercesImpl/2.12.2/xercesImpl-2.12.2-sources.jar).
Both exact disagreement lists are asserted; every other independent verdict must
agree. Qore must reject the three invalid cases according to the specification.

The Qore suite additionally checks 81-digit bounds, absent all-group references,
namespace constraints and collisions, malformed expanded names, invalid all
placement, missing wildcard reconstruction data, indirect reconstructed cycles,
unresolved restored references, cancellation/reuse and concurrent shared graphs.
Large cases exercise both the automaton and general counted paths without expanding
the numeric counts. Scalar regex regression suites guard the shared matcher.

Schema ambiguity checking and ordered message/provider/sample integration remain
the next P4 requirements. They are separate from this structural language predicate.
