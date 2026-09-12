# Default values, actual types and identity constraints: open P5 question

Copyright (C) 2026 Qore Technologies, s.r.o.

This investigation is not accepted behavior. Native canonical-default changes
remain outside P5-16d's fixed-value increment until the interaction below is
adjudicated. WSDL instance defaults and identity constraints remain required.

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
