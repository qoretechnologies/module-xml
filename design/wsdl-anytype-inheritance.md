# Effective wildcard particles in WSDL schemas

Copyright (C) 2026 Qore Technologies, s.r.o.

An extension of `xs:anyType` inherits its mixed content and its lax, unbounded
element wildcard. WSDL builds that builtin particle as ordinary schema-owned
metadata and combines it with the extension's effective content. The existing
particle matcher, attribution checks and wildcard value assessment then apply
without special cases in serialization or deserialization.

Absent content, zero-occurrence particles and literally empty compositors have the effective content
specified by XSD 1.0. An empty extension inherits the base particle directly.
With explicit mixed content, an absent or empty compositor contributes an empty
sequence. A named group reference remains a particle, including when its referenced
group is empty. A group reference with zero maximum occurrences is absent like
other zero-occurrence particles. Nonempty extensions of a mixed base must remain mixed; adding a
child after the unbounded builtin wildcard still fails unique particle attribution.
These rules also apply to transitive extensions of named complex types.

The type's `hasElementWildcard()` metadata is computed from its completed particle
graph after group resolution. It follows inherited and referenced particles,
visits shared nodes once, and excludes branches with `maxOccurs="0"`. Attribute
wildcards are independent. This metadata selects the existing wildcard-aware
provider types and preserves namespace context for their XML values.

Wildcard children retain the established XML-data representation: lexical strings
or XML hashes, with expanded names and preserved namespace bindings where needed.
Callers can also supply `XsdXmlValue` children. Mixed character segments retain
their existing scoped lexical values when lossless native decoding is requested.
Adjacent repeated children may be grouped into a list; their order and XML values
remain unchanged. Both ordinary and native providers use the same receiving
declaration checks, including after soft/mandatory conversion and Serializable
reconstruction. Bounded provider samples use the completed particle.

For a shipment envelope that accepts partner extensions while checking a known
quantity:

```qore
XsdSchema schema("<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
    "<xs:element name='quantity' type='xs:int'/>"
    "<xs:element name='shipment'><xs:complexType><xs:complexContent>"
    "<xs:extension base='xs:anyType'><xs:sequence/></xs:extension>"
    "</xs:complexContent></xs:complexType></xs:element></xs:schema>");
XsdXmlValue shipment = schema.serializeXmlValue("", "shipment", {
    "{}quantity": "+0017", "{urn:carrier}tracking": "007"
});
@assert(shipment.getChildValues()[0].getExpandedName() == "{}quantity");
@assert(shipment.getChildValues()[1].getExpandedName() == "{urn:carrier}tracking");
```

An invalid quantity is rejected even though the inherited wildcard is lax.
The derivation and component requirements are XSD 1.0 Part 1
[complex content](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#Complex_Type_Definition_details),
[derivation by extension](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-ct-extends)
and [the ur-type](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#ur-type-itself).
The native dependency's corresponding ownership rules are documented separately
in [native-anytype-particles.md](native-anytype-particles.md).

`test/wsdl-anytype-inheritance.qtest` exercises component shape, original and
reconstructed schemas, native values, providers, groups, samples and rejection.
`test/wsdl-interop/test_anytype_inheritance.py` independently validates values,
names, text, order, namespace bindings and both actual SOAP binding directions.
The shared mixed-value matrix keeps its original fixtures and assertions.
`test/wsdl-mixed-http.qtest` adds transitive inheritance through clients, handlers
and SoapDataProvider, with direct malformed HTTP requests and successful reuse.
