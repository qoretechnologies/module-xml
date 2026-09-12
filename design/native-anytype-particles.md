# Native builtin particles and anyType inheritance

Copyright (C) 2026 Qore Technologies, s.r.o.

The private libxml2 dependency uses one `xmlSchemaParticle` definition for parsed
schemas and builtin types. Both `xmlschemas.c` and `xmlschemastypes.c` include
`cmake/libxml2-particle-layout.h`. This keeps allocation size and field offsets
consistent when a schema inherits the builtin `anyType` particle.

The builtin content is mixed: a sequence occurring once contains a lax wildcard
occurring zero to unbounded times. The outer particle has a finite maximum and
a nullable term; the inner wildcard has an unbounded maximum and a non-nullable
term. Both carry an immutable builtin flag. Schema attribution reads these
values and only publishes computed occurrence metadata on schema-owned particles.
The shared builtin graph is initialized once by libxml2 and stays unchanged during
independent and concurrent schema compilations. Borrowed count-source links retain
their existing lifetime and cleanup contract. No new production allocation or
loop is introduced beyond the extra fields in each particle allocation.

An absent particle or a literally empty sequence can inherit the base content
unchanged. A reference to an empty model group supplies effective content;
its resulting model group must not be mistaken for an absent particle. Native
fixup checks the reference's source node before applying the empty-content rule.
An element-only extension of mixed `anyType` through such a group is rejected;
an explicitly mixed extension is valid and retains the inherited wildcard.
Adding an explicit child after the unbounded wildcard remains ambiguous and is
rejected. Restrictions replace the wildcard with their own permitted content.

For an open shipment envelope which also validates a known quantity:

```qore
string schema = "<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
    "<xs:element name='quantity' type='xs:int'/>"
    "<xs:element name='shipment'><xs:complexType><xs:complexContent>"
    "<xs:extension base='xs:anyType'><xs:sequence/></xs:extension>"
    "</xs:complexContent></xs:complexType></xs:element></xs:schema>";
string xml = "<shipment><carrier>Example Freight</carrier><quantity>17</quantity></shipment>";
hash<auto> value = parse_xml_with_schema(xml, schema);
@assert(value.shipment.quantity == "17");
```

The unknown `carrier` element is accepted by lax assessment, while a non-integer
`quantity` is rejected. DOM, XmlReader and XmlDoc preserve the original XML values.
The component mapping and constraints are specified by XSD 1.0 Part 1
[complex content](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#Complex_Type_Definition_details),
[type derivation](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-ct-extends)
and [the ur-type](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#ur-type-itself).

CMake's `builtin_particles` capability check traverses inherited builtin particles
and validates empty-group derivation through public schema APIs. Completed earlier
probe diagnostics are flushed first: an incompatible library can fail during
builtin traversal, and its failed process still rejects that provider. `AUTO`
selects the private pinned dependency on failure; `SYSTEM` rejects it. A fully
corrected system library remains usable. The build transformation verifies source
and result hashes, shares the header between translation units, leaves downloaded
sources intact and preserves generated timestamps on reconfiguration.

`test/xml-anytype-particles.qtest` covers direct, empty, grouped and transitive
extensions, restrictions, lax negative cases, cancellation and concurrent parsing.
`test/wsdl-interop/test_anytype_particles.py` checks schema acceptance, original
values and exact error categories through all three native APIs and pinned
Xerces. Native allocation tests fail every attribution allocation permanently
in turn, assert complete cleanup and recovery, and compare the entire builtin
particle storage before and after each attempt.
