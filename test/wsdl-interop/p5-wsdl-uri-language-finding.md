# P5 WSDL anyURI and language scalar validation

Copyright (C) 2026 Qore Technologies, s.r.o.

While connecting annotation attributes to the native anyURI checker, inspection
and a standalone reproduction found that WSDL's builtin anyURI and language
value paths use the generic string branch. `serializeXmlValue()` accepts
`http://[bad` as anyURI and `bad_lang` as language; native XSD validation rejects
both emitted values with `PARSE-XML-EXCEPTION`.

The reproduction and exact output are under
`/tmp/wsdl-p5-19f-wsdl-annotations/scalar-probe.qr` and `scalar-probe.log`.
The annotation increment validates these types only where they occur in schema
annotation attributes. It does not claim to close the scalar/provider gap.

P5-19g applies lexical/value separation to builtin anyURI and language
serialization/deserialization, derived types, lists/unions, fixed/default
constraints and saved providers. Both SOAP directions, native/Xerces validity,
primitive union identity, simple content, examples and cancellation are tested.
URI normalization reuses `normalize_xsd_uri()` without changing URI identity.
See [implemented design](../../design/wsdl-uri-language-values.md). Key/unique/keyref
and complete typed accounting remain next before P6–P9.

Requirements: [XSD 1.0 anyURI](https://www.w3.org/TR/xmlschema-2/#anyURI) and
[language](https://www.w3.org/TR/xmlschema-2/#language).
