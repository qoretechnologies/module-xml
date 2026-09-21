# NOTATION identity gate update audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied `/home/david/.claude/skills/audit-changes/SKILL.md` to the uncommitted changes on main
`develop` based on 1ea8a76. Scope: `test/wsdl-interop/test_wsdl_notation_values.py`,
`notation-values-evidence.md` and `EXECUTION.md`. No production code changed.

`test_wsdl_notation_values.py` failed on 24 rows after the SOAP 1.2 fixture actions were fixed. A
bisect showed `9b8276d` (P5-20j scoped identity tuples) as the behavior change. Its expectations predate
that commit: 16 duplicate-NOTATION rows are now correctly rejected at decoding, and 8 legacy
qname-same-name rows are now rejected at serialization under the approved legacy projection policy.

All 62 checks are explicitly accounted for:

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | External module repository. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | N/A | No module behavior changed. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No module added or changed. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No module added or changed. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No module added or changed. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No .qm changed. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No .qc changed. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include usage. |
| 9 | Copyright 2026 on all new files | Pass | The edited gate and evidence already carry the 2026 copyright; no new file other than this record, which carries it. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No module added or changed. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No module added or changed. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No production, C++, QPP or module change; this updates a Python gate and its evidence only. |
| 13 | `%modern` directive present | N/A | No Qore test or script changed; the worker `notation-values.qr` is unchanged. |
| 14 | Executable permission set (`chmod +x`) | Pass | The gate keeps mode 100755 (`git diff` shows no mode change). |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | N/A | No Qore test or script changed. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | No dependency changed; the gate still uses `lxml` and the pinned Xerces oracle. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No production, C++, QPP or module change; this updates a Python gate and its evidence only. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No production, C++, QPP or module change; this updates a Python gate and its evidence only. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No production, C++, QPP or module change; this updates a Python gate and its evidence only. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | No I/O usage changed. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No production, C++, QPP or module change; this updates a Python gate and its evidence only. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No production, C++, QPP or module change; this updates a Python gate and its evidence only. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No production, C++, QPP or module change; this updates a Python gate and its evidence only. |
| 24 | No blocking operations without cancellation support | N/A | No production, C++, QPP or module change; this updates a Python gate and its evidence only. |
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
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | No product code changes and no assertion is relaxed. Two special cases that recorded superseded behavior as accepted "findings" are removed. notation-alias rows now take the generic invalid-document path with the exact diagnostic asserted. The legacy qname-same-name rows follow the approved policy in `legacy-identity-projection.md`, asserting the decoded identities, error code and exact message. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | N/A | No production, C++, QPP or module change; this updates a Python gate and its evidence only. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | N/A | No production, C++, QPP or module change; this updates a Python gate and its evidence only. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Expected identities and diagnostics are exact typed literals; comparisons use `assertEqual` rather than substring matches. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | N/A | No production, C++, QPP or module change; this updates a Python gate and its evidence only. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Every row is on one of three explicit paths. Any unexpected error, invalid output or identity change fails the gate. The matrix counts are pinned exactly, so a path cannot silently absorb extra rows. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | The docstring, `notation-values-evidence.md` (resolution section) and `EXECUTION.md` describe the change. The stale method name `test_bindings_and_reported_identity_gaps` becomes `test_bindings_identities_and_legacy_projection`. Only historical validation inventories reference the old name. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No production, C++, QPP or module change; this updates a Python gate and its evidence only. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No credentials. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Both tests pass: 2,736 binding rows and 1,288 outputs validated by the Xerces oracle. Against the pre-`9b8276d` WSDL (temporarily restored, then put back) the gate fails on every notation-alias row, so the new assertions are not vacuous. A bisect confirmed `9b8276d` as the behavior change. |

Result: **11 Pass / 51 N/A / zero Fail**.
