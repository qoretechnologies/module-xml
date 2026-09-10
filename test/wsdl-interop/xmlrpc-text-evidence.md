# XML-RPC character data evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

P3-45 closes the XML-RPC text boundary deferred in P3-11. The implemented
[value contract](../../design/xmlrpc-character-data.md) follows XML 1.0 character
and line-ending rules and the XML-RPC string/default-string definitions.
It preserves Qore's historical empty-value and numeric/date extension policies.
This is not a claim of complete XML-RPC or SOAP protocol conformance.

Root causes and corrections:

- Literal CR was emitted directly and normalized to LF. All XML-RPC character
  data now uses validated XML escaping and CR references.
- Whitespace-skipping reads discarded scalar data and required a single text
  node. The collector joins text/CDATA while ignoring comments and processing
  instructions; nested elements reject. Untyped whitespace remains a string.
- Empty struct keys were replaced with a colliding sentinel. Empty names now
  survive; duplicate keys release the old value before retaining the last one.
- Depth comparisons mishandled expanded empty values and responses. The shared
  value reader preserves following siblings, and complete document validation
  consumes empty response boundaries before checking trailing XML.
- ASCII markup was appended into UTF-16 buffers. Generation now uses an ASCII
  compatible working encoding and converts the complete document once.
- The signed 32-bit lower bound excluded -2147483648. The integer wire type now
  includes it. Legacy response encoding wrappers retain the correct arguments.
- Optional logging was invoked even when no logger existed. Invalid requests now
  retain their XML-RPC fault without requiring a logging callback.

The HTTP peer checks also found two Qore prerequisites: buffered request bytes
lost the parsed charset, and a reused connection's protocol fields inherited the
previous body charset. Qore develop commit `38e8e0e52` fixes both, with 105 cases /
987 assertions and a clean focused Valgrind run. Main source and the isolated
Debug snapshot were byte-identical for the changed files. Nothing was installed
or pushed. XML merge `aec7c38` integrates origin/develop `c1403ef`, retains the
scalar hash widening and aligns its mixed-content tests with XSD validation.

Verification:

- 97 affected XML/SOAP suites pass: 998 cases and 38,810 reported assertions.
  The existing soap.qtest comparator negatives account for three intentionally
  caught unsuccessful assertions; all its test cases pass, as documented in P1.
- XML-RPC text: 13 cases / 226 assertions in AST, IR, JIT and tiered modes.
- Independent peer: four Python methods in every execution mode. Expat and
  xmlrpc.client decode 256 generated call/response documents and 16 fault
  documents from 144 rows across four encodings and four formatting modes.
- Real HTTP checks cover nine Qore-client exchanges and 25 Qore-handler exchanges,
  including exact CR-bearing fault messages. Readiness follows listener creation
  and an explicit control request; sockets and subprocesses have bounded deadlines.
- Valgrind passes XML-RPC text, xml, XmlRpcHandler, XmlRpcClientIo and XmlRpcClient,
  plus all three Qore peer processes. Every run has zero errors and zero definite,
  indirect or possible loss, with no suppressions. QORE_PCRE2_NO_JIT=1 disables
  PCRE2 JIT using its supported runtime control.
- All 2,411 survey rows, stage accounting and 144 diagnostic failure identities
  are unchanged. The strict gate covers 130 WSDLs / 1,260 directions with no
  selected failures. The two existing P6 binding-version Python assertions remain
  failures, assigned to P6; no test was skipped or relabelled as passing.

Independent reference identity for this run: CPython 3.14.7, Expat 2.8.1,
`xmlrpc.client.py` SHA-256
`ca052dc6dc70af60518c94cfaeaf9b3dfcc7d82629d0323e0417fba40839978b`.
The stdlib marshaller emits literal CR: `A\rB` decodes as `A\nB`. The separate
`test_reference_marshaller_literal_cr_reduction` records that defect; authored
incoming fixtures emit `&#13;` under the XML rule. No upstream fixture is modified.

Evidence logs use `/tmp/wsdl-p3-45-`: `full-gate-reviewed.log`,
`merge-features-native-validation.log`, `modes-final.log`,
`reviewed-valgrind*.log`, `peer-valgrind.log`, `peer-valgrind/*.log`,
`survey-final.json`, `coverage-final.json`, `survey-tests.log` and
`coverage-tests.log`. The final manifest records runtime and source hashes. The native XML module SHA-256 is
`6cb846f9b9a0e2748d8937a767c6e0d8737300153580976198a2a6cd71c932dc`;
the Debug core library SHA-256 is
`f8ed2bd8f96dea90d742f198324e93173d7438ffc7ba5b477ead92b2e333c6b9`.
The [full audit](audits/P3-45-xmlrpc-character-data.md) records all 62 checks
with 25 Pass, 37 N/A and no failures.

References: [XML-RPC specification](https://xmlrpc.com/spec.md),
[XML 1.0 line ends](https://www.w3.org/TR/REC-xml/#sec-line-ends),
[XML character production](https://www.w3.org/TR/REC-xml/#charsets),
[HTTP/1.1 message parsing](https://www.rfc-editor.org/rfc/rfc9112.html#section-2.2).
