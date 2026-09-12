# WSDL element value-constraint declarations

Copyright (C) 2026 Qore Technologies, s.r.o.

An element's default or fixed value belongs to its declaration. Two elements
using the same datatype can have different constraints. Global references use
the referenced declaration's constraint and retain their own occurrence limits.

Schema construction captures the original lexical value and the namespace
bindings needed to interpret it. After resolving and finalizing the type graph,
the element checks the constraint against its simple datatype, including
restrictions, lists and unions. A complex type permits a constraint when it has
simple content, or mixed content whose complete particle admits no children.
Required attributes do not prevent declaring a constraint. ID-derived types
cannot have default/fixed values. These rules implement XSD 1.0
[Element Declaration Properties Correct and Element Default Valid (Immediate)](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#e-props-correct).

Invalid values fail construction with `WSDL-ERROR`. Cancellation propagates
unchanged. Failed schema additions retain the existing schema and its declarations.
Constraint conversion does not evaluate document-dependent ENTITY requirements;
those require the instance document context.

`XsdElement::getValueConstraint()` returns `NOTHING` when there is no constraint,
or a copy of `XsdElementValueConstraintInfo`:

| Member | Meaning |
| --- | --- |
| `fixed` | `True` for fixed; `False` for default |
| `lexical` | Original XML attribute text, including meaningful whitespace |
| `namespaces` | Captured declaration bindings, including the default namespace |
| `value` | The converted simple-content value |

The value uses established datatype representations: exact decimal text, QName
objects for qualified names, ordinary text for unqualified names, and scoped
lexical values where a union must preserve an unbound prefix. The namespace
metadata accompanies the original text so an instance cannot reinterpret a
default's prefix. Serialized schemas preserve all four members. Mutating a
returned hash does not alter the declaration.

For example, inspect an invoice quantity's default before presenting it in an
application:

```qore
XsdSchema schema('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
    '<xs:element name="quantity" type="xs:int" default="17"/></xs:schema>');
hash<XsdElementValueConstraintInfo> constraint = schema.getElement("", "quantity").getValueConstraint();
@assert(!constraint.fixed && constraint.value == 17 && constraint.lexical == "17");
```

This API reports declaration metadata. Instance conversion, nil validation and
the distinction between absent, empty and defaulted elements have separate
acceptance coverage in P5. The metadata API does not imply that an absent
optional element should be created automatically.

`test/wsdl-element-constraints.qtest` covers declarations, namespace capture,
references, imported schemas, reconstruction, failed-addition recovery and
conversion failures. A deterministic sandbox interruption checks cancellation,
retained values and namespace cleanup before successful revalidation.
`test/wsdl-interop/test_element_constraints.py` compares 188 schemas and 376
actual SOAP 1.1/1.2 binding descriptions with pinned Xerces, including rejected
lexical values and incompatible complex content models.
