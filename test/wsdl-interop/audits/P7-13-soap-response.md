# P7-13 SOAP-response GET audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied `/home/david/.codex/skills/audit-changes/SKILL.md` to main develop based on
239deca. Scope: SoapClient/SoapHandler GET APIs, root-route collision fix, Qore/Python
regressions, transport extensions, release notes and durable design. No C++, new
module, DataProvider or DGC change. Unrelated `test/cmake/__pycache__/` is excluded.

The audit found a Doxygen warning for a return tag on the void registration method;
the unnecessary tag was removed and the documentation build rerun without warnings.
The root-path test found that Qore compares a missing path value equal to the empty
root key; both registration paths now check for a matching object before comparing
its path. Root registration and duplicate rejection are tested in both orders.

All 62 checks are explicitly accounted for:

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, registration, separated class or layout change; existing flat modules remain registered. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | External-module release notes in SoapClient.qm and SoapHandler.qm describe the new APIs and root-route fix. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module, registration, separated class or layout change; existing flat modules remain registered. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, registration, separated class or layout change; existing flat modules remain registered. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | Existing first module sections remain soapclientintro and soaphandlerintro. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | Both existing entry modules use %modern; no redundant parse directive was added. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, registration, separated class or layout change; existing flat modules remain registered. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include usage introduced. |
| 9 | Copyright 2026 on all new files | Pass | New tests, peer scripts and evidence carry 2026 copyright; edited module copyrights already include 2026. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, registration, separated class or layout change; existing flat modules remain registered. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, registration, separated class or layout change; existing flat modules remain registered. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No C++ or QPP change; native allocation, DGC, cancellation and sandbox enforcement are unchanged. |
| 13 | `%modern` directive present | Pass | The QUnit test and all changed Qore peers use %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | New qtest, Qore peers and Python gate are executable; modified transport peers retain executable modes. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Tests prepend local qlib before relative in-repo requirements, as the user explicitly requires. Compiled derivatives select fresh qmods. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | External json dependencies use %try-module. In-repo XML and core modules use hard requirements. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ or QPP change; native allocation, DGC, cancellation and sandbox enforcement are unchanged. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ or QPP change; native allocation, DGC, cancellation and sandbox enforcement are unchanged. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ or QPP change; native allocation, DGC, cancellation and sandbox enforcement are unchanged. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Client I/O uses core HTTPClient::sendUrl with its request-local URL, sandbox and cancellation behavior. Tests use read-only fixtures and bounded loopback servers with deterministic teardown. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ or QPP change; native allocation, DGC, cancellation and sandbox enforcement are unchanged. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ or QPP change; native allocation, DGC, cancellation and sandbox enforcement are unchanged. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ or QPP change; native allocation, DGC, cancellation and sandbox enforcement are unchanged. |
| 24 | No blocking operations without cancellation support | N/A | No C++ or QPP change; native allocation, DGC, cancellation and sandbox enforcement are unchanged. |
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
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | GET is an explicit safe-resource API using the existing response codec. No automatic operation remapping, local URI parser, transport workaround, skipped test or suppressed failure. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Validation precedes route publication and network I/O. Locks release with on_exit; callbacks execute outside locks. Cancellation propagates. Tests reap owned processes and close connections/listeners on exceptional paths. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Route registration/removal share the existing RWLock. Request-local header and URL copies preserve client defaults. Queues and Counter synchronize test threads; a provider removes its own service successfully. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Resource providers use code<auto(hash<auto>)>; selected bindings are checked as SoapBinding. HTTP context and message values use existing typed hash contracts; exceptions use ExceptionInfo. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Header suppression is linear in header count; exact routes use the existing TreeMap. No additional message parse or new busy loop; transport completion uses events. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Tests cover unsupported options, entity headers, SOAP 1.1/HTTP/no-output bindings, unknown operations, invalid/duplicate/root paths, HTTP template collisions in both orders, removal, faults, HTTP errors and cancellation recovery. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Both public APIs document parameters, exceptions, examples and caveats. The value-returning client documents its result; no return tag is emitted for the void registration method. Release notes and durable SOAP design are updated; docs rebuild without warnings. No DGC design change. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++ or QPP change; native allocation, DGC, cancellation and sandbox enforcement are unchanged. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Default Authorization/Cookie credentials remain origin-scoped; explicit per-call credentials remain intentional. Entity headers are suppressed without mutating defaults. Only dummy fixture tokens and loopback resources appear in tests; format strings are constant. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Independent HTTP peers validate wire methods, paths, headers, SOAP schemas and callback isolation. Native, saved-object, saved-data, retained-value and compiled-module matrices pass; validation report records broader regressions and corpus comparisons. |

**19 Pass / 43 N/A / zero Fail.** See [validation](../P7-13-validation.json) and
[evidence](../soap-response-evidence.md). No C++ change; Valgrind is not required.
P7 assertion accounting and P8–P9 remain open. No push or CI trigger.
