# P5-19e native annotation audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied all 62 audit-changes checks to changes based on `6dfcc3b`. All five
referenced guides were previously read and their hashes verified unchanged.
Scope: two native annotation attribute corrections, behavioral dependency
selection, regression fixtures/tests, documentation and acceptance evidence.
No main-Qore mutation, installation or push. Unrelated
`test/cmake/__pycache__/` is excluded.

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
| 9 | Copyright 2026 on all new files | Pass | Authored CMake/C probe, Qore/Python tests and documents carry 2026 copyright; the interoperability README identifies authored JSON fixture copyright. Third-party notices are unchanged. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new Qore module, separated source, QPP class, registration or layout change. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new Qore module, separated source, QPP class, registration or layout change. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new Qore module, separated source, QPP class, registration or layout change. |
| 13 | `%modern` directive present | Pass | The new Qore suite uses %modern; Python uses unittest with the existing bounded independent oracle. |
| 14 | Executable permission set (`chmod +x`) | Pass | The new .qtest and Python checker are executable. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The Qore suite prepends local qlib and every Qore command selects local Debug XML using QORE_MODULE_DIR. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project XML and core QUnit use hard requirements; external json uses %try-module and an explicit missing-dependency error. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | Pass | No production filesystem operation added. The hash-guarded CMake correction writes only build-tree copies, covered by source-distribution tests. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | Pass | No production network operation added. The existing pinned FetchContent/offline policy is unchanged; annotation source values are never dereferenced. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No new Qore C++ I/O or cancellation loop; private native C dependency has no Qore runtime dependency. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | ReadOnlyFile reads the committed local fixture as justified test input. Production Qore is unchanged. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No production C/C++ loop added or modified; the six-case configure probe is bounded. Existing cancellation boundaries are unchanged. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No new Qore C++ I/O or cancellation loop; private native C dependency has no Qore runtime dependency. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No new Qore C++ I/O or cancellation loop; private native C dependency has no Qore runtime dependency. |
| 24 | No blocking operations without cancellation support | Pass | No blocking production operation added. URI validation is local lexical assessment. |
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
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Directly fixes the native expanded-name condition and missing URI validation, without weakening grammar or rewriting source fixtures. The independent WSDL grammar defect is explicitly assigned to the next P5 increment. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Reuses the existing context-owned schema attribute validator and its checked extraction/type-validation diagnostics. No ownership transfer, new allocation primitive or shared state. The focused direct-ELF Valgrind has zero errors or lost memory; existing allocation regression tests also pass. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | All parser state remains per schema construction call; no new global or shared mutable state. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Native attribute checks retain explicit libxml2 pointer/status types. The probe bounds-checks snprintf; Qore test collections are typed. No public API or ABI changes. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Adds one URI validation per documentation element; no new tree traversal, recursion, or repeated component scan. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | The 117-schema matrix includes 54 valid and 63 invalid cases: foreign/own attributes, URI escaping, language boundaries, arbitrary mixed payloads and invalid annotation content in schema/notation/facet positions. Three native APIs assert exact errors and unchanged documents. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Durable native design, README, release notes, finding, evidence and inventory describe implemented behavior and an example. No new public method. Native documentation builds cleanly. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP method or flags changed. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | The configure probe uses a constant bounded format; source rewriting checks both SHA-256 values. No credentials, external annotation resource loading, or user-controlled format strings. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | The 117-schema matrix agrees with pinned Xerces. Focused Qore tests, all 66 dependency-provider tests, affected suites and survey unit tests pass. Both decoding modes preserve byte-identical diagnostic and strict corpus reports. Valgrind is clean. |

Result: 18 Pass, 44 N/A, zero Fail.
