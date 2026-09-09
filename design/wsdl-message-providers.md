# WSDL message provider validation

Copyright (C) 2026 Qore Technologies, s.r.o.

`WSMessage::getDataProviderType()` returns `XsdMessageDataType`, a
`HashDataType` subclass. Fields keep their WSDL part names, native types,
defaults and datatype choices. After normal field conversion, each supplied
part is checked by the same schema conversion used to emit the message.
A schema serialization failure becomes `RUNTIME-TYPE-ERROR` with the part
name and original description. Exceptions from schema callbacks retain
their categories, including cancellation and program interruption.

This closes the gap where a provider accepted an ENTITY name that the
corresponding SOAP message could not contain. The selected union member's
document requirement is checked after datatype selection; an unavailable
ENTITY declaration does not permit retrying a string alternative.
[XSD 1.0 ENTITY](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#ENTITY)
and [SOAP's document requirements](https://www.w3.org/TR/soap12-part1/#soapenv)
are explained in [the ENTITY design](wsdl-entity-values.md).
Detached simple-type providers continue to describe datatype values.

## Copies, projections and ownership

Optional and mandatory copies preserve the message context. Soft copies
soften fields and preserve their document checks. Deep optional copies can
omit top-level parts. `copyWithFields()` projections validate the original
parts whose fields remain in the projection. Additional fields retain the
normal `HashDataType` behavior. A projection is a partial record contract;
a complete SOAP message must still satisfy its declared required parts.

Enclosing list and field providers must call the message validator even
when a native hash already has a compatible Qore container type. The
message type therefore advertises no unconditional native assignment path.
The returned value remains the converted native record, including the
same caller-owned immutable QName and retained scalar objects.

The provider retains resolved part components and its namespace registry
strongly. Each validation call copies the registry and scopes QName output
allocation to that copy. Releasing the source service does not invalidate
the provider. Schema components are shared with the source service until
Serializable reconstruction; finish schema/custom-component mutations
before sharing providers between threads. Validation of an unchanged
provider uses call-local state and existing scoped datatype captures.

## Reconstruction

Serializable preserves the resolved component graph, including shared
part types and compiled QName defaults. It does not need to retrieve the
original WSDL or replay an import callback. Namespace/part metadata is
checked when restoring the message provider.

Groups and complex types serialize their private particle-emptiability
metadata as ordinary containers. Reconstruction explicitly restores the
private recursive hashdecl, with shape and flag checks. This preserves
both construction metadata and cached resolved results, without requiring
the global serializer to look up a module-private list element type.
The hook reads live class members: its input contains serialized references
and must not itself be used as the live component graph.

## Example

For a catalog contract whose `lookup` request has a `body` part with type
`ENTITY | int`, the numeric alternative can be validated before queuing:

```qore
WebService catalog(ReadOnlyFile::readTextFile("catalog.wsdl"), {"async_only": True});
WSMessage message = catalog.getBindingOperation("Soap", "lookup").input;
AbstractDataProviderType request_type = message.getDataProviderType();
hash<auto> request = request_type.acceptsValue({"body": 17});
AbstractDataProviderType restored = Serializable::deserialize(request_type.serialize());
@assert(restored.acceptsValue(request).body == 17);
# restored.acceptsValue({"body": "photo"}) raises RUNTIME-TYPE-ERROR.
```

The complete executable contracts are in
`test/wsdl-message-providers.qtest`. They cover scalar and list selection,
records, attributes, defaults, copies/projections, containers, detached
ownership, component reconstruction, malformed metadata, schema callbacks,
interruption and synchronized concurrent use. The independent ENTITY
matrix checks both actual SOAP bindings and both message directions.
