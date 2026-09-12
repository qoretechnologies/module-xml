# Nilled element values

Copyright (C) 2026 Qore Technologies, s.r.o.

Nillability belongs to the receiving `XsdElement`. An inline complex type does
not inherit permission to nil its parent from a nillable child. `minOccurs`
still governs presence, and a present nilled element counts as one occurrence.
Empty occurrence lists cannot satisfy required counts. The established `()` alias
for one non-nillable empty complex record retains its prior meaning.

The expanded attribute `{http://www.w3.org/2001/XMLSchema-instance}nil` uses
the XSD boolean lexical space: `true`, `1`, `false`, `0`, with XML whitespace
collapsed. An element that is not nillable cannot carry that attribute, even
with `false`. Other namespaces and unqualified `nil` are ordinary attributes.

A true nil value contains no characters or child elements and cannot have a
fixed element constraint. Comments and zero-length CDATA contribute no
characters. The selected type still validates required, prohibited, fixed,
defaulted and wildcard attributes. False nil values undergo ordinary content
validation. Empty complex types reject text, whitespace and children.

`XsdNilValue` is the additive native representation of a present nilled element.
It contains a copy-on-write hash of native attribute values. Declared attributes
use their normal field names; wildcard attributes use expanded names. The carrier
rejects invalid names and instance metadata. Receiving declarations validate
attribute datatypes and uses. There is no mutable carrier API, and Serializable
reconstruction validates its metadata.

```qore
%modern
%requires WSDL
XsdSchema schema('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
    '<xs:element name="weight" nillable="true"><xs:complexType><xs:simpleContent>'
    '<xs:extension base="xs:decimal"><xs:attribute name="unit" type="xs:string" use="required"/>'
    '</xs:extension></xs:simpleContent></xs:complexType></xs:element></xs:schema>');
XsdNilValue unavailable({"unit": "kg"});
XsdXmlValue xml = schema.serializeXmlValue("", "weight", unavailable);
@assert(xml.getChildValues().empty());
auto provider = schema.getNativeDataProviderType("", "weight");
@assert(provider.acceptsValue(unavailable) === unavailable);
```

Use the explicit carrier for optional nil fields and for nil occurrences in a
list. `NOTHING` retains the established optional-omission behavior. A required
nillable element can still serialize `NOTHING` as one nil occurrence when its
attributes permit this; an explicit carrier is needed to supply attributes.

With ordinary decoding, an attribute-free nil keeps its established `NOTHING`
projection. Native type capture (`preserve_types=True`) returns `XsdNilValue`
for same-type nil values, preserving their presence. A different selected type
uses the existing `^type^` / `^val^` wrapper; its attribute-free nil payload
remains `NOTHING`. A portable wrapper whose `^type^` is an `XsdQNameValue`
supplies a present nil occurrence on output. Legacy component-object wrappers
retain optional omission for a `NOTHING` payload. Attributes require a carrier in either projection. Substitution identity
continues to use the outer `^element^` wrapper.

Ordinary nillable providers use `XsdNillableDataType`, retaining the declared
value's fields, list metadata and finite choices while adding the explicit nil
alternative. Native selected-type providers validate carriers against their
receiving declarations. Mandatory/optional and soft copies, saved providers,
SOAP message providers and real client/handler consumers retain the checks.
Nil carriers are exempt from scalar enumeration comparisons, but their own
declaration, fixed-value and attribute checks remain mandatory.

Attribute conversion is shared with ordinary complex values. Per-call namespace
copies and scoped conversion state prevent failures or concurrent messages from
changing the receiving schema. Cancellation retains its original exception
category. Conversion errors use `SOAP-DESERIALIZATION-ERROR` on input,
`SOAP-SERIALIZATION-ERROR` on output and `RUNTIME-TYPE-ERROR` in providers;
omitted mandatory provider values use `MISSING-VALUE-ERROR`.

The normative basis is XSD 1.0 [Element Locally Valid](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-elt)
clauses 3.1–3.2 and [Element Locally Valid (Complex Type)](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-complex-type).
See the unit, HTTP and independent matrix in `test/wsdl-element-nil*` and
`test/wsdl-interop/test_element_nil.py`.
