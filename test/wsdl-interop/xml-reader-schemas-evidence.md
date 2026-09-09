# Reader schema attachment and resource evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

This increment repairs the native reader API and shared XSD resource loader used
by scalar validation. It does not complete P3 or change the production WSDL module.

## Contracts and root causes

`schemaValidate(location)` retains its historical file/URI meaning; the new
`schemaValidateString(text)` explicitly accepts XSD text. Constructor text schemas
use the same attachment path. The old API detached an existing validator before
compiling its replacement, allowing invalid integer XML after a missing schema.
The retained reproducer is `/tmp/wsdl-p3-36-attach-baseline.qr`. The fixed reader
compiles first, rechecks state after reentrant callbacks, and keeps every schema
alive until its referring native context is freed, including failed attachment.
See the implemented [ownership design](../../design/xml-reader-schemas.md).

The prior native file loader bypassed parse restrictions and sandbox path policy.
A shared scoped resource context now checks files, catalogs, network destinations
and redirects, and preserves callback exceptions without unchecked fallback.
Each resource owns a separate stream; nested loads restore the outer context.
HTTPS verifies certificates/hostnames using Qore's configured OpenSSL trust store.
Authorized local files retain libxml2's native loader and compression behavior;
this change does not claim to make that existing file loader fully interruptible.
Its blocking-I/O review stays explicitly assigned to P9.

The independent HTTP/1.0 redirect fixture exposed Qore's persistence bug, fixed
separately in core commit `1b357c9bd`. TLS negatives exposed an unconditional Debug
stderr diagnostic, fixed separately in core commit `8bbe7eed1`. Both have full
core audit reports and affected Valgrind tests. Main development proceeded
concurrently; only the exact separately tested core files were committed, without
pushing or installing for tests.

## Verification

- `xml-reader-schemas.qtest`: 12 cases / 191 assertions covering text/file/URI and
  stream attachment, integer boundaries, exact values, successful and failed
  replacement, started/tree/EOF states, UTF-8/16 and Latin-1 encodings, Unicode
  filenames, NUL rejection, coarse and path/IP policies, nested/reentrant callbacks,
  empty/oversized streams, original partial-read errors, interruption and recovery.
- AST/IR/JIT/tiered across UTC and Europe/Prague: eight runs, 96 cases / 1,528 assertions.
- Independent HTTP/HTTPS/catalog tests: seven Python methods, including a batch
  of malformed schema, HTTP 404 and successful recovery in one Qore process.
  Trusted TLS succeeds; an untrusted certificate fails before an HTTP request.
- The isolated installed-libxml2 2.12.10 compatibility build passes the attachment
  and existing callback suites, all seven resource methods and two explicit FTP
  methods. FTP checks exact resource paths, relative includes, binary transfers,
  invalid XML, missing resources, policy rejection and recovery. The production
  CMake probe still rejects this unpatched dependency's known QName defects.
- The 300-document / 30-schema QName union matrix now checks explicit text and file
  attachment as well as DOM, constructor reader and cursor paths. All native paths
  agree with pinned Xerces-J 2.12.2 and preserve exact text/attribute values. The
  21 known false-negative trials in the old lxml library remain reported separately.
- Final full XML gate: 84 suites / 902 cases / 33,321 reported assertions. Previous
  suite results remain unchanged; the SOAP suite's existing reported assertion
  accounting is retained rather than represented as a new conformance claim.
- Python survey: 15 methods pass; coverage: 13 methods execute with exactly the two
  already tracked P6-selected-binding-version failures (request/response SOAP 1.1).
  QName union validation adds one passing method and resource tests add seven.
  Both-version raw and strict corpus reports are structurally identical to P3-35,
  including all outstanding later-phase failures.
- Valgrind: final attachment suite plus existing callbacks, XML and cursor-value
  suites total 51 cases / 914 assertions, with zero errors and zero
  definite/indirect/possible lost bytes. A separate same-process network batch
  covers malformed schema, HTTP failure and successful recovery with the same
  memory result. Qore JIT remains enabled; the authorized test setting is
  `QORE_PCRE2_NO_JIT=1`, with `qore -b --enable-debug --exec-mode=jit`.
- Debug and Release native builds and Debug docs-module complete without warnings
  or errors. The final attachment and HTTP matrix also pass with the Release module.

Known unsuppressed Valgrind environment warnings remain P9 findings: the core
DWARF-reader warning and the SSSD service-lookup `fstat(-1)` warning in network runs.
The latter's syscall stack is preserved in `/tmp/wsdl-p3-36-core-http-fstat.strace`.
Neither is treated as a clean environment gate or a reason to weaken assertions.

The full native audit records 26 Pass / 36 N/A / 0 Fail in
[audits/P3-36-xml-reader-schemas.md](audits/P3-36-xml-reader-schemas.md).

## Frozen artifacts and reproduction

- Debug core SHA-256: `e7445dbdfd81e79f053c78cb9e60b77c368eaa04a619f9093014091ae4bda8da`.
- Debug XML module SHA-256: `6ee75b70b836aacb627abb81a56f80ef966737d16fd4cc666252787681defe77`.
- Release XML module SHA-256: `3c2b6651f73790a5e3550277ab7476af75ca83487046765b48cc734608b189c9`.
- Unchanged canonical QName fixture SHA-256:
  `4504254bd15b7e1ce2e33ca48893d6bb1a48fc994994d2ad5dfdbdeec13d46ad`.
- Both CMake builds use `/usr` prefix; their types are Debug and Release respectively.
  The isolated core/environment is `/tmp/wsdl-core-date-env.sh`; nothing is installed.
- Logs/manifests: `/tmp/wsdl-p3-36-native-*`,
  `/tmp/wsdl-p3-36-core-xml-*`, `/tmp/wsdl-p3-36-reader-modes.*`, and
  `/tmp/wsdl-p3-36-python-*`. The independent artifacts are
  `/tmp/xml-qname-union-validator-cp1nl1kw`.

Run the commands in [README.md](README.md) with the intended local binary in
`QORE_MODULE_DIR` and the isolated core library in `LD_LIBRARY_PATH`.
`QORE_SCHEMA_VALGRIND_DIR` enables separate unfiltered Valgrind logs for the HTTP
Python driver; create that directory first. The FTP test must be explicitly run
with a module advertising `LIBXML_FTP_ENABLED`.

## Independently discovered open P3 finding

[schema-uri-findings.json](schema-uri-findings.json) preserves raw and percent-encoded
schemaLocation spellings, their shared resource bytes, expected valid document and
actual results. XSD 1.0 anyURI maps international characters and spaces to URI
references using the specified escaping procedure; include schemaLocation is an
anyURI. References: [Datatypes 3.2.17](https://www.w3.org/TR/xmlschema-2/#anyURI) and
[Structures 4.2](https://www.w3.org/TR/xmlschema-1/#compound-schema).

A direct C probe against installed libxml2, with no Qore code, rejects the raw
include in xmlSchemaParseIncludeOrRedefine before a resource loader is called;
the percent-encoded include passes. This independently reproduced dependency
finding is assigned to the next P3 schema-URI increment. It remains a failure,
with neither original spelling rewritten nor valid source reclassified invalid.

The pinned Xerces direct-file probe also fails to resolve the raw include while
accepting its escaped form. The existing offline oracle rejects the raw location
in its own Java URI resolver before reaching Xerces and needs file-URI key
normalization coverage. These are additional explicit oracle findings, not
normative evidence against the input. Reproducers and outputs are
`/tmp/wsdl-p3-36-uri-repro.py`, `/tmp/wsdl-p3-36-uri-native.c`,
`/tmp/SchemaUriOracle.java` and their adjacent logs. That follow-up and the remaining
WSDL QName/list/union work must pass before P3 acceptance.
