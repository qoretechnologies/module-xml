# P5-20c retained identity components

Copyright (C) 2026 Qore Technologies, s.r.o.

Final base: `80c8f3f` (after the independently accepted native P5-20d/e fixes). This increment retains compiled key/unique/keyref components and
validates schema-wide relationships. Ordered declaration grammar was accepted
in P5-20b, but its grouped conversion did not construct identity components.
Names, paths and keyref relationships were therefore discarded after grammar
validation. The receiving element now retains immutable definitions, and the
complete schema resolver publishes them only after relationship validation.

The implementation follows XSD 1.0 Structures Second Edition §3.11.1, §3.11.2
and §3.11.6: identities are schema-wide expanded names, keyrefs target key/unique,
and field counts must agree. XPath namespace rules remain distinct from the
component QName rules. See [implemented design and example](../../design/wsdl-identity-components.md).

## Independent oracle adjudication

`fixtures/identity-components.json` retains 30 authored schemas: 14 valid and
16 invalid. Pinned Xerces-J 2.12.2 agrees with 28; it incorrectly accepts the two
forward keyref chains `absent/chain` and `target/chain`. Both fixtures remain
`schema_valid: false`. Their explicit `xerces_schema_valid: true` records oracle
behavior without changing the normative result. Reversed-order derivatives are
separate fixtures; Xerces correctly rejects those. Local WSDL and native XML
reject both orders with their schema error categories.

Root cause, verified in the pinned source archive already recorded in
[identity-path evidence](identity-paths-evidence.md):

- `XSDHandler.resolveKeyRefs()` processes its pending stack in order.
- For `R -> S -> K`, looking up pending `S` enters `getGlobalDecl()`, finds its
  source declaration, then calls `traverseGlobalDecl()`.
- That method's `IDENTITYCONSTRAINT_TYPE` branch assumes all identities have
  already been processed. It returns null without a diagnostic.
- `XSDKeyrefTraverser.traverse()` assumes a null lookup already reported an
  error, and returns without retaining `R`. `S -> K` then succeeds.
- Reversing the two keyrefs resolves `S` first; the category check then correctly
  rejects `R -> S`.

The archive is
[the Maven source artifact](https://repo.maven.apache.org/maven2/xerces/xercesImpl/2.12.2/xercesImpl-2.12.2-sources.jar),
SHA-256 `3c531edfc074e3e0885e5d4a777a9e7317e108028be50ef6e893a5a9cf3e12c2`.
Extracted relevant sources and original diagnostic logs are under
`/tmp/wsdl-p5-20c-identity-components/`. The normative requirement is explicit in
[the referenced-key property](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cIdentity-constraint_Definitions).
No dependency patch or validation workaround is introduced for this oracle bug.

## Acceptance

Acceptance passes against the frozen prebuilt Qore Debug runtime from the clean
source checkout at `e35e4d63c754d2d91d762347231c000f5098dcb8`. This is a local
build copied for testing. The separate developer subsequently updated the installed
Release runtime, which was frozen and verified independently. Its embedded configure-time git
hash remains `cc7c7606c`; the exact artifact hashes and regression results are in
`P5-20c-validation.json`. The fixed runtime reserves source identities without
retaining container values or delaying object destruction.

The previous 179-suite run had 178 passes and a corrupted detached-particle
serialization failure. The root cause and original reproducer remain in
`/tmp/wsdl-identity-serialization-lifetime/README.md`. The fixed runtime now passes
all 1,000 reproducer iterations and five core Serializable regression suites
(47,081 assertions). No XML serialization workaround was introduced.

The accepted gate covers all 181 Qore suites (90,936 assertions), including
`wsdl-particle-ambiguity`, with no Qore warnings or errors in the passing runs.
180 suites pass on Debug; the enterprise-schema whitespace suite exceeded its
600-second Debug deadline and passes on the newly installed Release runtime.
The initial timeout remains in the inventory. That Release runtime also passes
the 1,000-iteration reproducer and the 46,817-assertion transient-source suite. All 13 supplements
pass: the 480-assertion component suite in AST/IR/JIT/tiered modes and nine
Python checks, including the accepted native key/nil interpretation matrices.
WSDL documentation and metadata build cleanly. All four corpus reports retain
the prior results; only the runtime provenance and WSDL source hash differ.
The existing 24 NOTATION binding failures and 48 classified default-context
oracle differences remain visible; diagnostic exit status is not conformance.

The component suite and two focused detached-particle cases pass Valgrind with
zero errors and zero definitely, indirectly or possibly lost bytes. The full
particle suite exceeded the additional 300-second Valgrind deadline; its full
normal debug run passes. The focused memory run covers 14 assertions and does
not count filtered cases as executed. Valgrind reports a DWARF-reader warning
about missing inline debug origin metadata in the prebuilt Qore library; it is
retained in the logs, with no memory-error suppression. Final scripts and logs:
`/tmp/wsdl-p5-20c-serialization-fixed/`.

The component suite covers original/saved schemas, detached elements, independent
constraints and namespace registries; prefix shadowing, unqualified names,
wildcards, axes, unions and ordered fields; forward references, duplicate names,
invalid target categories/counts; unused and shared particles; imported and
chameleon declarations; malformed saved metadata; failed additions; cancellation
and a 501-definition registry. The existing grammar suite additionally covers
both WSDL SOAP bindings, saved providers and both public representation modes.

The implementation is Qore-only. Native validation is exercised by the fixture
tests; the extra consumer memory checks above verify the separate core fix. CI and
supported-environment acceptance remain P9. Scoped instance tuple enforcement
and the existing 24 NOTATION identity failures remain explicitly open in P5;
this increment makes no claim that declaration metadata enforces instance keys.
