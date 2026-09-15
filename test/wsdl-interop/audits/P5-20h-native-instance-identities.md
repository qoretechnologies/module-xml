# P5-20h native instance identity audit

Copyright (C) 2026 Qore Technologies, s.r.o.

The audit-changes skill and all five referenced guides were consulted for this
commit. All 62 checklist items are classified individually below. The audit
covers the exact native patches, configure probes, regression fixtures/tests,
documentation and approved decision record; no production Qore/DataProvider
implementation changes are included.

Expanded testing and review found unchecked identity/QName formatter allocations,
incorrect expanded-name formatting, and stale invalid-attribute match history.
Each root cause was fixed and the affected tests were rerun. Exact final sources,
guide hashes and validation logs are in [P5-20h-validation.json](../P5-20h-validation.json).

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No production Qore module, QPP class, registration or module-layout change. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | N/A | No production Qore module, QPP class, registration or module-layout change. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No production Qore module, QPP class, registration or module-layout change. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No production Qore module, QPP class, registration or module-layout change. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No production Qore module, QPP class, registration or module-layout change. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No production Qore module, QPP class, registration or module-layout change. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No production Qore module, QPP class, registration or module-layout change. |
| 8 | No `%include` usage (deprecated for modules) | N/A | No production Qore module, QPP class, registration or module-layout change. |
| 9 | Copyright 2026 on all new files | Pass | Authored CMake, C, Python, Qore, design, evidence and decision files carry 2026 notices; fixture copyright is recorded in README; third-party notices remain intact. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No production Qore module, QPP class, registration or module-layout change. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No production Qore module, QPP class, registration or module-layout change. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No production Qore module, QPP class, registration or module-layout change. |
| 13 | `%modern` directive present | Pass | The new Qore regression declares %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | The new .qtest and Python regression are executable (0755). |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The test prepends local qlib before requirements; the frozen ELF and explicit local Debug binary-module/qlib paths were verified. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | QUnit and same-repository XML are required; external json uses %try-module and an explicit missing-module error. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | Pass | No filesystem operations enter native assessment or formatting. CMake writes exact-hash guarded build-tree replacements; source preservation/distribution/guards are tested. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | Pass | No network operation is added; pinned/offline provider selection remains covered. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No new production resource access. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Only the test reads its local JSON fixture; no production Qore resource access changes. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | Private libxml2 C dependency loops do not call Qore APIs; no Qore C++ loop is introduced. Existing module reader/cancellation callback boundaries are retained. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No cancellation function is introduced or replaced. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No Qore C++ cancellation polling loop is introduced; private attribute/history and formatter scans remain linear. |
| 24 | No blocking operations without cancellation support | Pass | No new blocking or I/O operations; private formatter scans append through amortized growable buffers. |
| 25 | Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No DataProvider action, type, application, factory or JNI change. |
| 26 | Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No DataProvider action, type, application, factory or JNI change. |
| 27 | Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No DataProvider action, type, application, factory or JNI change. |
| 28 | DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DataProvider action, type, application, factory or JNI change. |
| 29 | DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No DataProvider action, type, application, factory or JNI change. |
| 30 | Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No DataProvider action, type, application, factory or JNI change. |
| 31 | Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No DataProvider action, type, application, factory or JNI change. |
| 32 | **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No DataProvider action, type, application, factory or JNI change. |
| 33 | Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No DataProvider action, type, application, factory or JNI change. |
| 34 | Response/output types use `private` Fields | N/A | No DataProvider action, type, application, factory or JNI change. |
| 35 | Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No DataProvider action, type, application, factory or JNI change. |
| 36 | Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No DataProvider action, type, application, factory or JNI change. |
| 37 | Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No DataProvider action, type, application, factory or JNI change. |
| 38 | Password/secret fields have `"sensitive": True` | N/A | No DataProvider action, type, application, factory or JNI change. |
| 39 | `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No DataProvider action, type, application, factory or JNI change. |
| 40 | App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No DataProvider action, type, application, factory or JNI change. |
| 41 | App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No DataProvider action, type, application, factory or JNI change. |
| 42 | `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No DataProvider action, type, application, factory or JNI change. |
| 43 | `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No DataProvider action, type, application, factory or JNI change. |
| 44 | `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No DataProvider action, type, application, factory or JNI change. |
| 45 | Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No DataProvider action, type, application, factory or JNI change. |
| 46 | No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No DataProvider action, type, application, factory or JNI change. |
| 47 | No bare field/option names in prose — must use backticks | N/A | No DataProvider action, type, application, factory or JNI change. |
| 48 | Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No DataProvider action, type, application, factory or JNI change. |
| 49 | **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No DataProvider action, type, application, factory or JNI change. |
| 50 | **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No DataProvider action, type, application, factory or JNI change. |
| 51 | **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No DataProvider action, type, application, factory or JNI change. |
| 52 | JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No DataProvider action, type, application, factory or JNI change. |
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Builtin attribute and selected value-variety rules are implemented directly. No fixture-specific production logic, ignored failures or stubs. Approved nil/skip/projection policies are explicitly recorded; WSDL tuple/P5 acceptance remains open. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Borrowed default values are detached before conversion; declaration namespace scope is restored on errors; context-owned anonymous types outlive keys. All formatter buffers have checked allocation/append/detach and cleanup. Invalid-attribute match history is unwound. 162 single/persistent fault positions and six invalid lexical/reuse cases pass exact live-count checks; native/Qore Valgrinds are clean. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | New type, key flags and assessment state belong to a validation context; no shared mutable production state. Fault controls exist only in a single-threaded test translation unit. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed C schema pointers/enums and Qore collections retain their types. The private context/key layouts gain embedded type and nil/list state; public API and public structure layouts are unchanged. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Whitespace and canonical formatting use linear scans and growable buffers instead of repeated growing-string concatenation. Attribute history cleanup traverses existing states once. Only matched defaults are reassessed to retain selected union variety. Existing tuple hash collision comparisons remain unchanged. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | 121 positive/negative cases cover presence, lexical rejection, wildcards, cardinality, nil/empty/list/atomic/union/default/keyref cases; tests assert public error categories, unchanged XML and reuse. Source guards reject missing, duplicate and unexpected native translation units. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | README, release notes, implemented design/examples, normative/oracle evidence, approved projection decision and execution records are updated; native docs build cleanly. No public method is added. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP method or flags change. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Checked growable buffers and exact source hashes; fixed format strings; no credentials or added external access. Attribute/history indices are bounded by their native counts and depth checks. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | All 121 native DOM/stream outcomes and 434 public assertions pass. Pinned Xerces agrees on 118 cases; three cardinality differences are explained and remain invalid. 65 affected suites pass 28,635 assertions without warnings/errors; provider/survey/docs and allocation tests pass. All four corpus reports are unchanged. |

Result: 18 Pass, 44 N/A, zero Fail. No install, push, main-Qore mutation or CI execution.
