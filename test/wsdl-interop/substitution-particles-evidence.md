# Child substitution processing evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

The applicable XSD 1.0 Structures rules are
[Element Sequence Locally Valid (Particle)](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-particle),
[Element Sequence Valid](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-model-group),
[Element Declarations Consistent](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-element-consistent)
and [Unique Particle Attribution](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-nonambig).
Actual member sets use the independently checked P5-06 affiliation and derivation
rules. A member supplies its own declaration and type while occupying its head's
particle position. Distinct group reference contexts remain distinct positions
for attribution, even when their terminal declarations are shared.

The initial reproduction resolved an abstract decimal head's integer `quantity`
member correctly, but the particle matched only the abstract head name. Both
native serialization and retained child validation rejected `quantity`, while
structural samples incorrectly named the abstract head. Finite member-name
alternatives now retain the head particle's identity and occurrence limits.
All-group aliases use one slot, preventing two members from satisfying one slot
twice. Member namespaces also participate in wildcard overlap checks.

Declaration membership is unavailable during the earlier type/group finalization
pass. A second, post-membership component pass checks all groups and reachable
complex types, including existing models affected by an incremental addition.
It detects member-induced ambiguity and conflicts between explicit declarations
and implicit members. The tests interrupt consistency checking after the new
membership has been published, observe that publication, then verify restoration
and a successful subsequent addition.

Integration exposed three additional conversion paths:

- A required slot with two member names gives each individual name a zero
  minimum. Treating every `NOTHING` field as absent then dropped present empty
  members. Substitution fields now distinguish key presence from absence, and
  decoding does not prepopulate an unused head key.
- A nonabstract head can have an abstract type. Selecting it for an ordinary
  sample failed despite an available concrete member. Name ordering now prefers
  members with concrete declared types without removing any admitted name.
- SOAP's flattened argument extraction used the old head-only field map.
  Explicit part wrappers worked, while the original W3C substituted member
  remained unserialized. Extraction now uses the same concrete declarations and
  aliases as conversion. Empty records for emptiable particles retain their
  enclosing message element; other part/header reservations remain in force.

`test/wsdl-substitution-particles.qtest` has 14 cases / 1,507 assertions. It covers
sequence, choice and all models, shared groups, exact occurrence ranges and
position identity, abstract/blocked empty languages, unused groups, nested
anonymous types, imported member namespace collisions, native and retained
values, integer rejection boundaries, provider reconstruction, concrete samples,
both actual SOAP bindings/directions, failed/interrupted additions, concurrent
readers, 96 members across 1,000 positions and 80-digit occurrence bounds.

`test_substitution_particles.py` builds 53 schemas: 41 valid and 12 invalid.
The 310 documents have 62 valid and 248 invalid instances, including cases whose
names match but whose member values or abstract types must be rejected. Each
document runs with both actual SOAP bindings, original and reconstructed schemas,
and request/response processing. The 2,586 rows include all construction outcomes
and document paths. Both explicit part wrappers and flattened records produce
992 valid SOAP outputs; 58 standalone generated samples are also independently
validated. Retained inputs preserve their exact XML, while native outputs preserve
expanded member identities and numeric values in each field's occurrence order.
The tests check row counts, identity, error categories and missing/extra outputs.

Pinned Xerces-J 2.12.2 validates all 1,050 generated payloads/samples. Independent
lxml 6.1.1/libxml2 2.12.10 additionally validates every output for schemas it
accepts. Its existing counter-insensitive UPA check rejects the valid exact
boundary model. Its transition coalescing misses overlapping all slots; both
validators omit unused groups from these component checks. The pinned Xerces
`XSConstraints.java` source confirms that `fullSchemaChecking()` traverses
unchecked complex types for consistency and UPA. The original sources and
validator binaries are unchanged.

The four P5-06 instance-validator discrepancies remain explicit through
`ORACLE_DIFFERENCES`; their normative negative classification is unchanged.
The separate native declaration-consistency omission remains a
[failed P5 requirement](p5-native-element-consistency-finding.md). WSDL rejects
both affected schemas; the native outcomes are reported independently and do
not count as conformance passes.

The strict selection adds the eight original W3C `SubstitutionGroup` message
directions. Its independent particle observation checks complete expanded member
names, exact string values and order. The complete diagnostic corpus retains
all other failures. Selected message-root identity, remaining P5 content
semantics and P6–P9 acceptance remain required by the plan.

The implemented APIs, field-presence contract and executable order example are
described in [the design](../../design/wsdl-substitution-particles.md).
Final execution modes, compiled consumers, full regression/corpus results and
source/log fingerprints are recorded in [P5-07 validation](P5-07-validation.json).
