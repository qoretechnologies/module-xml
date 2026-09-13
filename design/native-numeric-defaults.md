# Native canonical numeric constraint declarations

Copyright (C) 2026 Qore Technologies, s.r.o.

The native XSD 1.0 schema compiler checks numeric, boolean and binary default/fixed
constraints twice: the source spelling must be valid, and its canonical spelling
must also satisfy the receiving simple type. This implements
[e-props-correct.2 and a-props-correct.2](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#e-props-correct).
It applies to element declarations, complex simple content, attribute declarations
and constraints supplied by attribute references.

For example, an integer restriction with pattern `0017` can accept explicit
instance text `0017`, but cannot declare that spelling as a default: the canonical
form `17` fails its pattern. A pattern `0017|17` admits both and permits that
default. Default and fixed declarations use the same check.

The private libxml2 correction constructs a temporary lexical string from the
already selected computed value. Integer and decimal canonicalization retains
arbitrary precision and removes the sign of zero; booleans use `true` or `false`.
Hexadecimal binary text uses uppercase digits; Base64 text has no whitespace.
Lists join selected item spellings with one space. Numeric/boolean/binary union members
are canonicalized only when actually selected. A union selecting string first
keeps its text. Other atomic families retain their source spellings and namespace
context; QName has no context-independent canonical lexical form in XSD 1.0.

The second assessment checks validity only. It does not replace the declaration's
original lexical string, computed value, namespace context or selected member.
The temporary buffer and canonical item strings have one owner and are freed on
success, rejection and allocation failure. All state is local to the call, and
traversal and storage are linear in the constraint's size. Native entry and I/O
cancellation boundaries remain unchanged; the standalone libxml2 C dependency
does not acquire a Qore runtime dependency.

CMake tests the installed provider with positive and negative element/attribute
declarations. AUTO falls back to the pinned private library on failure; SYSTEM
rejects the provider. Both input and generated source hashes are checked. The
correction changes only build-tree source and preserves timestamps on repeated
configuration.

This is a schema-declaration correction for integer, decimal, boolean and binary families,
including their selected list/union members. Instance-default projection and
canonical handling of other atomic families have separate coverage ownership in
P5. In particular, this correction does not decide the interaction between
selected instance types and the E1-56 PSVI erratum.

The 396-case declaration matrix is exercised through native conversion, DOM and
stream validation in `test/xml-numeric-defaults.qtest`, with a pinned Xerces check
in `test/wsdl-interop/test_numeric_defaults.py`. The standalone C allocation test
checks each declaration entry point, exact temporary spellings, empty/singleton
lists, mixed QName/numeric lists, buffer growth and recovery after failure.
The [binary extension](native-binary-constraints.md) adds declaration, lexical
and allocation regressions for hexadecimal and Base64 values.
