# WebDAV property copy/move audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied the complete audit-changes skill to the WebDAV-only repair. All five referenced Qore design guides were consulted and their hashes reverified. WSDL development changes are excluded from this commit.

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, class namespace, build registration or layout change. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | N/A | No new module, class namespace, build registration or layout change. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module, class namespace, build registration or layout change. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, class namespace, build registration or layout change. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | Existing mainpage begins with webdavhandlerintro; no new module. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | Main qm retains %modern; no redundant directives. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | Pass | Changed separated qc files contain no parse directives. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No include directive introduced. |
| 9 | Copyright 2026 on all new files | Pass | Changed/new authored files carry 2026 copyright. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, class namespace, build registration or layout change. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, class namespace, build registration or layout change. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, class namespace, build registration or layout change. |
| 13 | `%modern` directive present | Pass | New regression uses %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | New qtest is executable. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Local qlib prepend precedes relative WebDavHandler require. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | QUnit and FsUtil are core dependencies; WebDavHandler is in this repository. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ changes, native I/O or native loop. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ changes, native I/O or native loop. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ changes, native I/O or native loop. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | No new production I/O path. Existing core File operations retain sandbox checks; tests use scoped TmpDir and existing local HTTP test servers. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ changes, native I/O or native loop. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ changes, native I/O or native loop. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ changes, native I/O or native loop. |
| 24 | No blocking operations without cancellation support | N/A | No C++ changes, native I/O or native loop. |
| 25 | Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 26 | Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 27 | Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 28 | DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 29 | DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 30 | Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 31 | Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 32 | **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 33 | Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 34 | Response/output types use `private` Fields | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 35 | Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 36 | Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 37 | Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 38 | Password/secret fields have `"sensitive": True` | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 39 | `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 40 | App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 41 | App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 42 | `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 43 | `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 44 | `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 45 | Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 46 | No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 47 | No bare field/option names in prose — must use backticks | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 48 | Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 49 | **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 50 | **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 51 | **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 52 | JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No provider app/action/type metadata, factory or JNI packaging changes. |
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Missing source properties remove a target entry instead of assigning NOTHING to a nonoptional typed value; same-source moves preserve ownership. No type weakening, stubs or workaround. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Copy assignment precedes source deletion, under the existing write lock. Automatic lock guards release on exceptions; tests exercise missing entries, reuse and scoped temporary directories. No native allocation change. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Both caches retain write locks for mutation. File save now uses the exclusive lock because it changes the file and dirty state. Queue barriers and counters verify completed concurrent updates after reload. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | The typed property maps remain unchanged. Absence is represented by removing entries; no optional-value widening or coercion. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Copy-on-write retains existing copy semantics. Missing entries use hash lookup/removal; no new full-map traversal. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Missing source and target are valid states, including overwriting stale target properties. Self moves preserve values; copy/move recovery and persistence are covered. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Method parameters, empty-source semantics, self moves, release notes and durable storage design document the resulting behavior. Docs build included. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP methods changed. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No new network endpoint, formatting input, credential handling or memory operation. New threaded tests use bounded queues and deterministic cleanup. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | The exact CI HTTP 500 reproduces locally. New tests cover both property stores, distinct namespaces, copy independence, source removal, persistence and concurrent sync. Existing HTTP client/provider and handler suites verify the repair. |

All 62 checks: **19 Pass / 43 N/A / zero Fail**.
