# Ordered native mixed content

Copyright (C) 2026 Qore Technologies, s.r.o.

Mixed complex content uses an ordered native hash. Each key identifies a text
fragment, comment or child segment. The converter matches the complete child
sequence against the existing bounded particle model, then converts each
occurrence in place using its selected declaration or wildcard assessment.
Text never moves around children to make an invalid sequence acceptable.

| Content | Native representation |
| --- | --- |
| Text | `^value^`, `^value1^`, `^value2^`, etc. |
| CDATA | `^cdata^` and numbered variants |
| Comment | `^comment^` and numbered variants, when included by the XML parser |
| Declared child | Its provider field name; expanded names disambiguate local-name collisions |
| Wildcard child | Its expanded XML name in native capture; ordinary decoding keeps the incoming field spelling |
| Later child segment | `name^1`, `name^2`, etc., at that position in the hash |
| Attributes | The existing `^attributes^` hash, independent of content order |

Adjacent occurrences of a child can share a list when each child has a scalar
value. An XSD list-valued child uses one native list per segment: `codes: (1, 2)`
and `codes^1: (3, 4)` represent two children. Empty lists are valid values for
such a child. Empty occurrence collections for other children are rejected.
Decoding may combine adjacent segments with the same child name; their XML order
and individual values stay unchanged.

Native type capture decodes pure text and empty mixed elements as ordered hashes,
including `{}` for an empty value. Ordinary decoding retains the established
scalar projection for a single text fragment and `NOTHING` for empty content. Direct serialization also accepts
a string as one text fragment and preserves whole numeric, boolean and date
scalar conversion through `make_xml()`. Providers use the hash form. Explicit
integer/boolean text fragments and unknown metadata are rejected. XML comments must
be valid comment text. Zero-length CDATA contributes no characters.

```qore
%modern
%requires WSDL
XsdSchema schema('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
    '<xs:element name="description"><xs:complexType mixed="true"><xs:sequence>'
    '<xs:element name="code" type="xs:int" maxOccurs="2"/>'
    '</xs:sequence></xs:complexType></xs:element></xs:schema>');
hash<auto> description = {"^value^": "Parts ", "code": 17, "^value1^": " and ",
    "code^1": 29, "^value2^": " are available."};
auto provider = schema.getNativeDataProviderType("", "description");
auto checked = provider.acceptsValue(description);
XsdXmlValue xml = schema.serializeXmlValue("", "description", checked);
@assert(xml.getChildValues().size() == 2);
@assert((keys checked) == (keys description));
```

Native type capture retains uninterpreted text/CDATA as `XsdScopedLexicalValue`
with its input namespace bindings. Typed QName children keep their own expanded
identity, even when their prefix shadows a prefix in surrounding text. On output,
the existing QName allocator preserves those contexts and prevents generated
prefixes from capturing originally unbound lexical tokens. It omits newly generated
redundant namespace declarations while preserving declarations explicitly supplied
in the XML data view. Ordinary decoding
keeps plain string fragments. Use capture for portable namespace-sensitive native
values, or `XsdXmlValue` for complete retained XML.

Component callers that need comments in the native view use
`parse_xml(xml, XPF_PRESERVE_ORDER | XPF_ADD_COMMENTS)`. Native HTTP consumers use
their established XML parser options; the explicit retained XML HTTP APIs preserve
comments and lexical XML. CDATA boundaries are a supported data-view feature;
they do not change the character items in the XML infoset.

`XsdMixedContentDataType` preserves ordered segments while applying the declared
field providers, including soft conversion and finite choices. Whole-record
requiredness, attributes, custom required groups and complete particle validation
remain enforced. Copied and reconstructed providers retain the component graph.
Bounded samples retain their selected particle schedule, including alternating
repeated groups and repeated list-valued children. `hasMixedContent()` exposes
the resolved content kind.

The converter uses linear storage in the supplied fragments and occurrences,
plus the existing particle matcher's documented limits. It does not construct
XML and parse it to coerce provider values. Namespaces are per call; completed
component graphs are read-only during conversion. Cancellation and unrelated
exceptions propagate, and rejected conversions preserve caller-owned data.

The normative basis is XSD 1.0 [complex content validation](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-complex-type)
clause 2.4, together with the XML Infoset's ordered [element children](https://www.w3.org/TR/xml-infoset/#infoitem.element).
Tests cover native and retained values, reconstructed providers, wildcard modes,
substitution/selected types, namespace collisions, cancellation, bounded samples
and both actual SOAP bindings through direct and HTTP consumers.
