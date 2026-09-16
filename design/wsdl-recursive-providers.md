# Ordinary recursive XML providers

Copyright (C) 2026 Qore Technologies, s.r.o.

An ordinary provider constructed from an XSD complex type retains its complete
field graph when a child refers to the same type, directly or through another
complex type. Recursive occurrences validate nested fields and expose completed
metadata after factory construction. Optional, mandatory, soft and serialized
copies preserve the receiving occurrence's requirements.

## Construction and ownership

`XsdOrdinaryProviderContext` registers each complex type by object identity
before building its fields. An edge to an unfinished type receives an
`XsdOrdinaryProviderReference`, which points to its
`XsdOrdinaryProviderDefinition`. An edge to a completed type reuses its provider.
This prevents a recursive occurrence from capturing a copy of an unfinished
field map. The schema owns its source type graph during construction;
definitions own the completed providers, and recursive references retain their
definitions.

The outer factory completes the soft providers for definitions with recursive
references before returning. Qore's shared-graph soft conversion processes each
distinct source provider within a conversion instead of copying every incoming
path. The required Qore fix is `16ae86ca7`; older DataProvider implementations
can perform exponential work on shared schema graphs. The graph-size regression
tests this dependency with an operation count, independently of elapsed time.

The construction context is thread-local and cleared on exit, including failed
construction, failed soft completion and program interruption. Completed
definitions are treated as immutable by the factories and consumers. Validation
does not lazily modify them, so saved providers can be shared by consumers.
The public definition and reference classes support serialization; applications
should obtain them through schema factories rather than construct or mutate
unfinished definitions directly. Deserialization rejects missing definitions,
incomplete value providers and invalid occurrence flags.

## Occurrence semantics

A recursive reference carries an optional occurrence override separately from
its shared target. A mandatory reference rejects `NOTHING` with
`MISSING-VALUE-ERROR`, and rejects `NULL` with `RUNTIME-TYPE-ERROR` even when its
target is optional. Acceptance and return metadata delegate to the corresponding
target maps and apply the occurrence override separately. In particular,
accepting `NULL` as optional input does not imply returning `NULL`.

Validating message, wildcard-content and wildcard-attribute record providers
have no single reflected Qore value type. They therefore expose their explicit
outer optionality directly and reject omitted mandatory input before field
conversion. Their existing document and wildcard checks remain in force.

## Example

A shipment can refer to related shipments using the same record definition.
Nested tracking values remain validated after saving and restoring its provider:

```qore
%modern
%requires WSDL

XsdSchema schema("<xs:schema xmlns:xs='http://www.w3.org/2001/XMLSchema'>"
    "<xs:complexType name='Shipment'><xs:sequence>"
    "<xs:element name='tracking' type='xs:string'/>"
    "<xs:element name='related' type='Shipment' minOccurs='0' maxOccurs='unbounded'/>"
    "</xs:sequence></xs:complexType><xs:element name='shipment' type='Shipment'/>"
    "</xs:schema>", {"async_only":True});
AbstractDataProviderType provider = schema.getElement("", "shipment").getDataProviderType();
AbstractDataProviderType saved = Serializable::deserialize(provider.serialize());
hash<auto> checked = saved.acceptsValue({"tracking":"OUT-100",
    "related":({"tracking":"OUT-101"},)});
@assert(checked.related[0].tracking == "OUT-101");
```

Omitting a related shipment's required `tracking` field raises
`RUNTIME-TYPE-ERROR`. Omitting the optional `related` field is permitted.
Soft copies convert nested fields using the same completed recursive graph.

## Regression coverage

`test/wsdl-recursive-providers.qtest` covers self and mutual recursion, saved
graphs, metadata, soft conversion, malformed serialization, sibling occurrence
independence, message containment, construction and completion recovery, actual
program interruption and concurrent consumers. `test/wsdl-provider-optionality.qtest`
checks validating-record omission through copies and containing fields.
`test/wsdl-provider-graph-size.qtest` checks bounded leaf conversions for shared
ordinary and wildcard record graphs at increasing depths.
