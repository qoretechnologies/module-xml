# QName values and declaration validation

Copyright (C) 2026 Qore Technologies, s.r.o.

## Enumeration declaration validation

QName enumeration literals capture their namespace URI while the facet's XML
namespace scope is active. Every literal is retained until the base type has
resolved, including duplicate spellings with different namespace bindings.
Captured state contains the normalized lexical text and one URI, rather than a
copy of all in-scope namespaces. Temporary declarations are released after
finalization, including when validation raises an exception.

Finalization validates the QName grammar and requires a bound prefix. It checks
each literal against every inherited pattern and enumeration. Namespace/local
identity uses nested hash keys, with no prefix comparison or URI normalization.
The new restriction's own pattern applies to instances; it does not constrain
the spelling used to declare that restriction's enumeration values. Deprecated
QName length facets do not measure the spelling.

Whole `XsdSchema` objects retain their original schema sources and reparse them
during Serializable reconstruction. The declaration checks therefore apply to
reconstructed schemas and subsequent additions. Instance conversion resolves text
in the containing XML element's namespace context before applying these constraints.

For example, a base enumeration declared as `a:Product` with `a` bound to
`urn:catalog` permits a derived enumeration `b:Product` with the same URI.
Rebinding `b` to `urn:other` rejects the derived schema. If the base additionally
requires the lexical pattern `a:Product`, the alias spelling does not satisfy
that inherited pattern.

## Explicit values and providers

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

## Attribute provider choices

`XsdAttributeDataType` separates attribute presence from scalar conversion.
`getWrappedType()` exposes the underlying validator; `getElementType()` still
returns only a collection's item provider. `XsdQNameDataField` unwraps attribute
presence before resolving its finite choices, then uses the same namespace and
expanded-name rules as an element field. Presence checks stay on the original
wrapper. Optional/mandatory copies and saved fields retain this behavior.

This applies to enumerated and fixed QName attributes, including references,
attribute groups and simple content. Record keys remain local names unless
attribute names collide. For example, a required attribute restricted to
`c:Product` in `urn:catalog` accepts an explicit `alias:Product` value in that URI,
but rejects the same local name in another URI and rejects omission. An optional
attribute with that default supplies the declared QName when omitted.

## SOAP and standalone XML

Ordinary SOAP decoding retains namespace-qualified QName values as
`XsdQNameValue`. Local names in no namespace and implicit `xml` names remain
strings. Scopes include Envelope, Header, Body, the payload and each descendant;
local rebinding and an empty default reset override their ancestors. Elements,
attributes, simple content, lists and ordered union trials share this behavior.
Attribute defaults and fixed values keep their declaration identity, independently
of the instance's aliases. Fixed comparisons use expanded names.

Serialization retains namespace-bearing values until the complete XML tree is
available. It declares data bindings on the containing element and rewrites
conflicting element/attribute prefixes without changing their expanded names.
Data spellings remain available to lexical pattern facets. Retained XML message
parts carry their validated native namespace requirements through envelope
allocation, preventing new ancestor bindings from changing string-fallback union
selection while preserving the supplied XML text. Values sharing one
element must require compatible data bindings; conflicting data spellings raise
`SOAP-SERIALIZATION-ERROR`. Standalone lists also reject a binding that would change
another item's unbound-prefix string selection. Input and output tree scopes restore
only the declarations changed at each node, avoiding full inherited-map copies at
every depth. Prefix filtering inspects each node's own declarations. Low-level `serializeValue()` results are XML fragments
whose structural namespace context belongs to their caller.

Decoding resolves parsed element keys to expanded names once per message body
(`XsdBase::expandElementNamespaces()`). Each distinct element key is checked as
an XML name once per document; its prefix is still resolved in the scope of
every occurrence. An element without attributes declares no prefixes, so its
scope is the parent's, and only the implicit `xml` binding is in scope for a
QName scope without attributes. Namespace binding checks depend only on the
prefix and URI: a binding found valid is remembered in a bounded map, keyed
unambiguously by the prefix length, prefix and URI, and replaced as a whole on
update so that concurrent readers see a consistent map. Invalid bindings are
never remembered and are rejected on every use.

`XsdSchema::serializeXmlValue(namespace_uri, local_name, value)` returns a complete
`XsdXmlValue` for a global element. It uses a private copy of the schema's namespace
registry, handles QName attributes and simple content, and leaves the original
registry unchanged after success or failure. Missing global elements raise
`WSDL-ERROR`; invalid native content raises `SOAP-SERIALIZATION-ERROR`.
`WSMessageHelper::getMessage()` and `getXmlMessage()` preserve declaration context
when generating QName union enumeration examples.

```qore
%modern
%requires WSDL
XsdSchema schema('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
    targetNamespace="urn:orders"><xs:element name="Category" type="xs:QName"/>
    </xs:schema>', {"async_only": True});
XsdQNameValue category("urn:catalog", "c:Product");
XsdXmlValue xml = schema.serializeXmlValue("urn:orders", "Category", category);
@assert(xml.getNamespaceUri() == "urn:orders");
@assert(xml.getLocalName() == "Category");
@assert(schema.validateXmlValue(xml) === xml);
```

## Namespace-sensitive union text

An ordered union can select a string after an earlier QName member rejects an
unbound prefix or a disallowed namespace identity. `XsdScopedLexicalValue` retains
that text and its namespace bindings, including the absence of a binding needed
to preserve the selected member. Lists retain these values per item; successful
QName alternatives return QName values and successful list alternatives return
lists. Patterned QName-capable collections retain item lists (including an empty
list), preserving each QName or scoped token while applying the whole-list lexical
pattern. Other patterned unions keep their existing string representation.
Malformed QName spellings that cannot select a QName remain ordinary text.

The public constructor takes XML character text and a prefix-to-URI map. It
preserves whitespace, permits empty or non-QName strings, and rejects invalid XML
characters or namespace bindings with `XSD-SCOPED-VALUE-ERROR`. The object is
immutable; getters return copies. Serializable reconstruction validates both fields
and raises `DESERIALIZATION-ERROR` for malformed state.

```qore
XsdScopedLexicalValue legacy("category:Legacy", {});
@assert(!legacy.getNamespaceBindings().hasKey("category"));
@assert(Serializable::deserialize(legacy.serialize()).getLexicalValue()
    == "category:Legacy");
```

Detached providers pass retained context only to the member receiving the value.
An independent provider called by a custom callback keeps its own bindings.
Schema serialization scopes additionally belong to the exact namespace registry
passed to that conversion; output retention is similarly restricted to its own
registry so independent callbacks keep ordinary serialization results. Per-thread
scopes restore their callers after normal return, validation failure and cancellation;
concurrent conversions do not share mutable namespace maps.

## Restricted providers and field choices

`XsdQNameRestrictionDataType` retains typed `XsdQNameFacetInfo` and its base
provider. Enumeration indexes compare URI/local identity; lexical patterns apply
at every derivation step. Optional copies and `withNamespaceBindings()` retain
all restrictions. Deep built-in restriction chains convert iteratively, while
custom base providers keep their callback behavior. Reconstruction rejects cyclic
or incomplete bases before invoking them and rebuilds transient indexes.

`XsdQNameDataField` compares scalar and repeated choices using expanded names.
It preserves the existing `AllowedValueInfo` display metadata, permits lexical
aliases only when provider patterns allow them, and updates choice indexes
after validating every new choice. As with the underlying `QoreDataField`, configure
field metadata before sharing it for concurrent conversions. Reconstructed fields
derive their indexes from authoritative choices.
Union field metadata also converts enumeration values with their declaration
bindings, so an alias does not become a different string choice.

The implementation follows [XSD 1.0 QName value space](https://www.w3.org/TR/xmlschema-2/#QName)
and [namespace scoping and default resets](https://www.w3.org/TR/1999/REC-xml-names-19990114/#scoping).
`test/wsdl-qname-values.qtest` covers identity, encodings, invalid values/state,
provider metadata, containers, cancellation and concurrent copies.
`test/wsdl-interop/test_qname_values.py` compares explicit values and providers
with independent XSD enumeration results through retained XML scopes.


Integration regressions are `wsdl-qname-provider-context.qtest`,
`wsdl-qname-provider-facets.qtest`, `wsdl-qname-schema-output.qtest`,
`wsdl-scoped-lexical-values.qtest` and `wsdl-qname-consumers.qtest`.
`test/wsdl-interop/test_qname_context.py` checks scoped XML, detached and
reconstructed consumers, native/retained XML examples, both SOAP versions and
directions, expanded values, and independent schema validation.
