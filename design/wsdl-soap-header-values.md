# SOAP body and header values

Copyright (C) 2026 Qore Technologies, s.r.o.

`SoapBinding` decodes body parts and bound headers independently before combining
their native results. Body values use WSDL part names. Header values use a
message-name container with part names inside it. Container names are local names
when unambiguous among the selected direction's body and header messages. When
distinct message namespaces share a local name, affected headers use expanded
`{namespace-uri}local-name` containers. The choice depends on the binding
declarations, so omitting an optional header does not change the remaining keys. The merge applies to requests
and responses, with document and RPC bindings.

For example, imported `{urn:billing}Session` and `{urn:shipping}Session` messages
with a `token` part retain separate containers even when only one header arrives.
When any bound header needs an expanded container and at least one bound header
is present, native decoding returns `{"^body^": <body part map>, "^headers^":
<header message/part map>}`. Serialization requires expanded containers for these
ambiguous header messages; it never guesses from a shared local name or flat part
name. Body/header maps also pass through SoapClient, SoapHandler and the request
DataProvider. Shared message descriptors remain unchanged during conversion.

Without headers, a single body part returns its value directly. If the same
message part is present in both locations, decoding returns exactly
`{"^body^": <body part map>, "^headers^": <header message/part map>}`. This check
precedes flattening and grouping. It keeps independently supplied values from
overwriting each other or being exchanged by the legacy serializer's preference
for message containers. Both request and response serialization accept these
maps, including client/handler and data-provider calls. See
[body selection](wsdl-body-parts.md) for input validation and examples.

With headers and no overlapping parts:

1. A single body part can return its value directly only if that value is
   `NOTHING` or a hash whose keys do not collide with header message names.
   Selected type and element wrappers always keep their part-name key.
2. If body part names collide with header message names, the body parts are
   grouped under the body message name. If headers already use that message
   name, body and header parts share its container; their part names are distinct.
3. Otherwise the body retains its part-name keys and header message hashes are
   added alongside them. Scalar body values use this rule too.

For example, a provisioning message `GetResponse` with body part `GetResponse`
and header part `SessionId`, explicitly excluded from the body parts list, returns `{MOAttributes: ..., GetResponse: {SessionId:
...}}` when the body fields have no conflicting name. If that root carries a
selected type, explicit native capture instead returns `{GetResponse:
{GetResponse: {"^type^": ..., "^val^": ...}, SessionId: ...}}`. The selected
wrapper remains intact inside its part key. A body field named `GetResponse`
also prevents flattening and keeps both parts inside the message container.

This merge controls the native API projection. Retained XML messages keep their
explicit `body` and `headers` part maps. Neither the wire placement of parts nor
their schema validation is changed by the native result shape.

`test/wsdl-header-merge.qtest` exercises independently authored envelopes, saved
services, absent headers, empty/nil/scalar bodies, colliding names and selected
wrappers across SOAP versions and directions. Client/server integration verifies
the same result through `SoapClient` and `SoapHandler`.

`BindingMessageDescription::getHeaderMessageKeys()` exposes the expanded-message
to container-key mapping. `WSMessage::getExpandedName()` derives the declaration
identity from the owned message namespace context, so detached and saved graphs
retain the same mapping. Retained XML fragment markers also include that identity
to prevent distinct header fragments from replacing each other during assembly.
`test/wsdl-header-identities.qtest` covers namespace collisions in both directions,
SOAP versions, document/RPC bindings, native/retained values and local consumers.

Concrete header descriptions retain their own `ns` and `encodingStyle` alongside
message, part and use. Encoded parts must reference types. The supported explicit
encoding style is `SOAP_ENCODING`; absent encoding style uses the same codec.
Unsupported explicit encodings reject at construction and saved-graph loading.
The encoded accessor uses the supplied binding namespace and part name,
independently of the body and operation style. Each encoded header block carries
its encodingStyle. Decoding matches its expanded accessor name and validates and
consumes that block's SOAP encodingStyle before applying the schema type; ordinary
attributes still undergo schema validation. Literal element headers keep their
schema-defined names and treat namespace/encoding metadata as format hints.

Old standalone header descriptors without optional namespace or encoding fields
retain absent values when restored. A descriptor without an encoded namespace
retains the existing unqualified accessor convention. Applications should supply
an explicit namespace for type-based encoded header blocks.

Source headers require message, part and valid use, a matching SOAP extension
namespace and recognized unqualified attributes. Manual and saved descriptors
validate part membership and encoded type/codec compatibility. These metadata
checks do not make shared descriptors mutable during operation execution.
`test/wsdl-header-metadata.qtest` covers independent metadata, schema conversion,
manual/saved graphs, local namespace declarations and real HTTP consumers.

Headerfault declarations are owned child descriptors of their ordinary header.
Their message, part, use, namespace and encoding metadata are independent of the
parent and of ordinary output headers. Nested headerfault declarations are not
valid, and their wire blocks must be namespace-qualified. Imported error messages
remain reachable through detached operation handles even when no abstract body
fault references them. Old standalone graphs without this child metadata expose
an empty list; reloading the source WSDL supplies declarations missing from them.

`SoapHeaderFaultInfo` selects a declared error message/part and supplies its schema
value. Its `request_header` field selects input declarations by default, or output
declarations when false. `WSOperation::serializeHeaderFault()` emits only that
headerfault block in Header with a generic Fault in Body and no application detail.
Local message names are accepted when unambiguous; expanded names distinguish
imports. Repeated descriptions with the same effective wire contract are
compatible; conflicting selections raise a binding error.

`deserializeHeaderFault()` explicitly decodes the selected block from a fault
envelope and supports native subtype capture. `deserializeXmlHeaderFault()`
returns its schema-validated literal element with lexical values and namespace
context intact. Encoding-specific XML retention is not supported. The envelope
must match the selected binding, contain one Header before Body, and contain one
Fault. The selected block must appear exactly once. Unknown qualified header
blocks remain outside the selected-value result. SOAP 1.2 Fault must be the sole
Body entry; SOAP 1.1 envelope extensions after Body remain allowed.

A SoapHandler callback can throw `SOAP_HEADER_FAULT` with `SoapHeaderFaultInfo` as
its exception argument. A declared application fault with that exact name takes
precedence. SoapClient keeps its ordinary fault exception; applications can pass
`call_info["response-body"]` to the explicit decode methods. Ordinary output
header descriptions and shared operation metadata are not changed during fault
conversion. All public operation boundaries own per-call identity/type scopes.
