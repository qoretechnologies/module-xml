# P5 content and dynamic-value acceptance

Copyright (C) 2026 Qore Technologies, s.r.o.

P5's implemented XML content and dynamic-value requirements are accepted under
the approved explicit native-capture and retained-XML contracts. This is a payload
and consumer acceptance record, not complete SOAP, WS-I, attachment or CI acceptance.
P6 binding/component work is next; P7–P9 remain required.

| Requirement | Implemented behavior and evidence |
| --- | --- |
| Expanded QName identity and namespace scope | [QName values](qname-values-evidence.md), [declaration context](qname-declarations-evidence.md), provider and SOAP consumers retain identity, shadowing and local bindings. Wrong/unbound prefixes and name collisions have negative tests. |
| Selected types and substitution elements | [Type substitution](type-substitution-evidence.md), [element affiliations](element-substitution-evidence.md), [child particles](substitution-particles-evidence.md) and [complete roots](substitution-roots-evidence.md) cover block/final/abstract/derivation rules, selected names, saved graphs, providers and actual HTTP consumers. |
| Wildcards and generic XML content | [Attribute wildcards](wildcard-attributes-evidence.md), [element wildcards](wildcard-elements-evidence.md), [generic values](generic-values-evidence.md) and [character whitespace](character-whitespace-evidence.md) retain ordered content, scoped names and strict/lax/skip behavior. |
| Nil, mixed content, defaults and fixed values | [Declaration constraints](element-constraints-evidence.md), [nil/mixed consumers](nil-mixed-values-evidence.md), [fixed values](fixed-values-evidence.md) and [empty defaults](wsdl-element-defaults-evidence.md) cover absent/empty/nil distinctions, exact selected values, attributes and both SOAP bindings. |
| Document identities and related value types | [ID bindings](id-bindings-evidence.md), [scoped key/unique/keyref tuples](identity-tuples-evidence.md), [NOTATION](notation-values-evidence.md) and [ENTITY/SOAP restrictions](entity-wsdl-evidence.md) retain the approved nil-as-missing, skipped-subtree and document-context rules. |
| Independent complete typed accounting | [Observer qualification](typed-observer-evidence.md) and [mandatory comparisons](typed-coverage-evidence.md) add exact scalar/list/type, namespace and character comparisons for every serialized valid corpus direction. Missing/malformed stages cannot pass; original normative assertions remain mandatory. |

The fresh expanded gate covers 172 WSDLs and 1,564 selected directions, including
all 34 assigned/supporting P5 requirement families and expected source rejections.
Across the complete diagnostic corpus, native capture accepts and preserves all
2,096 valid directions and correctly rejects the 176 invalid-source directions.
Every valid direction has a typed comparison; no typed stage is unassessed,
missing or skipped. P5's selected families require exact child order. The complete
corpus's established element-only flat-record contract permits regrouping distinct
names; equal-name occurrences and all mixed/generic order remain exact. Existing
stricter particle assertions are still enforced.

The approved ordinary projection remains the default. Its complete report retains
12 failures: four selected-type serialization failures, four inferred generic-type
annotations and four optional nil omissions. These are not converted into passing
conformance results. Callers use `preserve_types=True` for native type/presence
retention, explicit nil carriers where appropriate, and `XsdXmlValue` for complete
XML-carrier information. No API default or historical finding has been rewritten.

P5-21's final runtime acceptance tested the identical WSDL/native/core artifacts
through 193 suites / 97,747 assertions, independent actual-binding character
comparisons and four clean Valgrinds. P5-22a/b change only the reference harness,
selection and documentation. Their fresh Qore, reference, mutation and corpus
checks and exact hashes are recorded in [observer validation](P5-22a-validation.json)
and [coverage validation](P5-22b-validation.json). Existing reference defects stay
adjudicated independently rather than treating validator agreement as normative.

The two dual-binding selection failures remain explicit P6 tests. The previously
recorded deep QName AOT stack failure remains assigned to P9 runtime acceptance;
this phase does not waive it or change stack limits. The separate qdx parser patch
is documented outside the main Qore checkout. Supported-platform CI, complete
binding/protocol behavior, independent peers and attachment/reference acceptance
remain open. No install, push or main-Qore mutation was performed.
