# P6-02: detached operation and message ownership

Copyright (C) 2026 Qore Technologies, s.r.o.

The [original lifetime finding](p6-operation-lifetime-finding.md) is fixed. On
parent `ae5df37`, an operation extracted from a temporary WebService lost its
input/output messages and could lose its namespace context. Standalone zero-part
messages, header descriptions and sample helpers also lost their borrowed
contexts. The four initial regressions fail against that parent; raw reductions
and logs are in `/tmp/wsdl-p6-02-operation-ownership/`.

The [implemented ownership graph](../../design/wsdl-operation-ownership.md) uses
strong references for public handles' required dependencies. Saved legacy weak
references are promoted on reconstruction, without retaining a second service
or inventing missing objects. Shared header identities survive saved graphs.
Zero-part maps are initialized as empty hashes, including old saved empty
messages. QName attribute normalization builds fresh records so typed public
constructor inputs have the same semantics as parsed XML.

## Verification

`test/wsdl-operation-ownership.qtest` passes 11 cases / 405 assertions:

- Detached operations, zero-part messages, header descriptions and sample helpers.
- Source, binary-saved and structured-saved graphs; old `_weak` member shapes.
- Both actual SOAP bindings and both directions, shared headers, declared faults,
  one-way input, recursive records, strict global wildcard values and invalid values.
- Malformed reconstruction with exact errors and successful restoration afterward.
- Exact destructor counts for namespace/type cycles and all four message owners
  after normal release, failed serialization, a raised construction error and cancellation.
- Four concurrent independently restored graphs synchronized with queues, including
  distinct namespace/value state and deterministic worker cleanup.
- Real local HTTP through both service ports using detached operations and saved
  providers from different source graphs, preventing a routing service from masking
  missing ownership. Request/response values and headers are asserted.

The existing bounded sample generator can reject a recursive nonempty candidate
with `XSD-SAMPLE-ERROR`; this is its documented candidate-generation contract,
not a new lifetime failure. The regression checks that the detached helper can
still generate an independent simple message before and after that error.

Thirty affected suites pass 411 cases / 6,670 reported assertions. They include
namespace/recursive/provider ownership, saved providers, sample generation,
SOAP/client/handler suites and Cargo/CDA consumers. Seven comparator assertion
failures are deliberately caught by `soap.qtest`; all cases pass. WSDL documentation
builds without warnings or errors.

The entire new ownership suite also passes under Valgrind using the frozen Qore
ELF with `-b --enable-debug` and `QORE_PCRE2_NO_JIT=1`: zero errors; zero definite,
indirect and possible leaks; no suppressions. The run took 313.5 seconds and
retained 128,833 reachable bytes in process-global runtime/library state.
No C++ source was changed.

Run the regressions with the local module path:

```sh
qore -b --enable-debug test/wsdl-operation-ownership.qtest
qore -b --enable-debug test/wsdl-namespace-ownership.qtest
qore -b --enable-debug test/wsdl-message-providers.qtest
qore -b --enable-debug test/wsdl-sample-instances.qtest
```

Complete legacy/native surveys and typed coverage retain the parent's results:
2,096 native valid directions pass; 12 documented legacy projection losses remain
explicit; 176 invalid-source directions stay separately classified. The strict
legacy P5 selection still exits 1 for those 12 losses. All 16 independent coverage
and 17 survey harness tests pass.

[P6-02-validation.json](P6-02-validation.json) records source/runtime hashes,
fixture provenance, commands, final reports and memory results. All
[62 audit checks](audits/P6-02-operation-ownership.md) are individually classified:
18 Pass, 44 N/A, zero Fail. No installation, push or main-Qore mutation occurred.
P6 component/reference validation, parts/headers and HTTP/MIME acceptance remain
open, followed by P7–P9; this increment closes only the recorded ownership defect
and its directly related empty-message/typed-construction failures.
