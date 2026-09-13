# P5-17a native ID bindings audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied the full audit-changes skill and all five referenced design guides on
2026-09-13 to the final changes, parent `6a41ffc`. Guide hashes are unchanged
from the previously read versions recorded in P5-16h. The private third-party C
correction is reviewed for memory, threading, bounds and cleanup as native code.
See [evidence](../native-id-bindings-evidence.md) and [inventory](../P5-17a-validation.json).

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 8 | No `%include` usage (deprecated for modules) | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 9 | Copyright 2026 on all new files | Pass | All authored code/tests/design/evidence carry copyright 2026; fetched source and third-party notices remain unchanged. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new Qore module, module layout, QPP class or user-module registration. |
| 13 | `%modern` directive present | Pass | xml-id-bindings.qtest uses %modern; the Python integration is a separate executable unittest entry point. |
| 14 | Executable permission set (`chmod +x`) | Pass | Both new test entry points are mode 0755. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The Qore test prepends local qlib before requirements; QORE_MODULE_DIR loads the local Debug xml module. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Same-project xml and Qore QUnit use hard requirements; external json uses %try-module with a clear failure. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | Pass | Production C correction performs no filesystem operations. Standalone test fixture reads and CMake build-tree writes are offline test/build operations. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | Pass | No new production network operation. Fixtures use XML_PARSE_NONET; existing provider fetch policy is unchanged. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No new Qore filesystem/network entry point or resource callback. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | The Qore test reads its local committed JSON fixture using ReadOnlyFile; no service, credentials or external write. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ loop changes. Private libxml2 C has no Qore dependency. Context-owned traversal/hash loops retain existing runtime entry and I/O cancellation boundaries; no per-item Qore hook is claimed. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ cancellation hook is added or changed; no deprecated hook is introduced. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No new C++ runtime loop. Existing cancellation regressions pass in the final native suites. |
| 24 | No blocking operations without cancellation support | Pass | No blocking operation introduced. Early reader close/recovery and existing cancellation/concurrent-reader regressions pass. |
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
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | The missing cvc-id root check and union-trial DOM side effects are fixed at their native source. No fixture-specific production branches, skips or relaxed expectations; the native prerequisite is complete while WSDL/P6 failures remain tracked. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Each allocation is checked; failed hash insertion frees its payload, validation reset/destruction frees the table, and fatal diagnostics retain memory errors. 1,347 allocation positions check required-failure rejection, optional post-verdict reset and matching public/private verdicts. Valgrind confirms cleanup. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | The registry and monotonic owner counter belong to one validation context; schema metadata is read-only. No mutable shared state or saved pointers to recycled reader/SAX nodes. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Native C uses libxml2 typed pointers, value enums and an unsigned-long identity with overflow protection. Qore fixture data uses typed list/hash members; no new public loose API or C++ cast. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Token recording uses a hash table and one closure scan; it stores one owner plus a conflict bit per token. The 1,000-forward-reference case tests growth. Identity-capable values alone request additional computation; traversal uses existing validated type graphs. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Tests cover dangling/duplicate refs, repeated same-owner IDs, defaults, selected union/list items, nil, wildcards, dynamic types and subtree scope. Native negative APIs assert PARSE-XML-EXCEPTION/XSD-ERROR. Counter exhaustion and allocation errors reject; reuse frees old state. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | The durable design, README, release notes, executable example shapes, requirement evidence and separate corpus-mode accounting explain behavior and limits. No new public method requires additional QPP API documentation. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP method or flag change. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Diagnostic format strings are constant; token data is passed as arguments. Owner counter overflow and allocation sizes are checked; no credentials or new external I/O. Build-tree source hashes fail closed. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Normative XSD owner/default rules and WG issue 9922 adjudicate ten pinned Xerces disagreements explicitly. The final probe has 78 document cases; Qore tests assert values and error categories. Full/supplemental native suites, provider tests, allocation tests and both unchanged corpus modes are recorded in the inventory. |

Result: 18 Pass, 44 N/A, 0 Fail.
