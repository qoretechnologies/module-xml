# Schema identity and reconstruction

Copyright (C) 2026 Qore Technologies, s.r.o.

Element and simple-type QNames are captured in their declaration's namespace context.
`Namespaces::getTypeHash()` retains the local name, namespace URI, and optional output
prefix. An absent namespace is an empty URI; an unbound prefix is an error. Output
prefix allocation does not determine component identity. Declaration scopes restore
input and reverse maps, including new prefixes, shadowed XSD prefixes and `xmlns=""`.
An input prefix must be declared even when its spelling is `xsd`; builtin output
uses a separately registered canonical prefix. Builtin type names and component
declaration NCNames are checked during construction.

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

Simple-content derivations retain the expanded base identity as well. Extensions
inherit scalar content and attributes; restrictions apply their facets to the
effective scalar base, including anonymous restrictions and the anyType ur-type
with an inline simple type. Anonymous declarations participate in finalization.
The existing `^value^`/`^attributes^` representation is accepted by bare-message
extraction. False, zero and empty scalar results use the same return shape.

Simple-type dependencies resolve in depth-first order before union provider types
are constructed. Active dependencies detect cycles; completed dependencies are
resolved once per construction. Named union members precede anonymous members in
source order. Lists require atomic item types or unions of atomic types. Complex
dependencies and contradictory restriction/list/union declarations fail during
construction. List-item variety checks cache results per resolved type, so shared
union dependencies are visited once. These checks are separate from scalar lexical and facet semantics.

Element references retain their expanded name, including references with no namespace.
Local `form` overrides determine output qualification independently of the containing
type's schema default. Input QName lookup does not substitute the target namespace
for an absent default namespace.

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

Attribute declarations retain default/fixed lexical forms and resolve their typed
constraint values after simple-type dependencies are finalized. Referenced uses
inherit constraints; a local override of a globally fixed value must retain the
same fixed value. Absent optional attributes receive their default/fixed value.
Required fixed attributes still require an explicit value. Supplied fixed values
are checked during both serialization and deserialization. Bare complex messages
consume `^attributes^` alongside their element members, including empty content
models. Scalar value-space handling remains in the datatype layer.

Instance attribute names resolve against their actual in-scope namespace declarations
before the SOAP tree's element prefixes are removed. Descendants receive only the
prefix bindings used by their attributes, including descendants inside `^value^`
lists. Scoped traversal restores bindings between siblings and on exceptional exits;
SOAP decoding does not modify the caller's parsed input. Ordinary undeclared
attributes are rejected on simple and non-wildcard complex types.

Attribute maps and decoded `^attributes^` hashes retain local keys when the local
name is unique. When multiple declarations share a local name, every conflicting
key uses `{uri}name`, including `{}name` for no namespace. Serialization accepts
these keys and allocates wire prefixes from the declaration URI. An ambiguous
local key fails. The representation also survives groups, inheritance and schema
reconstruction. For example, an unqualified numeric invoice code and a qualified
boolean partner code remain separate:

```qore
hash<auto> invoice = {"^attributes^": {"{}code": 7, "{urn:partner}code": False}};
```

Prohibited declarations contribute no attribute-use component or reported field.
In a restriction, their expanded names suppress inherited uses. They cannot remove
a required base use unless a required replacement is supplied. Local group uses
resolve before inheritance, and duplicate live expanded uses are rejected.

Low-level `serializeValue()` results are XML fragments using the supplied output
namespace registry. A caller decoding such a fragment independently supplies its
enclosing namespace context with `XsdBase::inheritAttributeNamespaces()`; ordinary
SOAP serialization declares that context on the envelope.

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

All documents in an import/include graph contribute declarations before type
resolution starts. Cached bytes are shared by normalized location; component
deduplication also includes the effective namespace. Chameleon includes instantiate
their no-namespace definitions and QName references in each including namespace.
Active source, namespace and resolution-base identities recognize a root provided
as XML when a dependency refers back to it. Imports verify the retrieved target
namespace, while includes accept a matching or absent target namespace. An inline
schema without a target namespace does not inherit the surrounding WSDL's target.
Repeated identical references reuse successful validation; changing the import/include
mode validates that mode before reusing component identities.

Group and attribute-group definitions and references capture declaration scopes.
Internal references use canonical expanded keys; no-namespace registry aliases
remain available to callers using `getQualifiedName()`. Undefined references and
cycles are rejected even in unused groups. Nested references resolve before
complex-type consumers use their members. Group occurrence/order processing is
separate from these construction checks.

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
and [schema composition](https://www.w3.org/TR/xmlschema-1/#src-include).
Regression coverage is in `test/wsdl-namespace-context.qtest`,
`test/wsdl-derivation-context.qtest`, `test/wsdl-attribute-context.qtest`, the strict W3C namespace/empty-extension
selection, corrected attribute-owner derivatives, and whole-archive grammar checks.
Additional coverage is in `wsdl-simple-content.qtest`, `wsdl-element-form.qtest`,
`wsdl-schema-composition.qtest`, `wsdl-simple-resolution.qtest`,
`wsdl-group-context.qtest` and the independent `test_composition.py` matrix.
`wsdl-attribute-values.qtest` and `test_attribute_values.py` cover defaults, fixed
values, referenced constraints, reconstruction and both SOAP request/response directions.
`wsdl-qualified-attributes.qtest` covers qualification, collisions, input immutability,
scope recovery and bounded namespace materialization. `test_attribute_values.py`
also checks exact attribute infosets against both validators through separate
SOAP 1.1/1.2 bindings in both directions.
