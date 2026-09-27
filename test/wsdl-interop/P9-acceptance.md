# P9 acceptance: coverage in CI and the final gap register

Copyright (C) 2026 Qore Technologies, s.r.o.

**Status: pending CI confirmation.** All criteria are met locally with the Qore installed on 2026-09-26
(466733bc4). The final pipeline needs CI images built with that Qore. The images of 2026-09-25 (Qore 331b37b9e)
predate three fixes that the new AOT pass depends on: 486392806 (AOT stack frames), 820305238 (qmod resource
directories) and 466733bc4 (FileLocationHandler octets). P9a is accepted separately; see
[P9a acceptance](P9a-acceptance.md).

## P9 requirements

| Requirement | Evidence |
| --- | --- |
| Adjudicated regressions and the Python suite run in mandatory offline CI, with explicit dependency setup and archived results | P9c-01: the complete Python suite runs in six shards per distribution. A verify job fails on any missing, duplicate, skipped or failed test, and the results are archived for 30 days. P9c-03/04: the second validator is pinned (lxml 6.1.0 with libxml2 2.14.6, installed by hash). P9c-05/06: one module-xml pipeline runs at a time. Nothing is downloaded at run time. See [Continuous integration](README.md#continuous-integration). |
| Ubuntu and Alpine; the development modules are loaded; serialization, lifecycle and provider tests | The Qore and Python jobs run on both distributions from a Debug build of the checkout; `check-i18n.sh` and the AOT preflight load the build's own modules. 219 qtests exercise `Serializable` round trips of parsed schemas and services. `SoapClient`, `SoapHandler`, `soap-client-io` and `wsdl-identity-tuple-lifecycle` cover client and server lifecycles. The Cargo and CDA provider suites run with the rest. |
| Compiled modules and memory checking | P9c-08: the qtest jobs rerun all 256 tests that load in-repo modules against the AOT-compiled modules of the same build. `test-valgrind` runs the 43 native tests with `--error-exitcode`, treating definite and indirect leaks as errors (`QORE_PCRE2_NO_JIT=1`). The deep QName AOT stack failure recorded since P5-15 is resolved by Qore 486392806 (P9g-01): 24,280 instead of 88,616 bytes per recursion level. |
| Deterministic generated, boundary and mutation cases with recorded seeds and independent references | Scalar values (calendar, temporal, duration and IEEE lexicals). Particle groups (complete finite languages and Xerces). Namespace scopes (P9d-02, expat). SOAP faults (P9d-03, the W3C envelope schemas and lxml). Multipart attachments (P9d-04, Python's `email` parser). SOAP bindings (P9d-05, WSDL 1.1 section 3.5 and the SOAP encodings). Each generator pins its seed and a SHA-256 of its cases, and is mutation-tested. |
| Requirement identifiers, fixture hashes, expected and actual results, fix commits and test locations; counts cannot improve by losing cases | [assertion-ledger.json](assertion-ledger.json) has 493 requirement rows: 459 covered, each mapped to tests, and 34 not applicable with approved rationales (below). `verify_ledger.py` runs in every suite run (P9d-01). The coverage reports record input, schema and module hashes and the oracle versions. |
| Audits, documentation, and a separate current result set beside the preserved baseline | Every commit has an audit in [audits/](audits/). Release notes and durable design documents are in `design/`. P9f-01 published [current-report.json](current-report.json), [coverage-report.json](coverage-report.json) and [coverage-preserve-types-report.json](coverage-preserve-types-report.json) with the README's "Current results"; the 2026-09-07 baseline is unchanged. |
| Performance tracked by a deterministic benchmark, not by timeouts | P9b: [benchmark/](benchmark/README.md) holds pinned workloads, a Release reference and byte-identical output checks. Gate timeouts are hang guards with measured headroom. |

## Final acceptance criteria

| Criterion | Evidence |
| --- | --- |
| Zero unclassified findings or missing corpus dependencies | The corpus and every import resolve from pinned, hash-checked sources ([corpus/](corpus/), `catalog.json`). Every original finding is classified in [adjudications.json](adjudications.json). The ledger has no unmapped row. The libxml2 2.15 `xs:Name` disagreement is adjudicated (P9h-01). |
| Zero rejected valid inputs; zero serialization failures or invalid outputs; no value, namespace, type, order or binary-content loss | With `preserve_types` (native capture), all 2,096 valid corpus directions are preserved exactly, compared as typed values with an independent observer. No serialized output is rejected by libxml2 or Xerces. The default projection keeps its 12 documented, approved losses (see [P5 acceptance](P5-acceptance.md)), which the report retains as failures. |
| Invalid inputs rejected for the intended reason | All 176 invalid-source corpus directions are rejected with the intended exception category, and the strict selection (144 WSDLs, 1,388 directions) passes. The generated mutations of P9d are rejected. |
| Applicable protocol and binding requirements pass in both directions | Every applicable ledger row is covered: P6 bindings, P7 SOAP processing and HTTP, P8 attachments and P9a WS-Addressing, including live CXF exchanges in both directions. |
| All required tests pass without warnings or errors, with no regression skips | Qore 466733bc4: 299 qtests pass without warnings, 256 AOT test files pass, 43 native tests are valgrind-clean, and 556 Python tests pass in 6 shards. The only remaining skip is the Salesforce credentials gate (below), not a regression skip. |
| Deliberately unsupported optional capabilities are explicit, tested and approved | 34 not-applicable ledger rows. 30 are P7 rows: W3C obligations on specification authors, WS-I R1121/R1122 (cookies), R3002/R3003/R3010/R3011/R3100 (UDDI) and R9999. 4 are P9 rows: R1203/R1204 in Basic Profile 1.2 and 2.0 (non-addressable service instances, approved 2026-09-24). XSD name characters follow XML 1.0 Second Edition only (decided 2026-09-26). Omitted RPC accessors are absent values (decided 2026-09-25). |

## Environment gates outside the plan

`Salesforce.com.qtest` skips its live account case without Salesforce credentials, as intended (confirmed
2026-09-27). It predates this plan and does not cover WSDL/SOAP requirements.

The litmus WebDAV compliance suite is no longer skipped: the Ubuntu qtest job installs `litmus` and sets
`QORE_XML_REQUIRE_LITMUS=1`, so `webdav_FsWebDavHandler_litmus.qtest` fails instead of skipping there (decided
2026-09-27). Alpine has no `litmus` package, so the test skips explicitly there. Running it found WebDAV defects
that are now fixed (P9k-01), and all five litmus suites pass.

## Open

- A pipeline with CI images built from Qore 466733bc4 or later, including the P9c-08 jobs.
