# P6-08 file URI audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied `/home/david/.codex/skills/audit-changes/SKILL.md` to the exact file URI
increment. The previously read module-structure, sandboxing and cancellation
guides remain byte-identical. The two DataProvider guides have changed upstream;
their registration/metadata requirements do not apply to this increment.
No C++ changes; Valgrind is not required for this Qore-only change.

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, QPP class, registration or layout change. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | N/A | No new module, QPP class, registration or layout change. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module, QPP class, registration or layout change. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, QPP class, registration or layout change. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | Existing WSDL module retains wsdlintro; no module registration or layout change. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL.qm retains %modern without redundant directives. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, QPP class, registration or layout change. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include or separated module added. |
| 9 | Copyright 2026 on all new files | Pass | New test, evidence, audit and edited design documents carry 2026 notices. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, QPP class, registration or layout change. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, QPP class, registration or layout change. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, QPP class, registration or layout change. |
| 13 | `%modern` directive present | Pass | Both changed Qore tests use %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | Both test/wsdl-file-uris.qtest and test/wsdl-document-locations.qtest have mode 0755. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Local qlib is prepended before relative WSDL.qm and SoapClient.qm requires. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Tests use this repository’s WSDL/SoapClient and core QUnit; no new external Qore module dependency. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ code, native I/O or native cancellation loop changed. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ code, native I/O or native cancellation loop changed. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ code, native I/O or native cancellation loop changed. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Local retrieval continues through core ReadOnlyFile/FileLocationHandler. Tests create bounded temporary fixtures and remove them on scope exit; async completion uses socket readiness with a deadline. No process working-directory changes or new network access are introduced. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ code, native I/O or native cancellation loop changed. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ code, native I/O or native cancellation loop changed. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ code, native I/O or native cancellation loop changed. |
| 24 | No blocking operations without cancellation support | N/A | No C++ code, native I/O or native cancellation loop changed. |
| 25 | Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 26 | Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 27 | Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 28 | DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 29 | DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 30 | Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 31 | Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 32 | **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 33 | Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 34 | Response/output types use `private` Fields | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 35 | Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 36 | Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 37 | Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 38 | Password/secret fields have `"sensitive": True` | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 39 | `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 40 | App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 41 | App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 42 | `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 43 | `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 44 | `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 45 | Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 46 | No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 47 | No bare field/option names in prose — must use backticks | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 48 | Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 49 | **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 50 | **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 51 | **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 52 | JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No DataProvider action/app/type metadata, factory, JNI dependency or packaging change. |
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | The file URI parser splits components before decoding once. Canonical containing URIs fix nested references and resource identity; callback routing and inline-cycle matching are corrected at their decision points. Legacy literal paths remain an explicit existing API, not a fallback used to hide a URI error. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | All helper state is call-local managed Qore data. URI validation precedes retrieval. Added schema files restore document/base context on success and exception. Async operations abort on error; source files are removed before offline reconstruction tests. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | No shared mutable registry or cache is added. File location transformations are stateless and do not change cwd. Existing construction-before-sharing rules remain applicable. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | URI parsing uses WsdlUriParts, explicit string/bool return types and typed map/list values. No native casts or new untyped callbacks are introduced. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Location transformations process the path with existing normalization and per-segment encoding. Dependency hash lookups and cycle registries avoid repeated graph traversal. Full enterprise/partner schema acceptance passes. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Missing absolute paths, queries, bad escapes, NUL, invalid localhost authority and unescaped URI spaces reject deterministically before I/O. Missing resources retain FILE-OPEN2-ERROR. Tests cover later valid use, callback failure/retry, old caches and source-context restoration. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Updated API docs describe canonical returns, errors, supported URI spellings, legacy authority meaning and a realistic filename example. Release notes and both durable location/component designs describe the implementation. WSDL and SoapClient documentation builds pass without diagnostics. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP methods or flags changed. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | URI components are separated before decoding; NUL rejects and file authorities do not trigger new network access. Existing core I/O enforcement is retained. Strings are managed and messages use fixed format strings; no credentials or sensitive fixtures. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Seven focused cases / 291 assertions fail on the pre-change source and pass on the final source. The 36-suite gate passes 464 cases / 7547 reported assertions (seven existing intentionally caught comparator assertions). Enterprise passes 5 cases / 85 assertions; pinned WSDL4J, grammar/reference/contract checks and both corpus modes pass their documented gates. See validation for exact baseline comparison. |

All 62 checks: **18 Pass / 44 N/A / zero Fail**.
See [validation](../P6-08-validation.json) and [evidence](../file-uri-evidence.md).
