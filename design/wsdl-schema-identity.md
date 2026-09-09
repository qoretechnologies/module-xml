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

Named mixed bases also permit a simple-content restriction when their particle
is emptiable and the restriction supplies an inline simple type. The effective
mixed flag comes from `complexContent` when present, then `complexType`. An empty
extension inherits its base's content properties according to the XSD complex-type
mapping. Empty effective content differs from a nonempty particle that permits
an empty instance; nested empty groups do not automatically erase a particle.

Construction retains an internal tree for the emptiability predicate: elements
and wildcards require an occurrence, zero minimum occurrences permit absence,
sequences/all require every member to be emptiable, and choices require one.
Named group references retain declaration scopes and cache their computed result.
Every nested reference resolves, including optional branches, so missing and
cyclic group graphs fail before payload processing. `XsdGroup::isEmptiable()`
exposes this predicate to construction consumers. This metadata does not change
the existing public scalar/hash representation or perform instance matching.

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

Component QName resolution also checks the imports of the source document containing
the reference. A component loaded through another inline schema, an include or a
transitive import does not grant that document permission to reference its namespace.
During construction, `Namespaces::schema_reference_namespaces` contains the source
target namespace, its imports and builtin XSD types. It is restored on every exit,
so general public QName expansion outside construction retains its existing behavior.
For example, a billing schema referencing `customer:Account` declares an import for
the customer namespace even when the surrounding WSDL has already supplied that schema.

An import without a `namespace` attribute grants references to components with no
namespace. An explicit `namespace=""` does not grant that permission. Import reference
cache keys retain presence as well as value, and imported source target namespaces
must match both. A schema with no target namespace omits `targetNamespace`; empty
or whitespace-only target declarations are rejected. Chameleon adoption still uses
the including namespace before checking references to the adopted components.

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

Attribute restrictions resolve replacements by expanded identity before merging.
An omitted use remains inherited; a supplied replacement cannot weaken requiredness,
lose or change a fixed constraint, or use a simple type outside the base type's
ancestry. Extensions reject duplicate expanded uses, including repeated global refs.
Types with the same local name in different namespaces remain distinct. For example,
an invoice restriction can narrow a required `xs:int` quantity attribute to a required
`xs:short`; it cannot change it to an optional attribute or to `xs:string`.

Simple-type ancestry follows declared restriction links and the XSD builtin hierarchy.
Lists and unions derive from `anySimpleType`; a union also admits descendants of its
member types. Two separately declared lists with identical item types are distinct
types. A per-check memo records visited type pairs, including reused union members.
Inline simple-content restrictions use the same ancestry check against the effective
simple content of their complex base. These construction checks leave scalar facet
and value-space validation with the existing datatype layer.

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
in the hash; this helper does not replace the complete namespace context held
by `XsdXmlValue` for typed QName or mixed-content processing.

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

## Element declaration consistency

Construction retains local element declarations separately from the public field
maps until references have resolved. The XSD 1.0 `cos-element-consistent` check
compares declarations by expanded element name and resolved type identity before
field merges can discard an earlier declaration. Distinct declarations must use
the same named type. Repeated references to one global declaration, or reuse of
one local declaration through a named group, retain that declaration's identity
and can share its anonymous type; identical source text in two different local
anonymous declarations does not establish identity.

Named groups recursively retain declarations and references in nested
compositors. Each resolved group caches one checked representative per expanded
name. Combining cached maps is bounded by the sum of their distinct name counts
at reference edges, rather than by the number of expanded particle occurrences.
The shared 32-level group regression doubles references at each level without
expanding an exponential declaration list.

Extensions check the combined base and own declarations; restrictions check
their replacement content model. Child element types define their own declaration
scopes. A particle with both occurrence limits equal to zero contributes no
declaration, including its nested descendants. Ordinary optional particles still
contribute their declarations. Checks run before field/occurrence merges, so an
invalid addition cannot alter declarations already used by another schema type.

For example, two positions named `lineCode` in a purchase-order content model
can both reference the named `OrderCode` type. Assigning `xs:int` to one and
`xs:string` to the other is a schema error, even in disjoint nested branches.
A different namespace or a different containing element type establishes a
different identity or scope. Existing unambiguous provider fields remain local
names; namespace collisions retain the documented expanded field names.

This metadata checks construction consistency. Ordered occurrence matching is
still governed by the particle implementation, and implicit declarations from
substitution groups require the separate substitution-group resolution work.

## Attribute wildcard construction

`XsdAttributeWildcardInfo` describes the resolved namespace constraint and
processing strength of an attribute wildcard. The constraint is `Any`, `Not`, or
`Set`; the latter two carry an excluded namespace or a set of namespace names.
An empty string denotes no namespace. `Not` also excludes no namespace, as XSD
1.0 requires for `##other`. A present empty namespace list is an empty set and is
distinct from an absent wildcard. The public enums avoid stringly typed metadata.
`XsdComplexType::getAttributeWildcard()` and
`XsdAttributeGroup::getAttributeWildcard()` return this metadata after resolution.
Returned maps use copy-on-write; editing a view does not mutate the component.

Construction captures `##targetNamespace` and `##other` in the declaring schema's
context, including imported groups. Nested attribute groups intersect namespace
constraints. An explicit local wildcard determines processing strength; otherwise
the first non-absent group wildcard does. Extensions inherit an absent local
wildcard or union their own complete wildcard with the base, retaining the own
wildcard's processing strength. Unions/intersections use the XSD 1.0 intensional
rules and reject combinations that the specification declares non-expressible.

Restrictions can introduce an attribute absent from the base's explicit uses
only when the base attribute wildcard allows that attribute's namespace. The
restriction's wildcard must be an intensional subset of the base wildcard, with
identical or stronger processing (`strict` > `lax` > `skip`). The ur-type exception
permits weaker processing when restricting `xs:anyType`. An element wildcard does
not authorize additional attributes. Attribute-use merging and wildcard
composition finish before the resolved group/type publishes its new metadata.

For example, a base record admitting extension attributes only from a partner's
namespace can be restricted to a required `partner:accountId` declaration. Adding
an unqualified `accountId` instead is a schema error. This construction metadata
retains native field shapes; full runtime wildcard validation and lossless
unknown-attribute values remain part of the content processing implementation.

These rules follow [complex-type property mapping](https://www.w3.org/TR/xmlschema-1/#Complex_Type_Definitions),
[attribute derivation restrictions](https://www.w3.org/TR/xmlschema-1/#derivation-ok-restriction),
and [wildcard namespace algebra](https://www.w3.org/TR/xmlschema-1/#cos-aw-intersect).

## Element declarations and ID constraints

Element construction distinguishes schema-level declarations from local
particles and global-element references. A declaration has exactly one name or
reference and at most one type attribute, anonymous simple type or anonymous
complex type. An empty anonymous complex type is valid; a named or duplicate
inline type is rejected. References permit occurrence limits and annotations,
while declaration-only properties, type children and identity constraints are
rejected. Local/global property restrictions are checked independently of the
value of the property: `abstract="false"` is still invalid on a local element.
Both `default` and `fixed` cannot be present. Empty QName attributes follow the
same namespace error path as other malformed QNames.

The declaration booleans `nillable` and `abstract` accept `true`, `false`, `1`,
`0` and surrounding XML whitespace. In particular, `nillable="1"` sets the same
metadata as `nillable="true"`. Abstract-element runtime validation and general
element default/fixed application are separate from these construction checks.

Type-dependent checks run after resolution. Attributes with default/fixed
constraints cannot have an ID-derived type. Constrained elements are retained
in the construction resolver and checked after complex-type finalization, so
named and anonymous simple-content types are checked as well. Complex types
admit at most one ID-derived attribute use after local/group and inherited
attribute merging. A prohibited use is absent from this set; IDREF is a distinct
type. A failed check uses the existing schema-addition rollback and does not
publish a merged inherited attribute map.

For example, an account record may declare one `xs:ID` attribute named `id` and
an `xs:IDREF` attribute named `parent`. Giving `id` a fixed value or adding a
second ID-derived attribute through an extension is a schema error. Native
field representations, provider conversion and generated examples retain their
existing shapes. ID/IDREF document binding and uniqueness remain runtime work.

Requirements: [element representation](https://www.w3.org/TR/xmlschema-1/#src-element),
[attribute constraint rule 3](https://www.w3.org/TR/xmlschema-1/#a-props-correct),
[element constraint rule 5](https://www.w3.org/TR/xmlschema-1/#e-props-correct),
[complex-type rule 5](https://www.w3.org/TR/xmlschema-1/#ct-props-correct), and
[boolean whitespace](https://www.w3.org/TR/xmlschema-2/#rf-whiteSpace).

ID ancestry follows the resolved type objects directly. It does not need a
namespace lookup to inspect the already resolved base type.

## Declaration namespace ownership

Each `XsdAbstractType` owns its declaration `Namespaces` object. A type returned
by `XsdSchema::findType()` remains usable after its schema leaves scope, including
types parsed from incremental additions, imports and chameleon includes. Elements
and attributes retain that context through their resolved type. Sibling source
documents keep their own input prefix bindings and target namespace; retaining a
type does not merge those input scopes.

The namespace registry caches builtin types, so a cached builtin and its registry
form a reference cycle. Qore's cycle collector releases this graph when its last
external owner leaves scope, including during exception and cancellation cleanup.
Directly constructed builtins retain their registry without requiring a cache entry.
Raw `Serializable` reconstruction preserves indexed references and cycles; a
reconstructed graph owns an independent namespace registry. Whole-schema
reconstruction continues to use the retained schema documents.

For example, a consumer can retain a quantity type and reconstruct it
independently of the original schema:

```qore
%modern
%requires WSDL
XsdSchema schema('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
    targetNamespace="urn:orders"><xs:simpleType name="Quantity">
    <xs:restriction base="xs:int"><xs:minInclusive value="1"/></xs:restriction>
    </xs:simpleType></xs:schema>', {"async_only": True});
XsdAbstractType quantity = schema.findType(make_qname("urn:orders", "Quantity"));
remove schema;
XsdAbstractType restored = Serializable::deserialize(quantity.serialize());
@assert(restored.nsc.getTargetNamespaceUri() == "urn:orders");
@assert(restored.serializeValue(restored.nsc, 12, True) == 12);
```

Namespace mutation remains subject to the existing public API's synchronization
requirements. Concurrent consumers can reconstruct independent graphs; sharing a
type does not make concurrent namespace mutation safe. The scoped
`NamespacePrefixHelper` continues to borrow its registry for the enclosing call.

## Unwrapped document arguments

A document message with one selected part accepts its existing unwrapped record
form, including fields from nested choice blocks. The field set is the union of
the resolved element map and choice maps; declaration order is still enforced
by the existing serializer. Explicit element wildcards in parsed sequence/all
content permit the remaining element keys to travel with that record. An
attribute wildcard does not grant that permission, and a zero/zero element
particle or enclosing group is absent. `hasElementWildcard()` reports this
explicit parsed-content flag; `isEmpty()` accounts for choices and that flag.
These checks do not implement the remaining group particle or wildcard runtime
validation requirements.

Selection preserves supplied values addressed by another part's name or element
key, or by a declared header's part/element/message name. It also accepts the
legacy WSDL message-name container and removes that container only when all of
its selected values have been consumed. Known fields whose name equals the
message name remain eligible as ordinary fields. Caller hashes retain their
values through copy-on-write behavior.

For example, an account request may supply `{"{urn:partner}account": "AC-42",
"context": "tenant-7"}` when one document body part has an element wildcard and
`context` is explicitly bound to a header. The account element belongs to the
Body payload; `tenant-7` belongs to the declared Header element. Wrapping the
body value as `{"body": {"{urn:partner}account": "AC-42"}}` is equivalent. When
multiple body parts are selected, each value must identify its part or element
explicitly, because a bare record does not identify which part owns its fields.

The public wrappers and native scalar types are unchanged. Tests cover real
SOAP 1.1/1.2 bindings, request/response paths, reconstructed services, bare/part/
message-container forms, exact namespace identity and header separation.
Independent validators check every emitted payload and header. The wire
separation follows [WSDL SOAP body](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_soap:body) and
[SOAP header](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_soap:header) part definitions.
