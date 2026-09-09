# P3-34 audit: native QName union validation

Copyright (C) 2026 Qore Technologies, s.r.o.

The full audit-changes checklist and referenced module-structure, sandboxing,
cooperative-cancellation and DataProvider guides were applied to the exact
checksum-pinned dependency patch, native probe, provider integration tests,
Qore/Python regressions and documentation. WSDL and Qore core source are unchanged.

Checklist: **22 Pass / 40 N/A / 0 Fail**. Complete verification, exact source
hashes, corpus comparison and the existing P6 assertions are recorded in
[EXECUTION.md](../EXECUTION.md). Independently reduced reader API findings are
explicitly assigned to the next P3 increment in the [evidence](../qname-union-validator-evidence.md).

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | Existing external binary module; no Qore module index entry. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | Native xml 2.3.0 release notes document ordered union matching and preserved invalid-input diagnostics. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing native xml, namespace-probe and docs-module targets build successfully with Debug and /usr prefix; no new module registration. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No user module or QMOD entry added. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No .qm file is changed. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No .qm file is changed. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated .qc file is added or changed. |
| 8. No `%include` usage (deprecated for modules) | Pass | No deprecated %include usage is introduced. |
| 9. Copyright 2026 on all new files | Pass | All authored test, CMake, native-probe, design, evidence and audit files carry 2026 notices; third-party notices and sources remain intact. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No module layout change. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module file. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No QPP class change. |
| 13. `%modern` directive present | Pass | The new qtest and fixture driver explicitly use %modern; the executed design example does too. |
| 14. Executable permission set (`chmod +x`) | Pass | test/xml-qname-unions.qtest and qname-union-validator.qr are executable. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The qtest prepends repository qlib before requirements; xml is the same-repository binary selected from build-debug. The diagnostic has no user-module dependency. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | xml is supplied by this repository, QUnit by Qore; the diagnostic guards the external json binary with %try-module and an explicit missing-module error. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | Pass | The production fix adds no filesystem operation. C fixtures parse memory with XML_PARSE_NONET; provider builds use explicit temporary test directories. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | Pass | No network operation is added to production. Runtime fixtures have no external resources; independent oracle jobs are pinned and offline. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | The production patch adds no filesystem/network operation requiring a sandbox helper. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Only the diagnostic reads its explicitly named fixture using ReadOnlyFile. Test artifacts, subprocesses and local build/install staging are justified test I/O; production I/O is unchanged. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | Pass | The dependency fix adds no loop. Native-probe loops traverse fixed tiny tables/documents; the cancellation regression verifies the existing public reader interruption path. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No cancellation API is added or changed; the existing reader cancellation path is exercised. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No new unbounded production loop or cancellation-check frequency change. |
| 24. No blocking operations without cancellation support | Pass | No blocking production operation is added. Tests use bounded subprocess deadlines and deterministic interruption; no sleeps or polling loops. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 34. Response/output types use `private` Fields | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 47. No bare field/option names in prose — must use backticks | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | The fix propagates the existing fireErrors contract to the QName helper. It retains the candidate error return and guards only its diagnostic; no input rewriting, fallback override, TODO or stub. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | No production allocation/lifetime change. Rejected QName temporary names still free on the same return path. C fixture cleanup releases reader before validation context, schema and documents; both full native and Qore Valgrind runs report zero errors and zero definite/indirect/possible loss. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | The flag is a call parameter; no shared state is introduced. Test diagnostics belong to the individual parser/validation invocation, and lookup tables are immutable. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | The private C helper receives an int flag consistently at its only call site. C probe uses typed libxml2 pointers and fixed integer matrices; Qore helpers have typed arguments/returns and ExceptionInfo catches. Native C passes -Wall -Wextra -Werror. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | One flag check replaces an inappropriate diagnostic allocation/callback during a failed trial. Member traversal, XML copies and asymptotic costs are unchanged. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | All-invalid QName/union values still reject. Tests cover invalid content and attributes separately, namespace-dependent enumeration rejection, callback counts, later success and cancellation cleanup. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Implemented design, executable example, README, native release notes and independent evidence describe the root cause, selection behavior and unpatched-oracle differences. No public method is added or modified. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP method or flags change. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Fixed diagnostic format strings and bounded snprintf buffers are retained. CMake checks full original/final source hashes, leaves fetched sources intact and rejects unexpected overrides. No credentials or user-controlled native format strings. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | The exact previous dependency fails seven valid native pairs. Corrected native DOM/streaming probes pass 148 pairs; Qore and Xerces agree on 300 independent documents. All 18 provider tests, 82 Qore suites, eight execution-mode/timezone runs, unchanged corpus reports and Valgrind pass. The separately root-caused reader API defects are explicitly assigned to the next P3 increment as permitted by the execution plan. |
