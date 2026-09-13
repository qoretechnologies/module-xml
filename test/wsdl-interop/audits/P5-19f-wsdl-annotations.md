# P5-19f WSDL annotation audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied the full audit-changes skill to the final changes based on `9ed2230`.
All five referenced design guides were previously read and their SHA-256 values
verified unchanged. Scope: WSDL grammar/source/documentation handling, native URI
API, tests, release notes, design and acceptance records. No Qore mutation or push.

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, separated source, QPP class, registration or layout change. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | N/A | No new module, separated source, QPP class, registration or layout change. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module, separated source, QPP class, registration or layout change. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, separated source, QPP class, registration or layout change. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new module, separated source, QPP class, registration or layout change. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No new module, separated source, QPP class, registration or layout change. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, separated source, QPP class, registration or layout change. |
| 8 | No `%include` usage (deprecated for modules) | N/A | No new module, separated source, QPP class, registration or layout change. |
| 9 | Copyright 2026 on all new files | Pass | New tests, design and evidence carry 2026 copyright; existing production notices are current. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, separated source, QPP class, registration or layout change. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, separated source, QPP class, registration or layout change. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, separated source, QPP class, registration or layout change. |
| 13 | `%modern` directive present | Pass | All three affected Qore suites use %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | Both new .qtest files and the modified HTTP suite are executable (755). |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Tests prepend local qlib before relative WSDL requirements; QORE_MODULE_DIR selects the local Debug binary. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project XML and core QUnit are hard requirements; external json uses %try-module with an explicit missing-dependency error. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | Pass | No production filesystem operation added. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | Pass | No production network operation added; URI references are never retrieved. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No native filesystem/network I/O; lexical API needs no I/O sandbox domain. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | ReadOnlyFile reads a committed fixture; existing local HTTP tests exercise the annotated contracts. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | Pass | The native Unicode loop checks cancellation every 100 code points; interpreted Qore loops use runtime cancellation. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | Pass | The API uses qore_check_cancel before/after native validation and in the character loop. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | Pass | Native tight-loop frequency is every 100 code points, with boundary checks; cancellation/recovery tests pass. |
| 24 | No blocking operations without cancellation support | Pass | No blocking production operation added; lexical validation is local. |
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
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Root causes are fixed in ordered grammar, heterogeneous child grouping and text extraction. The separately reproduced scalar URI/language gap is explicitly assigned to the next P5 increment. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Native values use unique_ptr and ReferenceHolder; encoding/status/sink failures are checked. Reader attribute position is restored with on_exit. Both relevant direct-ELF Valgrinds have zero errors or lost memory. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Frames and ID maps belong to each parse; native builtin initialization uses the libxml2 types mutex. Four event-barrier concurrent reconstructions pass. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed frame hashdecl, explicit pointer/status types and list<auto> for intentionally heterogeneous XML values; no untyped code callbacks or C-style casts added. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Linear grammar/ID assessment and iterative documentation traversal; each grouped run is copied at most once, then appended without repeated accumulated-list copies. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | 117-schema positive/negative matrix, ID normalization/scope, URI/XML character and encoding errors, empty/repeated/mixed text, cancellation/retry, saved objects and both binding contracts pass. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public API documents parameters, return, errors, caveat and example; release notes, durable design and acceptance evidence are updated. Native/WSDL documentation builds pass. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | Pass | normalize_xsd_uri has RET_VALUE_ONLY,NAMED_ARGS; lexical/encoding/allocation/cancellation errors can throw. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Constant error formats, bounded Unicode decoding, checked native status, no credentials or external URI retrieval. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Pinned Xerces agrees on 117 schemas. Final 55 affected suites plus xsd-compliance, 12 supplements and both-mode corpus reports pass their stated gates. The earlier 172-suite run is explicitly distinguished; existing conformance failures remain visible. |

Result: 22 Pass, 40 N/A, zero Fail.
