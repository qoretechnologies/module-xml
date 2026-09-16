# P6-03 WSDL declaration identity evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

The previous parser accepted roots outside the WSDL namespace, silently replaced
duplicate declarations, and omitted empty services/port types. Namespace removal
and grouping happened before those checks. An expanded-name reader pass now
validates document/declaration identity before grouping or dependency retrieval;
normalized NCNames remain the keys used by construction. Empty component maps
are initialized before child traversal.

The requirements come from [WSDL 1.1 sections 2.1–2.7](https://www.w3.org/TR/wsdl.html)
and its [published schema](https://schemas.xmlsoap.org/wsdl/2003-02-11.xsd).
The schema is vendored with its original notice and hash-pinned in
`regressions/wsdl-declarations/oracle-cases.json`. The 25 authored oracle documents
cover root namespace, required NCNames, duplicate scopes, empty declarations and
separate component symbol spaces. Pinned Xerces 2.12.2 agrees on all outcomes.
Schema agreement establishes these declaration rules, not complete binding semantics.

Run with the local XML and WSDL modules and debugging enabled:

```sh
qore -b --enable-debug test/wsdl-declaration-identity.qtest
python3 -B test/wsdl-interop/test_wsdl_declarations.py -v
```

The focused Qore suite passes 9 cases / 89 assertions. The final affected gate
passes 31 suites / 420 cases / 6,750 reported assertions; a final supplemental
name/root check raises the aggregate to 6,759 assertions. The module's only change
after that gate relocates a Doxygen paragraph marker, verified against the tested
source hash. The final test has also been rerun. Existing tests include saved
providers, actual SOAP 1.1/1.2 HTTP consumers, cancellation and concurrent restoration.
The WSDL documentation target completes without warnings/errors.

The earlier 196-suite broad run passed 195 suites and hit its 600-second deadline
in `wsdl-schema-whitespace`. A bounded 1,200-second paired diagnostic subsequently
completed that entire test on both pushed parent and current implementation:
5 cases / 85 assertions each, 738.264 and 739.238 seconds respectively, without
warnings/errors. This does not turn the initial timeout into a passing run.
Both native stack samples were in Qore's collector. The independent runtime-cost
investigation, candidate analysis and complete reproduction are recorded in
`/tmp/wsdl-dgc-namespace-owner-cost/README.md` for the separate Qore workstream.
Ownership is retained; no workaround or core mutation was made. These timings
are diagnostics, not verified Release benchmarks. Runtime performance remains
part of P9 acceptance.

All six complete corpus reports differ from P6-02 only in version metadata.
Native mode retains 2,096 valid successful directions and the 176 required invalid
source rejections. Legacy retains 2,084 successes and twelve explicitly reported
projection losses; strict P5 legacy still exits one as expected. All 16 coverage
and 17 survey unit tests pass. An initial concurrent coverage-test run exceeded
its existing 60-second subprocess deadline; the complete subsequent run passed
without changing that deadline. No corpus fixture, selection or expectation changed.

Artifacts: `/tmp/wsdl-p6-03-component-grammar/`; source/runtime hashes and commands
are in [validation](P6-03-validation.json). All 62 [audit checks](audits/P6-03-declaration-identity.md)
pass or are N/A. No C++ change, installation or main-Qore modification.

This completes root/declaration identity and empty-component preservation only.
Full grammar, imported component/QName resolution, operation signatures, binding
parts/headers/faults and HTTP/MIME behavior remain P6 requirements. P7–P9 remain open.
See [implemented design](../../design/wsdl-declaration-identity.md).
