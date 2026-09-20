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
