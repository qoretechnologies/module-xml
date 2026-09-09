# QName lexical validation

Copyright (C) 2026 Qore Technologies, s.r.o.

`xs:QName` scalar conversion accepts a nonempty NCName or two NCNames separated by
one colon. It collapses XML whitespace before validation and retains the resulting
text. Both components use the XML 1.0 Second Edition character ranges referenced
by XSD 1.0, as do the existing `xs:NCName` datatype and XSD name regex escapes.
The XML parser's newer element-name rules are a separate contract.

Builtin serializers, decoders and data providers share this lexical check.
Invalid values raise `SOAP-SERIALIZATION-ERROR`, `SOAP-DESERIALIZATION-ERROR` or
`RUNTIME-TYPE-ERROR`, respectively. Optional providers accept omission, while
empty text remains an invalid QName. Reconstructed providers retain validation;
enclosing list providers cannot bypass item conversion through a direct native
string assignment. An invalid QName union alternative permits a later string
member to retain its original whitespace.

Restriction patterns apply to collapsed text at each derivation step, including
detached providers. QName length facets are deprecated and impose no value-length
constraint. Example generation checks the complete scalar serialization path for
each candidate: the supplied value, enumeration spellings, a bounded pattern
sample and a simple local name. It raises `XSD-SAMPLE-ERROR` if none satisfies the
lexical restrictions. Malformed enumeration spellings fail schema construction.

```qore
%modern
%requires WSDL
Namespaces namespaces({});
XsdBaseType name_type = namespaces.getBaseType("QName");
AbstractDataProviderType field = name_type.getDataProviderType();
@assert(field.acceptsValue(" \txml:lang\n") == "xml:lang");
@assert(name_type.serializeValue(namespaces, " Customer ", True) == "Customer");
# field.acceptsValue("customer:address:city") raises RUNTIME-TYPE-ERROR.
```

These scalar APIs return strings. Lexical acceptance alone does not establish a
prefix binding or namespace-based value equality. General message namespace
identity, QName enumeration equivalence and prefix allocation are not supplied
by this lexical validator. The existing `XsdXmlValue` representation retains
namespace context for callers that need the XML infoset.

Normative sources: [XSD 1.0 QName](https://www.w3.org/TR/xmlschema-2/#QName),
[the referenced 1999 QName grammar](https://www.w3.org/TR/1999/REC-xml-names-19990114/#NT-QName),
and [XSD length](https://www.w3.org/TR/xmlschema-2/#rf-length).

`test/wsdl-qname-lexical.qtest`, `test/wsdl-qname-consumers.qtest` and
`test/wsdl-interop/test_qname_lexical.py` cover positive/negative grammar,
4,036 character boundaries, patterns, examples, reconstruction, cancellation,
list/union membership and actual SOAP 1.1/1.2 bindings in both directions.
The independent binding matrix compares namespace/local identity for its local
and implicitly bound `xml` names as well as validating output with libxml2 and
Xerces-J.
