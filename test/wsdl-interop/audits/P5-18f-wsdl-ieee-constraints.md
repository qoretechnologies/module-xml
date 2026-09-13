# P5-18f WSDL IEEE constraints audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied all 62 audit-changes checks to the final changes based on `976fd28`
on 2026-09-13. All five referenced guides were read and their hashes verified.
Scope: native canonical API, WSDL capture, exact/consumer tests and documentation.
No main-Qore mutation, install or push. The unrelated test/cmake/__pycache__
directory is excluded. See [evidence](../wsdl-ieee-constraints-evidence.md) and
[inventory](../P5-18f-validation.json).

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 8 | No `%include` usage (deprecated for modules) | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 9 | Copyright 2026 on all new files | Pass | All authored API/tests/docs have 2026 copyright; existing notices and the unchanged JSON fixture remain intact. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 13 | `%modern` directive present | Pass | All new qtest/qr sources use %modern; Python entry points use unittest. |
| 14 | Executable permission set (`chmod +x`) | Pass | All new qtest/qr and Python test entry points are executable (0755). |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Tests prepend local qlib before requirements; source WSDL/SoapClient/SoapHandler/provider requirements are relative. Runtime environment selects the local Debug XML module. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Same-project xml and Qore QUnit/HttpServer use hard requirements. External json uses the %try-module pattern with a clear failure. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | Pass | The native API performs no filesystem access; there is no new sandboxed filesystem entry point. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | Pass | The native API performs no networking; there is no new network functional domain. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No new Qore filesystem/network entry point or resource callback. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Fixture reads are explicit local files. HTTP tests use listeners on dynamically assigned loopback ports, bounded socket deadlines, observed-result queues and deterministic teardown. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | Pass | The new length-aware NUL scan checks cancellation at entry and every 100 bytes, and conversion checks again before publishing the result. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | Pass | All added hooks use qore_check_cancel; no deprecated interrupt API is introduced. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | Pass | The only new potentially long C++ loop checks every 100 iterations. Native datatype formatting remains the already verified private dependency implementation. |
| 24 | No blocking operations without cancellation support | Pass | No native blocking I/O is added. API interruption/recovery and WSDL scope restoration pass; HTTP operations have deadlines and teardown. |
| 25 | Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 26 | Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 27 | Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 28 | DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 29 | DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 30 | Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 31 | Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 32 | **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 33 | Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 34 | Response/output types use `private` Fields | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 35 | Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 36 | Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 37 | Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 38 | Password/secret fields have `"sensitive": True` | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 39 | `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 40 | App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 41 | App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 42 | `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 43 | `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 44 | `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 45 | Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 46 | No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 47 | No bare field/option names in prose — must use backticks | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 48 | Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 49 | **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 50 | **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 51 | **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 52 | JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No DataProvider action, field, app, factory, JNI dependency or installation change. |
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | WSDL now computes the missing canonical IEEE spelling from the selected value. The public API reuses corrected native primitives. No fixture name affects production behavior, no heuristic changes values, and all oracle differences remain explicit. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | xmlSchemaVal and xmlChar results enter unique_ptr ownership immediately, including failure returns. Qore output uses ReferenceHolder; UTF-8 conversion and native statuses are checked. Four direct-Qore Valgrind runs have zero errors/lost bytes, with AST used for the large WSDL consumers; parent native allocation-failure coverage remains unchanged. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Native temporaries and buffers are per-call. Builtin type metadata is initialized through the native API and immutable thereafter. WSDL capture remains thread-local and restores previous scope. Four-worker API ownership and HTTP consumer tests pass. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | The C++ boundary has string/bool parameters, size_t indexing, typed custom deleters and explicit casts. WSDL uses its typed identity hashdecl; the HTTP callback has a typed code signature. No action/provider metadata contract changes. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Native lexical scanning is linear; formatting reuses the bounded native IEEE helper. Canonical work occurs only in declaration capture and introduces no extra work in ordinary value comparison. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Empty/malformed lexicals, embedded NULs, unsupported whitespace, complete exponents, special values, encoding, precision boundaries and long inputs are checked with categorized errors. WSDL rejects all 144 invalid declarations, and HTTP rejects invalid requests and responses then recovers. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | The new API has all parameter, return, error, cancellation and precision notes plus examples. Native/WSDL release notes, README and durable design are updated. Both affected documentation targets build without warnings. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | Pass | canonical_xsd_float is marked RET_VALUE_ONLY and NAMED_ARGS; it can throw and has no externally visible side effects. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No user-controlled diagnostic format or new external I/O is added. The NUL scan is length-bounded; native ownership and conversion statuses are checked. Test subprocesses and HTTP calls use deadlines. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | All 159 Qore suites and 22 supplements pass, including forced AST/IR/JIT/tiered and compiled WSDL consumers. Independent checks cover 1314 rational cases, 2148 WSDL records and 1248 preserved SOAP payloads. Four Valgrind runs are clean; both corpus modes equal parent semantic records. |

Result: 22 Pass, 40 N/A, zero Fail.
