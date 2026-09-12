# Native wildcard instance types and schema character content

Copyright (C) 2026 Qore Technologies, s.r.o.

Native DOM and streaming validation can strictly assess an element through an
available `xsi:type` even when no global declaration exists for its name. This
follows XSD 1.0 [Schema-Validity Assessment (Element), clause 1.2](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-assess-elt)
and [Wildcard Validation Rules](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-wildcard).
The wildcard still checks the element's namespace. A known declaration still
controls allowed type derivation; the selected type still checks facets,
attributes, children and abstractness. Unresolved or unbound types fail
assessment. `lax` assesses available declarations or instance types, and `skip`
does not assess the wildcard subtree.

For example, a shipment schema can admit partner records by type:

```xml
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:complexType name="Record">
    <xs:sequence><xs:element name="code" type="xs:int"/></xs:sequence>
    <xs:attribute name="tag" type="xs:string" use="required"/>
  </xs:complexType>
  <xs:element name="shipment"><xs:complexType><xs:sequence>
    <xs:any processContents="strict"/>
  </xs:sequence></xs:complexType></xs:element>
</xs:schema>
```

The following instance is valid without a global `partner` declaration:

```xml
<shipment xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <partner xsi:type="Record" tag="shipment"><code>17</code></partner>
</shipment>
```

An invalid integer, absent `tag`, or unresolved `xsi:type` rejects it.
`parse_xml_with_schema()` and `XmlReader` report `PARSE-XML-EXCEPTION`;
`XmlDoc::validateSchema()` reports `XSD-ERROR`. Validation preserves supplied XML
values. The native correction moves the strict-wildcard rejection after existing
instance-type assessment in `xmlSchemaValidateElemWildcard()`.

Schema compilation treats XML whitespace in declaration text and CDATA alike.
This follows [element-only content, clause 2.3](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-complex-type)
and XML's [CDATA character-data rules](https://www.w3.org/TR/REC-xml/#sec-cdata-sect).
Non-whitespace declaration text remains invalid. `xmlSchemaCleanupDoc()` removes
blank text and CDATA from declarations, and skips complete `appinfo` and
`documentation` subtrees to preserve annotation text, markup, comments and
processing instructions. Namespace identity determines these boundaries.
`xml:space` does not change schema validity; annotation content remains intact
with or without it. The former `xmlNodeGetSpacePreserve()` check on text nodes
always returned `-1` in the pinned dependency because it accepts only elements.

CMake probes these behaviors before accepting a system dependency. The wildcard
probe checks six schemas and 108 documents through DOM, streaming and repeated
validation. The whitespace probe checks 96 schemas through both memory and DOM
schema constructors, plus annotation preservation. `AUTO` falls back to pinned
private static libxml2 2.15.4; `SYSTEM` rejects a failing candidate. The two
corrections compose after earlier fixes, verify complete input/output SHA-256
values, and produce build-tree sources without changing downloaded source.

Allocation testing distinguishes required validation from context reset. The
reset recreates a dictionary after computing the verdict; failure there does
not invalidate a completed assessment. The harness records the first failed
allocation's phase, requires errors for preparation/walk failures, and checks
that reset failure preserves the verdict and leaves a null dictionary. Every
fault is repeated through the public API, with equal verdicts and allocation
counts, complete cleanup and fresh-context recovery. All six document shapes
also have a successful baseline. No production allocation change is involved.
Module-xml creates a context for each validation call and destroys it afterward;
the native test does not assume reuse of a context after reset allocation failure.

`test/xml-wildcard-types.qtest` covers all processing modes, selected primitive,
restricted and complex types, error recovery, cancellation and concurrent readers.
`test_native_wildcard_types.py` checks 36 schemas and 684 documents against
Xerces-J 2.12.2, with six namespace constraints. Pinned lxml/libxml2 2.12.10's
strict instance-type rejection remains an explicit oracle disagreement; native
expectations follow XSD and Xerces. Schema declaration and annotation behavior
also has WSDL/provider/import/reconstruction tests in
`test/wsdl-schema-whitespace.qtest` and `test_schema_whitespace.py`.
