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
Template matching and decoding use HttpServer's raw request path, trying the full
path and then the path with the handler mount prefix removed. Port-relative
templates resolve through Qore before registration; explicit registration paths
override both matching and decoding. Encoded slashes and percent signs are decoded once.
For example, `/items/A%2FB%252F/view` supplies `A/B%2F` to the callback.

HTTP route registration holds the write lock. `removeService(unique_id)` removes
static and replacement routes belonging to that identifier. In-flight requests
retain their selected method, while subsequent lookups observe the removal.
The replacement regression covers default and mounted handlers, source and saved
services, repeated values, suffix validation, overlapping templates and removal.

## MIME content and media-type constraints

`mime:content` carries one opaque message part. Its optional `type` declaration is
parsed as a complete media type, with WSDL wildcards allowed as either complete
component (`image/*`, `*/xml`, `*/*`). Omission accepts every concrete media type;
an explicitly empty or malformed declaration raises `WSDL-ERROR`. Wire
Content-Type values must be concrete and syntactically complete, even for an
unrestricted declaration. Prefixes such as `text/xml-extra` do not match `text/xml`.

The parser follows HTTP token, optional whitespace, quoted-string and quoted-pair
syntax. Type/subtype and parameter names compare without case. Declared parameters
must be present; additional wire parameters are retained. Charset values compare
without case; opaque parameter values, including boundaries and SOAP actions,
compare exactly. `multipart/related`'s `type` parameter is a media type/subtype;
XOP's `type` can contain a complete media type with its own parameters. Those
values compare by their parsed components and parameter sets, retaining nested
action case. Generic `start-info` and unregistered `type` parameters remain opaque.
Repeated constrained parameters must agree. A work list handles nested type
comparisons without recursive calls or a duplicate-value cross product.

For example, `text/plain;charset="UTF-8";profile=Report` accepts
`TEXT/PLAIN;PROFILE="Report";CHARSET=utf-8`, and rejects `profile=report`.
`application/xop+xml;type="application/soap+xml;action=\"urn:Order\""`
retains the case of `urn:Order` while ignoring case in the nested media-type name.

`BindingContentDescription::addContentType()` validates before changing descriptor
state. Its existing exact-type and family lists remain available; wildcard-major
and parameterized wildcard declarations use `acceptedContentPatterns`. Saved
services rebuild these declarations from their source; detached operations retain
the descriptor. Descriptors are immutable while shared by active operations.

HTTP `Accept` advertises exact types and representable media ranges. HTTP cannot
express WSDL's `*/subtype` constraint, so such an output declaration omits Accept;
the binding still validates the complete constraint when receiving the response.
Wildcard or multiple-type declarations require explicit per-value
`^attributes^.^content-type^` metadata when sending. A single concrete media type can supply the default, including repeated equivalent
declarations whose parameter order or case-insensitive components differ. An explicit charset controls text encoding and prevents a
second charset from being appended. Binary bodies retain their bytes. Form bodies
continue to percent-encode UTF-8 and preserve any declared media-type parameters.

SoapClient and SoapHandler choose MIME content handling from the selected binding.
They preserve the whole body even for XML and multipart media types; those values
are not interpreted as SOAP envelopes or attachment containers.
`WSDLLib::parseMultiPartSOAPMessage()` and `parseSOAPMessage()` expose an optional
`mime_content` argument for this selection. Empty MIME bodies remain empty, and
returned `^content-type^` metadata retains the complete Content-Type value.
Explicit charset parameters determine text decoding; other raw bodies remain
binary for the selected part's codec.

SOAP and XOP classification uses the same complete media-type parser. SOAP 1.2
serialization quotes and escapes its action parameter. SoapHandler obtains the
decoded parameter using `WSDLLib::getContentTypeParameter()`, checks the declared
action exactly, and uses the actual body element for body-based dispatch. URI
suffixes do not identify operations.

## Operation URI boundaries

HTTP operation locations must be relative references under WSDL 1.1 section 4.5.
Construction rejects scheme-bearing values such as `http://example.invalid/send`
or `urn:send`. Paths, query-only references and network-path references have no
scheme and remain relative. Qore's URI mapping classifies the XSD anyURI spelling;
it does not change the stored location or percent-decode it.

An explicitly empty `http:operation/@location` is a valid relative URI. It is
separate from an absent required attribute and targets the selected port's base
URI. An empty URL-replacement map likewise represents an active zero-part binding;
serialization, path decoding and handler dispatch check its presence. Required
message parts still need declared replacement patterns.

Replacement matching converts a caller path to UTF-8 once and uses byte offsets
for searching and slicing, consistent with the compiled literal tokens. Unicode
literal prefixes and separators remain distinct from percent-encoded part values.
URL-encoded requests strip an operation-location prefix using the same byte
units before parsing the query. For example, `/č/(id)/é` with `id=ž` emits
`/č/%C5%BE/é` and decodes to the original value, including when a direct caller
supplies the request path in a different string encoding.

SoapHandler stores locations containing a fixed query alongside replacement
routes under their verb and complete template. `/reports?revision=1` accepts an
appended `&id=71`, but does not match `revision=10` or `/reportsExtra`. Ordinary
static routes require their exact path, optionally followed by `?` parameters.
Routing compares the actual URI rather than treating TreeMap's component-relative
unmatched suffix as raw URI text. Static routes retain precedence over template
routes; multiple matching templates fail explicitly. Removal by service identifier
also removes fixed-query routes, and re-registration restores them.

## HTTP form part presence

Every declared part must have a wire key when decoding all message parts.
`WSMessage::deserializeAllPartData()` checks key presence before type conversion;
it does not infer presence from a scalar converter's empty-value behavior. An
explicit `label=` pair retains its key even when the MIME parser represents its
empty value as `NOTHING`, so a string part decodes to `""`. Omitting that pair
raises `SOAP-DESERIALIZATION-ERROR`. Numeric and boolean empty values still fail
their datatype rules. Extra unbound form/query keys retain their existing ignored
behavior.

GET requests with no query, an empty query, or only the fixed operation query
pass through the same message checks as nonempty queries. POST and MIME form
decoding treat a normalized absent body as zero octets, then apply those checks.
A zero-part operation accepts the resulting empty map; other operations reject
before a handler callback runs. Invalid requests do not change subsequent valid
request handling. The source, saved-service and detached-operation paths share
these rules.


## Direct MIME representation selection

Repeated direct `mime:content` and `mime:mimeXml` declarations are alternative
representations. The binding groups content declarations by public message part,
coalesces repeated XML declarations for the same part, and retains distinct XML
part mappings. Form encoding has one representation covering all abstract parts.
Content media alternatives for one part retain their declared order, including
repeated declarations. Selectors are stable under XML prefix or declaration-order
changes: `content:partName`, `xml:partName`, and `form`.

`BindingMessageDescription::getMimeFormats()` returns copied, typed
`WsdlMimeFormatInfo` values containing `kind`, `part`, and `media_types`.
`WsdlMimeFormatKind` distinguishes opaque content, form encoding, and schema XML.
The legacy `content` and `mimeXml` fields retain their first corresponding
representation. New services compile every alternative; detached operations save
the complete map. Descriptions saved before the map was introduced retain their
single-description behavior and do not expose new selectors. Invalid selected
saved maps, recursive child layouts, or selector/part mismatches fail explicitly.

The final optional `mime_format` argument on the four ordinary `WSOperation`
request/response serialization/deserialization methods selects a representation.
Without it, a concrete Content-Type must match exactly one representation.
Outgoing opaque values may supply that type through
`^attributes^.^content-type^`. A single representation can use its usual default.
Already parsed XML supplied to direct decoding considers only XML representations;
multiple XML part mappings still need a selector. Unknown, unavailable, or
ambiguous selections raise `SOAP-MESSAGE-ERROR`. The selected schema is applied
once, with no fallback to opaque content after a validation failure.

SoapClient call options `request_mime_format` and `response_mime_format` select the
two directions independently. SoapHandler registration accepts the same choices
as trailing optional `addMethod()` arguments. A handler can leave the request
selector absent for automatic Content-Type selection and choose an explicit
response selector. For example, an invoice operation offering both an opaque
`text/xml` upload and a schema-bound invoice uses `xml:invoice` for the latter.
These selectors are local API metadata, not custom wire headers. Client options
are validated before sending, and handler selections before route registration.

HTTP Content-Type headers participate in selection before serialization. Header
names are case-insensitive; non-string, malformed, or conflicting duplicates
reject. The chosen header cannot later overwrite the serializer with a different
media label. Explicit headers and opaque part metadata must agree. Existing
native part shapes and abstract-message provider types remain unchanged;
providers describe all abstract parts, while the selected format chooses which
part is present in an individual wire message.

A per-thread scope carries selection through the existing virtual binding API
and restores prior state on both success and exception. Binding descriptions are
immutable while in use. Each handler request updates its local method-value copy,
so automatic selection does not change later or concurrent requests.

## MIME transport character encoding

HTTP binding serialization encodes the selected media charset before sending.
SoapClient passes these payloads to HTTPClient as bytes so the client's default
encoding cannot convert them again. Binary content remains unchanged. Generic
UTF-16 XML includes a byte-order mark as required by XML 1.0 and RFC 7303; explicit
UTF-16BE/UTF-16LE retain their distinct encoding labels.

Opaque content with a charset uses Qore's `binary_to_string()` to resolve a UTF-16
BOM. If a supplied Qore string already has resolved UTF-16BE/UTF-16LE byte order,
reapplying the generic UTF-16 label does not discard that information. Text
without a charset retains the existing binary-body contract.

SOAP/MIME XML transport decoding shares the resource decoder: BOM takes
precedence, then transport charset, then XML declaration/signature and UTF-8
default. The decoded UTF-8 text goes to the XML parser. This implements the wire
encoding decision once; it does not infer a different MIME representation.
`test_mime_representations.py` tests actual octets with an independent Python HTTP
peer in both directions, including little-endian UTF-16 input and neutral UTF-16
XML output, from source and saved services.
