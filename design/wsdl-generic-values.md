# Generic XML values

Copyright (C) 2026 Qore Technologies, s.r.o.

`xs:anyType` has mixed content with lax element and attribute wildcards. Known
global declarations and available `xsi:type` definitions are assessed, including
known descendants below an unknown wrapper. `xs:anySimpleType` has unconstrained
lexical text but remains a simple type: it cannot contain ordinary attributes or
child elements. Namespace declarations and the recognized instance attributes
are distinct from ordinary attributes. These rules follow XSD 1.0
[the ur-type definitions](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#ur-type-itself)
and [local type validity](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-type).

## Native and complete XML representations

A plain anyType XML text value decodes as text. Structured anyType content retains
XML data, with expanded child keys, lexical attributes, text/CDATA fragments and
ordered repeated-name suffixes. Namespace declarations are retained at the root
of each detached generic value. The decoder does not replace a known child with
its numeric or other native value: assessment checks it while retaining its XML
lexical form. For example, a known integer child containing `017` keeps `017`.

```qore
XsdSchema schema('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
    '<xs:element name="record" type="xs:anyType"/></xs:schema>');
auto shipment = {"^attributes^":{"xmlns:p":"urn:partner"},
    "^value^":"Shipment ", "{urn:partner}category":"p:Priority",
    "^value1^":" received"};
XsdXmlValue output = schema.serializeXmlValue("", "record", shipment);
```

Generic XML-data serialization accepts expanded or properly bound lexical child
names. It assesses the same expanded names that will be emitted. Unsupported
metadata, unbound prefixes, malformed XML-data shapes and invalid known content
raise `SOAP-SERIALIZATION-ERROR`. Callers' records and shared declaration
namespace registries remain unchanged.

An anySimpleType native result remains a scalar. Use `XsdXmlValue` and the
schema/message XML APIs when namespace context, schema-location hints, comments,
CDATA boundaries or other complete XML information must survive that projection.
A complete carrier is validated in place and keeps its original document; the
schema's `serializeXmlValue()` API instead constructs XML from a native value.
SOAP XML request/response options and XML providers accept complete carriers.
The tests exercise both contracts, including saved carriers and real HTTP.

Scalar anyType serializer inputs retain the existing inferred builtin mappings.
Arbitrary-precision numbers use the existing exact decimal formatter. Numeric
infinities and NaN select `xs:double`, whose value space includes them. Finite
native floats retain their established decimal mapping. Explicit portable
`^type^` / `^val^` wrappers select an available valid type; selected-type capture
keeps the type identity when native values are decoded for later emission.

## Namespace handling and assessment

Generic strings and attributes can contain uninterpreted QName-like tokens.
During complete output generation, internal scoped lexical values retain each
token's required bindings, including an absent binding. The shared QName output
adapter handles every text and CDATA fragment at a node. Generated envelope or
schema prefixes are renamed when their introduction would change the meaning of
an originally unbound token. These internal values are removed before the XML
generator receives the final lexical data.

Completed declaration registries remain owned by namespace contexts, detached
components and providers. Every conversion has a local namespace/output scope.
Declared anyType values assess their own descendants; wildcard dispatch does
not repeat that recursive work. Complete generic XML validation also avoids a
redundant scalar re-encoding traversal. A 32-level declared generic tree tests
recursive assessment and invalid-leaf rejection.

## Providers

`XsdGenericDataType` validates generic inputs through the receiving component and
its completed declaration registry. It reports scalar/XML-data categories and
prevents enclosing fields from bypassing validation through direct Qore type
matches. Optional and mandatory variants preserve the content rules. The soft
variant uses the same rules because the generic serializer already accepts its
supported scalar representations. Saved providers retain their component;
malformed component/optionality metadata rejects during reconstruction.

Ordinary, native selected-type, list, field and SOAP providers all exercise these
rules. A generic type provider has a type context, while the enclosing element
owns occurrence, element selection and declaration constraints. Complete XML
providers retain the full XML representation.
