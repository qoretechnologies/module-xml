# Native wildcard ID attributes and type ancestry

Copyright (C) 2026 Qore Technologies, s.r.o.

Native DOM and streaming validation enforce XSD 1.0 Structures
[3.4.4 clauses 5.1 and 5.2](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-complex-type).
An element can have at most one assessed wildcard attribute of type ID or an ID
restriction. If it has one, its complex type cannot declare an ID attribute use,
even when that optional attribute is absent. `skip` does not assess wildcard IDs;
`strict` and `lax` assess attributes with available declarations. Attribute order
and namespace prefix spelling do not alter these rules.

The private libxml2 source correction reports the two existing attribute error
states using `XML_SCHEMAV_CVC_COMPLEX_TYPE_5_1` and `_5_2`. Both public validation
paths raise `PARSE-XML-EXCEPTION`. Previously the final reporting switch silently
ignored both states and validation could return success.

ID ancestry follows `baseType`, as prescribed by the type definition hierarchy
in [2.2.1.1](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#concepts-type)
and the base property mapping in [3.14.2](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#Simple_Type_Definition_details).
`subtypes` holds list items or content; it does not encode restriction ancestry.
The corrected helper also enforces ID declaration rules on complex types,
attribute groups, attributes, elements and simple content. A list or union has
`anySimpleType` as its base, even when an item/member is ID. Document-level ID
uniqueness and reference checking remain separate from this schema ancestry test.

Referenced attribute value constraints were guarded by a non-null typed value,
although that value had not yet been computed. The corrected guard validates the
lexical constraint and stores its typed value once. Invalid ID constraints and
invalid lexical values reject construction with `XSD-SYNTAX-ERROR`. Existing
schema destruction owns the computed value; allocation-failure tests exercise
both computation and error reporting. The correction adds no shared mutable
state, I/O, or new public API. Existing Qore cancellation boundaries remain.

CMake tests behavior through 24 wildcard schemas/180 documents and 100 ancestry
schemas before accepting a system provider. AUTO uses the pinned private static
libxml2 2.15.4 when any required check fails; SYSTEM reports configuration failure.
The build-tree correction verifies its input and output hashes and preserves the
original archive and source tree. Reconfiguration preserves generated file times.

The independent matrix records validator differences explicitly. Xerces-J 2.12.2
agrees with all 180 wildcard document outcomes. It accepts six prohibited ID
simple-content constraints and rejects 48 schemas by treating ID list/union
membership as ID ancestry. These results do not replace the separate normative
native expectations. The pinned lxml/libxml2 2.12.10 accepts all 80 invalid
wildcard documents; the native correction must reject them.

For example, a shipment element with a wildcard may carry one declared ID
attribute from its partner namespace:

```xml
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:s="urn:shipment" targetNamespace="urn:shipment">
  <xs:attribute name="tracking" type="xs:ID"/>
  <xs:attribute name="alternate" type="xs:ID"/>
  <xs:element name="shipment">
    <xs:complexType><xs:anyAttribute processContents="strict"/></xs:complexType>
  </xs:element>
</xs:schema>
```

`<s:shipment xmlns:s="urn:shipment" s:tracking="parcel17"/>` is valid.
Adding `s:alternate="parcel18"` violates clause 5.1 even though the two values
are distinct. The executable `test/xml-wildcard-ids.qtest` tests this shape
through both APIs, with restricted IDs, both attribute orders, all processing
modes, schema rejection, recovery, cancellation and concurrent readers.
