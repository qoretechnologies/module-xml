# SOAP envelope processing

Copyright (C) 2026 Qore Technologies, s.r.o.

`SoapEnvelopeHelper` validates protocol containers before native namespace removal
or retained payload conversion. It traverses the document root, Envelope, Header
and Body with declaration-local namespace maps. Ordered parser occurrence lists
and suffixes remain visible during cardinality and order checks. Application
payloads continue through their schema validators.

A supported Envelope contains one Body, with at most one Header before it.
SOAP 1.1 permits qualified extension elements after Body; SOAP 1.2 does not.
Protocol containers reject non-whitespace text. Header blocks must be qualified,
including unbound compatibility headers. Envelope attributes must be qualified;
SOAP 1.2 applies that rule to Header and Body too, and prohibits encodingStyle on
these containers. Native serialization validates the same container representation
before publishing the wire value. Raw compatibility fragments retain the XML generator's standalone namespace
isolation and pass the same header checks in the enclosing namespace context. Encoded headers without a binding namespace and
literal headers without qualified element names cannot produce valid SOAP blocks
and reject when emitted.

Header-block attributes are identified by their expanded names in the active
SOAP envelope namespace. SOAP 1.1 `mustUnderstand` accepts `0` and `1` after XML
whitespace collapse. SOAP 1.2 `mustUnderstand` and `relay` use `xs:boolean` lexical
forms, including `true` and `false`. Unqualified, foreign-version and descendant
attributes are not interpreted as these protocol attributes. Serialization checks
the actual attribute string representation: native booleans and integer zero/one
produce valid forms, while a floating `1.0` cannot pass as the lexical form `1`.
These checks validate attribute syntax; they do not execute header application semantics.

`WSDLLib::validateSOAPEnvelope()` exposes the structure check and optional expected
version for parsed data. `SoapBinding` supplies its immutable version for native
and retained decoding. The serialized response override only affects output.
Wrong root identities and incompatible versions raise `SOAP-VERSION-MISMATCH`.
SOAP 1.2 clients can decode a SOAP 1.1 VersionMismatch response for version
negotiation. One-way operations still accept an empty transport response, while
nonempty SOAP responses undergo validation.

Raw XML checks run before projection in SOAP client/handler paths and through
`parseSOAPMessage(message, False, True)`. They reject DTDs and processing
instructions using XmlReader. Retained values and complete serialized SOAP output
use the same check. Already-projected hashes cannot recover discarded document
constructs; callers needing those checks must supply wire XML. HTTP MIME XML and
opaque MIME values do not acquire SOAP restrictions.

SoapHandler validates before invoking application callbacks. Protocol structure
errors use Client/Sender faults. Version mismatch responses preserve the supported
version, with SOAP 1.1 transition responses where required, and carry an Upgrade
header identifying the registered supported envelope. SOAP 1.2 Reason/Text values
include `xml:lang="en"`. Fault generation and request validation use local state;
rejected requests do not alter a service graph or subsequent valid exchanges.

For example, a SOAP 1.2 invoice endpoint receiving a SOAP 1.1 envelope returns a
SOAP 1.1 VersionMismatch fault with a SOAP 1.2 SupportedEnvelope declaration. A
subsequent SOAP 1.2 request on the same client connection executes normally.


`SoapProcessingNode` holds an immutable `SoapNodeOptions` capability registry keyed
by expanded header names. `SoapHeaderProcessor` callbacks receive a caller context
and `SoapNodeHeader`, including the original retained XML, effective role,
mandatory/relay flags, targeting and original index. A WSDL declaration does not
constitute a processing capability. All targeted mandatory headers must have a
processor before any processor runs. A missing capability raises
`SOAP-MUST-UNDERSTAND` with the ordered unknown headers. Processor exceptions
propagate and stop subsequent processing; application side effects from earlier
processors cannot be rolled back.

Every node assumes its SOAP version's `next` role. Ultimate receivers also assume
the default ultimate role; additional absolute roles come from configuration.
SOAP 1.2 `none` is never assumed. Role identities use Qore URI reference resolution
with inherited XML Base and the document retrieval URI. Comparisons do not decode
percent escapes or apply scheme-specific normalization. XML Base IRI references
use Qore's URI encoding; SOAP role attribute values use Qore's strict ASCII URI
validation (`RESOLVE_URL_ASCII`). The node
configuration cannot change during message processing.

A known targeted optional header is processed as well. `SoapNodeResult.headers`
keeps all blocks and outcomes in input order. Its `application_message` contains
only targeted headers for an ultimate receiver. An intermediary receives
`forward_message` instead: processed headers are removed; untargeted headers are
retained; targeted but unprocessed optional headers are removed in SOAP 1.1 and
retained only with `relay=true` in SOAP 1.2. Body content, surviving header order,
namespace bindings, XML context and lexical values survive forwarding. The
forwarded envelope records its effective XML base so a different next-hop
retrieval URI does not change relative identifier meanings. Intermediaries use
this API directly and arrange their own forwarding transport; the class does not
execute application body semantics.

`SoapHandler` takes an optional ultimate-receiver node as its fifth constructor
argument. It processes headers before application decoding and dispatch and
provides the complete result as `cx.soap_processing`. Unknown targeted mandatory
headers produce HTTP 500 `MustUnderstand` faults in both SOAP versions. SOAP 1.2
faults include qualified `NotUnderstood` blocks with correctly scoped QName
attributes. Application body callbacks receive only the targeted headers; the
processing result retains every original block. WSDL and XSD validation remain
responsible for the selected application values.

`SoapClient` accepts an ultimate-receiver `soap_node` constructor option and an
optional per-call override. Response processing precedes body decoding, including
fault-body decoding. Unknown targeted mandatory response headers raise
`SOAP-MUST-UNDERSTAND`. The call information's `soap-processing` field contains the
complete typed result, while ordinary and retained decoding see only targeted
headers. Relative response roles use the native HTTP client's effective response
URL, including redirects. Empty one-way responses remain valid. Neither client
nor handler accepts an intermediary node as an application endpoint.

HTTP contexts and native information hashes can be legacy untyped containers.
The adapters copy those fields into explicit `hash<auto>` containers before
adding typed node results; this prevents legacy assignment semantics from stripping
nested hash declarations. XML handed to the application decoder goes through the
existing SOAP parser, preserving its comment projection and XOP substitution.

Response fault detection compares the body's expanded element names with `Fault`
in the actual envelope namespace before projecting the legacy exception payload.
Application elements with the same local name remain ordinary schema values in
native and retained decoding. The actual received version also selects fault
decoding for the SOAP 1.1 VersionMismatch transition response to a SOAP 1.2 binding.

SOAP 1.2 fault validation runs in the shared envelope validator before namespace
projection. A protocol `Fault` must be the sole Body child. Its fields occur once
in the order `Code`, `Reason`, optional `Node`, optional `Role`, optional `Detail`;
the first two are required. Code and each nested Subcode contain `Value` followed
by at most one Subcode. Values resolve as QNames in their own namespace scopes,
and the top code must name one of the five SOAP 1.2 standard codes. Subcode chains
are traversed iteratively.

Reason contains one or more text-only SOAP `Text` elements, each carrying its own
explicit `xml:lang`; inherited language alone does not satisfy this requirement.
Language values follow the XML language declaration, including an empty reset.
Repeated languages remain accepted because distinct languages are recommended,
not mandatory. Node and Role allow relative URI references and use Qore's ASCII
URI grammar validation without rewriting their original spelling. Detail allows
element content and qualified attributes but forbids SOAP `encodingStyle`.

The same validation covers native and retained response consumers, saved services,
node processing, HTTP clients/handlers and generated WSDL fault envelopes. Malformed
fault structures raise `SOAP-DESERIALIZATION-ERROR` on input and
`SOAP-SERIALIZATION-ERROR` on the WSDL serialization path. Valid faults retain the
existing `SOAP-SERVER-FAULT-RESPONSE` exception contract. Application detail schemas
and declared fault selection remain separate from this protocol validation.
