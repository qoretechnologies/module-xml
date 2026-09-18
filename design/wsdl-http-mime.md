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

MIME XML uses the selected part's document codec, following the schema-root mapping
in [WSDL 1.1 section 5.6](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_mime:mimeXml). Element-based parts emit the
actual global element QName and schema-qualified children; type-based parts use
an unqualified WSDL part name. The complete document carries namespace bindings
for its content and QName values. Serialization uses a per-call namespace copy,
so one request cannot change the shared service namespace registry. XML encoding
and generator flags apply to the final document.

Decoding resolves element names to expanded identities before matching the one
selected part, rejecting missing, extra, repeated and wrongly qualified roots.
The selected declaration then validates content, nil and native type wrappers.
An `XsdXmlValue` supplied as an element part is validated and emitted with its
retained lexical content and namespace context, including processing instructions
inside the element. The element-fragment generator rejects DOCTYPEs. Standalone
MIME output also rejects a retained value with inherited XML attributes: there is
no enclosing element on which to preserve that context, and adding the attributes
to the root could change its schema validity. Explicit `deserializeXmlRequest`
and `deserializeXmlResponse` remain SOAP-only APIs.

For example, `{"order": {"count": 71, "category": new XsdQNameValue("urn:catalog",
"p:Product")}}` produces a complete qualified order document when the `order`
part references a global element. A peer may use a different prefix for that
element and the category value; decoding compares their namespace identities.
`test/wsdl-http-xml-values.qtest` covers this behavior in source, saved-service,
detached-operation and real HTTP paths, including negative inputs and nil values.

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

## URL-replacement routing

The binding compiles replacement patterns using the selected abstract message.
Only an exact, case-sensitive `(partName)` for a declared message part is a
pattern. Other parentheses remain literal URI characters, including unmatched or
nested parentheses. For example, `/version(v1)/items/((id))` with part `id` and
value `A/B` produces `/version(v1)/items/(A%2FB)`. Pattern discovery completes
before substitution; a value containing `(id)` never triggers another replacement.
Every declared part must have a pattern. A message with no parts can use a static
URI containing literal parentheses.

`BindingMessageDescription::setUrlReplacement()` accepts an optional `WSMessage`
for these rules. The one-argument form retains its legacy interpretation of every
parenthesized token as a part name. Both forms build a local token map and assign
it only after validation succeeds, so repeated calls replace the prior map and
failed calls preserve it. Descriptors shared by operation handles must be treated
as immutable while in use. The compiler scans UTF-8 byte offsets and emits slices
at ASCII delimiter boundaries, preserving Unicode part names and literal text.
Saved services rebuild from the retained source; detached operations retain the
compiled map.

`HttpBinding::matchesRequestPath()` checks the complete operation-relative
replacement template without applying schema types. Prefix literals, internal
separators and suffixes must match; repeated references to a part must decode to
the same value. A trailing unmatched resource path fails. Token traversal is
linear; each parameter uses the immediately following literal as its delimiter.
Message type conversion follows successful matching.

SoapHandler stores replacement routes separately from static HTTP paths, under
the HTTP verb and template. It tries exact static routes first, then complete
replacement templates. Duplicate template registration fails; a request matching
multiple replacement routes fails instead of selecting an arbitrary callback.
Template matching and decoding use HttpServer's raw request path, with the handler
mount prefix removed, so encoded slashes and percent signs are decoded once.
For example, `/items/A%2FB%252F/view` supplies `A/B%2F` to the callback.

HTTP route registration holds the write lock. `removeService(unique_id)` removes
static and replacement routes belonging to that identifier. In-flight requests
retain their selected method, while subsequent lookups observe the removal.
The replacement regression covers default and mounted handlers, source and saved
services, repeated values, suffix validation, overlapping templates and removal.
