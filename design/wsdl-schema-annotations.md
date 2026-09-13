# WSDL schema annotation grammar

Copyright (C) 2026 Qore Technologies, s.r.o.

`XsdSchema` and inline WSDL schema loading validate annotation markup before
`XsdSchemaSource` groups XML children for component construction. The streaming
checker validates annotation content, own attributes, `source` URI references,
`xml:lang`, annotation placement and declaration IDs. The existing facet checker
runs first, retaining its established error categories for facet ordering.
Other malformed annotation and ID declarations raise `WSDL-ERROR`.

The checker tracks element frames by depth and IDs by normalized value. Each
original parsed document has its own ID table; IDs from independently added,
imported or included documents do not collide. Inline schemas in one WSDL input
share the document check. Schema/redefine containers permit repeated annotations;
other components permit one annotation before their content. The checker skips
arbitrary mixed appinfo/documentation payloads, including embedded XSD elements,
so payload IDs and markup do not become schema declarations.

URI validation uses the binary module's `normalize_xsd_uri()` API. It returns
whitespace-collapsed XSD anyURI text without fetching, resolving, percent-decoding
or percent-encoding it. Native datatype and temporary value ownership remain
inside the call; allocation, encoding and cancellation errors propagate.
Only lexical URI errors are mapped to the schema error category. Language tags
follow the XSD 1.0 `language` pattern after XML whitespace collapse.

For example, application metadata may use its own `lang` attribute, while
`xml:lang` has the XSD language type:

```xml
<xs:annotation xmlns:xs="http://www.w3.org/2001/XMLSchema" id="manual">
  <xs:documentation xmlns:app="urn:product" app:lang="internal label"
                    xml:lang="en-US" source="../manuals/product guide.xml">
    Product instructions
  </xs:documentation>
  <xs:appinfo><example xmlns="urn:product">application data</example></xs:appinfo>
  <xs:documentation/>
</xs:annotation>
```

Complex types accept empty annotations and empty documentation. Their plain-text
documentation field flattens mixed markup in XML order, ignores attributes and
application information, trims each documentation fragment and joins fragments
with newlines. The original markup remains in saved schema source. Annotation
payloads retain ordered child runs during source conversion; extracting text does
not reorder repeated elements around intervening character data.

The grouping conversion creates `list<auto>` containers explicitly when merging
separated child runs. An earlier run containing hashes must not constrain later
empty or string-valued occurrences. The original run is copied at most once;
subsequent items append without repeatedly copying all prior items. Schema source
bytes remain available for Serializable reconstruction, which repeats grammar
validation. Per-call grammar tables avoid state retained after failures or shared
between reconstructed schemas.

Tests: `test/wsdl-annotations.qtest`, `test/xml-uri-values.qtest` and the annotated
SOAP 1.1/1.2 contracts in `test/wsdl-notation-http.qtest`. The shared native/Xerces
annotation matrix is unchanged from P5-19e.

Normative sources: [XSD 1.0 annotations](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cAnnotations),
[ID validation](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-id),
[anyURI](https://www.w3.org/TR/xmlschema-2/#anyURI) and
[language](https://www.w3.org/TR/xmlschema-2/#language).
