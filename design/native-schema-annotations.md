# Native XSD annotation attributes

Copyright (C) 2026 Qore Technologies, s.r.o.

XSD 1.0 annotations accept foreign namespace attributes, including an attribute
whose local name is `lang`. Only the expanded name `xml:lang` on `documentation`
has the declared `xs:language` type. The empty string is invalid for that XSD 1.0
representation, independently of XML's general language-reset convention.
Both `appinfo` and `documentation` validate their unqualified `source` as
`xs:anyURI`; validation never dereferences that value.

The private libxml2 correction removes an erroneous local-name restriction on
foreign attributes and applies the existing URI attribute validator to
`documentation`. It preserves existing annotation structure, arbitrary mixed
payloads, ID checks and language validation. The existing parser context owns
all diagnostics and temporary values; no shared mutable state or public ABI is
added. The correction introduces no production loop or resource loading.

CMake's behavior probe checks the corrected and rejected cases. A system library
with either defect fails selection; AUTO uses the pinned private dependency and
SYSTEM reports a configuration error. Build-tree source rewriting verifies both
input and output SHA-256 and does not modify the fetched source archive.

For example, this annotation retains application metadata without requiring a
resource fetch:

```xml
<xs:annotation xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:documentation xmlns:catalog="urn:catalog" catalog:lang="internal"
                    xml:lang="en-US" source="../manual">
    Product format documentation
  </xs:documentation>
</xs:annotation>
```

Tests: `test/xml-annotations.qtest`, the 117-schema
`test/wsdl-interop/fixtures/annotations.json` matrix, the pinned independent
Xerces checker `test/wsdl-interop/test_annotations.py`, and actual dependency
selection tests in `test/cmake/test_libxml2_provider.py`.

Normative source: [XSD 1.0 Part 1, §3.13.2–3](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cAnnotations).
