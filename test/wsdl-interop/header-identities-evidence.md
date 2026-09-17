# Imported SOAP header value identities (P6-18)

Copyright (C) 2026 Qore Technologies, s.r.o.

The reduced three-document fixture declares `{urn:header:a}H` and `{urn:header:b}H`,
both with part `token` and distinct namespace-qualified `Token` elements. Before
this increment, native and retained decoding both stored only the second value
under `H.token`. The declarations had already resolved correctly; their local
message names collided during result projection. Retained output fragment keys
also lacked the message namespace.

[WSDL 1.1 sections 2.1.1 and 3.7](https://www.w3.org/TR/2001/NOTE-wsdl-20010315)
identify components and header references by namespace-qualified message names.
Pinned WSDL4J independently reports both distinct imported header references in
both directions and SOAP versions. The native container representation is the
module's API contract, not a format prescribed by WSDL.

The fix derives stable container keys from the selected direction's body/header
message declarations. Unique local names retain their existing keys; collisions
use expanded names and native results retain independent body/header maps.
Serialization consumes qualified containers separately without changing shared
messages. Retained fragment markers include full message identity.

Eight Qore cases / 181 assertions cover source and offline saved graphs, both
SOAP versions/directions, document and RPC, optional headers, ambiguous/invalid
input, multiple parts per message, zero-part bodies, prefix changes, and actual
SoapClient/SoapHandler/SoapRequestDataProvider calls. The affected gate passes
23 suites / 481 cases / 9,053 reported assertions. All 16 corpus commands meet
expected outcomes; six reports differ only in version metadata, retaining 2,096
native valid successes, 2,084 legacy successes, 12 approved legacy projection
losses and 176 invalid source directions rejected.

Doxygen and astparser checks pass. The complete skill audit records 18 Pass,
44 N/A and zero Fail. No C++ changes or new DGC architecture were introduced.
See [validation](P6-18-validation.json), [audit](audits/P6-18-header-identities.md)
and [durable design](../../design/wsdl-soap-header-values.md).

P6 remains open for concrete header metadata/headerfault handling, typed fault
consumption, complete binding grammar, HTTP/MIME and pinned CXF replay. P7–P9
remain open. A separate encoded-header probe confirms that existing descriptors
lose an explicitly supplied namespace and encodingStyle; that is the next
concrete-header increment, not covered by this identity fix.
