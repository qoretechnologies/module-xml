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

Compositors (`sequence`, `choice`, and `all`) establish namespace scopes before
their children are constructed. This also applies while collecting nested choice
alternatives and reading legacy array element sequences. Captured type/reference
QNames retain those scopes through deferred resolution; sibling declarations see
the enclosing bindings after each compositor exits. For example, an invoice schema
can declare its quantity type prefix on the sequence itself:

```xml
<xs:sequence xmlns:scalar="http://www.w3.org/2001/XMLSchema">
  <xs:element name="quantity" type="scalar:int"/>
</xs:sequence>
```

Default namespace declarations likewise apply to unprefixed QName values in child
`type` and `ref` attributes. `xmlns=""` restores no-namespace references. These
declaration scopes do not change the public decoded value shape.

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

Encoded array item QNames use the namespace scope of the attribute carrying
`wsdl:arrayType`, including default resets. Finalization uses the resolved item
object (or its canonical expanded registry key), never a bare-name alias, and
restores its completion flag after failure. The named array itself belongs to its
declaring schema's target namespace. For example, an array of invoice quantities
can declare the scalar namespace on the array annotation:

```xml
<xs:attribute ref="soapenc:arrayType"
              xmlns:scalar="http://www.w3.org/2001/XMLSchema"
              wsdl:arrayType="scalar:int[]"/>
```

New schema namespace contexts reserve the enclosing output registry before
allocating prefixes. Types can therefore retain their captured output names
through subsequent merges, including nested imports and namespaces with the same
last URI segment. Input prefix scopes remain local to each source declaration.

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
normalized location. File additions temporarily use the file's containing directory,
so two root files may import different dependencies with the same relative filename.
The first successful addition establishes an unset default base; subsequent additions
restore the existing default. File or directory failures restore the prior default.
Each successfully added file retains its own base for reconstruction.
Serializable reconstruction rebuilds transient registries from
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

## Attribute consumer fields and examples

Complex types with element content or empty content expose their declared attributes
through a `^attributes^` provider field. The nested fields use the same local or
expanded collision keys as serialization. Each reports its use's requiredness,
typed optional default/fixed values, and finite allowed choices. Required fixed
attributes have an example and allowed choice but no default: callers must supply
them. `XsdAttributeDataType` enforces presence separately from scalar conversion,
including default `anySimpleType`, union and list representations. Optional copies
do not modify the original type. Prohibited uses contribute no provider field.

For example, an invoice with required fixed `currency="EUR"` and optional
`approved` defaulting to false accepts:

```qore
hash<auto> input = {"^attributes^": {"currency": "EUR"}};
auto fields = schema.getElement("urn:invoice", "invoice").getDataProviderType();
auto converted = fields.acceptsValue(input);
# converted.^attributes^ also contains approved: False
```

`WSMessageHelper` uses a resolved attribute constraint before attempting a generated
scalar example. This applies to simple content as well as element/empty content;
false, zero and empty-string constraints are retained. Unconstrained attributes
continue to use the existing type-specific example generator. Attributed simple content uses
`XsdSimpleContentDataType`: a scalar stays scalar when all attributes are optional,
and a hash stays a hash with `^value^` and `^attributes^`. A supplied hash must have
`^value^`; required attributes and finite scalar choices are checked in that shape.
Missing optional attribute constraints are filled only for the structured provider
value; scalar callers retain their original return shape, and serialization applies
attribute defaults as usual. Optional provider variants accept an omitted complete
value while retaining required fields when a hash is supplied.

For example, an attributed integer measurement can be passed as
`{"^value^": "0", "^attributes^": {"unit": "cm"}}`; its provider converts the
value to integer zero and retains the unit. If `unit` is required, a bare scalar
is rejected. If every attribute is optional, a bare scalar still converts to an
integer without being silently wrapped. `getFields()` describes the structured
alternative. Scalar enumerations belong to the `^value^` field, and
`getDataProviderAllowedValues()` reports choices for complete values separately
from the existing scalar `getAllowedValues()` API.

Tests: `wsdl-attribute-consumers.qtest` checks metadata, conversions, rejection,
namespace collisions and reconstruction. `test_attribute_values.py` independently
validates twelve generated request/response payloads from actual SOAP 1.1 and 1.2
contracts; all twelve pass through provider default insertion, including simple content.

Requiredness metadata depends on the Qore `HashDataType` insertion-order fix in
commit `5c8899669`. The interoperability README documents loading the rebuilt local
DataProvider during development without installing it.

## Incoming document element names

Document bodies and declared SOAP headers resolve XML element names before schema
matching. Namespace declarations apply to the declaring element itself and its
descendants, with local rebinding and default namespace resets. The root of a
global declaration is qualified by its target namespace; local declarations use
their effective `form`. A payload with the right local name and the wrong URI
raises `SOAP-DESERIALIZATION-ERROR`. Prefix spelling is immaterial.

`XsdBase::expandElementNamespaces()` returns a separate parsed-XML hash keyed by
`{uri}local`, including `{}local` for no namespace. Consecutive aliases for the
same expanded name form one list; separated occurrences retain `^N` suffixes.
False, zero, empty and null values are retained. Traversal restores one mutable
scope map on every exit, and repeated lists are promoted once before appending.
Only declarations used by attribute names are materialized when their scope
would otherwise be detached. Metadata and existing local declarations remain
in the hash; this helper does not retain every unused ancestor binding or replace an ordered XML
representation for typed QName and mixed-content processing.

Known element identities map back to the declared public record fields, so
ordinary callers retain their native scalar and record types. Wildcard elements
retain expanded keys. `restoreElementNamespaces()` converts these keys for the
XML generator, allocates unused prefixes and explicitly resets empty namespaces.
It reserves existing declarations and lexical generated-prefix references before
allocation, preserving both existing QName bindings and undeclared references.
The implicit XML namespace always uses `xml`.

```qore
hash<auto> value = XsdBase::expandElementNamespaces(parse_xml(
    "<shipment xmlns='urn:shipping'><item xmlns='urn:stock'>009</item></shipment>"));
string xml = make_xml(XsdBase::restoreElementNamespaces(value));
```

SoapHandler performs operation routing on a separate parsed hash. The original
message reaches schema decoding without synthetic routing fields or stripped
payload names. The real HTTP regression rejects a wrong SOAP 1.2 payload
namespace and verifies that the next valid request succeeds.

Tests are in `wsdl-element-namespaces.qtest`, `SoapHandler.qtest`, and
`test/wsdl-interop/test_element_namespaces.py`. Independent lxml/Xerces checks
cover actual SOAP 1.1/1.2 bindings in both directions, exact names and values,
local/default/rebound namespaces and invalid qualification. The applicable
rules are [XML namespace scoping/defaulting](https://www.w3.org/TR/REC-xml-names/#scoping)
and [XSD element validity](https://www.w3.org/TR/xmlschema-1/#cvc-elt).

## Colliding element fields

Schema construction indexes local and referenced elements by their expanded
names. Deferred references capture their namespace before resolution, so an
imported reference is never temporarily indexed using the referring schema's
namespace. Base and group maps are reindexed when incorporated into another
type. Every complex type, including nested anonymous types, enters the
resolution queue and selects its final field names after composition.

One local-name count covers the type's elements and all its choices. A name
that denotes only one expanded identity retains its existing field name. If
more than one namespace uses that local name, every such field uses an expanded
key. For example, an unqualified boolean `item` and an integer `item` in
`urn:inventory` are represented as:

```qore
hash<auto> value = {"{}item": False, "{urn:inventory}item": 0};
```

Both keys appear in provider fields and generated examples. Serialization uses
the element declaration's local XML name and namespace, independently of the
public hash key. Choices and their alternatives use the same field mapping,
including inherited choices. Finalizing a derived type does not rename fields
in its base. Serializable schema/WebService reconstruction reapplies these rules.

`test/wsdl-element-collisions.qtest` covers local forms, imported/no-namespace
references, choices, inheritance, nested/reused groups, provider conversion,
ambiguous/wrong input names and generated examples with anonymous types.
`test/wsdl-interop/test_element_collisions.py` independently validates 136
documents with lxml and pinned Xerces across actual SOAP 1.1/1.2 bindings in
both directions, checking exact names, order, lexical values and provider types.

## WSDL message part names

`WSMessage` resolves each part's element QName in the message and part XML
namespace scope. An unprefixed QName uses that scope's default namespace,
including an explicit empty default. It never falls back to the WSDL target
namespace. Part names remain unique within the message and serve as the keys
for provider values and binding selection.

Argument aliases are selected after every part has been resolved. A unique
element local name keeps its existing alias. When names collide with another
element or a type-part name, element aliases use expanded names; type parts
keep their part names. `pmap` maps each part name to its argument key, so
bindings select parts independently of XML prefix spelling. Output obtains
the actual XML name from the element declaration; no-namespace roots are
unqualified. Body/header parts can therefore share an element local name
while retaining different namespace identities and values.

For example, two parts named `approved` and `quantity` may both reference
an element named `value`, one in `urn:approval` and one in `urn:stock`.
Callers can supply `{"approved": False, "quantity": 0}`. Provider fields and
multipart examples use those part names. Namespace-aware decoding returns
the corresponding part values, with the existing message wrapper convention
for SOAP headers. Single-part example generation retains its previous shape.

Tests: `test/wsdl-message-identity.qtest`, `test/wsdl-interop/message-identity.qr`
and `test/wsdl-interop/test_message_identity.py`. The independent test checks
160 element documents, including header/body placement, both SOAP versions,
both directions and provider/example reconstruction. Its explicitly failing
P3 lexical-rejection assertions remain visible in the execution record.
The namespace/part rules come from [WSDL 1.1 sections 2.3, 3.5 and 3.7](https://www.w3.org/TR/2001/NOTE-wsdl-20010315).
