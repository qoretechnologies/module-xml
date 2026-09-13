# WSDL URI and language values

Copyright (C) 2026 Qore Technologies, s.r.o.

Builtin `anyURI` and `language` conversion validates the complete normalized
lexical value before accepting it. The shared text helper collapses XML
whitespace. URI validation calls `normalize_xsd_uri()`; language uses the XSD 1.0
pattern `[a-zA-Z]{1,8}(-[a-zA-Z0-9]{1,8})*`. Annotation language attributes use the
same helper. Only native URI lexical rejection is translated to the caller's
error category; allocation, encoding and cancellation errors propagate.

The URI result keeps its spelling: `a%2Fb` differs from `a/b`, and `%41` differs
from `A`. No reference is fetched, resolved or decoded. Language is derived from
string, so `en-US` and `EN-US` are distinct XSD values even though applications may
compare language tags case-insensitively. Empty URI values are valid; empty
language values are invalid. The legacy empty-element compatibility option still
controls omitted XML character data without turning explicit empty strings into
omitted values.

`XsdSizedFacetInfo.text_type` carries builtin URI/language validation in generated
providers. It requires string values, collapsed whitespace and no conflicting
name-type metadata. Derived providers validate through their base chain before
length, pattern and enumeration checks. Optional/list variants and Serializable
reconstruction retain this metadata. Diagnostic names are not used to infer a
datatype; existing name-validation metadata remains separate.

Schema conversion, declaration enumeration/default/fixed assessment, list items,
union trials, simple content and element/attribute fields all use the same
builtin validation. A union `language | boolean` rejects language spelling `1`
and selects boolean true. Its public value remains lexical `1` when converting
to `true` would select the earlier language member. Tests compare primitive
identity as well as the returned public value.

For example, a document connector can declare a URI for a product manual and a
language for its content:

```xml
<xs:complexType xmlns:xs="http://www.w3.org/2001/XMLSchema" name="Manual">
  <xs:sequence>
    <xs:element name="location" type="xs:anyURI"/>
    <xs:element name="language" type="xs:language"/>
  </xs:sequence>
</xs:complexType>
```

A value such as `../manuals/product guide.xml` is retained with its space.
`http://[bad` and `bad_lang` reject in the corresponding fields. The authored
`uri-language.json` matrix is checked by pinned Xerces, native validation and
WSDL original/saved schema/provider tests. Real SOAP 1.1/1.2 HTTP tests cover both
consumer directions, selected dynamic types, list/union fields and attributes.

Requirements: [XSD 1.0 anyURI](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#anyURI)
and [language](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#language).
