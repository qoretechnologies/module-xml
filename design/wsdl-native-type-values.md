# Portable native XSD type values

Copyright (C) 2026 Qore Technologies, s.r.o.

Native decoding can explicitly retain the selected type at an element or WSDL
type-part boundary. `WSOperation::deserializeRequest()` and `deserializeResponse()`
accept a final `preserve_types` boolean, defaulting to `False`. The corresponding
`SoapClient::callOperation()` option and final `SoapHandler::addMethod()` argument
select the same representation for results and callback arguments.

A selection different from the declaration becomes:

```qore
{"^type^": new XsdQNameValue("urn:parts", "DescribedPart"),
 "^val^": {"number": 17, "description": "Replacement part"}}
```

The wrapper has exactly those two keys. Its native value cannot itself be a type
wrapper, but nested element fields and individual occurrences can have their own
wrappers. An identical selected type keeps the ordinary native value. A selected
nilled value uses `NOTHING` in `^val^`. Existing calls continue to return their
established scalar, list and record shapes.

The expanded QName can be saved through `Serializable` independently of the
schema. Serialization resolves it against the receiving schema, then checks the
resolved definition's derivation, effective block exclusions, abstract status,
facets, occurrence count and content. Saving a value does not authorize a type
that the receiver does not declare or permit. Canonical XSD builtin QNames use
canonical builtin definitions; a custom conversion subclass cannot impersonate
one through its name. Unbound output type names and malformed wrappers raise
`SOAP-SERIALIZATION-ERROR`.

The original `XsdAbstractType` wrapper remains available and keeps component
identity semantics. Passing a foreign component does not rebind it by name.
QName wrappers explicitly request receiver resolution. Neither representation
merges foreign definitions into the receiving schema.

For example, an application can store a typed invoice amount independently of
its schema and reconstruct both before emitting it:

```qore
%modern
%requires WSDL
%requires xml
XsdSchema invoice("<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
    "<xs:simpleType name='TaxableAmount'><xs:restriction base='xs:decimal'>"
    "<xs:minInclusive value='0'/></xs:restriction></xs:simpleType>"
    "<xs:element name='amount' type='xs:decimal'/></xs:schema>");
auto parsed = parse_xml("<amount xmlns:i='http://www.w3.org/2001/XMLSchema-instance'"
    " i:type='TaxableAmount'>12345678901234567890.25</amount>").amount;
auto amount = invoice.getElement("", "amount").deserializeValue(
    invoice.getTypeMap(), NOTHING, parsed, True, True);
auto saved_amount = Serializable::serialize(amount);
auto saved_schema = Serializable::serialize(invoice);
XsdSchema receiver = Serializable::deserialize(saved_schema);
XsdXmlValue output = receiver.serializeXmlValue("", "amount",
    Serializable::deserialize(saved_amount));
```

Complete schema and message serializers scope the receiving type map
automatically. Low-level `XsdElement::serializeValue()` and `serializeOccurrence()`
accept an optional final type map. Without one they inherit the containing
serializer's map; declared identity and canonical builtins need no lookup.
Low-level `deserializeValue()` accepts an optional final capture choice;
`NOTHING` inherits the containing operation's choice. Internal scalar and union
validation probes retain their existing conversion shapes. Attributes and the
text of complex simple content cannot select an instance type; type wrappers
in those positions reject. Only elements and WSDL type parts interpret wrappers.

Thread-local scopes restore the capture flag and receiving map on normal,
exception and cancellation exits. They borrow copy-on-write maps and do not
change shared schema state. Nested element calls allocate a scope only for an
explicit override. Type lookup uses an expanded-name hash key; subsequent
derivation uses the bounded resolved-graph algorithm described in
[type substitution](wsdl-type-substitution.md).

A selected single root is a whole native argument, including for RPC type
parts. When SOAP headers are present, its body part-name key remains around the
wrapper so header message fields cannot be merged into it. Header values retain
their usual message/part keys, and their selected element types are captured too.
Applications keep the `WebService` alive while using its operation handles.

`xml_values` and `preserve_types` select different representations and cannot be
enabled together. Client validation rejects the conflicting options before I/O;
handler registration rejects them before adding a method. `XsdXmlValue` remains
the representation for the complete XML infoset, lexical spelling and ordering.
Native type capture alone does not retain those properties. Ordinary provider
factories continue to describe the native projection. Applications accepting
captured values use `XsdSchema::getNativeDataProviderType(uri, element_name)` or
`WSMessage::getDataProviderType(True)`. Message providers retain WSDL part-name
keys around each value; operation decoding can still unwrap a single part.

These providers accept the declared native form and selected-type wrappers.
Their `union_types` metadata describes the declared native fields and the
two-field wrapper separately. Abstract declarations expose only the wrapper
alternative. `getSelectedValueType(qname_or_component)` resolves a permitted
selection and exposes its native fields, including derived fields and wrappers
in nested elements. An anonymous declaration has no type QName; its metadata
uses the resolved component as the wrapper example. Such a component keeps the
existing identity contract, while ordinary values use the declaration implicitly.
A different anonymous component cannot supply an `xsi:type` annotation.
Selection lookup raises `SOAP-SERIALIZATION-ERROR`;
`acceptsValue()` reports invalid selection or XML instance content as
`RUNTIME-TYPE-ERROR`. Missing mandatory fields and finite provider choices retain
their usual `MISSING-VALUE-ERROR` and `FIELD-VALUE-ERROR` categories. Cancellation
and custom conversion errors propagate unchanged.

For the invoice above, a stored amount can pass through a provider before
serialization:

```qore
AbstractDataProviderType amount_type = receiver.getNativeDataProviderType("", "amount");
amount_type = Serializable::deserialize(amount_type.serialize());
auto checked = amount_type.acceptsValue(Serializable::deserialize(saved_amount));
XsdXmlValue validated_output = receiver.serializeXmlValue("", "amount", checked);
```

Provider construction indexes definitions before traversing nested elements,
so recursive types share one native definition. It completes named alternatives
and soft variants before returning. Restoring serialized providers rebuilds
the component index in one pass using restored object identities; validation
performs hash lookup. Unused canonical builtin scalar adapters can be created
independently on demand without extending the shared graph. No XML encoding and
decoding round-trip is used to convert provider values. Instance checks use the
receiving schema's existing serialization validators with a private namespace
scope.

Field choices compare the unwrapped scalar or each unwrapped occurrence with
the existing numeric, QName, calendar, binary, list and union comparators.
QName choices retain the declaration's lexical bindings. Editing choices on a
copied field does not change its source field. Provider examples delegate to
the native branch; an abstract type selects a permitted concrete definition or
raises `XSD-SAMPLE-ERROR` if none exists. The ordinary native provider's example
policy still applies to the selected value. Applications customizing mutable
provider field metadata must finish those edits before concurrent validation;
validation itself does not mutate the completed graph.

This contract builds on XSD 1.0 [Element Locally Valid](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-elt)
and [QName value identity](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#QName).
The wrapper and explicit capture choice are Qore API decisions, not wire syntax
prescribed by XML Schema. Tests are `wsdl-native-type-values.qtest` and the
independent `test_native_type_values.py` matrix. Provider coverage is in
`wsdl-native-type-providers.qtest` and `test_native_type_providers.py`, which
also validates output with independent schema implementations.
