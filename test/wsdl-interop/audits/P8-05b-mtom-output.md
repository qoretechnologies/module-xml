# P8-05b MTOM/XOP output audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied `/home/david/.claude/skills/audit-changes/SKILL.md` to the uncommitted P8-05b changes on main `develop`
based on 0ad23d7. Scope: `qlib/WSDL.qm` (SoapMtomScope, XOP writer, serialization hooks, packaging and fallback,
random boundaries, envelope validation of absent values, release notes), `qlib/SoapHandler.qm` (MTOM mirroring,
setMtomThreshold, mixed-version routes), `qlib/SoapClient.qm` and `qlib/SoapClientIo` (mtom options; complete
response Content-Type), `test/soap-mtom-output.qtest`, `test/mtom-output.wsdl`, `test/soap-actions.qtest` with
`soap-action-peer/versions.wsdl`, `test/wsdl-interop/mtom-peer/`, `test/wsdl-interop/test_mtom_xop.py`, the root-entity helper in
`test_cxf_peer.py` with the three transport gates that read it, the design documents, and PLAN.md and
EXECUTION.md.

All 62 checks are explicitly accounted for:

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | External module repository. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL v0.5.8 (MTOM output, random boundaries, envelope validation of absent values), SoapHandler 0.3.4 (MTOM mirroring, mixed-version routes), SoapClient v1.0.4 (mtom options) and SoapClientIo v1.0 (MTOM feature) release notes. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No module added. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No module added. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No module added. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | All four modules keep their %modern directive. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | SoapClientIo.qc changed without parse directives; no other .qc changed. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include usage. |
| 9 | Copyright 2026 on all new files | Pass | test/soap-mtom-output.qtest, test/mtom-output.wsdl, soap-action-peer/versions.wsdl, mtom-peer/{MtomPeer.java, qore-peer.qr, README.md}, test_mtom_xop.py, design/soap-mtom-output.md and this record carry the 2026 copyright. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No module added. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No module added. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No C++ or QPP change; the changes are Qore module code in qlib/WSDL.qm, qlib/SoapHandler.qm, qlib/SoapClient.qm and qlib/SoapClientIo, tests, a Java peer and documentation. |
| 13 | `%modern` directive present | Pass | test/soap-mtom-output.qtest uses %modern, and the peer script mtom-peer/qore-peer.qr does too. |
| 14 | Executable permission set (`chmod +x`) | Pass | test/soap-mtom-output.qtest, mtom-peer/qore-peer.qr and test_mtom_xop.py are executable. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The suite and the peer script use %prepend-module-path before relative %requires of WSDL.qm, SoapHandler.qm, SoapClient.qm and SoapClientIo. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | No external module: QUnit, Mime and HttpServer are delivered with Qore, and xml is this repository's module. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ or QPP change. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ or QPP change. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ or QPP change. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | No new I/O in the modules; the suites use HttpServer, HTTPClient and SoapClientIo on 127.0.0.1 only, and the live runner starts loopback listeners. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ or QPP change. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ or QPP change. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ or QPP change. |
| 24 | No blocking operations without cancellation support | N/A | No C++ or QPP change. |
| 25 | Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No DataProvider, factory, application registration or JNI change. |
| 26 | Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No DataProvider, factory, application registration or JNI change. |
| 27 | Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No DataProvider, factory, application registration or JNI change. |
| 28 | DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DataProvider, factory, application registration or JNI change. |
| 29 | DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No DataProvider, factory, application registration or JNI change. |
| 30 | Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No DataProvider, factory, application registration or JNI change. |
| 31 | Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No DataProvider, factory, application registration or JNI change. |
| 32 | **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No DataProvider, factory, application registration or JNI change. |
| 33 | Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No DataProvider, factory, application registration or JNI change. |
| 34 | Response/output types use `private` Fields | N/A | No DataProvider, factory, application registration or JNI change. |
| 35 | Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No DataProvider, factory, application registration or JNI change. |
| 36 | Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No DataProvider, factory, application registration or JNI change. |
| 37 | Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No DataProvider, factory, application registration or JNI change. |
| 38 | Password/secret fields have `"sensitive": True` | N/A | No DataProvider, factory, application registration or JNI change. |
| 39 | `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No DataProvider, factory, application registration or JNI change. |
| 40 | App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No DataProvider, factory, application registration or JNI change. |
| 41 | App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No DataProvider, factory, application registration or JNI change. |
| 42 | `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No DataProvider, factory, application registration or JNI change. |
| 43 | `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No DataProvider, factory, application registration or JNI change. |
| 44 | `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No DataProvider, factory, application registration or JNI change. |
| 45 | Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No DataProvider, factory, application registration or JNI change. |
| 46 | No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No DataProvider, factory, application registration or JNI change. |
| 47 | No bare field/option names in prose — must use backticks | N/A | No DataProvider, factory, application registration or JNI change. |
| 48 | Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No DataProvider, factory, application registration or JNI change. |
| 49 | **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No DataProvider, factory, application registration or JNI change. |
| 50 | **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No DataProvider, factory, application registration or JNI change. |
| 51 | **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No DataProvider, factory, application registration or JNI change. |
| 52 | JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No DataProvider, factory, application registration or JNI change. |
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | MTOM output is complete for SOAP 1.1 and 1.2 requests, responses and declared faults. The content that stays inline is an XOP 1.0 section 3.1 choice (only canonical content may be optimized; optimization is optional), documented with its reasons. The three defects found while testing are fixed at their root, not worked around. SoapConnection/SoapIoConnection option metadata for MTOM is a separate connection-provider change and is reported, not stubbed. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | SoapMtomScope and XopOutputScope restore their thread-local selections in destructors; the suite checks restoration after a serialization exception and after a rejected negative threshold (the previous value is saved before validation). The writer is per message, so a failed serialization leaves no shared state; the fallback re-serializes in a nested plain scope. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | The MTOM selection and XOP writer are thread-local, and a new thread starts without them (tested). SoapHandler's version maps are written under the registration write lock and read under the dispatch read lock; mtom_threshold is a single member assignment. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | hashdecl XopPartInfo, typed version maps, typed bool/int client options validated with explicit errors, and a typed *int handler threshold. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | With MTOM off, serialization adds one thread-local check per element. Optimization is linear in the content, and part selection is one XmlReader pass that runs only when the root contains 'Include'. Version-aware dispatch adds hash lookups. The full suite ran at its previous cost (394 parallel targets in 1003 s). |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Negative thresholds and wrongly typed client options raise SOAP-SERIALIZATION-ERROR, SOAP-HANDLER-ERROR, SOAP-CLIENT-ERROR or SOAP-CLIENT-IO-ERROR; an invalid xmime:contentType keeps the value inline as XOP 1.0 section 3.1 recommends. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | design/soap-mtom-output.md; updates to wsdl-multipart-input.md, soap-envelope-processing.md and soap-async-io-client.md; Doxygen for SoapMtomScope (with example), XMIME_NS, MTOM_THRESHOLD, setMtomThreshold()/getMtomThreshold() (with example) and the client options; release notes; mtom-peer/README.md; PLAN.md and EXECUTION.md. Docs build with no warnings. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP change. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | An xmime:contentType with control characters never reaches a MIME header (tested with CRLF injections); boundaries are 128-bit random; no credentials; loopback listeners only. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Checked against the pinned XOP 1.0 and SOAP 1.2 MTOM texts and live against Apache CXF 4.1.3 in both directions, with each side verifying the other's package form and part count across the threshold. The live runner fails in both directions against the previous modules. The full suite passes on one runtime (461 targets, 3,637 cases, 174,344 assertions) except the two core-blocked IEEE gates. |

Result: **18 Pass / 44 N/A / zero Fail**.
