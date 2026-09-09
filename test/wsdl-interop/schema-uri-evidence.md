# P3-37: native schema URI identity

Copyright (C) 2026 Qore Technologies, s.r.o.

The preserved [original finding](schema-uri-findings.json) is closed by an
executable test using its exact schema and resource bytes. The original JSON
remains historical evidence. Raw Unicode/space schema locations and their escaped
forms now identify the same resource; reserved percent escapes retain their
meaning. The implementation is described in
[XML schema resource URI identity](../../design/xml-schema-uris.md).

## Requirements and root causes

XSD 1.0 [anyURI](https://www.w3.org/TR/xmlschema-2/#anyURI) applies whitespace
collapse and the [XLink 1.0 escaping procedure](https://www.w3.org/TR/2001/REC-xlink-20010627/#link-locators).
[XML Base](https://www.w3.org/TR/xmlbase/) supplies the element base URI and
recommends preserving unescaped LEIRIs in base-access APIs. The resolver follows
[RFC 3986 section 5.2](https://www.rfc-editor.org/rfc/rfc3986#section-5.2), including
empty path segments and dot-segment removal. No source document is rewritten.

The native root causes were unescaped XSD references, percent decoding before URI
resolution, filesystem normalization applied to URI paths, and an extended-parser
NUL-terminator omission. Runtime schema hints also bypassed escaping without a
base, split a single noNamespaceSchemaLocation into tokens, selected only one of
the two hint attributes, and ignored the streaming reader's document locator.
The checked dependency patch fixes these boundaries directly. Ordinary decoded
public URI parsing remains compatible, and actual filesystem bases retain their
filesystem semantics.

The Qore HTTP resource loader now escapes direct raw URLs once and uses the
existing pre-encoded client option. Core prerequisite `3b70f8ccd` removes the
incorrect rejection of the unreserved tilde in that option. Both changes assert
the exact request target against an independent raw peer. Optional schema warning
callbacks use detailed debug logging so caught diagnostics do not corrupt stdout.

## Independent validator evidence

[schema-uri-validator-defects.json](schema-uri-validator-defects.json) retains the
complete twelve-schema native/Xerces comparison, unchanged schema bytes and hashes,
and six explicit Xerces XML Base false negatives. The document checks for those
six schemas remain unreachable, not passing. The native test accepts value 17 and
requires PARSE-XML-EXCEPTION for bad integer content in every source schema.

Pinned Xerces-J 2.12.2 JAR SHA-256 is
`6fc991829af1708d15aea50c66f0beadcd2cfeb6968e0b2f55c1b0909883fe16`.
Bytecode inspection of `XSDHandler.doc2SystemId` shows that include, import and
redefine resolve against the SchemaDOM document URI rather than XML Base.
The captured inspection is `/tmp/wsdl-p3-37-xerces-XSDHandler.bytecode`.
No alias for the incorrect URI or modified source is supplied to make Xerces pass.

The offline worker separately corrects Java's legacy URI resolution and catalog
key comparison. It retains raw components, rejects duplicate URI aliases even with
identical bytes, and refuses missing or malformed resources without external I/O.
The five oracle methods cover 22 exact-identity jobs, two file aliases, two duplicate
manifests, four missing/malformed references and the twelve component schemas.
All seven existing independent-worker tests also pass with javac warnings treated
as errors. Captured runs use Java `25.0.4.1+1`.

## Verification

All Qore runs use the local Debug module, `--enable-debug`, the isolated core in
`/tmp/wsdl-core-date`, and the environment in `/tmp/wsdl-core-date-env.sh`.
Debug and Release builds both use prefix `/usr`; neither is installed to test.

| Gate | Result and evidence |
| --- | --- |
| Direct native URI and schema probes | 106 URI/XML Base, 12 component and 24 runtime-hint checks; all 142 pass. `/tmp/wsdl-p3-37-final-audit-probe.log` |
| Allocation failures and recovery | 29 checks, including every allocation in both tested URI/base operations. `/tmp/wsdl-p3-37-final-audit-allocation.log` |
| Direct native Valgrind | Both probe executables have zero errors, zero bytes at exit and no suppressions. Corresponding `-memory.log` files. |
| Live URI regressions | Six methods pass in AST, IR, JIT and tiered modes. 36 file/component fixtures and 28 HTTP fixtures include positive and invalid integer inputs; 14 HTTP reference forms assert 56 exact requests. `/tmp/wsdl-p3-37-final-uri-modes.json` |
| Existing schema resources | Seven HTTP/HTTPS/policy/catalog/recovery methods pass in Debug and Release. `/tmp/wsdl-p3-37-final-schema-resources.log`, `/tmp/wsdl-p3-37-release-resource-tests.log` |
| Reader modes/timezones | Eight runs, 96 cases / 1,528 assertions pass. `/tmp/wsdl-p3-37-final-reader-modes.json` |
| Full XML gate | 84 suites, 902 cases / 33,321 reported assertions pass without warnings. `/tmp/wsdl-p3-37-final-xml-gate.json` |
| Existing QName oracle | 300 documents / 30 schemas pass all six native paths and pinned Xerces with exact values. `/tmp/xml-qname-union-validator-ob2hlq_e`; fixture SHA-256 `4504254bd15b7e1ce2e33ca48893d6bb1a48fc994994d2ad5dfdbdeec13d46ad` |
| Provider configuration | 20 methods pass, including a QName-fixed but URI-broken installed library, fixed backports, offline source integrity, source switching and cross builds. `/tmp/wsdl-p3-37-final-audit-provider.log` |
| Affected Qore Valgrind | 51 cases / 914 assertions pass with zero errors and zero definite/indirect/possible lost bytes. `/tmp/wsdl-p3-37-final-native-memory.json` |
| HTTP Valgrind | Three processes cover exact URI targets, raw/encoded direct URLs and optional-import failure/recovery; zero errors and zero lost bytes, no suppressions. `/tmp/wsdl-p3-37-final-http-memory/` |
| Survey unit tests | All 15 methods pass. `/tmp/wsdl-p3-37-final-survey-unit.log` |
| Coverage unit tests | 13 methods run; exactly the two previously recorded P6-selected-binding-version subcases fail. They remain failures. `/tmp/wsdl-p3-37-final-coverage-unit.log` |
| Both-version corpus | Final raw survey and strict adjudicated report are structurally identical to P3-36. `/tmp/wsdl-p3-37-final-xml-{survey,coverage}.json` |
| Builds/documentation | Debug, Release and docs-module complete without compiler or documentation warnings/errors. Final build logs use `/tmp/wsdl-p3-37-final-audit-`. |

Valgrind runs disable PCRE2 JIT with `QORE_PCRE2_NO_JIT=1`; Qore executes in JIT
mode with signals disabled (`-b`). Known unsuppressed DWARF and SSSD environment
warnings remain recorded P9 findings. The native local-file loader's interruptible
I/O review is also still P9 work. The existing SOAP suite's reported assertion
accounting anomaly is preserved; the reported total is not presented as a count of
independently inspected assertions.

An oracle run overlapped an earlier Debug module relink and failed with a truncated
module load. Its failed log is retained; after the build completed, the oracle,
QName comparison and both corpus reports all passed their checks. A first make
invocation also retained its pre-regeneration target graph for a newly added test
target; a fresh invocation built it. Neither event required a source workaround.

The final audit is [P3-37-schema-uris.md](audits/P3-37-schema-uris.md). Final source,
dependency and artifact hashes are captured in `/tmp/wsdl-p3-37-final-manifest.json`.
P3 QName/list/union WSDL integration and the later phases remain open.
