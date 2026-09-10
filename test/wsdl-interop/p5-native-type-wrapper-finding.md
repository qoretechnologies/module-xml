# P5 open finding: builtin native type-wrapper identity

Copyright (C) 2026 Qore Technologies, s.r.o.

Status: the reproduced identity failure is fixed in P5-01, with positive,
negative and independently validated annotation regressions in
`test/wsdl-type-identity.qtest` and `test/wsdl-interop/test_type_identity.py`.
The full remaining P5 derivation and substitution-control requirements remain
open; identity alone is not counted as full dynamic-type acceptance.

The native `^type^` / `^val^` wrapper selects an `XsdAbstractType`. When reproduced
in P4-10, selecting the same builtin scalar object as the element's declared type
raised `SOAP-SERIALIZATION-ERROR` before value conversion.
`XsdAbstractType::checkExtends()` unconditionally threw; only the complex-type
override accepted identity and its existing extension relationship. Both the
existing `serializeValue()` and the new single-occurrence delegate used that
dispatch.

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
Historical actual: the error reported that explicit type `int` is incompatible with type `int`.
The existing API reproducer exited 3; historical logs are
`/tmp/wsdl-p4-10-builtin-wrapper.log` and the initial single-occurrence test log
`/tmp/wsdl-p4-10-serialization-first.log`.

XSD 1.0 [Type Derivation OK (Simple), clause 1](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-st-derived-ok)
accepts identity. P5 must apply the full appropriate derivation relationship,
including simple/complex type restrictions and applicable substitution controls,
to native wrappers and wire `xsi:type` selection. A name-only comparison is
insufficient because same-named components in different namespaces can differ.

The P4 single-occurrence suite covered the existing complex wrapper path. P5-01
adds declared-component identity (including canonical builtins in separate
registries), annotation namespace ownership, named/anonymous simple type checks,
and complex dispatch before derived attribute validation. Its regressions also
fix delegated base annotations and nested simple-content value hashes. Full
transitive derivation, `block`/`final`, and retained selected-type semantics remain
part of P5 acceptance.
