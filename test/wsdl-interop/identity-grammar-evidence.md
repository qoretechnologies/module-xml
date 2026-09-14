# P5-20b identity representation and component QName resolution

Copyright (C) 2026 Qore Technologies, s.r.o.

Based on `14cf23f`. WSDL previously checked identity declarations only when
forbidding them on element references; it otherwise discarded their structure.
The new reader-level grammar validates required names and attributes, selector
and field order, placement, lexical paths and prefix bindings before child
names are grouped. Annotation payload remains application data. This closes
the representation checks in [XSD 1.0 §3.11.2–3 and §3.11.6](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cIdentity-constraint_Definitions).
It does not claim component-reference or instance-value enforcement.

The authored 86-schema structural matrix has 22 valid and 64 invalid cases;
the earlier 54-path matrix adds 22 valid and 32 invalid declarations. The new
WSDL suite checks all 140, original and saved schemas/providers, both binding
definitions, both public conversion modes, exact errors, failed-addition
rollback and cancellation: four cases/1,568 assertions. Valid empty complex
content uses the established `NOTHING` provider projection. The real SOAP 1.1/1.2
NOTATION service now contains a unique declaration and retains all 440 assertions.

The `refer=" K "` positive case exposed a native prerequisite: libxml2's
`xmlSchemaPValAttrNodeQNameValue` validated whitespace-tolerant syntax but
interned and resolved the original spelling. That shared resolver is now
corrected for all component references using bounded normalized slices.
The 91-schema component matrix has 52 valid and 39 invalid cases covering 13
contexts: element/attribute types, simple/complex/simple-content bases, list
items, union members, element/attribute/group/attribute-group references,
substitution affiliations and keyrefs. It checks prefixed and default-namespace
names, surrounding XML whitespace and malformed/unbound values. All three
native APIs agree with pinned Xerces-J 2.12.2; the native suite has 313 assertions
and preserves input DOM data.

## Allocation root cause and correction

The isolated resolver test also found that the legacy `xmlSearchNs` API erased
allocation status when creating the implicit `xml` namespace. For valid
`xml:lang`, injected allocation 4 returned unbound-prefix error 3037. The corrected
resolver uses `xmlSearchNsSafe`, checks dictionary results, clears failed output
pointers and reports memory failure through its parser context. All returned
strings retain dictionary ownership. The test injects one-shot and persistent
failures only around extraction/resolution, initializes builtin types before
the baseline, and releases the last-error record between trials. Invalid input
may retain its existing syntax error if error-message formatting cannot allocate;
valid input must specifically report `XML_ERR_NO_MEMORY`.

The requested separate-session writeup is
`/tmp/wsdl-p5-20-identities/COMPONENT-QNAME-ALLOCATION.md`. The issue is in the
private libxml2 dependency of module-xml, not Qore. It is fixed in this increment;
no separate-session work is needed. Direct Valgrind frees all 30,648 harness
allocations, with zero errors. The direct Qore native suite has zero errors,
zero lost bytes and 117,480 reachable bytes with signals and PCRE2 JIT disabled.

## Acceptance and remaining scope

The [inventory](P5-20b-validation.json) records exact inputs and logs;
[the full audit](audits/P5-20b-identity-grammar.md) covers all 62 checks.
The final gate contains 178 broad Qore suites, 70 dependency-provider tests and
10 supplements (four execution modes and six independent Python checks).
Native/WSDL documentation and metadata build cleanly. The four corpus reports
retain every prior result, differing only in the WSDL source hash. The separate
NOTATION report retains 24 failed identity/legacy-projection rows and 48 classified
default-context oracle differences. The two path-spacing oracle differences
remain documented with unchanged originals in [P5-20a](identity-paths-evidence.md).

Main Qore remains read-only; no installation or push. The unrelated Python
cache is excluded. Artifacts: `/tmp/wsdl-p5-20b-identity-grammar/final/`; final
provider fixtures: `/tmp/qore-xml-libxml2-test-_6y8hs4i/`. The initial exploratory
provider run in `/tmp/wsdl-p5-20-identities/component-provider.log` includes
failures while the safe-API header and harness were being corrected; it is not
acceptance evidence and is superseded by the final frozen run.

Next P5 work is retained identity component metadata/compiled paths, complete
schema name uniqueness and keyref resolution/category/field-count checks across
imports and saved graphs, followed by scoped instance tuples and typed accounting.
All P6–P9 binding, protocol, attachment, peer, supported-environment and CI
requirements remain open. No question is pending.
