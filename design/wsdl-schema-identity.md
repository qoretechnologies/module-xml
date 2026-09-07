# Schema identity and reconstruction

Copyright (C) 2026 Qore Technologies, s.r.o.

Element and simple-type QNames are captured in their declaration's namespace context.
`Namespaces::getTypeHash()` retains the local name, namespace URI, and optional output
prefix. An absent namespace is an empty URI; an unbound prefix is an error. Output
prefix allocation does not determine component identity. Declaration scopes restore
input and reverse maps, including new prefixes, shadowed XSD prefixes and `xmlns=""`.

The type registry contains canonical `{uri}name` keys, including `{}name` for types
without a target namespace. Existing bare-name aliases remain available to public
callers; source QName resolution never uses those aliases. `make_qname()` retains its
existing public formatting behavior. Global elements retain their original declaration
attributes while resolving their types.

Complex-content base references likewise retain their declaration context in
`baseTypeInfo`; `baseType` holds the resolved type object after validation.
Empty extensions inherit the base content model, elements and attributes.
Restrictions retain the declared restricted particle rather than merging removed
base elements back into it. SOAP encoding's Array base is identified by URI and
local name, so unrelated custom types named Array remain usable. Finalization
distinguishes an active derivation from a completed type and rejects cycles before
publishing base links. Generic/mixed content handling is separate from base identity.

Global attributes have their own expanded-name registry, `XsdSchema::attributeMap`,
and can be inspected with `getAttribute(uri, localName)`. Attribute references retain
their declaration namespace in `refInfo`, resolve through this registry, and share the
declared simple type. Local anonymous simple types enter the normal late-resolution
queue. An attribute with no explicit type has `xs:anySimpleType`, whose scalar lexical
strings remain strings, including empty content and whitespace.

Attribute construction checks name/ref and type/anonymous exclusivity, global/local
constraints, use/form values, and contradictory default/fixed declarations. It rejects
complex attribute types before payload processing. Each declaration records its namespace
URI, including local form overrides and the scoped schema attribute form default. Required
and prohibited uses apply independently of whether the incoming value has an attribute hash.
The attribute registry participates in failed-addition rollback and source reconstruction.

For example, a consumer can inspect an imported partner flag without depending on the
source prefix spelling:

```qore
XsdAttribute flag = schema.getAttribute("urn:partner:invoice", "approved");
auto typed_flag = flag.getValue("false");  // False for an xs:boolean declaration
```

`XsdSchema` stores original XSD documents with their resolution bases in
`XsdSourceInfo` records. Successfully retrieved import/include bytes are cached by
normalized location. Serializable reconstruction rebuilds transient registries from
the saved documents and dependencies, without invoking the original import callback.
`WebService` retains its WSDL reconstruction hook and inherits the dependency cache.
Old standalone serialized schemas with no source documents produce
`DESERIALIZATION-ERROR`; their omitted declarations cannot be recovered.

Failed additions restore the component registries, dependency cache and import marks.
Namespace guards restore declaration context on both normal and exceptional exits.
Schema construction is mutable and must finish before an object is shared between
threads. Restored schemas remain extensible through the existing addition methods.

An ordered XmlReader pass checks XSD schema child names and the requirement that
imports/includes/redefines precede component declarations. It runs before schema
resolution for standalone, imported and WSDL-inline schemas. It ignores annotation
payloads and preserves the original malformed-XML error from `parse_xml()`.
This implements those construction constraints, not the complete WSDL grammar.

The implementation follows XSD 1.0 [QName resolution](https://www.w3.org/TR/xmlschema-1/#src-resolve),
[complex type derivation](https://www.w3.org/TR/xmlschema-1/#derivation-ok-extension),
[attribute declarations](https://www.w3.org/TR/xmlschema-1/#src-attribute),
and [schema representation](https://www.w3.org/TR/xmlschema-1/#element-schema).
Regression coverage is in `test/wsdl-namespace-context.qtest`,
`test/wsdl-derivation-context.qtest`, `test/wsdl-attribute-context.qtest`, the strict W3C namespace/empty-extension
selection, corrected attribute-owner derivatives, and whole-archive grammar checks.
