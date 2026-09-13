# P5-19c QName attribute provider audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied every audit-changes checklist item to changes based on `36bc967`.
The skill was reread before commit; all five previously read design guides retain
their verified hashes. Scope: WSDL wrapper access and QName finite choices,
two updated suites, release notes, implemented design and acceptance evidence.
Main Qore is read-only; no push or install. Unrelated `test/cmake/__pycache__/`
is excluded. See [evidence](../qname-attribute-provider-evidence.md) and
[inventory](../P5-19c-validation.json).

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, separated source, QPP class, build registration or layout change. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | External WSDL v0.5.8 notes describe QName attribute choices through wrappers. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module, separated source, QPP class, build registration or layout change. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, separated source, QPP class, build registration or layout change. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | Existing module keeps wsdlintro as its first documentation section. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | Existing WSDL module and authored Qore tests use %modern; no redundant directives introduced. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, separated source, QPP class, build registration or layout change. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include introduced; WSDL remains a single module source. |
| 9 | Copyright 2026 on all new files | Pass | Authored documentation carries 2026 copyright; updated Qore tests retain 2026 notices. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, separated source, QPP class, build registration or layout change. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, separated source, QPP class, build registration or layout change. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, separated source, QPP class, build registration or layout change. |
| 13 | `%modern` directive present | Pass | Both updated suites use %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | Both updated .qtest files retain executable permissions. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Both suites prepend local qlib before relative WSDL/consumer requirements; local Debug XML is used. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | XML/WSDL/SoapClient/SoapHandler belong to this project; QUnit and HttpServer are core Qore modules. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C/C++/QPP change or new blocking production operation; no additional Valgrind requirement. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C/C++/QPP change or new blocking production operation; no additional Valgrind requirement. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C/C++/QPP change or new blocking production operation; no additional Valgrind requirement. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Only existing loopback HttpServer/SoapClient test APIs are used, with bounded queue and request deadlines and on_exit cleanup; no new production I/O. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C/C++/QPP change or new blocking production operation; no additional Valgrind requirement. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C/C++/QPP change or new blocking production operation; no additional Valgrind requirement. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C/C++/QPP change or new blocking production operation; no additional Valgrind requirement. |
| 24 | No blocking operations without cancellation support | N/A | No C/C++/QPP change or new blocking production operation; no additional Valgrind requirement. |
| 25 | Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 26 | Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 27 | Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 28 | DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 29 | DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 30 | Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 31 | Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 32 | **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 33 | Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 34 | Response/output types use `private` Fields | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 35 | Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 36 | Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 37 | Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | Pass | Existing AllowedValueInfo value/display_name metadata is preserved. QName choices resolve with the actual wrapped namespace validator; scalar and repeated original/saved fields are covered. |
| 38 | Password/secret fields have `"sensitive": True` | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 39 | `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 40 | App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 41 | App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 42 | `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 43 | `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 44 | `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 45 | Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 46 | No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 47 | No bare field/option names in prose — must use backticks | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 48 | Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 49 | **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 50 | **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 51 | **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 52 | JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No DataProvider action, request/response field, app, factory, JNI dependency or installation change. |
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Fixes the wrapper abstraction at its source; no scalar fallback, skipped validation, TODO or fixture-specific branch. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Accessor and local unwrapping do not mutate provider state. Failed choice updates remain atomic; tests verify rejection followed by successful reuse and HTTP cleanup. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | No new shared mutable state; returned underlying provider retains the existing construction/read concurrency contract. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Accessor returns AbstractDataProviderType; checked instanceof precedes each cast. Tests use typed providers and exact QName identity. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | One constant-time wrapper lookup, with no new loops or metadata copies in production. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Exact categories cover omission, invalid lexical prefix, invalid namespace identity, finite choices and failed metadata updates; default/fixed omission remains valid. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public getter has return/since documentation; implemented QName design includes an attribute example. Release notes, evidence and execution records match tested behavior; docs and metadata build cleanly. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C/C++/QPP change or new blocking production operation; no additional Valgrind requirement. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No new production I/O, format strings, native buffers or credentials; HTTP tests use bounded queues/timeouts and cleanup. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 38 affected Qore suites, six supplements, 437 focused unit assertions and 468 HTTP assertions pass; native XSD output checks and unchanged both-mode corpus records supply independent validation. |

Result: 20 Pass, 42 N/A, zero Fail.
