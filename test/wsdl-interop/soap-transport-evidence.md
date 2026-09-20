# P7-12 SOAP transport interruption and cancellation

Copyright (C) 2026 Qore Technologies, s.r.o.

The independent raw TCP peer receives a complete request and then closes before
headers, after a partial status line, during a Content-Length body, or during chunked
framing. SoapClient preserves SOCKET-CLOSED and invokes no header processors.
A valid response follows every interrupted exchange on the same client.

Cancellation waits for Qore's actual HTTP response-header event before cancelling
the calling thread. The peer withholds the body in length and chunked modes. Tests
require THREAD-CANCELLED, the original reason and sticky cancellation flag, peer EOF,
zero header callbacks, and successful reuse. No XML close() workaround or elapsed-time
readiness assumption is used. Worker completion and peer shutdown use explicit
synchronization; socket/process bounds are failure deadlines, not readiness delays.

Handler tests disconnect during headers, Content-Length and chunked input. Incomplete
requests invoke neither header nor body callbacks; the next complete request succeeds.
The matrix covers SOAP 1.1/1.2, request-response and one-way operations, source/object/
data service graphs, and native/retained values. Empty one-way recovery uses HTTP 202;
a truncated envelope cannot masquerade as an empty successful acknowledgment.
Generated complete messages validate against the unchanged pinned W3C schemas.

Two core-only reductions identified missing HTTPClient request events and missing
request abandonment after a cancelled Future wait. Installed Qore resolves both.
The complete matrix passes without changing the XML production adapters. The core
owns transport cancellation/connection cleanup; XML preserves its exceptions.

Run from the checkout:

```bash
python3 -B test/wsdl-interop/test_soap_transport.py -v
```

The gate selects local Debug XML and local qlib, always enabling Qore debugging and
disabling signal handling. The compiled check builds the three modules with qcc -m,
then runs the same Python matrix using peer derivatives whose requirements select
those qmods; fixture paths still point to the original pinned contract.

Six affected native Qore suites pass: **38 cases / 2,223 assertions**. Three independent
Python gates pass, including all **432 new transport exchanges**. The full new matrix
also passes with freshly compiled WSDL, SoapClient and SoapHandler modules (another
432 exchanges). Both peer scripts pass astparser without diagnostics. Installed Qore
is `25346118e`. Audit: **16 Pass / 46 N/A / zero Fail**.

The requirement scope is abnormal exchange termination in SOAP 1.2 Part 2 sections
6.2.2 and 6.3.2 and exception-safe transport cleanup. These tests do not establish
full HTTP binding/profile conformance. P7 remains open for explicit SOAP-response GET
and complete W3C/WS-I applicability/test accounting; P8–P9 follow. No push or CI action.
