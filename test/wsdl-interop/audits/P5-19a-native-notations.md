# P5-19a native NOTATION audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied all 62 audit-changes items to final changes based on `16be41b`.
All five referenced guides were read; their previously recorded hashes remain
unchanged. Scope: private native declaration/type-use/allocation correction,
CMake integration, tests, release notes, design and acceptance evidence. Main
Qore remains read-only. No push or installation; unrelated
`test/cmake/__pycache__/` is excluded. See [evidence](../native-notations-evidence.md)
and [inventory](../P5-19a-validation.json).

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new Qore module, separated source, QPP class, registration or layout change. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | N/A | No new Qore module, separated source, QPP class, registration or layout change. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new Qore module, separated source, QPP class, registration or layout change. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No new Qore module, separated source, QPP class, registration or layout change. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new Qore module, separated source, QPP class, registration or layout change. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No new Qore module, separated source, QPP class, registration or layout change. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new Qore module, separated source, QPP class, registration or layout change. |
| 8 | No `%include` usage (deprecated for modules) | N/A | No new Qore module, separated source, QPP class, registration or layout change. |
| 9 | Copyright 2026 on all new files | Pass | Authored C/CMake, Qore/Python and documentation carry 2026 copyright; README explicitly identifies the authored JSON/XSD fixture copyright. Third-party notices remain unchanged. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new Qore module, separated source, QPP class, registration or layout change. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new Qore module, separated source, QPP class, registration or layout change. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new Qore module, separated source, QPP class, registration or layout change. |
| 13 | `%modern` directive present | Pass | The Qore suite and worker use %modern. Python checks use unittest and bounded subprocesses. |
| 14 | Executable permission set (`chmod +x`) | Pass | The new .qtest, .qr worker and Python test are executable. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Qore suite and worker prepend local qlib; all commands select the local Debug XML through QORE_MODULE_DIR. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project XML and core Qore QUnit are hard requirements. External json uses %try-module with an explicit missing dependency error. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | Pass | No production filesystem operation added. CMake writes hash-guarded sources only to the build tree; the source-distribution check includes every dependency input. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | Pass | No production networking added; existing pinned FetchContent and offline source override are unchanged. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No new Qore C++ I/O or cancellation loop; private native C dependency has no Qore runtime dependency. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Test fixture reads and the explicitly mapped local import are justified offline test I/O. Production Qore is unchanged. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | Pass | No C++ loop added. Private native C walks are iterative and cache shared ancestry, with no Qore runtime dependency. Existing entry/I/O cancellation boundaries remain; the full cancellation/cleanup suites pass. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No new Qore C++ I/O or cancellation loop; private native C dependency has no Qore runtime dependency. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No new Qore C++ I/O or cancellation loop; private native C dependency has no Qore runtime dependency. |
| 24 | No blocking operations without cancellation support | Pass | No new blocking production operation. Existing schema callback, interruption, cleanup and HTTP tests pass in the complete gate. |
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
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Implements declaration representation checks, enumeration-derived use validation and correct allocation classification. No weakened validation, fixture-name branch, hidden skip or workaround. WSDL conversion remains an explicit next increment within P5. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Checks extraction, interning, component/list/hash allocation and frees all owned temporary containers on every exit. ID trimming uses its owned validated buffer. 1064 single/persistent allocation faults preserve ownership and recovery; three Valgrind runs report zero errors and lost memory. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | All mutable state belongs to the schema construction call. Cache markers are immutable; component pointers are borrowed. Fault-injection globals are restricted to standalone single-thread test programs. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Native C uses explicit pointer/enum/status types and checked size conversions; status caches distinguish other primitives, unrestricted NOTATION and enumerated NOTATION. Qore test containers are typed. No public layout/API change. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Visited component and atomic-status caches make shared list/union/restriction assessment proportional to graph size and facets. Builtins terminate ancestry traversal. No recursive walk or document copy is added. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Covers malformed declarations, absent/empty identifiers, foreign/unknown attributes, normalized NCNames and IDs, inherited/late enum, simple content, lists/unions, imported/no namespaces, defaults/fixed and QName versus NOTATION identity. Expected error categories and unchanged XML are checked through three APIs. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Durable native design, README, native release notes and evidence document implementation, API examples, ownership, behavioral provider selection and seven explicit Xerces disagreements. Doxygen builds cleanly; no new public Qore method. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP method or flags changed. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Constant format strings, checked bounded buffers/source hashes, allocation checks and native cycle validation protect the new paths. Test subprocesses have deadlines; no credentials or production I/O are introduced. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 166 Qore suites, 65 provider tests and 13 supplements pass. The 64-schema/231-document matrix and 848-assertion unit test include independent Xerces assessment and all three native validation APIs. All four corpus reports are byte-identical to the parent. Four execution modes and three Valgrinds pass. |

Result: 19 Pass, 43 N/A, zero Fail.
