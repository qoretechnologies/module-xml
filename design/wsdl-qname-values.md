# Explicit QName values and providers

Copyright (C) 2026 Qore Technologies, s.r.o.

`XsdQNameValue` retains a namespace URI, a local name, and the normalized QName
spelling. `equals()` compares the URI and local name exactly. Prefix aliases,
including an unprefixed spelling under a default namespace, do not change that
identity. URI case, percent escapes and Unicode composition remain significant.
The lexical spelling is retained separately for pattern restrictions.

The constructor takes an explicit URI and lexical QName. `fromLexical()` resolves
text using a prefix-to-URI map; the empty key supplies the default namespace.
XML whitespace is collapsed, both components use the XSD 1.0 NCName grammar,
and unbound prefixes, reserved namespace bindings and non-XML URI characters
are rejected. The implicit `xml` prefix always denotes the XML namespace.
An explicit empty default namespace and an absent default namespace both
produce an empty URI. Namespace maps are validated in full, including unused
bindings. These operations raise `XSD-QNAME-VALUE-ERROR` on invalid values.

The class is immutable. `Serializable` reconstructs it from the URI and lexical
strings, validates both, and derives the local name and prefix again. Invalid
serialized state raises `DESERIALIZATION-ERROR`. Returned strings and maps use
Qore's copy-on-write semantics.

`XsdQNameDataType` accepts lexical text with an explicit namespace context, or
an existing `XsdQNameValue` carrying its own identity. Namespace-qualified
text results are objects. No-namespace text and implicit `xml` text remain
strings. Explicit QName objects retain their object representation, including
no-namespace values. Repeated conversion through the same provider or one with
another default namespace therefore preserves their identity.

Provider construction rejects invalid bindings with `XSD-SIMPLETYPE-ERROR`;
conversion uses `RUNTIME-TYPE-ERROR`. Omitted mandatory values raise
`MISSING-VALUE-ERROR`; optional providers accept omission but reject empty text.
Mandatory/optional copies and reconstruction retain the namespace context.
`getValueType()` returns `NOTHING` and `getDirectTypeHash()` is empty so enclosing
record and list providers always validate their contents. The legacy base
category is `string`; `getReturnTypeHash()` advertises `string` and `object`.

```qore
%modern
%requires WSDL
XsdQNameDataType category({"c": "urn:catalog", "alias": "urn:catalog"});
XsdQNameValue product = category.acceptsValue(" c:Product ");
XsdQNameValue same_product = category.acceptsValue("alias:Product");
@assert(product.equals(same_product));
@assert(product.getNamespaceUri() == "urn:catalog");
@assert(product.getLocalName() == "Product");
@assert(product.getLexicalValue() == "c:Product");
XsdQNameDataType restored = Serializable::deserialize(category.serialize());
@assert(restored.acceptsValue("alias:Product").equals(product));
```

These APIs provide explicit QName values and detached provider conversion.
Ordinary WSDL scalar decoding, schema enumeration/default/fixed constraints,
and XML prefix allocation still use their existing paths. The explicit object
is not yet an implicit input or output of those paths. Complete retained XML
continues to use `XsdXmlValue`.

The implementation follows [XSD 1.0 QName value space](https://www.w3.org/TR/xmlschema-2/#QName)
and [namespace scoping and default resets](https://www.w3.org/TR/1999/REC-xml-names-19990114/#scoping).
`test/wsdl-qname-values.qtest` covers identity, encodings, invalid values/state,
provider metadata, containers, cancellation and concurrent copies.
`test/wsdl-interop/test_qname_values.py` compares explicit values and providers
with independent XSD enumeration results through retained XML scopes.
