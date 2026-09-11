# Strict element wildcard rejects an available instance type

Copyright (C) 2026 Qore Technologies, s.r.o.

Status: reproduced native libxml2 defect for P5-13, following the independent
core graph-cleanup prerequisite P5-12. No production change for this finding
is included in P5-12.

The following schema permits a child whose declaration is unknown but whose
`xsi:type` supplies a known type:

```xml
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="root">
    <xs:complexType>
      <xs:sequence>
        <xs:any processContents="strict"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
```

```xml
<root xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <unknown xsi:type="xs:int">17</unknown>
</root>
```

XSD 1.0 Structures [3.10.4](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-wildcard)
assigns `mustFind` assessment to a strict wildcard. Strict assessment can use
either an element declaration or an available instance type under
[3.3.4, Schema-Validity Assessment (Element), 1.2](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-assess-elt).
Assessment Outcome (Element), 1.1.3 rejects a `mustFind` child whose validity
remains unknown; a correctly typed child has known validity.

Pinned Xerces-J 2.12.2 accepts this input and rejects invalid integer text or
an unresolved instance type. Both native Qore DOM/reader paths using the P5-11
private libxml2 2.15.4 and the independent lxml/libxml2 2.12.10 reject the valid
input. Their diagnostic demands a global element declaration. Ordinary unknown
children without a type remain correctly rejected in strict mode.

`xmlSchemaValidateElemWildcard()` reports the missing strict declaration before
calling `xmlSchemaProcessXSIType()`. The existing instance-type path is therefore
available only for lax processing. The type validation path already checks the
selected type and its content; the ordering of this early rejection is the root
cause. Namespace admission and skip processing happen separately and must retain
their behavior.

The initial three-mode matrix has 24 documents: declared valid/invalid children,
unknown children, valid/invalid/unresolved instance types, and known descendants
inside lax unknown content. Reproduction files are
`/tmp/wsdl-p5-13-investigate.py`, `-wildcard-assessment.json`,
`-wildcard-xerces.json`, `-wildcard-native.log` and `-investigate.log` with the
same `/tmp/wsdl-p5-13` prefix. This is baseline failure evidence, not passing
compatibility coverage. Required implementation checks include configure-time
detection, both native paths, known/unknown declarations and types, namespace
constraints, simple/complex types, invalid content, cancellation and cleanup.
