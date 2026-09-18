# P6-25 shared element part audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied `/home/david/.codex/skills/audit-changes/SKILL.md` to message-part identity,
wire-key lookup, native/retained regressions, the independent WSDL4J observer and
durable documentation. No C++ changes; Valgrind is not required.

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, separated class file, registration or layout change. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | N/A | No new module, separated class file, registration or layout change. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module, separated class file, registration or layout change. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, separated class file, registration or layout change. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | WSDL retains its lowercase introduction section. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL retains %modern. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, separated class file, registration or layout change. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include introduced. |
| 9 | Copyright 2026 on all new files | Pass | New Qore/Python/Java tests and modified source/design documents carry 2026 copyright. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, separated class file, registration or layout change. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, separated class file, registration or layout change. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 13 | `%modern` directive present | Pass | The new Qore regression uses %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | The new Qore regression and Python oracle test are executable. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The Qore test prepends local qlib before requiring repository WSDL, SoapClient and SoapHandler. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | QUnit/HttpServer are core dependencies and xml is part of this repository. The independent oracle verifies pinned WSDL4J 1.6.3 hashes before use. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | No production I/O change. Tests use the pinned local SwA fixture and bounded loopback HTTP calls; on_exit stops servers, and Java subprocesses have deadlines and temporary-directory cleanup. |
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
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | The message constructor incorrectly required element QName uniqueness rather than part-name uniqueness. Distinct parts now retain separate argument keys; actual wire names still come from element declarations. Same-location ambiguous selections continue rejecting. No fixture was rewritten. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Part descriptors are assembled locally before publication; existing Qore ownership and exception unwinding apply. Saved graphs retain independent descriptors. Tests clean servers and oracle classes with on_exit/class cleanup. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Argument maps are immutable during message use. No shared per-call mutation, cache or transport configuration changed. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | QName occurrence counts use hash<string, int>; descriptors retain hash<ArgInfo> and typed element references. Provider fields remain keyed by WSDL part name. HTTP callback uses code<auto(hash<auto>, auto)>. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | The existing two linear constructor passes are retained. Hash-count lookup replaces duplicate rejection; no pairwise search or per-message traversal was introduced. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Distinct values in Body/Header, both SOAP versions/directions, source/saved services and detached operations, native/retained values, provider fields, collisions with type-part aliases, duplicate part-name rejection and same-body ambiguity are tested. Real HTTP calls preserve independent request and response values. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Release notes and durable message-identity design describe part-specific internal keys, stable public part fields and unchanged wire QNames. Public method documentation describes wire-key lookup and raw-value decoding. No DGC design changes. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No new I/O capabilities, credentials, unmanaged buffers or format strings. Synthetic internal keys cannot equal ordinary NCNames or an expanded element name, and never appear as wire names. Pinned fixture and JAR hashes are verified. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | The 30-suite gate passes 519 cases / 10,639 reported assertions; the final focused suite adds two raw-value decoder checks for 96 assertions. WSDL4J independently retains both same-element parts in the original SwA request/response. Source/saved and real HTTP tests verify separate values. Attachment interoperability remains P8 work. |

All 62 checks: **18 Pass / 44 N/A / zero Fail**.
