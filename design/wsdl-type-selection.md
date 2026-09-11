# WSDL native type identity and XML type annotations

Copyright (C) 2026 Qore Technologies, s.r.o.

`XsdElement::serializeValue()` and `serializeOccurrence()` accept a native
`{"^type^": selected, "^val^": value}` wrapper. Selecting the declaration's own
type retains the ordinary conversion, facet, nil and occurrence checks. The
wrapper does not create an additional element occurrence or change the shared
declaration. A repeated native record field uses an occurrence list whose entries
can each select a type; the low-level collection API also accepts one wrapper
around the complete occurrence list.

`XsdTypeDerivationHelper::sameType()` recognizes the same component object. Two
canonical `XsdBaseType` objects also identify the same definition when they have
the same recognized XSD name and the XSD namespace in their owned output registry.
The legacy HTTP `binary` type and custom conversion subclasses are excluded from
this cross-registry rule. User-defined components are not equated by local name
or by coincidentally matching names from separately constructed schemas. Within
one assembled schema, resolved references and deduplicated global declarations
already share their component objects. Foreign component objects do not merge
their definitions into that schema merely by being passed in a wrapper. Accepted
equivalent builtins normalize to the element's declared object before conversion,
so an explicitly selected identical type does not force unnecessary annotations.

Resolved simple and complex ancestry is checked by the
[type substitution implementation](wsdl-type-substitution.md), including effective
`block` controls and abstract declarations. Wire decoding resolves the expanded
`{namespace}local` identity of `xsi:type` in the instance scope before validating
attributes and children. Scoped QName context restores on every return and
exception. Unknown, unbound, malformed and incompatible selections report
`SOAP-DESERIALIZATION-ERROR`; native compatibility failures report
`SOAP-SERIALIZATION-ERROR`.

`XsdDocumentValueHelper::typeAttributes()` translates the selected component's
owned namespace into the current output registry and allocates the XML Schema
instance prefix there. Element qualification never determines the namespace of
the type QName. Element conversion merges the selected type annotation after
conversion, preserving other attributes, comments and children. This prevents a
restriction, list or union converter's delegated base/member annotation from
replacing the selected component. Anonymous simple types omit delegated type
annotations because their bases and members are not names for the anonymous
component. The existing `anyType` scalar inference owns its runtime annotation.

Complex simple content contributes scalar text and any lexical namespace
declarations directly to the containing XML value. It does not nest an XML value
hash in `^value^` or emit the simple base's annotation as the complex type.
Complete `serializeXmlValue()` and SOAP message APIs still perform their final
QName namespace allocation; their existing contract is required when data QName
prefixes collide with structural prefixes.

All new helper state is local to a call. Schema registries are read through their
owned output mapping, and only the caller's output registry acquires prefixes.
Identity checks require constant component operations. Different selected types
use the bounded resolved-graph traversal documented with substitution controls.
Serialization visits each occurrence once. Cancellation propagates unchanged,
and custom value conversion is invoked once per occurrence.

For an invoice quantity, the explicit spelling can be used without changing its
ordinary native representation:

```qore
XsdSchema schema("<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
    "<xs:element name='quantity' type='xs:int'/></xs:schema>");
XsdElement quantity = schema.getElement("", "quantity");
XsdXmlValue output = schema.serializeXmlValue("", "quantity",
    {"^type^": quantity.type, "^val^": 17});
```

The implementation follows XSD 1.0 Structures
[Type Derivation OK (Simple), clause 1](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cos-st-derived-ok),
[builtin definitions in section 3.14.7](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/),
and [Element Locally Valid](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-elt).
The executable scope is recorded by `test/wsdl-type-identity.qtest` and the
independent `test/wsdl-interop/test_type_identity.py` matrix. The derivation and
instance-control regressions extend that scope in `wsdl-type-substitution.qtest`.
Native result retention and the remaining P5 semantics retain their full plan
ownership; retained XML carries the original selected type annotation.
