# Optional WSDL transport metadata

Copyright (C) 2026 Qore Technologies, s.r.o.

WSDL can describe endpoints whose protocols are unavailable to the client or
server. The parser recognizes Apache CXF's XML binding namespace
`http://cxf.apache.org/bindings/xformat` and JMS declarations using
`http://cxf.apache.org/transports/jms` or `http://www.w3.org/2010/soapjms/`.
The SOAP/JMS transport URI follows [W3C SOAP/JMS section 3.3.2](https://www.w3.org/TR/soapjms/#wsdl-transport).
These declarations remain metadata; they do not register callable operations.
An empty CXF binding element retains its namespace identity during parser key
normalization. Abstract port-type, operation and fault references still resolve.

`Binding::isSupported()` identifies callable bindings.
`Binding::getUnsupportedReason()` returns a reason for unavailable bindings, and
`Binding::getDeclarationData()` exposes their normalized parsed declarations.
The declaration retains operation extensions such as `xformat:body/@rootNode`,
their nested content and in-scope namespace bindings. Its outer child keys use
local names and `ns` prefix metadata, as elsewhere in the WSDL parser. Returned
hashes are copy-on-write; modifying one does not alter the binding. Standalone
binding serialization retains these fields. Saved services reconstruct them
from their retained source graph.

Service port metadata similarly includes `unsupported_reason` and `declaration`
for unsupported endpoints. JMS address extensions retain their queue and JNDI
properties; a `jms:` location is also recognized, even if its SOAP binding uses
the ordinary HTTP transport URI. Address declarations scoped to a port retain
that port's namespace context. Ordinary SOAP/HTTP ports remain callable in the
same service. Unknown extension families still raise the existing construction
error; recognition of these optional families does not imply generic protocol
support.

`WebService::getBindingOperation()` rejects unsupported binding selection with
`WSDL-BINDING-ERROR`. `SoapClient` rejects unsupported port selection with
`SOAP-CLIENT-ERROR` before setting up the selected transport. A URL override does
not change the selected port's protocol. Its established default remains the
first port; callers select a supported port explicitly in mixed services, for
example `new SoapClient({"wsdl": service, "service": "SOAPHeaderService",
"port": "SoapPort"})` for the pinned RPC-header contract. Source retrieval keeps
the original WSDL. Mounted address rewriting walks service/port address elements
by namespace, rewriting only supported endpoints. It copies other subtrees and
non-element nodes intact, so shared URL strings in unsupported addresses or
documentation are not replaced. Attribute values use the XML generator's escaping.

`test/wsdl-unsupported-ports.qtest` covers source and saved services, detached
bindings, namespace variants, SOAP/JMS version metadata, malformed component
references, explicit/default selection errors and real SOAP HTTP exchanges.
The pinned RPC-header and MTOM contracts exercise CXF XML and JMS declarations
without editing their source files.
