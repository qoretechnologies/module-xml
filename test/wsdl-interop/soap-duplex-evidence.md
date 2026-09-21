# P7-14 SOAP full-duplex buffered requests

Copyright (C) 2026 Qore Technologies, s.r.o.

## Implemented contract

A SOAP request is an ordinary buffered HTTP body. [RFC 9112 section
6](https://www.rfc-editor.org/rfc/rfc9112#section-6) and [RFC 9110 section
9.3.1](https://www.rfc-editor.org/rfc/rfc9110#section-9.3.1) allow a server to send a
complete response before it has read the whole request, and the SOAP 1.1 and SOAP 1.2
HTTP bindings inherit that behavior. A client that sends its entire request before
beginning to read therefore cannot interoperate with a conforming peer whose response
does not fit in the transport's unread buffers.

P7-13's assertion review reproduced exactly that deadlock in Qore's core HTTP/1.1
client, independently of XML, and handed it off at
`/tmp/qore-httpclient-buffered-duplex/README.md`. Qore fixed it in
`fix: read the HTTP/1.1 response while a buffered request body is still sending`
(rebased onto `develop` as `8a1c3e5f3`), which reads response data while the remaining
buffered body is sent, preserves Content-Length completion, handles early responses and
100 Continue, and prevents reuse of a connection with an incomplete upload.

This increment adds no XML production code. It establishes the SOAP-level contract that
depends on the core progression, and the executable evidence that it holds: neither
SoapClient nor SoapHandler serializes the two directions, and neither substitutes a
streaming send to avoid the interleaving. The durable statement of the contract is in
[SOAP processing](../../design/soap-envelope-processing.md).

## Forcing a genuine full-duplex exchange

Both gates make the duplex property observable rather than assumed.

The independent gate bounds the peer's socket buffers to 2048 bytes and scripts a 1 MiB
request against a 512 KiB response. A serialized send-then-receive reference client was
measured to deadlock on this transport at a 512 KiB request with a 256 KiB response, so
the scripted sizes keep a factor of two in hand. The peer records how many request-body
bytes it had read at the moment its whole response had been written; every scripted
exchange records a value far below the declared request length, and every drained
exchange ends with the full declared length received.

Qore's `Socket` class exposes no receive-buffer control, so the in-repo suite instead
sizes the exchange beyond any plausible kernel buffer: an 8 MiB request against a 4 MiB
response, the sizes at which a serialized reference client was measured to deadlock with
default buffers. Its peer reads the request header, writes the complete response and
only then reads the request body, so the recorded count of request bytes read when the
response completed is exactly zero for every exchange. A client that finished sending
before reading would leave both ends blocked and the bounded deadline would expire.

## Executable coverage

- `test/soap-duplex.qtest`: 5 cases / 203 assertions over 40 exchanges of 8 MiB each.
  Early responses across SOAP 1.1/1.2, source/saved-object/saved-data graphs and
  native/retained values; Content-Length and chunked response framing; the drained
  request re-parsed as a well-formed envelope carrying the whole value; early faults
  with version-specific code, reason, detail size and detail namespace binding;
  truncated early responses; a peer that disappears mid-upload; a peer that withholds
  both the response body and the request drain until the client's own deadline expires;
  thread cancellation while both directions are active, with the cancellation reason
  preserved and the sticky flag cleared; and same-client recovery after every failure.
- `test/wsdl-interop/test_soap_duplex.py`: 2 tests over 146 independent HTTP exchanges.
  The 144-exchange matrix runs twelve ordered steps against one SoapClient for each of
  SOAP 1.1/1.2 × source/saved/data × native/retained, covering length and chunked
  framing, early faults, peer EOF, event-triggered cancellation, client timeout,
  keep-alive delivery and keep-alive reuse, with a recovery step after each failure.
  `cancel` and `timeout` answer on keep-alive connections and their recovery steps are
  scripted as new connections, so a client that reused a connection carrying an
  incomplete upload would never be served. The remaining two exchanges validate the
  duplex request against the pinned W3C SOAP 1.1 and 1.2 schemas and confirm it carries
  the complete 1 MiB value.

Neither gate uses a sleep or a readiness poll. The independent peer never drains a held
request, so the client announces its own completion over a control channel instead of
the peer inferring it from transport state; the in-repo peer holds a connection open on
a `Counter` released by the test thread. All servers, worker threads and sockets are
torn down deterministically and every wait carries a bounded deadline.

## Reproduction

```
QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug test/soap-duplex.qtest
QORE_MODULE_DIR=build-debug:qlib python3 -B test/wsdl-interop/test_soap_duplex.py -v
python3 /tmp/qore-httpclient-buffered-duplex/run.py
python3 /tmp/qore-httpclient-buffered-duplex/run.py reference
QORE_MODULE_DIR=build-debug:qlib python3 /tmp/qore-httpclient-buffered-duplex/run.py xml
```

The three reproducer modes all succeed on the current runtime: the core-only client, the
raw-socket reference control and the SOAP client each upload 8 MiB while receiving a
4 MiB response. Exact commands, digests and results are committed in
[P7-14-validation.json](P7-14-validation.json); the audit is
[P7-14-soap-duplex.md](audits/P7-14-soap-duplex.md).

## Results

All 41 affected Qore suites pass: **473 cases / 27,857 assertions**. All 17 independent
Python gates pass. All 16 corpus commands meet their recorded outcomes, and all six
semantic reports are unchanged from P7-13 apart from the Qore runtime identifier. The
compiled matrix builds WSDL, SoapClient and SoapHandler with `qcc -m -o` and passes
**11 gates / 44 cases / 849 assertions**, including the new suite and the new independent
gate against the freshly compiled modules. Documentation and both new Qore files pass
documentation and AST checks without warnings or errors. Installed Qore is `a6744554`.
Audit: **16 Pass / 46 N/A / zero Fail**.

## Peer defects found after the first run

Running this gate under concurrent load exposed two defects in its own raw peer, both fixed:

- The scripted connection was published through a shared attribute on the server and read by
  the handler thread, so overlapping accepts could hand two handlers the same script and a
  connection could be served the wrong behavior.  Each accepted socket now carries its own
  assignment, made on the accept thread before the handler starts.
- Records were collected in handler-completion order, but a draining handler outlives the
  client call it answered, so a slower handler could report after a later one.  Each record
  now carries its accept order and the sequence is sorted before comparison.

The peer step-accounting assertion was also moved ahead of the per-call outcome comparison.
That ordering matters: a client that reused a pooled connection the peer had already closed
would fail a call without opening a connection, and the accounting assertion names that
directly instead of letting it surface as an unexplained transport error on a later row.
With that guard in place, the peer-EOF step accepts either terminal error, because when both
directions are active either side may legitimately observe the closure first.

## Related core defect

`test_soap_transport.py::test_get_response_interruption_and_recovery` fails intermittently on
this runtime with `SOCKET-CLOSED` for a GET recovery step. It is not caused by this increment
and does not affect this gate. It was root-caused to Qore core HTTP connection management: a
connection whose response read failed is published to the waiting application thread before it
is marked closed, so the pool can hand the dead connection to the next request. Counting
accepted connections during failing runs shows the shortfall directly (324 and 328 accepted
for 336 client calls). See `/tmp/qore-soap-get-recovery-flake/README.md`.

## Scope

This increment does not claim P7 acceptance. The current-normative W3C and WS-I
assertion ledger remains open, and the SOAP data-model, encoding and RPC assertions
remain routed to P8. No XML production code, C++ code or Qore checkout changed, so
Valgrind is not required.
