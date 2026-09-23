# P8-07 ledger rows and P8 acceptance audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied `/home/david/.claude/skills/audit-changes/SKILL.md` to P8-07. Scope: the SOAP 1.2 struct member label check, the RPC response struct name and the SOAP 1.2-encoded header style in `qlib/WSDL.qm` with its release note; `design/soap-encoding.md`; the new cases in `test/soap12-encoding.qtest` and `test/soap12-rpc.qtest`; the 26 rows of `test/wsdl-interop/assertion-ledger.json` and the P8 rule in `verify_ledger.py`.

All 62 checks are explicitly accounted for:

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | External module repository. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | The WSDL v0.5.8 release notes describe the member label, response struct name and SOAP 1.2-encoded header changes; design/soap-encoding.md documents them. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No module added. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No module added. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No module added. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | qlib/WSDL.qm keeps its %modern directive. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No .qc changed. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include usage. |
| 9 | Copyright 2026 on all new files | Pass | No new source files; this record carries the 2026 copyright. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No module added. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No module added. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No C++ or QPP change; the changes are Qore module code in qlib/WSDL.qm, tests and documentation. |
| 13 | `%modern` directive present | Pass | The changed suites keep %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | The changed suites keep their executable permissions. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The changed suites keep %prepend-module-path before their relative %requires. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | No module dependency was added. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ or QPP change. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ or QPP change. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ or QPP change. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | No I/O was added. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ or QPP change. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ or QPP change. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ or QPP change. |
| 24 | No blocking operations without cancellation support | N/A | No C++ or QPP change. |
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
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Every routed row is covered against the current text; the three defects found are root-caused and fixed; the first, too broad fix for member labels was withdrawn in favor of a targeted check. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | The checks only read the value being decoded and throw SOAP-DESERIALIZATION-ERROR before any result is built; no state is kept. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | No shared state; the checks use the per-thread QName scopes. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed lookups of declared members; the header style check names both supported encoding constants. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | One pass over a struct's members per decode; the declared-member table is built from the type's own maps. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | A member in another namespace, a misnamed invocation struct and argument mismatches are rejected with descriptive errors and the SOAP 1.2 subcodes. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | design/soap-encoding.md, the release notes, PLAN and EXECUTION record the behavior and the acceptance; docs build with no warnings. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP change. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No credentials or format strings. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Seven new cases in soap12-encoding.qtest and soap12-rpc.qtest demonstrate the formerly unmapped requirements, and those for the fixed defects fail against the previous module; verify_ledger.py checks every mapping and quote; the full suite passes except the two core-blocked IEEE gates. |

Result: **18 Pass / 44 N/A / zero Fail**.
