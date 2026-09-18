# HTTP MIME XML bindings

Copyright (C) 2026 Qore Technologies, s.r.o.

`Binding` resolves each input/output `mime:mimeXml/@part` against the abstract
message selected for that direction. Explicit selections must name an existing
part. An omitted selection uses the sole part of a single-part message; it is
ambiguous for a multiple-part message and raises `WSDL-ERROR` before transport.
The resulting `MimeXmlMessageDescription` is retained by saved services and
detached saved operations.

For example, a message containing `quantity` and `confirmation` parts can bind
the request with `<mime:mimeXml part="quantity"/>` and the response with
`<mime:mimeXml part="confirmation"/>`. Callers supply `{"quantity": 71}` and
receive a part map such as `{"confirmation": "accepted"}`. Wire names and typed
conversion come from the selected message part through the existing XML codec.

`SoapHandler` applies a response SOAP-version override only when the selected
operational binding is a `SoapBinding`. HTTP binding responses do not require
the service to declare a SOAP version. `SoapClient` likewise restricts SOAP fault
recovery from HTTP error responses to SOAP bindings. An HTTP binding retains
`HTTP-CLIENT-RECEIVE-ERROR` even when its error body resembles a SOAP fault;
that body must not become a successful MIME value.

`test/wsdl-mimexml-parts.qtest` covers independent selections, malformed names,
omitted-part behavior, saved metadata, exact wire values and local HTTP success
and failure. Existing SOAP version/fault tests cover the SOAP-specific path.

## URL-encoded requests

`http:urlEncoded` with POST serializes all message parts to an
`application/x-www-form-urlencoded` body. The media type has no charset parameter;
form text is encoded as UTF-8 bytes before percent encoding. GET places the same
part names and lexical values in the query. SoapHandler chooses body decoding for
POST and path decoding for GET, then applies the selected message's type codecs.
This implements [WSDL 1.1 section 4.6](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_http:urlEncoded).

An HTTP-bound SoapClient enables HTTPClient's pre-encoded URL mode because the
binding has already percent-encoded its path substitutions and query values.
This preserves reserved delimiters and Unicode without a second encoding pass.
A GET argument `{"label": "A & č+"}` therefore contains
`label=A%20%26%20%C4%8D%2B` in the request target; the corresponding POST sends it
in the body. The same behavior applies after saved-service reconstruction.
