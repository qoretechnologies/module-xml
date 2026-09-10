# Validation of generated WSDL instances

Copyright (C) 2026 Qore Technologies, s.r.o.

Default `WSMessageHelper::getMessage()` calls check their generated native
candidate against the requested element or type-part instance requirements
before returning it. Ordinary schema rejection raises `XSD-SAMPLE-ERROR` and
includes the declaration and the underlying reason. Unexpected callback
failures and cancellation keep their own exception categories.

Datatype-valid text is not always a valid XML instance. For example, an ENTITY
name can satisfy NCName syntax while lacking the unparsed declaration required
by [XSD 1.0](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#ENTITY).
SOAP cannot contain that declaration. Sample checking uses the same selected
union/list instance rules as [normal document conversion](wsdl-entity-values.md).
It also checks attributes, defaults, simple content and generated occurrence
counts. Every successful default call passes the existing instance conversion.

## Generation and validation

The existing datatype/facet generators assemble a candidate. Nested element
construction preserves public `getMessage()` overrides, followed by one
validation traversal of the root element. A thread-local context identifies
only the intended child call and is consumed when that call enters the base
method. Reentrant calls receive their own check; scoped restoration also runs
when an override throws. This avoids validating every subtree again while
retaining subclass customization. Each part of a multipart message is checked before the result
can return. Type-based parts use the same document-value helper as normal WSDL
conversion. QName output allocation uses a private copy of the type's owned
namespace registry, without changing the service's output prefixes.

This check is not a proof that a schema has no values. Bounded generation may
fail to find a value even when a caller can supply one. In particular, the current
first-member union generator may choose ENTITY for `ENTITY | int`; `17` is a valid
supplied value even when the generated candidate fails. Datatype-only
`XsdSimpleType::getSampleValue()` retains its datatype contract and does not require
an instance declaration. Generation errors do not mark those datatypes unsupported.

The `max_items` option still bounds generated repetitions. If it is smaller than
a required occurrence count, generation raises an error rather than returning a
truncated instance. A sufficient `max_items` permits the existing valid sample.

## Explanatory options and retained XML

The existing `choices: True` option creates descriptions containing every
alternative in `^choices...^` fields. These are explanatory data, not complete
instances, and preserve their existing shape. `comments: True` alone does not
disable instance checking. Normal comments remain supported.

`getXmlMessage()` first obtains the native candidate, so it can now raise
`XSD-SAMPLE-ERROR` before creating XML. Its subsequent XML checks remain required,
including when explanatory choices are requested; an invalid XML candidate still
raises `SOAP-SERIALIZATION-ERROR`. No option returns unchecked retained XML.

## Example

For a catalog WSDL with a `body` part of type `ENTITY | int`, a generated ENTITY
candidate produces a precise error, while an explicit numeric reference remains
usable:

```qore
WebService catalog(ReadOnlyFile::readTextFile("catalog.wsdl"), {"async_only": True});
WSMessage request = catalog.getBindingOperation("Soap", "lookup").input;
WSMessageHelper examples(catalog);
try {
    auto example = examples.getMessage(request);
    printf("Generated request: %Y\n", example);
} catch (hash<ExceptionInfo> ex) {
    if (ex.err != "XSD-SAMPLE-ERROR") {
        rethrow;
    }
    printf("Supply a request example: %s\n", ex.desc);
}
@assert(request.getDataProviderType().acceptsValue({"body": 17}).body == 17);
```

`test/wsdl-sample-instances.qtest` covers every native entry point, original and
reconstructed services, element/type and multipart messages, attributes, simple
content, occurrence limits, comments/choices, QName identity, detached lifetime,
callback counts, nested generation, program interruption and concurrent use.
The independent ENTITY and QName context matrices cover both actual SOAP bindings
and both directions with exact preserved-value and document checks.

## Complete groups and bounded construction

Normal named-element examples now obtain a complete child schedule from the
[particle sampler](wsdl-particles.md#bounded-structural-examples). The helper
canonicalizes its per-name counts using the same ordering and attribution as
native serialization before generating declaration-specific values. A repeated
quantity/note group therefore produces complete pairs, and fields sharing a name
retain each occurrence. An XSD list-valued child remains one value inside its
outer occurrence list. Namespace aliases account for every active alternative,
including an alternative not selected for the example.

`max_items` is a positive integer limiting nonempty repetitions of each particle.
Nested groups can produce more values of a field than that per-particle limit.
`max_elements` is a positive integer, defaulting to 10000, limiting generated
elements in each message part, including its root and nested children. Construction
reserves counts before allocating or invoking child hooks. Before returning an
instance, it also counts the converted XML output, including whole values supplied
by overrides and embedded XML fragments. This check ignores attributes, comments
and scalar text. Its iterative traversal reserves pending nodes against the same
limit; it does not repeat value conversion or callbacks. Required structure is
never truncated. The existing bounded-candidate contract still applies: the helper
may need a larger budget or an explicit supplied example even when a different
candidate would fit. These generation limits do not restrict accepted XML.

Every attributed child is generated through the public `getMessage()` override
with a call-local one-occurrence context. Shared declarations keep their original
limits. Repeated complex values are constructed separately so every nested element
is accounted for. Type-based complex message parts use the same value builder,
including child particles and attributes, while retaining the existing single-part
and multipart return shapes. Comments describe complete field occurrence ranges;
repeated fields carry occurrence indices. Explanatory `choices: True` retains its
separate descriptive representation.

Each root call owns its budget and active type set. Reentrant public calls receive
independent root validation and budgets, including calls made by an override while
an outer example has reserved all its children. Scoped restoration runs after
callback failures and interruption. A recursive type can terminate with an empty
particle when that content is permitted; a cycle without such a candidate raises
`XSD-SAMPLE-ERROR`. No recursion or budget failure returns partial output.

Group finalization resolves and indexes shared declarations without changing their
`minOccurs` or `maxOccurs`. Provider fields, encoding, decoding and examples share
an active declaration index obtained from the authoritative particle graph. It
preserves schema order, omits zero-occurrence declarations and visits shared group
definitions once. Full particle matching still selects each actual declaration
position for conversion.

### Shipment example

```qore
WebService shipping("<w:definitions xmlns:w='http://schemas.xmlsoap.org/wsdl/'"
    " xmlns:xs='http://www.w3.org/2001/XMLSchema' xmlns:t='urn:shipping' targetNamespace='urn:shipping'>"
    "<w:types><xs:schema targetNamespace='urn:shipping'><xs:complexType name='Batch'>"
    "<xs:sequence minOccurs='2' maxOccurs='3'><xs:element name='quantity' type='xs:int'/>"
    "<xs:element name='note' type='xs:string'/></xs:sequence></xs:complexType>"
    "<xs:element name='batch' type='t:Batch'/></xs:schema></w:types>"
    "<w:message name='Request'><w:part name='body' element='t:batch'/></w:message></w:definitions>",
    {"async_only": True});
WSMessageHelper examples(shipping, {"max_elements": 5});
hash<auto> sample = examples.getMessage(shipping.messages.Request);
@assert(sample.batch.quantity == (123, 123));
@assert(sample.batch.note == ("abc", "abc"));
XsdXmlValue retained = examples.getXmlMessage(shipping.messages.Request).body;
@assert(retained.getLocalName() == "batch");
```

The five-element budget contains the batch root and two complete pairs.
`wsdl-sample-instances.qtest` covers these values, nested lists, reused groups,
typed parts, comments, recursion, budgets, overrides, reentrancy, cancellation
and concurrent calls. `test_sample_particles.py` exercises both actual SOAP
bindings and both directions, including reconstructed schemas. It compares child
order and exact integer values, and independently validates native and retained
outputs with libxml2 and Xerces. Budget rejections are accounted separately.
