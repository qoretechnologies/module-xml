# P6-24 HTTP replacement audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied `/home/david/.codex/skills/audit-changes/SKILL.md` to complete-template
routing, raw-path decoding, registration/removal locking, regressions and docs.
No C++ or DataProvider changes; Valgrind is not required.

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, separated class file, registration or layout change. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | N/A | No new module, separated class file, registration or layout change. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module, separated class file, registration or layout change. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, separated class file, registration or layout change. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | The existing WSDL and SoapHandler introduction sections remain lowercase. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL and SoapHandler retain %modern. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, separated class file, registration or layout change. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include introduced. |
| 9 | Copyright 2026 on all new files | Pass | The new regression carries 2026 copyright; modified test/source/design files already carry 2026. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, separated class file, registration or layout change. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, separated class file, registration or layout change. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 13 | `%modern` directive present | Pass | Both affected Qore tests use %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | Both test/wsdl-http-replacement.qtest and test/SoapClient.qtest are executable. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Both tests prepend repository qlib before requiring local WSDL, SoapClient and SoapHandler. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | QUnit and HttpServer are core dependencies; xml and the three modules belong to this repository. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Transport continues through existing clients/handlers. The integration test uses loopback, a bounded request timeout, Queue completion and on_exit server cleanup. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 24 | No blocking operations without cancellation support | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 25 | Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 26 | Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 27 | Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 28 | DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 29 | DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 30 | Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 31 | Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 32 | **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 33 | Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 34 | Response/output types use `private` Fields | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 35 | Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 36 | Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 37 | Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 38 | Password/secret fields have `"sensitive": True` | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 39 | `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 40 | App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 41 | App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 42 | `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 43 | `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 44 | `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 45 | Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 46 | No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 47 | No bare field/option names in prose — must use backticks | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 48 | Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 49 | **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 50 | **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 51 | **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 52 | JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No DataProvider action, static field catalog, app, factory or JNI packaging changes. |
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Replacement routes previously used a literal TreeMap key containing placeholders. Full-template matching now selects the route. Raw request paths avoid a second percent-decoding pass. Static mount fallback uses the same exact-match check as unmounted routing. No workaround or suppression. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Route locks always release with on_exit; callbacks run after lookup releases the lock. Matching uses local values and throws no schema conversion errors. Registration rejects duplicate templates before publication. Tests stop each server on exit; service removal drops owned references. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | HTTP registration now acquires the write lock. Route lookup acquires the read lock and retains the selected method for in-flight dispatch. removeService uses the existing write lock for static/replacement removal. Template conversion does not mutate shared descriptions. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | The replacement registry uses nested typed hashes; matching has a bool result and extraction an optional hash. Callbacks use code<auto(hash<auto>, auto)> and the duplicate-registration test uses code<nothing()>. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Path extraction traverses ordered tokens once instead of rescanning the token list for every part. Lookup scans registered replacement templates for the selected verb, allowing complete-match ambiguity detection. Static TreeMap lookup remains first. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Complete prefix/suffix matching, empty/Unicode/reserved values, percent signs, repeated values, source/saved operations and services, duplicate/ambiguous routes, static-route coexistence, plain/Unicode mounts, remove/re-add lifecycle and real client callbacks are tested. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public matchesRequestPath documents its argument, result, decoding error, type-validation boundary and a concrete example. WSDL/SoapHandler release notes and durable HTTP/MIME design describe routing, encoded-path ownership, locking and removal. No DGC design change. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No credentials, unmanaged allocations or new transport facilities. Full template checks prevent suffix acceptance; ambiguous routes never invoke a callback. Percent-encoded delimiters are preserved until part extraction. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Twelve affected suites pass: 148 cases / 3,270 reported assertions. The new suite passes 4 cases / 187 assertions; the pre-existing SoapClient URL-replacement expected failure is now a successful call with explicit callback-value assertions. Docs and astparser pass. |

All 62 checks: **18 Pass / 44 N/A / zero Fail**.
