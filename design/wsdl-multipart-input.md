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

## SOAP with Attachments references

When the root is not an XOP entity, `WSDLLib::parseSOAPMessage()` resolves the references the SOAP with
Attachments Note (section 3) defines before any SOAP processing:

- A reference is the value of an `href` attribute, which is a SOAP 1.1 section 5.4.1 accessor reference, in the
  Header or the Body. A child element named `href` is ordinary content.
- A same-document reference (`#id`) is excluded (SwA Note section 3) and keeps its SOAP encoding meaning. SOAP
  encoding resolves it later, so one encoded message can combine multi-reference values and attachments. Apache
  Axis 1.x sends messages like this.
- Any other reference is made absolute against its base URI, in the Note's order: `xml:base` on the element or an
  ancestor, then the `Content-Location` of the root part, then `thismessage:/` (RFC 2557). The retrieval URI is
  never a base.
- The absolute reference is compared with each non-root part's labels. The label is `cid:` plus the Content-ID,
  which also matches a percent-encoded `cid:` URI and any case of the scheme (RFC 2392). An absolute
  `Content-Location` is also a label, and a relative one is resolved against `thismessage:/`.
- A matching reference element's value becomes the part's content, and the element keeps no attributes. A part can
  be referenced more than once. Replaced content is not searched again.
- A reference that matches no part is left unchanged for normal resolution. A `cid:` reference is the exception:
  it can only name a part of this message, so an unmatched one raises `SOAP-MESSAGE-ERROR`. So do a malformed
  percent-encoding and a `Content-Location` label that several parts share.

WS-I Attachments Profile 1.0 constrains the same packages (R2931, R2932). Its `swaRef` type (R2928) is a typed
reference that the schema drives, and is separate from this `href` resolution; see below. The SwA Note and the profile cannot
be redistributed. `normative/sources.json` pins the Note by digest, with the section 3 phrases above, and pins the
profile as the reproducible requirement extract `normative/wsiap10-requirements.json`.

## swaRef attachment references

WS-I Attachments Profile 1.0, section 4.4, types a reference to an attachment as `ref:swaRef`, a restriction of
`xs:anyURI` in the namespace `http://ws-i.org/profiles/basic/1.1/xsd`. R2928 requires the URI of such a value in
an envelope to resolve to a MIME part of the same message. The native value is therefore the part's content, and
`XsdSimpleType::isAttachmentReference()` identifies the type: `swaRef` or a restriction of it, but not a list or
union, whose items are URIs.

- **Output.** `serializeMessageWithDescription()` sets a `SwaRefPackageWriter` for each message. At the start of
  `XsdDocumentValueHelper::serializeValue()`, a `swaRef` value becomes a new part, and its `cid:` URI is the
  value that the `anyURI` checks, fixed values and identity constraints see. This covers elements, attributes,
  simple content and typed message parts. Binary data becomes `application/octet-stream`, and a string becomes
  `text/plain` in the message encoding. The Content-IDs contain no `=`, so they never name a MIME-bound WSDL
  part (R2933). Only the parts that the final envelope references are packaged, as discarded trial serializations
  can create others. A message with parts becomes a SOAP with Attachments package with the SOAP media type as
  its root type, and it can be an MTOM package at the same time.
- **Input.** `parseSOAPMessage()` keeps the package's labels and base URI under `^mime-references^`, next to
  `^mime-parts^`. `deserializeMessageImpl()` sets them as the `SwaPackageReferences` of the message. Once a value
  has been decoded and checked as a URI, it is resolved like an `href`: `cid:` by Content-ID, anything else by
  Content-Location against the root's base URI. A text part (with a `charset`) decodes as a string, and any other
  part as binary. Attributes resolve after their fixed-value check. A URI that identifies no part, or more than
  one, raises `SOAP-DESERIALIZATION-ERROR`, and so does a `swaRef` value in a message that is not a package.
- **Scope.** R2928 covers the envelope. XML attachment entities bound with `mime:content` suspend both hooks,
  so their `swaRef` values stay URIs. Retained XML validation (`RetainedXmlValidationNamespaces`) does too, and
  retained XML values keep the URIs.
- **Provider types.** A `swaRef` field accepts binary or string data. List items and union members use
  `getLexicalDataProviderType()`.

`test/soap-swaref.qtest` covers the WS-I `SendClaim` example shape in SOAP 1.1 and 1.2. The live SwA peer
exchanges CXF's `echoDataRef` operation with Apache CXF 4.1.3 in both directions.

`WSDLLib::packageMtom()` writes the root as `application/xop+xml` with the XML serialization's content type
in `type`, and repeats it in the package's `start-info`: `text/xml` for SOAP 1.1, and `application/soap+xml`
with any `action` parameter for SOAP 1.2 (SOAP 1.2 MTOM section 3.2). MTOM output from WSDL serialization is
described in [soap-mtom-output.md](soap-mtom-output.md). The pinned sources are in
`test/wsdl-interop/normative/`, and `test_attachment_sources.py` checks their digests.

