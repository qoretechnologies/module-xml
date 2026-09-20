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

SOAP 1.1 faults have separate validation rules. Body contains at most one protocol
Fault, with required unqualified `faultcode` and `faultstring` and optional
unqualified `faultactor` and `detail`, each occurring once. These fields are
recognized by name; the generic receiver does not impose SOAP 1.2 field ordering.
Codes use QName syntax and may name application codes or dotted subcategories.
Fault strings accept optional `xml:lang`, including an empty reset. Fault actors
use URI-reference syntax; detail contains element content. Qualified extension
fields and additional Body entries remain accepted under the SOAP 1.1 protocol.

Native fault decoding selects the original protocol Fault before namespace
projection. An application Body sibling named Fault cannot merge with it.
SOAP 1.1 extension field names remain qualified, so a qualified extension named
`faultcode` cannot replace the protocol field. The exception argument retains
in-scope namespace declarations in `^attributes^` for interpreting QName values and
qualified extension fields. This namespace context is retained for SOAP 1.2 faults
as well. Standard field names and the fault exception category remain unchanged.

`WSDLLib::getSOAPFaultInfo(xml, expected_soap12)` provides an explicit protocol
view. `SoapFaultInfo` resolves Code/Subcode QNames in each Value's own scope,
retains ordered `SoapFaultReason` text/language pairs, distinguishes absent from
empty actor/node/role references and Detail containers, and retains header and
SOAP 1.1 extension elements. URI fields use XSD whitespace normalization without
resolving relative references; retained XML context supplies their original base.
Its `envelope` retains the supplied document for exact forwarding, including
attributes, comments and SOAP 1.1 application Body siblings. The `fault` and
`detail` subtrees also retain namespace bindings and inherited XML context.

This protocol view does not validate application detail schemas. Declared detail
and header-fault values continue through the operation's existing explicit fault
consumers. Ordinary response decoding keeps its existing exception category and
native representation. An expected SOAP 1.2 version permits the protocol-defined
SOAP 1.1 VersionMismatch reply; other mismatches reject.

`WSOperation::serializeFault()` and `serializeHeaderFault()` accept a trailing
`SoapFaultOptions` argument. It selects a QName code, an ordered subcode chain,
explicit reasons, and the version's actor/node/role fields. Omitted options keep
existing defaults. SOAP 1.1 requires one reason and rejects subcodes/node/role;
SOAP 1.2 requires one or more reasons with explicit language and rejects actor.
Invalid codes, URI/language values, empty reason lists and XML-invalid reason
characters raise `SOAP-SERIALIZATION-ERROR`. Empty reason text and explicit empty
language/URI values remain distinguishable from absence.

Fault options are applied after schema detail and header serialization, before the
shared envelope validator and XML generator. QName fields receive local bindings
and namespace resets, preserving expanded identities even when a caller's prefix
collides with an envelope alias. Generated prefixes may differ from input spellings.
Subcode creation and reading use iterative traversals. Operation metadata and input
options are never mutated.

```qore
hash<SoapFaultOptions> fields = <SoapFaultOptions>{
    "code": new XsdQNameValue(SOAP_12_ENV, "Receiver"),
    "subcodes": (new XsdQNameValue("urn:orders", "o:Unavailable"),),
    "reasons": (<SoapFaultReason>{"text": "Stock service unavailable", "language": "en"},
                <SoapFaultReason>{"text": "Service de stock indisponible", "language": "fr"}),
    "node": "https://orders.example/soap",
};
hash<auto> response = operation.serializeFault("OrderRejected", "Unavailable", detail,
    NOTHING, NOTHING, NOTHING, NOTHING, NOTHING, "Soap12Binding", fields);
hash<SoapFaultInfo> received = WSDLLib::getSOAPFaultInfo(response.body, True);
```

SOAP 1.2 `encodingStyle` is rejected on Fault, Code, Value, Subcode, Reason, Text,
Node, Role and Detail. It remains permitted on application detail entries and their
descendants. An application-qualified attribute also named `encodingStyle` is
independent. Detail retains the normative schema's qualified-attribute restriction.


SoapHandler separates header processing, body conversion and application dispatch
when mapping faults. A header processor's `SOAP_HEADER_FAULT` exception is retained
while the handler resolves the operation identity from the action or Body element.
It then uses that binding's header-fault declaration without converting the Body or
calling the application. Unknown targeted mandatory headers still fail preflight
before any processor runs. The selected binding's SOAP version is checked before
sending a declared header fault.

Body callbacks and header processors share declared-fault serialization. A body
callback preserves the precedence of a declared application fault named
`SOAP-HEADER-FAULT`; a header processor always selects header-fault metadata.
Invalid header-fault declarations or values are server-side failures. Error hooks
receive the selected operation context when declared fault serialization fails.

Input conversion and routing failures produce Client/Sender faults. Unexpected
header processor, application callback and output serialization failures produce
Server/Receiver faults. SOAP 1.1 uses HTTP 500 for both; SOAP 1.2 uses HTTP 400 for
Sender and HTTP 500 for Receiver, MustUnderstand and VersionMismatch.
`THREAD-CANCELLED` and `PROGRAM-INTERRUPTED` propagate across these boundaries
without invoking error hooks or being converted to SOAP responses.

Generic fault diagnostics accept arbitrary exception code/description values.
Strings retain their text; non-string values use Qore's diagnostic representation,
and an absent description becomes `no description provided`. Unicode points outside
XML 1.0's character repertoire appear as visible `\u{XXXX}` escapes. This rendering
applies only to generated diagnostic text; application payloads and original error
logging are unchanged. Empty text, ordinary Unicode, tabs and newlines retain their
values. Character traversal is linear and uses a Unicode character iterator.

For HTTP 400 and 500-series errors on a SOAP binding, SoapClient normalizes the MIME
root and decodes its charset before recognizing a Fault by expanded name under a
matching SOAP Envelope and Body. It reuses the parsed message for ordinary processing,
which still validates envelope structure, fault fields and header capabilities.
Recognition accounts for repeated Body occurrences so an invalid envelope containing
a Fault reaches protocol validation. Prefix spelling and XML whitespace do not affect
recognition. Application names, comments, CDATA and Fault elements outside Body do not
replace the original HTTP error. Malformed SOAP/XML error entities report the parsing
or protocol error; non-SOAP entities and other HTTP status errors retain the original
transport exception. HTTP WSDL bindings retain their independent error behavior.

SoapProcessingNode emits UTF-8 XML after selecting application-visible headers. Both
SoapClient and SoapHandler reparse that generated document with a UTF-8 content type,
while retaining original HTTP/MIME metadata and attachment entities separately. The
wire charset applies to incoming bytes only; it does not describe the generated XML.
This distinction applies to ordinary messages and faults, including native and retained
values. No transport metadata or shared service graph is rewritten.

One-way SOAP operations have no application output declaration. Native response
decoding recognizes protocol faults before testing for that declaration or applying
SOAP encoding to application values. Empty Bodies, including whitespace-only content,
return NOTHING; unexpected application children still reject. Direct retained XML
response decoding also reports protocol faults first, but otherwise requires an output
declaration because its result represents declared application parts.

SoapClient accepts empty one-way HTTP acknowledgments and applies the ordinary SOAP
processing model to any supplied envelope. This includes registered response-header
processors and unknown targeted mandatory-header rejection. The `xml_values` option
does not require output parts for an empty one-way acknowledgment. Response processing
metadata remains in call information. An HTTP success status confirms transmission;
it is not an application validation or delivery guarantee.

SoapHandler sends an empty HTTP 202 acknowledgment for a successful one-way operation
in either SOAP version. SOAP 1.2 requires this status when there is no response envelope;
WS-I Basic Profile 1.2 lists it as a preferred SOAP 1.1 one-way acknowledgment.
Processing failures still generate the applicable SOAP fault and HTTP status. The
handler does not synthesize an application response or change HTTP WSDL bindings.

Request actions have version-specific transport representations. SOAP 1.1 uses a
quoted SOAPAction HTTP header, including the quoted empty default. SOAP 1.2 uses
the quoted action parameter of the XML root's application/soap+xml media type and
omits SOAPAction. Responses do not inherit a request action. The per-call override
remains available; an explicit empty override suppresses both representations.

`WSDLLib::getSOAPAction()` decodes normalized root metadata. For SOAP 1.1 it removes
HTTP quoting and surrounding optional whitespace, while accepting legacy unquoted
URI references. For SOAP 1.2 it ignores SOAPAction and reads the media-type action;
XOP places that media type inside its type parameter. Qore's RFC 3986 ASCII mode
validates syntax: SOAP 1.1 permits empty/relative references, while a present SOAP
1.2 action must be nonempty and absolute. Validation does not resolve, percent-decode,
case-fold or otherwise change the action's lexical identity. Conflicting duplicate
media parameters reject; identical duplicates retain the same value.

SoapHandler dispatches actions after MIME root normalization and envelope version
validation. The callback and header processors receive the decoded `cx.soap_action`,
or NOTHING when absent. Bound actions can disambiguate empty Bodies. Otherwise the
Body or registered route must identify a unique operation. A nonempty action that
disagrees with a nonempty selected binding action produces a Client/Sender fault
before the body callback. SOAP 1.2 does not depend on the legacy SOAPAction header;
its absence and presence alone do not prevent Body dispatch. HTTP WSDL bindings
continue to use their registered method/path and MIME selection.

SoapProcessingNode implements Serializable for its immutable configuration. Restore
uses the same role/name checks as construction and reconstructs the transient role
lookup; missing configuration rejects. Default and role-only nodes can be saved,
including through a URL-loaded WebService whose transport options retain a SoapClient.
Qore call references and closures are not serializable: nodes containing processors
raise SERIALIZATION-ERROR. Serialization never silently removes callback capabilities,
and a failed attempt leaves the original node usable.

SoapClient restoration validates the saved node as an ultimate receiver before
assigning members. A saved client without a processing-node field receives the same
default node as a new client. Invalid node objects and intermediary configurations
reject during restoration, before any request can use the client.

SOAP HTTP media validation is separate from XML protocol processing.
`parseMultiPartSOAPMessage(..., soap_envelope=True)` requires a supported transport
and normalized XML root. Multipart SOAP uses multipart/related; XOP declares its XML
media type in the type parameter. `validateSOAPMediaType()` accepts text/xml,
application/xml and application/soap+xml, validates charset/type ambiguity, and uses
Qore's conversion-stream constructor to check charset support without consuming the
payload. Empty charsets reject. The application/soap+xml representation requires an
actual SOAP 1.2 envelope. Generic XML representations remain available for either
supported SOAP version. Opaque WSDL HTTP MIME bindings opt out of SOAP validation.

SoapHandler returns plain UTF-8 HTTP 400 responses for malformed transport metadata
and 415 for unsupported transport, root media or charset. These failures precede
header and body callbacks. Envelope-version negotiation precedes the final media/
envelope identity check, preserving VersionMismatch and Upgrade behavior. Errors
while interpreting a recognized SOAP envelope retain protocol faults. Error logging
records the input byte count and original exception without decoding invalid body
text. Valid character encodings with malformed payload bytes therefore retain their
original protocol error and do not trigger a secondary logging failure.

Unsupported methods on registered resources return HTTP 405 with an Allow header
computed from applicable SOAP and WSDL HTTP bindings. SOAP WSDL invocation uses POST;
registered HTTP binding methods retain their explicit routes. GET ?wsdl retrieval
continues independently. Method discovery holds the registry read lock and does not
invoke application callbacks.

SoapClient validates nonempty SOAP response media before header processing. The
response mode of `validateSOAPEnvelope()` permits the SOAP 1.1 VersionMismatch fault
required for SOAP 1.2 negotiation, sharing the processing node's version rules.
Empty one-way acknowledgments require no XML media type. Non-SOAP HTTP error responses
retain the original HTTP exception and status. MIME-content HTTP bindings retain
their declared opaque format and body.

Mandatory-header capability checks precede validation of SOAP Body content and fault
grammar. Adapter envelope preflight sets `headers_pending=True` to check container
structure and version without issuing Body-content faults. SoapProcessingNode scans
all targeted mandatory headers, raises a single MustUnderstand fault if any capability
is missing, then completes Body/fault validation before calling processors. The
public envelope validator retains complete validation by default. This ordering is
shared by direct nodes, handler requests and client responses, including HTTP faults.
