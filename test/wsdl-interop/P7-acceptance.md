# P7 SOAP processing and HTTP acceptance

Copyright (C) 2026 Qore Technologies, s.r.o.

P7 is accepted on the main `develop` candidate at `eefcf5f`. The installed Qore runtime is `922cd9bb0`,
with `build-debug` clean-rebuilt against it. Acceptance covers SOAP 1.1 and 1.2 envelope processing, node roles
and mandatory headers, faults, and the SOAP HTTP binding for the advertised client and handler roles. Attachment
reference semantics, legacy SOAP encoding and the 26 W3C assertions routed there remain P8. Required
cross-platform CI, the performance benchmark and the remaining gap register remain P9.

The module makes no formal WS-I Basic Profile conformance claim. WS-Addressing is not implemented. Its 49
dependent profile requirements are recorded as gaps, not as not applicable, under the approved scope decision.
Unknown mandatory WS-Addressing headers are rejected by the generic `mustUnderstand` processing.

| P7 requirement | Implementation and executable evidence |
| --- | --- |
| Envelope namespace, version, Header/Body structure and order, document restrictions, qualified header blocks, processing attributes, version mismatch | P7-01 and P7-02: [soap-envelope](../soap-envelope.qtest), [soap-header-processing](../soap-header-processing.qtest), [test_soap_envelope.py](test_soap_envelope.py), [test_soap_processing_attributes.py](test_soap_processing_attributes.py); malformed and unexpected messages, prefix independence, both versions. [Evidence](soap-envelope-evidence.md), [attributes](soap-processing-attributes-evidence.md). |
| Roles, actors, `mustUnderstand`, relay, targeted headers, explicit handler capabilities, intermediary and ultimate receiver | P7-03 and P7-07: [soap-node](../soap-node.qtest), [soap-node-http](../soap-node-http.qtest), [soap-node-uri](../soap-node-uri.qtest), [soap-handler-faults](../soap-handler-faults.qtest), [soap-processing-priority](../soap-processing-priority.qtest), [test_soap_node.py](test_soap_node.py), [test_soap_handler_faults.py](test_soap_handler_faults.py), [test_soap_processing_priority.py](test_soap_processing_priority.py). Unknown mandatory targeted headers are never silently ignored. [Evidence](soap-node-evidence.md), [handler faults](soap-handler-fault-evidence.md). |
| Conforming faults: version codes, QName subcodes, multilingual reasons, roles, nodes, actors, details, declared and header faults | P7-04 to P7-06 and P7-08: [soap12-faults](../soap12-faults.qtest), [soap11-faults](../soap11-faults.qtest), [soap-fault-data](../soap-fault-data.qtest), [soap-fault-identity](../soap-fault-identity.qtest), [soap-http-faults](../soap-http-faults.qtest), [test_soap_faults.py](test_soap_faults.py), [test_soap_fault_data.py](test_soap_fault_data.py), [test_soap_http_faults.py](test_soap_http_faults.py). Every generated fault validates against the pinned W3C schemas. |
| SOAPAction and SOAP 1.2 `action`, content types, charsets, HTTP methods and statuses, one-way and empty responses | P7-09 to P7-11 and P7-13: [soap-oneway](../soap-oneway.qtest), [soap-actions](../soap-actions.qtest), [soap-http-binding](../soap-http-binding.qtest), [soap-response](../soap-response.qtest), [test_soap_oneway.py](test_soap_oneway.py), [test_soap_actions.py](test_soap_actions.py), [test_soap_http_binding.py](test_soap_http_binding.py), [test_soap_response.py](test_soap_response.py), [test_multipart_reader.py](test_multipart_reader.py). |
| Transport failures, interruption, cancellation, exception-safe cleanup and full duplex | P7-12 and P7-14: [soap-duplex](../soap-duplex.qtest), [test_soap_transport.py](test_soap_transport.py), [test_soap_duplex.py](test_soap_duplex.py): same-client recovery after every failure, deterministic teardown, and buffered full-duplex exchanges of 8 MiB. [Transport](soap-transport-evidence.md), [duplex](soap-duplex-evidence.md). |
| Independent-peer exchanges in both directions | Python peers for every increment, plus the pinned CXF 4.1.3 contracts ([test_cxf_peer.py](test_cxf_peer.py)) and known-good messages ([soap-known-good](../soap-known-good.qtest)). |
| Async I/O client | [SoapClientIo](../../qlib/SoapClientIo/SoapClientIo.qm) over `HttpClientIo` reuses the same WSDL model, envelope validation, node processing and fault grammar: [soap-client-io](../soap-client-io.qtest), [design](../../design/soap-async-io-client.md). |
| Every applicable WS-I and W3C assertion has an executable test or a reviewed rationale | [assertion-ledger.json](assertion-ledger.json), enforced by [verify_ledger.py](verify_ledger.py): 493 rows (140 W3C, 353 WS-I BP 1.2/2.0), 388 covered with 815 verified executable mappings, 30 not applicable with specification-based rationale, 49 recorded WS-Addressing gaps, 26 routed to P8. [Evidence](assertion-ledger-evidence.md). |

## Phase-boundary validation

All numbers come from one run on one runtime. The libqore, qore and native XML module hashes are identical
before and after it; see [P7 acceptance validation](P7-acceptance-validation.json).

- All 271 Qore suites pass: **3,581 cases / 172,677 assertions**. The 24 SOAP suites contribute 245 cases and
  17,628 assertions.
- 176 of 178 independent Python gates pass. `test_ieee_conversion.py` and `test_ieee_scalars.py` fail on the
  Qore core NaN-boxing defect, which is still present in `922cd9bb0` (negative doubles with magnitude in
  [2^1021, 2^1023) decode as a short string or nothing; see `/tmp/qore-nanbox-negative-double/README.md`). They
  are P5 scalar gates outside P7's scope, remain failing, and must pass before final acceptance. There is no XML
  workaround.
- All 16 corpus commands meet their expected outcomes. All six reports are semantically unchanged from P7-13.
- The CMake-built AOT modules (WSDL, SoapClient, SoapHandler, SoapClientIo) are verified as the loaded modules.
  Nine compiled suites pass **64 cases / 2,650 assertions**.
- Documentation builds with no warnings or errors, and astparser reports no errors on the ten Qore files changed
  since P7-13. The assertion ledger verifier passes.
- Valgrind on `test/xml.qtest` (C++ changed in `6cc6352`) passes 26 cases / 192 assertions, with zero bytes
  definitely, indirectly or possibly lost and no invalid accesses. Its remaining conditional-jump reports are in
  generated code: the PCRE2 JIT class reproduced in C at P2-10. They are not suppressed, and the memcheck is not
  claimed clean.

The full-suite triage before acceptance fixed or correctly re-scoped 11 gates: stale SOAP 1.2 fixture actions,
NOTATION identity expectations, and the P7-11 multipart status. It also restored the pinned corpus extraction and
fixed one performance defect, the recompiled constant regexes (`8f1f8b2`). Hang guards with thin headroom were
recalibrated after the approved performance pass (`eefcf5f`). See `EXECUTION.md`.

P8 is next: attachment reference semantics and legacy SOAP encoding. No install, push or CI trigger.
