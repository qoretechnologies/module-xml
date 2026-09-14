# Native key field declaration assessment

Copyright (C) 2026 Qore Technologies, s.r.o.

[XSD 1.0 Structures 3.11.4, clause 4.2.3](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-identity-constraint)
forbids key fields assessed against an element declaration with `nillable=true`.
This property belongs to the declaration; it is independent of whether an
instance has `xsi:nil`, and independent of its selected simple or complex type.

For example, this declaration cannot supply a key field, even when the document
contains `<productCode>42</productCode>`:

```xml
<xs:element name="productCode" type="xs:int" nillable="true"/>
```

A required product key should instead use a non-nillable declaration:

```xml
<xs:element name="productCode" type="xs:int"/>
```

An attribute key such as `@productCode` on a nillable product element remains
valid. Likewise, a nillable declaration outside the selector's target nodes does
not invalidate the key. Unique and keyref fields with non-nil values remain
valid; nil tuple qualification follows the approved
[nil-as-missing interpretation](../test/wsdl-interop/nil-identity-interpretation.md).

## Assessment and ownership

The private libxml2 correction checks matched key fields in
`xmlSchemaXPathProcessHistory()` against `inode->decl`. It first distinguishes
element fields from attribute fields, then checks the constraint category and
the effective declaration's nillable flag. Consequently element references,
substitution members, strict wildcards and `xsi:type` all use the declaration
that actually assessed the field. Simple-content complex types follow the same
rule as simple types.

A rejected match uses the existing validation error machinery, pops its history
entry and joins the normal state deregistration path. It neither consumes the
node's computed value nor changes shared tuple state, so other constraints
matching that field retain their assessment. All state belongs to the current
validation context; no new shared data, traversal or blocking work is added.
Allocation failure while formatting an already-invalid field's diagnostic must
preserve rejection and cleanup; six allocation positions are tested with both
one-shot and persistent failure followed by successful recovery.

## Dependency selection and coverage

The `key_nillable` configure probe tests ten positive and negative cases through
both DOM and reader validation, including context reuse after rejection. AUTO
chooses the pinned private dependency when the system library fails; SYSTEM
reports the failed probe. The build-tree fix checks input and output SHA-256,
preserves the unpacked upstream source and is idempotent on reconfiguration.
The correction adds no Qore ABI or public API.

`test/xml-key-nillable.qtest` covers 63 schema/document pairs through the reader,
parser and DOM APIs, asserts rejection categories and verifies unchanged DOM
content. `test/wsdl-interop/test_key_nillable.py` independently checks the same
matrix against pinned Xerces. Provider tests cover selection, distribution,
idempotence and allocation cleanup. Full acceptance evidence is recorded in
[test/wsdl-interop/native-key-nillable-evidence.md](../test/wsdl-interop/native-key-nillable-evidence.md).
