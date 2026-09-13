# Default values, actual types and identity constraints: approved interpretation

Copyright (C) 2026 Qore Technologies, s.r.o.

This record preserves the investigation that preceded the approved interpretation
at the end of this document. Native canonical-default changes were kept outside
P5-16d's fixed-value increment pending that decision. Implementation and acceptance
are tracked separately; WSDL instance defaults and identity constraints remain required.

XSD 1.0 [cvc-elt 5.1.1/5.1.2](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-elt)
requires assessment of a default's canonical lexical representation against the
actual type. The later [E1-56 erratum](https://www.w3.org/2004/03/xmlschema-errata.html#E1-56)
changes PSVI contributions to use the constraint's `{lexical form}`. XSD 1.0's
value-constraint component has no property with that name: it contains a value
and default/fixed variety. [WG issue 6836](https://www.w3.org/Bugs/Public/show_bug.cgi?id=6836)
records adoption of the erratum; [issue 2632](https://www.w3.org/Bugs/Public/show_bug.cgi?id=2632)
separates the XSD 1.1 decision from the XSD 1.0 erratum.

A small schema makes the difference observable:

```xml
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:simpleType name="Base"><xs:union memberTypes="xs:boolean xs:string"/></xs:simpleType>
  <xs:element name="root">
    <xs:complexType><xs:sequence>
      <xs:element name="item" type="Base" default="1" maxOccurs="unbounded"/>
    </xs:sequence></xs:complexType>
    <xs:unique name="key"><xs:selector xpath="item"/><xs:field xpath="."/></xs:unique>
  </xs:element>
</xs:schema>
```

The instance contains an empty `item` with `xsi:type="xs:string"`, followed by an
explicit string-typed item. If the explicit string is `true`, the experimental
canonical-default patch reports a duplicate. Pinned Xerces 2.12.2 accepts both
that document and one whose explicit string is `1`: it retains the declaration's
boolean value. Processing the original spelling as the selected string type
instead gives `1`. Identity constraints use type-determined values of PSVI's
schema-normalized values, so this cannot be settled solely by lexical validation.

A union of boolean and QName with the same default and actual QName is an
additional boundary to assess: the canonical spelling `true` is a QName lexical,
whereas original `1` is not. Do not introduce a fallback or value-copy rule merely
to match one validator. No such rule has been added.

Reproduction files and observations are retained under
`/tmp/wsdl-p5-16d-values/default-key-*`; the broader native investigation is
`/tmp/wsdl-native-value-constraints/README.md`. Pending implementation and tests
are in `/tmp/wsdl-p5-16d-values/pending`, with the complete pre-split snapshot in
`/tmp/wsdl-p5-16d-values/before-native-split`. Restore them by integrating only
the remaining canonical-default changes on top of P5-16d; do not overwrite the
completed fixed, time, unsigned or allocation corrections with the older snapshot.

## Reduced implementation and decision boundary (2026-09-13)

After P5-18h's exact calendar correction, the unchanged-source reduction under
`/tmp/wsdl-p5-18i-default-assessment/` covers 40 valid schemas and 200 documents.
Each native conversion/DOM/reader path has 54 invalid acceptances and 54 valid
rejections; WSDL rejects 66 valid documents. The native root cause is the explicit
noncanonical shortcut in `xmlSchemaValidatorPopElem`; WSDL sends empty content
to the datatype without applying its element constraint.

The isolated canonical-assessment prototype corrects every native verdict
(600 stage records), with unchanged DOM text. It is not integrated or accepted
as PSVI behavior. Seven additional identity documents reproduce the distinction
on both the current provider and prototype, across all three native APIs, with
pinned Xerces results recorded separately in `identity-comparison.json`.

For an empty boolean-or-string element with default `1` and actual `xs:string`:

| Interpretation | Resulting value | Duplicate explicit string `1` | Duplicate explicit string `true` | Duplicate explicit boolean `true` |
| --- | --- | --- | --- | --- |
| Original spelling under actual type (current native) | string `1` | yes | no | no |
| Canonical assessment under actual type (prototype) | string `true` | no | yes | no |
| Declared constraint value (Xerces) | boolean true | no | no | yes |

The proposed interpretation is the canonical value assessed under the actual
type, retaining the original spelling, declaration namespaces and original
constraint value separately. This is coherent with the unchanged XSD 1.0
validity clauses and avoids assigning an invalid lexical `1` to an actual QName.
The missing erratum property prevents claiming that this choice follows an
unambiguous normative PSVI rule. It requires an explicit decision before the
prototype is integrated; no validator-specific fallback or scope reduction is
proposed. Default PSVI, identity constraints and full P5 acceptance remain open.

## Approved interpretation

On 2026-09-13 the user explicitly approved the proposed canonical-actual-type
interpretation above. Empty defaults use the canonical spelling validated under
the actual type for the instance value and identity. Original declaration text,
namespace context and declared constraint value remain separately preserved.
This resolves the policy decision; implementation and acceptance are in progress.
No additional confirmation is required for this interpretation.
