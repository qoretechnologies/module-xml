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
