# P5 native element-declaration consistency requirement

Copyright (C) 2026 Qore Technologies, s.r.o.

The P5 child-substitution matrix found a pre-existing native schema-construction
gap. WSDL rejects two schemas in which a substitution member and an explicit
local element have the same expanded name and different types. The P5-07 private
libxml2 provider accepted both: one model is used by `Container`; the other is an
unused named group. These are failed native requirements, not valid schemas.
P5-08 implements their correction before P5 acceptance; the original observations
below are preserved as historical evidence.

XSD 1.0 Structures [Element Declarations Consistent](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-element-consistent)
includes implicit substitution members and applies to all model groups. The
conflict is between `Quantity` of type `xs:int` in `Head`'s group and a qualified
local `Quantity` of type `xs:string`. Required sequential positions make
attribution unambiguous, isolating declaration consistency from UPA.

The native root cause is explicit in pinned libxml2 2.15.4 `xmlschemas.c`:
`xmlSchemaCheckElementDeclConsistent()` is under the undefined
`WXS_ELEM_DECL_CONS_ENABLED` guard and immediately returns zero. Its call is also
guarded. `xmlSchemaFixupComponents()` finishes with an unimplemented
`cos-element-consistent` marker. The existing counted attribution checker handles
UPA but does not implement this separate constraint. Independent lxml/libxml2
2.12.10 has the same omission. Xerces rejects the used type, but its
`XSConstraints.fullSchemaChecking()` visits unchecked complex types rather than
unused named groups, so it misses the unused-group conflict.

[P5-native-element-consistency-diagnostics.json](P5-native-element-consistency-diagnostics.json)
retains both complete schemas, their hashes, the native outcome and its source
and module fingerprints. The module binary is the unchanged P5-06 build, so
these native failures are independent of the Qore child-particle changes.
`test_substitution_particles.py` asserts these observed native outcomes through
its explicitly named `SCHEMA_DIFFERENCES` entries while requiring WSDL rejection.
Remove the native discrepancy entries once the native correction passes; retain
the historical diagnostic. Validator discrepancies do not change the normative
classification or supported scope.

Reproduce the matrix with the local module and runtime paths:

```sh
python3 test/wsdl-interop/test_substitution_particles.py -v
```

The worker reports `native_error` separately from WSDL `error` for every schema.
The two native failures are `invalid-5` and `unused-invalid-5`; their required
native error is `XSD-SYNTAX-ERROR`, while the recorded result is empty.

## Implemented correction (P5-08)

The private provider now checks all resolved complex models and named groups
before automaton construction, with separate declaration scopes and an iterative
visited graph. It includes explicit abstract heads and admitted concrete members,
uses exact expanded names, and preserves canonical declaration identity. Native
reader/DOM construction rejects both original fixtures with `XSD-SYNTAX-ERROR`;
the native discrepancy overrides were removed from the child-substitution matrix.
The original diagnostic JSON and supporting lxml/Xerces discrepancies remain.

A 34-schema configure probe checks positive/negative cases and rejects a real
system library missing only EDC. All 38 distinct provider tests pass, including corrected
system selection, AUTO fallback, SYSTEM rejection, stable reconfiguration,
source hash guards, distribution and 69 injected allocation failures. The new
native unit tests include actual imported member/group conflicts, anonymous and
inherited models, shared graphs, zero and large counts, replacement recovery,
cancellation and concurrent readers. An independent 43-schema matrix compares
native DOM/reader and WSDL original/reconstructed validation against pinned
Xerces and lxml, keeping unused-group oracle omissions explicit.

The [implemented design](../../design/native-element-consistency.md) describes
the scope, error mapping and allocation ownership. Final mode, regression,
Valgrind and corpus evidence belongs in `P5-08-validation.json` and the P5-08
execution entry; P5 and later phases remain open.
