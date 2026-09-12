# WSDL element wildcard assessment and values

Copyright (C) 2026 Qore Technologies, s.r.o.

Element particles attribute complete child sequences before conversion. A
wildcard then enforces its namespace constraint and processing mode. `strict`
requires an available global element declaration or `xsi:type`; `lax` assesses
available declarations and types, including known descendants of an unknown
wrapper; `skip` does not assess its subtree. A known element retains its own
abstractness and permitted type derivations. This follows XSD 1.0
[Schema-Validity Assessment (Element)](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-assess-elt)
and [Wildcard Validation Rules](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-wildcard).

Wildcard fields keep the existing XML-data representation. For example, a
wildcard integer whose XML text is `017` remains the string `017`. Validation
uses the resolved declaration without replacing that lexical value with a native
integer. Structured wildcard values retain namespace declarations on their
subtree root, including inherited prefixes used only by text or attribute
values. This detaches one subtree instead of copying all bindings to every
one of its descendants. Ordinary declared fields keep their existing typed
conversion and field names.

Use the existing `XsdXmlValue` representation when scalar namespace context,
comments, CDATA, or exact interleaving must be retained. A scalar wildcard field
still returns a scalar; it cannot independently carry an inherited namespace map.
Complete XML-value APIs retain that information. `getChildValues()` can extract
an independent child for a wildcard field, and the serializer checks that its
expanded root name matches that field. For example:

```qore
XsdXmlValue source("<shipment xmlns:p='urn:products'><category>p:Stock</category></shipment>");
XsdXmlValue category = source.getChildValues()[0];
hash<auto> record = {"{}category": category};
```

A retained child is validated from its XML and emitted as an XML fragment. It
keeps comments, CDATA, lexical values and child order. Its lexical namespace
requirements participate in output prefix allocation so generated ancestors
cannot bind a prefix that its text requires to remain unbound. Inherited
`xml:lang`, `xml:space` and `xml:base` are applied to the containing element and
must satisfy its attribute rules. Retained siblings must agree on that inherited
context, and conflicting supplied container attributes are rejected. DOCTYPEs
and processing instructions follow the existing SOAP XML-value restrictions.

Explicit `^type^` / `^val^` wrappers also work in wildcard fields. Known element
names retain their declaration's type constraints; otherwise the wrapper names
the assessment type. For example, this portable value can satisfy an undeclared
strict wildcard element in an admitted namespace:

```qore
hash<auto> record = {"{urn:partner}quantity": {
    "^type^": new XsdQNameValue(XSD_NS, "int"), "^val^": 17,
}};
```

For element-only content, native serialization schedules declared and wildcard
fields together using the complete particle, then checks each attributed
occurrence before emitting it. Expanded names distinguish wildcard fields from
similarly named declared fields. Repeated native fields remain occurrence lists;
a flat field map does not retain arbitrary original interleaving. Complete
`XsdXmlValue` APIs retain that order and validate each child in place.

`XsdGlobalElementRegistry` shares completed global elements and named types among
declaration namespace contexts, detached components and providers. Schema
construction publishes completed maps, and failed additions restore the earlier
maps. Concurrent reads do not mutate them. Serializable reconstruction validates
map types and component classes; complex-type wildcard metadata is checked
before assignment so malformed shared data reports `DESERIALIZATION-ERROR`
independently of graph visitation order.

`XsdWildcardContentDataType` preserves declared field metadata, admits additional
XML-data fields, and validates the complete emitted content model. Ordinary,
soft and explicitly typed providers use the same instance checks. Invalid input
reports `RUNTIME-TYPE-ERROR`; conversion APIs use `SOAP-DESERIALIZATION-ERROR` or
`SOAP-SERIALIZATION-ERROR` according to direction. Interruptions propagate.

Bounded samples select fresh wildcard names within the particle's namespace
constraint, avoiding conflicting global declarations. Strict samples carry an
available builtin string type; lax and skip samples can use unassessed text.
`WSMessageHelper::getTypeExample()` provides this generation for detached types,
and mandatory wildcard providers use it for examples. Existing repetition and
total-element bounds apply before values are generated and to the emitted XML.

The regressions are `test/wsdl-wildcard-elements.qtest`,
`test/wsdl-wildcard-element-values.qtest`, and
`test/wsdl-wildcard-element-http.qtest`. The Python wildcard matrix checks 36
schemas and 684 documents, both conversion directions and providers; successful
outputs also undergo native DOM/reader and independent Xerces validation with
explicit comparisons of expanded names, lexical/typed values and order. Real
SOAP 1.1/1.2 client, handler and provider tests cover both directions,
reconstruction, concurrent output and cancellation.
