# SOAP body and header values

Copyright (C) 2026 Qore Technologies, s.r.o.

`SoapBinding` decodes body parts and bound headers independently before combining
their native results. Body values use WSDL part names. Header values use a
message-name container with part names inside it. The merge applies to requests
and responses, with document and RPC bindings.

Without headers, a single body part returns its value directly. With headers:

1. A single body part can return its value directly only if that value is
   `NOTHING` or a hash whose keys do not collide with header message names.
   Selected type and element wrappers always keep their part-name key.
2. If body part names collide with header message names, the body parts are
   grouped under the body message name. If headers already use that message
   name, body and header parts share its container; their part names are distinct.
3. Otherwise the body retains its part-name keys and header message hashes are
   added alongside them. Scalar body values use this rule too.

For example, a provisioning message `GetResponse` with body part `GetResponse`
and header part `SessionId` returns `{MOAttributes: ..., GetResponse: {SessionId:
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
