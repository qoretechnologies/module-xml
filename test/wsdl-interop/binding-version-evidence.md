# P6-01: binding-specific SOAP versions

Copyright (C) 2026 Qore Technologies, s.r.o.

The independent dual-binding measurement regression previously failed both SOAP
1.1 serialization directions: `Namespaces.hasSoap12()` reflected every namespace
declaration in the document, so selecting `Soap11` still emitted a SOAP 1.2
envelope. Fault defaults and version queries had the same root cause. Fault
interpretation also used this document-wide flag instead of the incoming envelope.
The previous failing results remain in P5-22b evidence; they have not been rewritten.

The [implemented design](../../design/wsdl-binding-version.md) records scoped
extension resolution, immutable per-binding metadata, defaults, saved-object
compatibility and the existing explicit response-version override. This increment
implements binding-derived defaults; it does not claim P6 component acceptance or
P7 envelope/version-mismatch enforcement. General operation ownership, component
resolution, headers/parts and HTTP/MIME completion remain P6 work.

## Requirements and tests

| Requirement | Evidence |
| --- | --- |
| Expanded binding name selects SOAP protocol | WSDL 1.1 section 3.3 and SOAP 1.2 binding extension section 3; `versions`, `scopes`, `invalid` in `wsdl-binding-version.qtest` |
| Selected version controls request, default response and fault | Both binding orders, both directions, media types and fault envelopes; independent measurement regression |
| Unused declarations do not select a version | SOAP 1.1-only and HTTP-only services retain unused SOAP 1.2 declarations; capability queries remain false |
| Lexical prefix/default scope and sibling isolation | Binding-local and extension-local declarations, default namespaces, source and saved services |
| Saved metadata and honest legacy ambiguity | New standalone bindings retain versions; an old standalone shape without metadata raises `WSDL-BINDING-ERROR`, while explicit-version serialization remains available |
| Invalid protocol extensions reject | Missing/duplicate/unknown/unqualified extensions, SOAP/HTTP attribute mixing, invalid transport/style; valid construction and output after each rejection |
| Fault interpretation uses received namespace | Authored SOAP 1.1/1.2 faults, both selected bindings, prefixed/default envelopes and misleading unused declarations retain reason text |
| Real selected service ports | Loopback SoapClient/SoapHandler for both actual ports; inspect request/response envelope, content type and value, with bounded calls and deterministic server cleanup |
| Existing complex message behavior | `soap.qtest` checks the full original golden payload on both actual named bindings; only the version-dependent expected envelope differs |

## Validation

Run with local modules and `qore -b --enable-debug`:

```sh
qore -b --enable-debug test/wsdl-binding-version.qtest
python3 -B test/wsdl-interop/test_coverage.py -v
python3 -B test/wsdl-interop/test_survey.py -v
```

The new suite passes 7 cases / 946 assertions. Eight affected existing Qore suites
pass 217 cases / 1,621 reported assertions, including the extended multi-binding
golden check. `soap.qtest` intentionally catches seven comparator assertion
failures; all 22 cases succeed. All 16 independent coverage tests now pass,
including the formerly failing SOAP 1.1 subtests. The 17 survey harness tests pass.
WSDL and native documentation targets build without warnings or errors.

Both complete survey modes retain exactly the parent result outside runtime
version hashes. Complete native, legacy and strict P5 coverage also retain the
parent accounting: 2,096 native directions assessed successfully; 12 explicitly
recorded legacy projection failures remain, with 176 invalid-source directions
separately classified. Legacy P5 strict coverage must exit 1 for those 12 losses;
it is not counted as a conformance pass.

[P6-01-validation.json](P6-01-validation.json) records exact source/runtime/test
hashes, commands, report hashes and parent comparisons. Raw logs and complete
reports are in `/tmp/wsdl-p6-01-binding-version/`. The frozen Qore and XML runtime
paths are included in the validation commands. No C++ code changed, so Valgrind
was not required. No installation or push was performed.

All [62 audit items](audits/P6-01-binding-version.md) are individually classified:
18 Pass, 44 N/A, zero Fail. The next P6 increment addresses the separately
reproduced [detached operation ownership defect](p6-operation-lifetime-finding.md).
