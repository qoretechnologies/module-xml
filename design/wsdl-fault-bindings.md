# Concrete SOAP fault descriptions

Copyright (C) 2026 Qore Technologies, s.r.o.

A `SoapBinding` retains a fault-name map of `BindingMessageBodyDescription`
objects, separate from its ordinary output description. `getFaultBindings()`
returns that metadata. Construction resolves each fault against the selected
abstract operation, requires exactly one message part, exactly one fault
extension in the binding's SOAP version, matching abstract/concrete fault names
and a valid literal/encoded use. One-way and notification abstract operations
cannot declare faults. Descriptions with part selections reject, because fault
detail always uses the fault message's sole part.

`WSOperation::serializeFault()` selects the concrete description by fault name.
An abstract fault absent from that binding rejects instead of using the ordinary
output body. Fault detail uses document-style serialization even when requests
and successful responses use RPC. The selected fault's use controls value
conversion; normal output part selections, use and MIME attachments do not
control the detail. Normal output header descriptions remain available to the
explicit header argument. A per-call message description combines them without
mutating shared binding state. Fault serialization establishes the same document
identity-check scope as request/response serialization.

For example:

```qore
hash<auto> response = operation.serializeFault("OrderRejected", "Insufficient stock",
    {"orderId": "PO-724", "available": 12});
```

Encoded faults require a type-based part. The implemented codec is SOAP 1.1
encoding (`http://schemas.xmlsoap.org/soap/encoding/`); other explicitly selected
encoding URIs reject. An omitted encodingStyle selects that codec. Its accessor
uses the fault's namespace, independently of the ordinary output namespace.
The encodingStyle attribute is attached to application detail, rather than the
SOAP-defined Detail element. Literal encodingStyle metadata is retained as a
hint and does not enable encoded conversion.

A generic fault has no selected message or declared detail. Pass `NOTHING` for
both the fault name and detail value. It can be produced without an output
message description, including for a one-way operation.

Source-backed saved services reconstruct concrete descriptions from WSDL.
Standalone binding graphs retain the map and validate its shape and entries
when restored. Associating a manual or saved binding with an operation checks
that its fault names and message part kinds match that operation. Saved one-way
and notification operations cannot gain declared faults through metadata edits.
`NOTHING` marks a legacy graph lacking fault metadata; an empty
map means the binding declares no faults. Named serialization from a legacy graph
requires reloading its WSDL. Generic faults without detail remain available when
protocol-version metadata is present.

Ordinary response decoding raises `SOAP-SERVER-FAULT-RESPONSE` with the raw
fault hash. Explicit `WSOperation::deserializeFault(xml, fault, binding,
preserve_types)` selects a declared fault by WSDL name and decodes its single
application detail part. `deserializeXmlFault()` retains a literal element's
lexical values and namespace context after schema validation. This works for
RPC operations because detail is document style. The name must be present in
the selected concrete binding; reason strings and fault codes do not infer a
schema. Imported and detached saved operations use their owned fault messages.

The explicit APIs require a matching SOAP envelope version and one Fault in Body.
The version-specific detail container must occur once and contain the declared
single part. Literal details match expanded element names, including substitution
members. Encoded details match the fault namespace and part, consume the supported
block-local codec attribute, and use the declared type. Retained XML requires a
literal element-based part. Generic faults without application detail continue
through the raw exception API rather than a declared-detail decoder.

Each explicit operation decode owns identity and native-type scopes. An unrelated
header cannot supply an ID to satisfy an IDREF within the fault detail. Native
subtype/element capture follows the same opt-in policy as ordinary messages;
retained values can be passed back to `serializeFault()` for lexical forwarding.
Envelope extraction is shared with headerfault decoding; it preserves Header
order, duplicate-container detection and qualified header checks. Full protocol
code/reason/role processing is separate from explicit application-part decoding.

For example:

```qore
auto rejection = operation.deserializeFault(call_info."response-body", "OrderRejected");
XsdXmlValue detail = operation.deserializeXmlFault(call_info."response-body", "OrderRejected");
hash<auto> forwarded = operation.serializeFault("OrderRejected", "Forwarded partner rejection", detail);
```

The binding rules follow [WSDL 1.1 section 3.6](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_soap:fault).
