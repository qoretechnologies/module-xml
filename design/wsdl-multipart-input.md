# SOAP multipart input

Copyright (C) 2026 Qore Technologies, s.r.o.

`WSDLLib::parseMultiPartSOAPMessage()` separates transport framing from SOAP value
conversion. Explicit HTTP `mime:content` selection bypasses this interpretation,
so an uploaded MIME document remains one opaque value.

The original transport Content-Type is parsed by `WsdlMediaType`, preserving
quoted parameters and comparing parameter names and media type/subtype without
case sensitivity. The SOAP transport accepts `multipart/related`. Its required
`type` parameter identifies the root media type; `start` selects a Content-ID,
or the first wire part is the root when `start` is absent. Content-ID matching is
case sensitive. Legacy callers supplying only Qore's parsed multipart metadata
can still provide their boundary and start fields directly.

`WsdlMultipartHelper` delegates MIME framing to
`Mime::MultiPartMessage::parseBody(boundary, body, False)`. It delegates transfer
decoding to `mime_decode_transfer_data()`, keeping the resulting entity bodies
binary. Charset decoding happens afterward, in the selected content codec. It
checks boundary syntax, singleton header value types, Content-ID brackets and
uniqueness, media parameters, root presence and agreement with the outer type.
All validation state is local to the call; failed messages publish no partial
result. Shared MIME framing errors become `SOAP-MESSAGE-ERROR` and cancellation
exceptions propagate.

The normalized transport result contains:

- `body`: root entity bytes;
- `content-type`: the root Content-Type, including parameters;
- `header`: transport header metadata combined with root headers;
- `parts`: non-root entities keyed by unbracketed Content-ID, each with `hdr` and
  binary `body`;
- `unidentified_parts`: non-root entities without Content-ID;
- `is_mtom`: whether the selected root is an XOP entity.

Absent part Content-Type defaults to `text/plain; charset=us-ascii`. A reference
cannot select an unidentified part. Selecting a root never depends on WSDL part
order, and repeated identifiers across root and non-root parts reject.

`WSDLLib::getXmlMessageText()` converts the selected root to UTF-8 using the common
resource decoder's BOM, transport-charset and XML-declaration rules.
`parseSOAPMessage()`, SoapClient's retained XML response path and SoapHandler's
routing/retained XML path share it. Root XML is decoded separately from attachment
bytes; no HTTP-client default charset is applied to attachment bodies.

For a normalized transport message `message`, a retained XML consumer uses:

```qore
hash<SoapXmlMessageInfo> request = operation.deserializeXmlRequest(
    WSDLLib::getXmlMessageText(message), "InvoiceSoap");
```

This interface describes MIME transport normalization. WSDL attachment-part
binding and SOAP/XOP reference interpretation remain separate consumers.
