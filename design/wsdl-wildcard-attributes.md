# Wildcard attribute values

Copyright (C) 2026 Qore Technologies, s.r.o.

`XsdComplexType` uses its resolved attribute wildcard for instance admission.
Element wildcard admission is independent. The namespace algebra for groups,
extensions and restrictions remains in `XsdAttributeWildcardHelper`; conversion
uses that completed component rather than the legacy `anyAttribute` content flag.

The rules follow [XSD 1.0 Structures, second edition, sections 3.4.4 and 3.10.4](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/).
An explicitly declared attribute use takes precedence. Every wildcard attribute
must satisfy the namespace constraint, including under `skip`. `strict` requires
a global attribute declaration and validates its value. `lax` validates an
available declaration; otherwise it preserves unassessed text. `skip` preserves
text without consulting a declaration. Global default values do not introduce
absent wildcard attributes. Available declarations enforce fixed values and
scalar/list/QName constraints through the existing attribute conversion APIs.

For assessed wildcard IDs, at most one wildcard attribute can have an ID-derived
type. If one does, the containing type cannot also have a declared ID attribute
use, even when that optional attribute is absent. `skip` does not assess IDs.
These checks are local attribute-use rules; document-wide identity constraints
are separate. The interoperability record identifies the independently
reproduced native libxml2 reporting defect without counting it as a passing check.

## Public representation

Native values retain the existing `^attributes^` hash. Declared uses keep their
existing field names. Wildcard attributes use `{namespace-uri}local`, including
`{}local` for no namespace. Identical local names in different namespaces remain
distinct. Serialization also accepts a bare key for an unqualified wildcard
attribute and an expanded alias for a declared field. Two keys identifying the
same XML attribute are rejected before either value can overwrite the other.
Namespace declarations are context, not attribute entries; malformed expanded
names, invalid XML characters and `xmlns` attribute keys are rejected.

Known attributes retain their typed native values. Unassessed attributes use
`XsdScopedLexicalValue`, retaining text and the complete input namespace context,
including absence of a default namespace. This is additive: these values were
previously discarded. Output keeps unassessed lexical spelling rather than
inferring a scalar datatype. Callers may supply plain XML text when constructing
an unassessed attribute, or an explicit carrier when its namespace context matters.
Conflicting lexical namespace requirements on one element cause a serialization
error. Use `serializeXmlValue()` for standalone XML and the SOAP operation APIs
for messages; their complete XML trees permit namespace allocation and rewriting.

For example, a shipment may carry a declared quantity and a partner's unassessed
classification:

```qore
XsdSchema schema('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"'
    ' targetNamespace="urn:shipments"><xs:attribute name="quantity" type="xs:int"/>'
    '<xs:element name="shipment"><xs:complexType><xs:anyAttribute processContents="lax"/>'
    '</xs:complexType></xs:element></xs:schema>');
auto native = {"^attributes^":{
    "{urn:shipments}quantity":17,
    "{urn:partner}classification":new XsdScopedLexicalValue("p:Stock", {"p":"urn:products"}),
}};
XsdXmlValue xml = schema.serializeXmlValue("urn:shipments", "shipment", native);
```

Retained `XsdXmlValue` paths validate these same rules and keep the original
lexical XML. Request and response processing use the same attribute conversion.

## Declaration and namespace ownership

Each schema namespace context shares an `XsdGlobalAttributeRegistry`. Resolution
publishes the complete global attribute map only after successful component and
substitution validation. A failed incremental addition restores the earlier map.
Imported, no-namespace and existing contexts therefore see the same completed
attribute declarations. Schema and WebService reconstruction replay source
schemas; serialized provider graphs carry the registry and resolved declarations.

Schema configuration, including `addSchemaString()`, must finish before concurrent
use. Existing wildcard providers use the shared live declaration registry during
that configuration stage. A separately serialized provider has its own restored
registry. Unlike finite substitution alternatives, wildcard metadata describes
an open namespace constraint; it does not promise a closed list of known fields.

SOAP serialization copies the namespace map for each message. Body and header
conversion allocate names in that map; envelope declarations are collected after
all parts have been serialized. New partner namespaces cannot mutate the shared
schema or leak between concurrent messages. Standalone serialization already
uses its own map. Scoped output context restores on errors and cancellation.

## Providers, validation and cost

`XsdAttributeMapDataType` extends `HashDataType`. Its ordinary native acceptance
path normalizes aliases before required-field conversion, rejects duplicate XML
names, checks wildcard namespaces and available declarations, and preserves
unassessed carriers. It disables direct native assignment shortcuts that would
bypass these checks. Soft and optional copies retain the subclass and constraints;
serialized metadata is checked before it is accepted.

`getAttributeWildcard()` returns a copy of the effective namespace and processing
metadata. Declared fields retain their descriptions, fixed/enumerated choices and
defaults. Wildcard-only and simple-content providers include the attribute map;
empty complex content without required attributes keeps its native `NOTHING`
value. Element presence is checked by the surrounding element/message contract.

An invocation builds indexes for the declared uses and performs constant-time
lookups for supplied attributes. Attribute admission and ID-use checks take
O(D + A) index work and storage, excluding datatype conversion and ID-ancestry
checks, where D is the number of
declared uses and A the number of supplied attributes. Namespace maps and native
hashes use Qore's copy-on-write values. No production filesystem/network operation
or unbounded retry loop is introduced.

Executable unit, provider, HTTP, concurrency, cancellation and independent
validator coverage is recorded in
[the P5-10 evidence](../test/wsdl-interop/wildcard-attributes-evidence.md).
