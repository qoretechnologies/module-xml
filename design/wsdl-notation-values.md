# WSDL NOTATION values and providers

Copyright (C) 2026 Qore Technologies, s.r.o.

## Primitive values

`XsdNotationValue` retains a namespace URI, local name and normalized QName
spelling. Its value space is distinct from QName; the immutable implementation
contains an `XsdQNameValue` but does not inherit from it. `equals()` compares two
notation expanded names, and `asQName()` explicitly returns the name as a QName.
Construction validates spelling and reserved bindings; the receiving schema or
provider separately requires a matching notation declaration. Invalid carrier
construction raises `XSD-NOTATION-VALUE-ERROR`.

```qore
%modern
%requires WSDL
XsdSchema schema('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:m="urn:media" targetNamespace="urn:media">
    <xs:notation name="jpeg" public="image/jpeg"/>
    <xs:simpleType name="Format"><xs:restriction base="xs:NOTATION">
    <xs:enumeration value="m:jpeg"/></xs:restriction></xs:simpleType>
    <xs:element name="format" type="m:Format"/></xs:schema>');
XsdNotationDataType format(schema.nsc.getNotationRegistry(), {"m": "urn:media"});
XsdNotationValue value = format.acceptsValue(" m:jpeg ");
@assert(value.equals(new XsdNotationValue("urn:media", "alias:jpeg")));
XsdXmlValue xml = schema.serializeXmlValue("urn:media", "format", value);
@assert(schema.validateXmlValue(xml) === xml);
```

Every successful NOTATION conversion returns a carrier, including names without
a namespace. This applies in ordinary decoding as well as `preserve_types=True`.
The latter additionally retains selected schema types at element boundaries.
Scalar conversion, lists, unions, fixed/default constraints, native fields and
message providers share the declaration and expanded-name rules. Union identity
keys include the primitive family, so a QName and NOTATION with the same expanded
name have distinct identities. XML prefix allocation uses the wrapped QName only
after the primitive identity has been captured.

An explicit notation supplied to generic `anyType`/`anySimpleType` emits its
builtin `xsi:type`. Dynamically selected builtins retain the receiving declaration
registries while using independent output namespace state.

## Declaration and type-use validation

The completed [notation registry](wsdl-notation-declarations.md) is published
before restrictions resolve. NOTATION enumeration literals must identify a
declared notation and satisfy inherited restrictions. Enumeration membership
compares expanded names; patterns constrain lexical spelling. Schema declaration
bindings remain separate from instance bindings and provider lexical contexts.

The enumeration requirement is checked on schema component uses. Elements and
attributes cannot use unrestricted NOTATION, and list items/union members must
be appropriately restricted, including in unused collection definitions. Unused
atomic or simple-content intermediate restrictions remain legal; a later
restriction can supply the enumeration. Builtin NOTATION selected dynamically
still has its declared-notation value space. Validation does not invent an empty
builtin lexical space to enforce a component constraint.

The late resolver records element/attribute uses and simple definitions whether
or not they require forward-reference resolution. After the existing type graph
has resolved, iterative ancestry and collection walks apply the use constraint.
Ancestry results and visited collection nodes are cached. The temporary tracking
lists belong to the construction helper and are discarded with it.

## Detached providers

`XsdNotationDataType` owns the shared `XsdNotationRegistry` and lexical bindings.
It does not retain the complete namespace/type graph merely for declaration
lookup. This permits facet validation during saved-provider reconstruction
without calling through a partly initialized schema cycle. Registry mutation is
construction-only; complete it before concurrent reads. Returned declaration
maps have value semantics.

The provider accepts lexical/scoped text, an explicit notation carrier or an
explicit QName used as the notation's name. A QName provider requires explicit
`asQName()` conversion before accepting a notation carrier. Mandatory omission
raises `MISSING-VALUE-ERROR`; invalid names, bindings or membership raise
`RUNTIME-TYPE-ERROR`. Optional, mandatory and namespace-context copies preserve
restrictions and declaration membership. Return metadata advertises objects;
legacy base metadata remains the closest string category. Direct assignment is
disabled so enclosing records always validate supplied values.

`XsdNotationRestrictionDataType` validates its acyclic base chain and applies
inherited facets iteratively. Corrupt reconstructed registries, values, providers
and facets raise `DESERIALIZATION-ERROR`. `XsdNotationDataField` validates finite
choices using the actual scalar provider, including through attribute wrappers.
Choice indexes are rebuilt from authoritative saved choices; failed replacements
publish no partial state. Examples are checked notation values, using enumeration
spellings and available namespace aliases. If none satisfies the provider,
`XSD-SAMPLE-ERROR` is preferable to returning an invalid generic string.

Identity-checking element wrappers establish their receiving named-type map for
their own serialization pass. A nested native provider's temporary map has already
been restored when the outer wrapper performs that pass. This keeps named dynamic
QName and NOTATION types resolvable through standalone, saved and message providers.
All conversion scopes restore on success, validation failure and cancellation.

## Requirements

- [XSD 1.0 Part 1 notation declarations](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cNotation_Declarations).
- [XSD 1.0 Part 2 NOTATION](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#NOTATION).
- [Element validity and defaults](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-elt),
  with the project's approved canonical-actual-type default interpretation.
