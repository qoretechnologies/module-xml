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

## MTOM/XOP reconstruction

When the root is an XOP entity, `WSDLLib::substXopInclude()` rebuilds the original infoset before SOAP processing,
as XOP 1.0 section 3.2 and SOAP 1.2 MTOM section 3.3 describe:

- `xop:Include` is recognized by its expanded name. The namespace may be declared on it, on an ancestor, or as
  the default namespace.
- It must be the only child of its element, so text or white space beside it is rejected. The SOAP parser keeps
  no comments. The element keeps its attributes, and its value becomes the referenced part's bytes.
- Its `href` must be a `cid:` URI (XOP 1.0 section 2.2). The scheme is case-insensitive, and the identifier is
  percent-decoded (RFC 2392), as CXF's `cid:...%40cxf.apache.org` references require. The only unqualified
  attribute is `href`. Other attributes and child elements must be namespace-qualified outside the XOP
  namespace, and are ignored (section 2.1).
- The part must exist among the non-root parts, and each part may be referenced once (SOAP 1.2 MTOM section
  4.3.1). Parts that no `xop:Include` references are not part of the SOAP message.

Errors are `SOAP-MESSAGE-ERROR` exceptions. A package's `start-info` must name the same media type as the XOP
root's `type` parameter (XOP 1.0 section 4.1); packages without `start-info` are accepted. Before P8-05 every
MTOM message failed with `RUNTIME-TYPE-ERROR`, because the previous recognizer read regex captures through `$1`.

`WSDLLib::packageMtom()` writes the root as `application/xop+xml` with the XML serialization's content type
in `type`, and repeats it in the package's `start-info`: `text/xml` for SOAP 1.1, and `application/soap+xml`
with any `action` parameter for SOAP 1.2 (SOAP 1.2 MTOM section 3.2). The pinned sources are in
`test/wsdl-interop/normative/`, and `test_attachment_sources.py` checks their digests.

