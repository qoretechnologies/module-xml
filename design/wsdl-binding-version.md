# Binding-specific SOAP versions

Copyright (C) 2026 Qore Technologies, s.r.o.

WSDL binds a port type to a concrete protocol. The expanded name of the binding
extension selects SOAP 1.1, SOAP 1.2 or HTTP; `transport`, `verb`, prefix spelling
and unrelated namespace declarations cannot substitute for this identity.
This implements [WSDL 1.1 section 3.3](https://www.w3.org/TR/wsdl.html#_soap:binding)
and the [SOAP 1.2 binding extension section 3](https://www.w3.org/submissions/2006/SUBM-wsdl11soap12-20060405/).

`Binding` resolves its extension in nested namespace scopes for the WSDL binding
and extension node. Scope destruction restores the enclosing mappings on success
and exception. Exactly one supported extension is required. SOAP requires a
supported transport and rejects an HTTP verb; HTTP requires a verb and rejects a
SOAP transport. The resulting SOAP version is immutable after construction and
is passed to every `SoapBinding` for that binding's operations.

`WSOperation.serializeRequest()`, `serializeFault()` and `serializeResponse()`
without an explicit version use the selected operational binding. Omitting its
name retains the established first-assigned-binding selection. The optional
binding argument to `WSOperation.isSoap12()` uses the same rule. HTTP bindings
report false. `WebService.isSoap12()` reports whether any actual binding is SOAP
1.2, even if it has no operations or service port; declarations alone do not count.

For example, a dual-version shipping service can explicitly serialize a request
for its SOAP 1.1 endpoint:

```qore
WSOperation operation = service.getOperation("ship");
hash<auto> request = operation.serializeRequest(order, NOTHING, NOTHING, NOTHING,
    NOTHING, NOTHING, "ShippingSoap");
```

A `SoapClient` configured with the intended service/port obtains that port's
binding; `SoapHandler.addMethod()` accepts its explicit binding argument. Tests
inspect actual HTTP request and response envelopes and media types on both ports.

Saved `WebService` objects retain their source WSDL and reconstruct version
metadata on load. New standalone `Binding` and `SoapBinding` objects serialize
that metadata. Old standalone SOAP bindings did not contain enough information
to recover their version: implicit queries raise `WSDL-BINDING-ERROR` with reload
instructions. The existing explicit-version `SoapBinding.serializeMessage()`
API remains usable, and the public constructor accepts an optional final version
argument. No version is inferred from a saved document's unrelated declarations.

The explicit `WSOperation.serializeResponse(..., soap12, ...)` override retains
its historical availability check against the document namespace registry.
SoapHandler validates the registered binding before invoking callbacks, so ordinary
request/response decoding uses the selected version. Root names/namespaces and
cross-version ordinary envelopes raise `SOAP-VERSION-MISMATCH`. Native fault
interpretation then follows the received envelope namespace. A SOAP 1.1
`VersionMismatch` response remains interpretable by a SOAP 1.2 client, as required
for version transition; other mismatched responses reject. The explicit response
serialization override does not change the binding's accepted input version.

See [SOAP envelope processing](soap-envelope-processing.md) for shared structure,
document checks and protocol-fault generation.

Regression coverage is in `test/wsdl-binding-version.qtest`, the existing large
multi-binding golden messages in `test/soap.qtest`, and the independent
`test_simple_content_independent_bindings_and_facets` coverage test. No schema
value conversion or provider representation changes are required.
