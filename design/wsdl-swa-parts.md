# SOAP MIME attachment part values

Copyright (C) 2026 Qore Technologies, s.r.o.

SOAP multipart bindings select attachment parts independently of the SOAP body
and header projections. The binding's content map uses message argument keys;
wire identifiers and native maps use public WSDL part names. Body `parts` omission
still selects all abstract message parts, including parts also bound as attachments.

A type-based `mime:content` part carries raw media bytes. Its abstract XSD type does
not encode or validate those bytes, following WS-I Attachments Profile R2943.
Strings use the selected charset, or the call's encoding. An explicit charset on
input returns a string; other media values remain binary. In particular, an
`xs:base64Binary` attachment is not base64 text unless MIME transfer encoding calls
for it. An element-based part instead carries a complete schema-validated XML
document with the declared global root. Its media type must identify XML. The
standalone codec is shared with HTTP `mime:mimeXml`, including namespace allocation,
retained XML values, charset selection and the UTF-16 BOM.

One concrete media declaration, including equivalent duplicates, supplies the
default. Distinct alternatives and wildcard declarations require the existing
`^attributes^.^content-type^` selector. The input result preserves that selector
with `^value^` whenever the declaration has no single concrete default. A failed
media/schema check cannot select another representation.

```qore
hash<auto> request = {
    "order": order,
    "document": {"^value^": pdf_bytes,
        "^attributes^": {"^content-type^": "application/pdf"}}
};
hash<auto> wire = operation.serializeRequest(request);
```

Ordinary part-name maps combine body and attachment values when their identities
do not overlap. A part selected in more than one location can use distinct values:

```qore
hash<auto> request = {
    "^body^": {"invoice": original_invoice},
    "^headers^": {},
    "^attachments^": {"invoice": signed_invoice}
};
```

All three maps are required in this explicit form. Unknown attachment values
reject. Decoding returns this form when merging attachment values would overwrite
body or header parts, or header message names require namespace qualification.
Ordinary body/header merge rules remain in force otherwise.
A declared attachment is required even when its body is empty; an absent part and
an empty binary value are different inputs.

Outgoing identifiers contain the UTF-8 percent-encoded WSDL part name, `=`, a
random 128-bit value, and a domain. The SOAP root gets its own identifier. Incoming
parts are matched by the encoded public name, independently of MIME order and
internal element aliases. Missing parts, duplicate entities selecting one part,
malformed identifiers and incompatible media types reject. Extra unbound entities
do not replace declared values. SOAP root charset and SOAP 1.2 action parameters
belong to the root's Content-Type; the outer multipart header carries the boundary,
root media type and start identifier.

The transport reader preserves normalized entities. `parseSOAPMessage()` keeps
them under the reserved `^mime-parts^` key alongside the parsed envelope. SOAP
binding decoding excludes this metadata from XML namespace processing before
combining the independently decoded values.

`SoapXmlMessageInfo.attachments` carries the same part identities. Element parts
are `XsdXmlValue` objects after schema validation; type parts retain media data.
The optional final `mime_parts` argument to `deserializeXmlRequest()` and
`deserializeXmlResponse()` accepts entities from the transport reader. SoapClient
and SoapHandler supply them for `xml_values` calls. Retained body/header/attachment
maps can be forwarded through the explicit representation above. Abstract-message
providers and sample helpers still describe the abstract XSD message, independently
of a concrete MIME binding's raw type-part representation.

State is local to each call. Schema graphs and binding descriptions are unchanged
by selection, encoding, decoding or failure. Saved services reconstruct the same
binding map, and detached operations retain their message and schema dependencies.

`WsdlSoapMimeDataType` supplies concrete binding metadata to SoapDataProvider.
Body and header fields use their schema descriptions; attachment fields describe
raw media or schema XML and the existing media-selector wrapper. Overlaps use
explicit map metadata. The provider validates the complete value with the selected
operation's serializer, without I/O, and returns the original native value. This
adds a linear serialization pass during provider validation and prevents coercion
of raw bytes by the abstract XSD type. It also keeps required parts, schema checks,
media selection and header placement identical to transport serialization.

The provider selects the configured SoapClient binding, or the default service
port used by a lazy client. Saved, soft and optional copies retain that selection
and complete validation. Example generation uses schema values for body/header/XML
parts and raw bytes for type attachments, selecting a concrete declared media
alternative when available. Wildcard-only media examples fail explicitly until a
concrete media example is supplied. Abstract `WSMessage` providers remain separate.
