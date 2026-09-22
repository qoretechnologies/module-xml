# SOAP MTOM/XOP output

Copyright (C) 2026 Qore Technologies, s.r.o.

MTOM output sends a SOAP message as an XOP package (XOP 1.0 section 3.1; SOAP 1.2 MTOM sections 3.2 and 4.3.1):
base64Binary content travels as raw octets in its own MIME part, referenced by an `xop:Include` element. Input
reconstruction is described in [wsdl-multipart-input.md](wsdl-multipart-input.md).

## Selection

`WSDL::SoapMtomScope` selects MTOM output for the messages that its thread serializes while the object exists.
It is a thread-local setting, restored when the object is destroyed, even by an exception. Scopes nest, a
`SoapMtomScope(False)` suspends MTOM output within an enclosing scope, and new threads start without it. The
selection covers requests, responses and declared faults of SOAP 1.1 and SOAP 1.2 bindings. It keeps the
serialization signatures unchanged. A message is an XOP package even when nothing is extracted, which tells the
receiver that MTOM is in use.

- `SoapClient` and `SoapClientIo` take `mtom` and `mtom_threshold` constructor options, which `SoapConnection`
  and `SoapIoConnection` also publish, and apply the scope while a request is serialized. Saved `SoapClient`
  objects keep the options, and objects saved before them restore with MTOM disabled.
- `SoapHandler` answers a request that arrived as an XOP package with an XOP response, since its sender accepts
  MTOM. `setMtomThreshold()` sets the threshold, or turns mirroring off with `NOTHING`. Ordinary requests and
  fault responses stay ordinary SOAP messages.

## What is optimized

`XsdElement::serializeTypedValue()` replaces an element's content after its facets, fixed value and identity
constraints are checked. Typed RPC and document parts use the same rule. Content is nominated when:

- its type is `xs:base64Binary`, a restriction of it, or a complex type with such simple content (the form that
  carries an `xmime:contentType` attribute), or `xs:anyType` holding binary data, which is written as
  `xs:base64Binary`;
- it is the element's only child, without comments, and in the canonical base64 form without white space (XOP
  1.0 section 3.1), so a retained non-canonical lexical form stays inline;
- it has at least the threshold's number of octets (`MTOM_THRESHOLD`, 1024, by default; 0 extracts every value,
  including empty ones).

List and union values are never one base64 value and stay inline. SOAP-encoded bodies and headers stay inline
because the encoding rewrites the value graph. SwA attachment entities are not part of the envelope and are
never optimized.

The element keeps its attributes and receives `<xop:Include xmlns:xop="..." href="cid:..."/>`. An
`xmime:contentType` attribute (namespace `XMIME_NS`) names the part's media type. It must be a valid concrete
media type without control characters, or the value stays inline, as XOP 1.0 section 3.1 recommends for
content that cannot be packaged. Otherwise the part is `application/octet-stream`.

## Packaging

The writer collects parts per message under unique `<random>-<n>@qore.org` identifiers. Trial serializations
can nominate content that the final message does not contain. So after the root is written, one `XmlReader`
pass selects the parts that its `xop:Include` elements reference, in document order, each exactly once.

If the root contains an `xop:Include` that the writer did not create, the original infoset held one. XOP cannot
represent such an infoset, and SOAP 1.2 MTOM section 4.3.1 requires sending the message without XOP. The message
is then serialized again as an ordinary SOAP message.

The package reuses the multipart container of SwA attachment parts:

- the root is `application/xop+xml` with the XML charset, and its `type` parameter holds the SOAP media type:
  `text/xml`, or `application/soap+xml` with any `action` parameter;
- the package's `start-info` repeats that type;
- each extracted part is binary, with its `Content-Transfer-Encoding` (SOAP 1.2 MTOM section 4.3.1).

Multipart boundaries are 128-bit random values. Binary parts are not transfer-encoded, so a predictable
boundary could appear inside one and break the framing.

## Independent verification

`test/soap-mtom-output.qtest` covers the rules above. `test/wsdl-interop/test_mtom_xop.py` exchanges both
operations of the unmodified CXF `mtom_xop.wsdl` contract live with Apache CXF 4.1.3, in both directions, with
and without MTOM. Each side checks the other's package form and number of extracted parts across the threshold.
