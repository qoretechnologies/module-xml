# Open P5 native element-declaration consistency requirement

Copyright (C) 2026 Qore Technologies, s.r.o.

The P5 child-substitution matrix found a pre-existing native schema-construction
gap. WSDL rejects two schemas in which a substitution member and an explicit
local element have the same expanded name and different types. The private
libxml2 provider accepts both: one model is used by `Container`; the other is an
unused named group. These are failed native requirements, not valid schemas.
The next native P5 increment owns their correction before P5 acceptance.

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
