# XSD instance type substitution

Copyright (C) 2026 Qore Technologies, s.r.o.

Schema construction retains effective `block` sets and `abstract` flags.
`Namespaces::schema_block_default` belongs to the active source and restores on
all exits. Imported, included and reconstructed schemas use their own defaults.
Complex types filter defaults to extension/restriction; element declarations
also retain substitution. An explicit empty block overrides the default.
`XsdSubstitutionMethod` identifies these names. `getBlockedSubstitutions()` returns
a copy of the component set; `isAbstract()` exposes its abstract property.
Global references copy the referenced declaration's controls and nillability.
Legacy array adapters carry the enclosing complex declaration's properties.

Control parsing uses XML whitespace. Invalid methods, mixed `#all` lists and
misplaced anonymous/simple-type controls fail with `WSDL-ERROR`. Boolean controls
accept the four XSD spellings after XML whitespace normalization. Block metadata
is distinct from the [construction-time final controls](wsdl-type-final.md).

`XsdTypeSubstitutionHelper` checks resolved component identities and follows the
complete simple or complex derivation path. Canonical builtins use their fixed
parent graph; custom conversion classes retain their own identity. Simple union
bases contribute their composed member definitions. Each derived/base pair is
queued once with an explicit worklist, avoiding recursive path expansion in
shared union graphs. Base restriction chains cache their union members, including
an absent union, for the duration of each check. Memory is bounded by reachable
component pairs and the cached base graph; duplicate edges do not allocate
duplicate pending pairs. Builtin
ancestry has a fixed maximum depth; identity takes the constant-time path.
Tests exercise 1000-step complex and unrelated simple chains, 10000 repeated
member references and 40 levels of duplicated union edges,
as well as defensive termination for a subsequently mutated cyclic graph.
Schema construction independently rejects invalid declaration cycles.

The checks implement XSD 1.0 Structures
[Type Derivation OK (Complex)](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-ct-derived-ok),
[Type Derivation OK (Simple)](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-st-derived-ok)
and [Element Locally Valid](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-elt).
The exclusion set stays fixed while following a path. Complex selections combine
the element's block with the declared type's block. Intermediate ancestors do
not add their block sets. Identity remains valid under block; an abstract selected
type still cannot validate an instance. Abstract element declarations require an
actual substitution member; merely choosing a concrete type does not instantiate
the abstract element itself. Optional absent occurrences create no instance.

Selection resolves `xsi:type` using the current instance namespace scope before
attribute or value conversion. Unknown/unbound/incompatible/abstract selections
raise `SOAP-DESERIALIZATION-ERROR`. The private working hash consumes the checked
annotation and keeps its other attributes and namespace bindings. Direct builtin,
simple and complex type APIs share selection with element and document APIs.
Native wrappers validate the selected component before emission and retain its
owned type annotation. A different anonymous component cannot provide an
`xsi:type` name and is rejected by native serialization. Omitted optional values
are handled before instantiation checks.

`XsdXmlValue` keeps the original type annotation in its immutable source XML.
Native conversion retains the established scalar/record field shapes by default.
The explicit [native type capture option](wsdl-native-type-values.md) retains
portable selected QNames and values for independent reconstruction. Callers
that need the complete XML instance can use the retained XML APIs; callers that
select a native type explicitly use the existing `^type^`/`^val^` wrapper. For
example, an invoice can select a concrete taxable amount derived from its base:

```qore
XsdSchema invoice("<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
    "<xs:simpleType name='Amount'><xs:restriction base='xs:decimal'/></xs:simpleType>"
    "<xs:simpleType name='TaxableAmount'><xs:restriction base='Amount'>"
    "<xs:minInclusive value='0'/></xs:restriction></xs:simpleType>"
    "<xs:element name='amount' type='Amount' block='extension'/></xs:schema>");
XsdXmlValue output = invoice.serializeXmlValue("", "amount",
    {"^type^": invoice.findType("TaxableAmount"), "^val^": "12345678901234567890.25"});
```

Detached serializer output requires the output namespace context when used as
input. Union value probes now carry prefixes used by both attribute names and
their type QName values. This avoids changing the chosen union value merely
because a detached probe lacked an emitted prefix binding. Test callers that
construct detached IEEE and array fragments supply their actual output context.
Unbound wire prefixes remain errors.

All traversal and conversion state is local. Getters return immutable-after-
construction metadata by value; caller output registries own new prefixes.
Canonical builtin selection uses independent output state instead of updating a
shared schema's lazy cache. Cancellation propagates through the existing Qore
runtime; namespace scopes restore on errors. Concurrent tests use queue barriers
and bounded completion counters.
