# Compiled constant regular expressions audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied `/home/david/.claude/skills/audit-changes/SKILL.md` to the uncommitted change on main `develop`
based on 8d9943d. Scope: `qlib/WSDL.qm`.

`test_regex_classes.py` and `test_ieee_facets.py` exceeded the shared list-values worker's 90 s limit. On an
identical manifest the worker took 91.4 s at HEAD against 25.9 s at `039958f` (2026-09-09), with identical
output. One cause was a defect: every Name/NCName/QName check compiled a multi-kilobyte Unicode character
class with `regex()` on each call. Namespace prefix checks, XSD pattern character classes and the XSD regex
parser did the same. P7 envelope validation and later identity work multiplied the calls. The rest of the
growth is spread over validation added in P5 to P7 and is handled by the separate performance pass.

All 62 checks are explicitly accounted for:

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | External module repository. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL v0.5.8 release notes in `qlib/WSDL.qm` describe the change. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No module added. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No module added. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No module added. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | `qlib/WSDL.qm` keeps its existing `%modern` directive and no redundant directives. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No .qc changed. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include usage. |
| 9 | Copyright 2026 on all new files | Pass | No new file except this record, which carries the 2026 copyright. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No module added. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No module added. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No C++ or QPP change. |
| 13 | `%modern` directive present | N/A | No test changed. |
| 14 | Executable permission set (`chmod +x`) | N/A | No test changed. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | N/A | No test changed. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | N/A | No test changed. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ change. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ change. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ change. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | No I/O classes are used; the change uses only the Qore `Regex` class and regex operators. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ change. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ change. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ change. |
| 24 | No blocking operations without cancellation support | N/A | No C++ change. |
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
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | A complete fix of one defect class: every constant regular expression on a WSDL validation path is compiled once instead of on every call. The two remaining runtime calls are the legacy string branch of `XsdPatternConstraintHelper::matches()`, reached only by serialized pre-0.5.8 patterns, and SOAP-encoded array dimension parsing, which is not a validation hot path. Both are unchanged. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Static `Regex` members compile constant patterns at class initialization. `XsdRegexCharacterPredicate` catches only `REGEX-COMPILATION-ERROR` and rethrows it unchanged when a match evaluates that node, so error timing and text are identical. `sampleForPattern()` keeps its single try/catch around both compilation and matching, as before. Other exceptions, including cancellation, propagate. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Compiled objects are immutable after construction and shared across concurrent matches. Qore `Regex::match()` allocates match data per call and uses a thread-local JIT context (`lib/QoreRegex.cpp`, `lib/QoreRegexBase.cpp`). Per-match state stays in each `XsdRegexMatcher`. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed members `*Regex`, `*hash<ExceptionInfo>` and `list<*XsdRegexCharacterPredicate>`. No untyped values are introduced. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | On an identical 384-row manifest the list-values worker drops from 91.4 s to 79.7 s with byte-identical output. The full suite drops from 6,043 s to 5,401 s. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Validation outcomes and diagnostics are unchanged. `Regex` and `regex()` raise the same `REGEX-COMPILATION-ERROR` code and message, which was checked directly. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | The new internal `XsdNameLexicalHelper::matches()` and `XsdRegexCharacterPredicate` are commented. The release note records the behavior. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP change. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Patterns are module constants or XSD-derived character classes, as before; no credentials. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Static `Regex` and `regex()` agree on Unicode, `\A`/`\z` and multi-code-point probes. 36 targeted name/QName/NOTATION/regex/pattern/sample/namespace suites pass. The full suite passes 449 targets, 3,581 cases and 172,677 assertions, except the two IEEE gates blocked on the documented Qore core NaN-boxing defect. The list-values worker output is byte-identical. |

Result: **14 Pass / 48 N/A / zero Fail**.
