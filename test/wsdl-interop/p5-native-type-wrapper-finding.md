# P5 open finding: builtin native type-wrapper identity

Copyright (C) 2026 Qore Technologies, s.r.o.

Status: reproduced during P4-10, assigned to the existing P5 type-derivation
requirement. This valid input still fails and is not counted as an expected
rejection or a passing conformance case.

The native `^type^` / `^val^` wrapper selects an `XsdAbstractType`. Selecting the
same builtin scalar object as the element's declared type raises
`SOAP-SERIALIZATION-ERROR` before value conversion. `XsdAbstractType::checkExtends()`
unconditionally throws; only the complex-type override accepts identity and its
existing extension relationship. Both the existing `serializeValue()` and the
new single-occurrence delegate use this unchanged dispatch.

Reproducer, with the local WSDL module loaded:

```qore
XsdSchema schema("<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
    "<xs:complexType name='Record'><xs:sequence>"
    "<xs:element name='item' type='xs:int' minOccurs='2' maxOccurs='3'/>"
    "</xs:sequence></xs:complexType></xs:schema>");
XsdElement element = cast<XsdComplexType>(schema.findType("Record")).getParticle().getChildren()[0].getElement();
element.serializeValue(schema.nsc.copy(), {"^type^": element.type, "^val^": (1, 2)},
    True, "item", "Record");
```

Expected: the two integer occurrences are accepted with the same declared type.
Actual: the error reports that explicit type `int` is incompatible with type `int`.
The existing API reproducer exits 3; logs are
`/tmp/wsdl-p4-10-builtin-wrapper.log` and the initial single-occurrence test log
`/tmp/wsdl-p4-10-serialization-first.log`.

XSD 1.0 [Type Derivation OK (Simple), clause 1](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-st-derived-ok)
accepts identity. P5 must apply the full appropriate derivation relationship,
including simple/complex type restrictions and applicable substitution controls,
to native wrappers and wire `xsi:type` selection. A name-only comparison is
insufficient because same-named components in different namespaces can differ.

The P4 single-occurrence suite checks the existing supported complex-type wrapper
path, incompatible types and invalid values. It makes no claim that this scalar
wrapper failure or full P5 dynamic-type semantics have been fixed.
