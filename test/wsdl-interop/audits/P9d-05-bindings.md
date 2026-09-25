# P9d-05 generated bindings and RPC accessor checks audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied `/home/david/.claude/skills/audit-changes/SKILL.md` on `develop` based on cebed58. Scope: `qlib/WSDL.qm` (`WSMessage::deserializeRpc()` omitted literal accessors as absent values; `SoapBinding` accessor qualification check; release notes); `test/wsdl-rpc-accessors.qtest`; `test/soap.qtest` (SoapUI fixture expectation); `test/wsdl-body-parts.qtest` (RPC missing-part expectation); `test/wsdl-interop/test_binding_generation.py`, `binding-messages.qr`; `assertion-ledger.json` (R2735); `design/wsdl-body-parts.md`; `PLAN.md`; `EXECUTION.md`.

All 62 checks are explicitly accounted for:

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | External module repository. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL v0.5.8 release notes describe the RPC accessor checks. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | Not affected. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | Not affected. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | Not affected. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL.qm keeps %modern. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | Not affected. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include usage. |
| 9 | Copyright 2026 on all new files | Pass | The new qtest, worker and Python test and this record carry the 2026 copyright. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | Not affected. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | Not affected. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | Not affected. |
| 13 | `%modern` directive present | Pass | The new qtest and worker use %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | The new qtest, worker and Python test are executable. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The qtest and worker use %prepend-module-path before relative %requires. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | QUnit and xml are delivered with Qore and this module; the worker uses the %try-module pattern for json. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | Not affected. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | Not affected. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | Not affected. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | N/A | No File/Socket/HTTPClient use. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | Not affected. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | Not affected. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | Not affected. |
| 24 | No blocking operations without cancellation support | N/A | No blocking operation added. |
| 25 | Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No DataProvider registration, factory, application or JNI change. |
| 26 | Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No DataProvider registration, factory, application or JNI change. |
| 27 | Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No DataProvider registration, factory, application or JNI change. |
| 28 | DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DataProvider registration, factory, application or JNI change. |
| 29 | DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No DataProvider registration, factory, application or JNI change. |
| 30 | Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No DataProvider registration, factory, application or JNI change. |
| 31 | Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No DataProvider registration, factory, application or JNI change. |
| 32 | **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No DataProvider registration, factory, application or JNI change. |
| 33 | Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No DataProvider registration, factory, application or JNI change. |
| 34 | Response/output types use `private` Fields | N/A | No DataProvider registration, factory, application or JNI change. |
| 35 | Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No DataProvider registration, factory, application or JNI change. |
| 36 | Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No DataProvider registration, factory, application or JNI change. |
| 37 | Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No DataProvider registration, factory, application or JNI change. |
| 38 | Password/secret fields have `"sensitive": True` | N/A | No DataProvider registration, factory, application or JNI change. |
| 39 | `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No DataProvider registration, factory, application or JNI change. |
| 40 | App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No DataProvider registration, factory, application or JNI change. |
| 41 | App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No DataProvider registration, factory, application or JNI change. |
| 42 | `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No DataProvider registration, factory, application or JNI change. |
| 43 | `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No DataProvider registration, factory, application or JNI change. |
| 44 | `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No DataProvider registration, factory, application or JNI change. |
| 45 | Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No DataProvider registration, factory, application or JNI change. |
| 46 | No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No DataProvider registration, factory, application or JNI change. |
| 47 | No bare field/option names in prose — must use backticks | N/A | No DataProvider registration, factory, application or JNI change. |
| 48 | Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No DataProvider registration, factory, application or JNI change. |
| 49 | **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No DataProvider registration, factory, application or JNI change. |
| 50 | **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No DataProvider registration, factory, application or JNI change. |
| 51 | **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No DataProvider registration, factory, application or JNI change. |
| 52 | JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No DataProvider registration, factory, application or JNI change. |
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Root-caused: type parts did not receive whether their accessor was present, and accessor names were matched after removing prefixes. Both policies were decided by the user on 2026-09-25: only literal type-part accessors must be unqualified (WS-I R2735), and an omitted literal accessor is an absent value. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | No C++ change; both checks throw before any value is produced. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | N/A | No shared state added. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed locals; expanded names compared as strings from XsdBase::expandElementNamespaces(). |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | One pass over the wrapper's children per message. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Qualified literal type-part accessors (prefix or default namespace) are rejected with SOAP-DESERIALIZATION-ERROR; element parts and encoded accessors may be qualified; omitted accessors decode as NOTHING in every style, empty ones as empty values (an empty int is rejected); the generated mutations (wrapper name and namespace, extra accessors, qualified literal accessors, missing and unknown document parts) are rejected. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | design/wsdl-body-parts.md 'RPC part accessors'; the R2735 ledger rows; EXECUTION.md. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | Not affected. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No format strings from input beyond %Y of names; no credentials. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | test_binding_generation.py (6 tests, pinned digest identical on CPython 3.12 and 3.14) and wsdl-rpc-accessors.qtest (6 cases, 27 assertions; its absent-value and qualified-literal cases fail against the previous module); soap.qtest's SoapUI fixture and wsdl-body-parts.qtest's RPC missing-part case now assert the absent value; the full suite (all qtests, 556 Python tests in 6 shards) passes; verify_ledger.py OK; the full suite result is recorded in EXECUTION.md. |

Result: **16 Pass / 46 N/A / zero Fail**.
