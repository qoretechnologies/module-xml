# P9a acceptance: WS-Addressing and the WS-I gap register

Copyright (C) 2026 Qore Technologies, s.r.o.

Accepted 2026-09-25 on `develop`. The scope was approved on 2026-09-23, with defaults on 2026-09-24: WS-Addressing
1.0 in full (Core, SOAP Binding and Metadata, including the WS-Policy 1.5 attachment of `wsam:Addressing`).
Incoming headers are processed when present. Non-anonymous response endpoints are used only with an address
authorizer. The durable design is [design/soap-addressing.md](../../design/soap-addressing.md).

| Criterion | Evidence |
| --- | --- |
| Every applicable WS-Addressing row is covered by tests, in both directions where the requirement has two sides | [assertion-ledger.json](assertion-ledger.json) (P9a-08): 45 of the 49 WS-I Basic Profile 1.2 and 2.0 rows are covered, and R1203/R1204 are not applicable (non-addressable service instances; approved 2026-09-24). [verify_ledger.py](verify_ledger.py) rejects any WS-Addressing gap. Mapping the rows fixed R1041 (`wsa:FaultDetail`), R2745 (explicit empty SOAPAction) and Basic Profile 2.0 R2901. |
| CXF exchanges pass for anonymous and decoupled responses | [test_ws_addressing.py](test_ws_addressing.py): CXF 4.1.3's unmodified `add_numbers.wsdl` and `add_numbers_soap12.wsdl`. Qore clients call CXF servers on all three ports (12 runs, including non-anonymous responses received by `SoapReplyHandler`). CXF clients call the Qore handler on all three ports (6 runs, including CXF decoupled endpoints). Every run finishes without diagnostics. |
| Decoupled replies follow the acknowledgment | `SoapHandler` sends them from HttpServer's `after_send` callback. [soap-addressing-transports](../soap-addressing-transports.qtest) proves the order over HTTP/1.1, HTTP/2 and HTTP/3 with an endpoint that waits for the client's acknowledgment; it fails with delivery before the 202. |
| Invalid MAPs fail with the predefined WS-Addressing faults | [soap-addressing-messages](../soap-addressing-messages.qtest) and [soap-addressing-handler](../soap-addressing-handler.qtest): cardinality, missing headers, invalid addresses and EPRs, action mismatches, `OnlyAnonymousAddressSupported` and `OnlyNonAnonymousAddressSupported`, as SOAP 1.1 faults with `wsa:FaultDetail` and SOAP 1.2 subcodes, related to the request when its message ID can be read. |
| No request can make a handler contact an address its configuration did not approve | [soap-addressing-decoupled](../soap-addressing-decoupled.qtest) ("response endpoints need approval"): without an authorizer, a refusing authorizer, an anonymous-responses policy or a non-HTTP address, the request is refused before the operation runs, and nothing is sent. Delivery options cannot override the URL or timeouts. |
| Transports | [soap-addressing-transports](../soap-addressing-transports.qtest): anonymous, decoupled and refused exchanges, TLS options and delivery order over HTTP/1.1, HTTP/2 and HTTP/3. |
| Full suites pass without warnings | On Qore installed 2026-09-25 (at or after 97899cc02) in the developer's normal environment: all 292 qtests and all 498 Python tests pass. Targeted: soap-addressing-transports 5 cases / 145 assertions (stable over 5 runs; fails against synchronous delivery), webdav_streaming 8 / 74, test_ws_addressing.py 3 tests (18 live CXF runs) over 3 runs; docs-SoapHandler builds without warnings. |

**Runtime:** Qore installed 2026-09-25, with the NaN-boxing fix, HttpServerUtil 1.6 (`after_send`) and HttpServer
1.7 (`cx."header-info".max_request_body_size`). The suites run in the developer's normal environment.
