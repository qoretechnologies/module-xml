# Native XML character-content assessment

Copyright (C) 2026 Qore Technologies, s.r.o.

Schema validation counts XML character information items independently of text
or CDATA event boundaries. An empty CDATA section contributes no characters.
Whitespace inside CDATA has the same content-model meaning as ordinary XML
whitespace. This follows XSD 1.0 [element validity](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-elt)
and [complex-type validity](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-complex-type).

The native validator therefore accepts empty CDATA on a nilled element, or on
an element whose complex type has empty content. Actual characters, including
whitespace, still reject in those contexts. An element-only content model admits
XML whitespace inside or outside CDATA, while rejecting other text. Required
attributes, required particles and fixed-value constraints remain enforced.

For example, a missing shipment quantity can retain a producer's empty CDATA:

```qore
string schema = '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
    '<xs:element name="quantity" type="xs:int" nillable="true"/></xs:schema>';
string xml = '<quantity xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
    ' xsi:nil="true"><![CDATA[]]></quantity>';
XmlDoc document(xml);
document.validateSchema(schema);
```

Replacing that empty CDATA with a space rejects: a nilled quantity cannot have
character children. On a non-nilled empty element, a declared default/fixed
value can apply even when the original XML contains empty CDATA and comments.
Validation preserves the document's lexical XML data; it does not insert default
text or remove CDATA to make an input pass.

## Event handling and ownership

`xmlSchemaVPushText` checks for a zero-length event before nil/content checks or
ownership transfer. Its consumed result remains false for caller-owned empty
buffers. A zero length is authoritative even if the buffer is not NUL-terminated.
For actual characters the helper clears the element-empty flag once and applies
the content rule. Text and CDATA use the same whitespace check.

The DOM and SAX callers no longer clear the empty flag before that decision.
Public XmlReader schema validation uses those SAX handlers. The upstream internal
reader walker is disabled in the pinned source; its call signature remains
consistent. Empty events introduce no allocation, and temporary schema/context
ownership otherwise follows the existing native validation paths.

## Dependency selection and verification

The configure probe tests positive and negative character-content cases through
DOM and public reader validation. AUTO retains a system library only when the
complete probe passes; otherwise it selects the pinned private dependency.
SYSTEM rejects a defective library. The character-content correction follows
the existing private source transformations, verifies input/output hashes and
leaves upstream files untouched. Reconfiguration preserves identical output.

`xml-character-content.qtest` covers nil, empty/element-only content, text/CDATA
boundaries, XML versus non-XML whitespace, required attributes, defaults/fixed
values and recovery. `test_character_content.py` checks sixteen schemas and 812
documents against specification-derived verdicts and pinned Xerces, including
unchanged valid XML data. Native ownership tests cover all three text ownership
modes and both SAX callbacks with empty and non-terminated zero-length buffers.
The complete dependency probe and affected Qore suite also run under Valgrind.

These native rules apply to XmlDoc, parse_xml_with_schema and XmlReader. WSDL's
own declaration-level nil/default/fixed conversion has separate implementation
and acceptance requirements.
