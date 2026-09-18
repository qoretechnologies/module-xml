# Core WSDL grammar and extension isolation

Copyright (C) 2026 Qore Technologies, s.r.o.

WSDL document construction validates core declaration structure before converting
XML into grouped hashes. `WsdlDeclarationGrammar` drives `WsdlStructureGrammar`
with the same `XmlReader` stream used for component names and references. The
structure frames are private to one construction and disappear on failure.

## Ordered declarations

The grammar distinguishes abstract operations and their messages from concrete
binding operations and messages. It checks permitted core children and attributes,
documentation placement, non-whitespace character data, operation message counts
and fault ordering. Abstract faults require both input and output. A concrete
operation's input precedes its output. Name/reference checks remain owned by the
declaration scanner and component registry.

Documentation appears at most once, before other children. Its mixed XML payload
is opaque. Other foreign extension payloads are also opaque to the core scanner;
embedded WSDL-looking names do not declare components. Inline XSD is checked by
the schema implementation independently. Schema normalization begins only at an
actual schema document root or a schema directly under WSDL `types`; an XSD-looking
element nested in optional vendor metadata does not activate it.

The extension slots follow the corrected
[WSDL schema dated 2004-08-24](https://ws-i.org/profiles/basic/1.1/wsdl-2004-08-24.xsd):
all core component types permit foreign attributes and foreign elements preceding
their core children. `definitions` also permits interleaved foreign elements.
`documentation` has its own mixed-content type without the foreign-attribute
wildcard. Unqualified extension elements and attributes in the WSDL namespace do
not satisfy the foreign-namespace wildcard.

`parameterOrder` uses the XSD `NMTOKENS` lexical rules. URI-valued core attributes
use the shared XSD URI lexical validator. Schema-instance type declarations must
name the corresponding published WSDL type; core declarations are not nillable.
Schema location hints are checked lexically and never fetched. Other foreign
attributes, including unknown names in the schema-instance namespace, follow the
component's attribute wildcard.

A supplied `definitions/@targetNamespace` must be absolute, as required by WSDL
1.1 section 2.1.1. An absent attribute declares components without a namespace;
an explicit empty value or another relative reference rejects. Qore's URI mapping
classifies the normalized anyURI value without rewriting its stored spelling or
namespace identity. Imported WSDL documents pass through the same checks. URI
schemes are not restricted to HTTP: `urn:inventory` is a valid target namespace.

## Optional and required extensions

An extension's `wsdl:required` value has XML boolean syntax. An unknown extension
with `true` or `1` fails construction; absent, `false` and `0` allow it to remain
opaque. Supported SOAP, HTTP and MIME declarations are recognized by expanded
name and parent context. The separately documented CXF XML/JMS boundary preserves
their declarations while rejecting unsupported port selection.

`WsdlSourceProjection` runs before namespace prefixes are removed from grouped
core data. It walks core WSDL elements with their namespace scopes and separates
unknown foreign children into the internal `.wsdlExtensions` collection. Each
entry retains its authored name and grouped payload. Original source text retains
the exact XML order. Thus an optional `vendor:operation`
or `vendor:body` cannot replace a core operation or SOAP body simply because their
local names match. Known extension payloads, XSD and documentation remain opaque
to this projection. Binding compilation consumes core documentation and the
isolated extension collection without treating them as message data.

Original WSDL source and dependency text remain available in source and saved
services. Unsupported binding and port declaration metadata also preserves the
isolated payloads, with ancestor namespace bindings attached by the existing
metadata owner. These internal collections do not add callable operations.

This core validation is not a WS-I profile certification. Component resolution,
binding capabilities and schema/message validation have separate owners. Classic
WSDL imports of XSD and import-resource deduplication remain available; profile
restrictions on those features are not imposed by the core structure pass.

## Example and verification

An inventory binding can include an optional foreign annotation before its WSDL
operations without creating another operation:

```xml
<wsdl:binding name="Inventory" type="tns:InventoryPortType">
  <vendor:operation xmlns:vendor="urn:inventory:metadata" category="stock"/>
  <soap:binding transport="http://schemas.xmlsoap.org/soap/http"/>
  <wsdl:operation name="GetStock">...</wsdl:operation>
</wsdl:binding>
```

Adding `wsdl:required="true"` to that unknown annotation rejects construction.
`test/wsdl-grammar.qtest` verifies source/saved services, namespace collisions,
provider samples, request/response values, unsupported metadata and recovery.
The offline Python oracle checks the same fixture inventory against the pinned
corrected schema using Xerces and libxml2, with capability errors kept separate
from schema validity.
