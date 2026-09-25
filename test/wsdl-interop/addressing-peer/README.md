# Independent WS-Addressing peer

Copyright (C) 2026 Qore Technologies, s.r.o.

This peer uses Apache CXF 4.1.3 and the pinned artifacts and notices in `../cxf-peer/`. The contracts are the
unmodified CXF system test resources `../cxf/add_numbers.wsdl` (SOAP 1.1) and `../cxf/add_numbers_soap12.wsdl`
(SOAP 1.2), verified against their digests in `../cxf/catalog.json`. Each has three ports:
- `AddNumbersPort` requires WS-Addressing.
- `AddNumbersOnlyAnonPort` allows only anonymous responses.
- `AddNumbersNonAnonPort` allows only non-anonymous responses.

`AddressingPeer.java` works in two modes, both with CXF's `WSAddressingFeature`:
- **Server:** checks each request's action and message ID.
- **Client:** records the properties that CXF sent (CXF replaces a supplied message ID), then checks each
  response's action and its relationship to the request. It covers `addNumbers`, `addNumbers2` and a declared
  `addNumbers` fault. SOAP 1.2 Sender faults arrive with HTTP 400, as the SOAP 1.2 HTTP binding requires, so the
  client sets `org.apache.cxf.transport.process_fault_on_http_400`. With `decoupled`, the client receives replies
  and faults at a decoupled endpoint on a free local port, which its requests name as `wsa:ReplyTo`.

`qore-peer.qr` is the Qore side:
- **Server:** a `SoapHandler` serves the port's binding at `/add`, and its authorizer approves loopback response
  endpoints.
- **Client:** `SoapClient` or `SoapClientIo` makes the same calls. For the non-anonymous port, replies are received
  at a `SoapReplyHandler` endpoint.

Both sides expect `addNumbers3`'s relative `3in` action to be rejected, because an `[action]` is an absolute IRI
(WS-Addressing Core section 3.1).

The generated classes compile with `-Xlint:all,-serial -Werror`: the generated fault exception keeps the contract's
fault bean, which is not serializable. The peer compiles with `-Xlint:all -Werror`.

Run `python3 -B test/wsdl-interop/test_ws_addressing.py -v` from the repository root. The runner:
- verifies the pinned dependencies and contracts;
- generates and compiles one peer for each contract;
- makes 12 Qore-client runs against CXF servers (3 ports × 2 clients × 2 SOAP versions);
- makes 6 CXF-client runs against the Qore handler (3 ports × 2 SOAP versions); for
  `AddNumbersNonAnonPort`, CXF uses a decoupled endpoint.

Listeners report readiness and accept a STOP event, and every run must finish without diagnostics.

CXF clients with a decoupled endpoint only accept a reply that arrives after the 202 acknowledgment. `SoapHandler`
sends replies and faults to non-anonymous endpoints from HttpServer's `after_send` callback, once the 202 has been
sent, so the decoupled exchanges pass.
