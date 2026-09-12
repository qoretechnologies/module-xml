# Receiving element fixed-value equality

Copyright (C) 2026 Qore Technologies, s.r.o.

An element declaration's fixed constraint belongs to the receiving element,
independently of its datatype. WSDL compares an occurrence with actual content
after validating and converting its selected type. The comparison uses XSD value
identity: integer and decimal restrictions share decimal values, while separate
primitive spaces remain distinct. QName identity uses namespace URI and local
name; lists compare ordered item identities, including the selected union member.
Mixed content must have matching character content and no element children.
Empty-element default processing is governed by a separate XSD rule.

The declaration records its computed identity alongside its resolved constraint.
References use the global declaration's identity; substitution members use their
own receiving declarations. The existing public constraint accessor retains its
lexical, namespace and native-value contract. Computed identity metadata has a
public hash declaration so Serializable can restore providers that retain an
element graph.

Providers saved before computed identity metadata existed retain the declaration's
original lexical value and type graph. Their first constraint check computes the
missing identity under a per-declaration mutex. The restore hook initializes only
local runtime state; type conversion waits until graph reconstruction is complete.
Successful computation is cached, while exceptions and cancellation release the
lock and permit a later retry. Re-saving retains the computed identity. Schema
objects continue to reconstruct their declarations from saved source documents.

Document conversion captures the selected union/list member during the original
conversion. A complex type's simple content shares that capture with its scalar
converter. This avoids selecting another member from a converted native value.
Generic XML output passes the identity from its existing validation of `xsi:type`
back to the receiving element; it does not repeat conversion. Every temporary
capture is scoped and restored on errors and cancellation. Constraints and
schema graphs hold no mutable per-document capture state.

Custom builtin converters retain their declared builtin XML value space. Equality
uses the input XML during decoding and the emitted XML during encoding, without
calling the custom converter again. Other custom conversion classes retain their
native value identity, scoped to the class and expanded datatype name. Such
classes remain responsible for a consistent native/wire conversion contract.

`XsdFixedElementDataType` preserves the ordinary provider's scalar/list/record
shape, requiredness, tags and soft conversion while checking the receiving constraint.
Its base category remains visible even though values must pass validation; native
XSD list providers explicitly report list behavior independently of that check.
Native type providers already perform receiving-element output validation and
use the same comparison. Mandatory examples use the fixed value and preserve
required attributes. Optional variants may omit the element; explicit nil still
uses the existing nillability and fixed-value exclusion rules.

For a fixed invoice quantity with a required unit:

```qore
XsdSchema schema("<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
    "<xs:element name='quantity' fixed='17'><xs:complexType><xs:simpleContent>"
    "<xs:extension base='xs:int'><xs:attribute name='unit' type='xs:token' use='required'/>"
    "</xs:extension></xs:simpleContent></xs:complexType></xs:element></xs:schema>");
AbstractDataProviderType quantity = schema.getNativeDataProviderType("", "quantity");
auto value = quantity.acceptsValue({"^value^":17, "^attributes^":{"unit":"kg"}});
XsdXmlValue xml = schema.serializeXmlValue("", "quantity", value);
@assert(xml.getXml().find(">17</") >= 0);
```

A value of 18 is rejected before the provider returns it. A different lexical
spelling of the same integer remains valid. The applicable requirements are
[XSD 1.0 element local validity](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-elt)
and [datatype value equality](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#equal).
The element declaration's [default/PSVI interaction](../test/wsdl-interop/default-identity-investigation.md)
is tracked separately from explicit fixed-value equality.
