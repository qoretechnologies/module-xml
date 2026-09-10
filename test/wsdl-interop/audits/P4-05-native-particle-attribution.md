# P4-05 audit: native counted attribution and execution

Copyright (C) 2026 Qore Technologies, s.r.o.

Date: 2026-09-10. Scope: final intended changes after `0bacf95`.
All 62 checks are individually resolved: **20 Pass / 42 N/A / 0 Fail**.

The full [audit skill](/home/david/.codex/skills/audit-changes/SKILL.md) and its
module-structure, sandboxing and cooperative-cancellation references were applied.
Data-provider checklist/development-guide scope was checked; no provider code,
new Qore module, QPP class or JNI asset changes. C dependency sources embedded in
checked CMake replacements, probes and standalone fixtures were reviewed together.
The [validation inventory](../P4-05-validation.json) records final hashes and tests.

Review corrected required empty-language all summaries, tightened malformed test
input checks, strengthened the incomplete-counter-backport probe and confined
counter changes to schema automata. The fixes and affected checks were rerun.
No workaround, scope reduction or approval exception was used. The separate
native large-count parser defect remains a failing P4-owned diagnostic and must
close before P4 acceptance. P5–P9 retain all original requirements, including
mandatory Python CI setup and the previously recorded documentation diagnostics.

Changed files include native provider patches/helpers/probes, source distribution,
Qore/Python/C regressions and diagnostics, design/example, README/release notes,
interop evidence/reports/execution record, validation inventory and this audit.
No Qore/WSDL production source changes or system installation were made.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new Qore module, layout, QPP class or module registration. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | Native 2.3 release notes describe counted attribution, abstract callbacks and nullable counter execution. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new Qore module, layout, QPP class or module registration. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new Qore module, layout, QPP class or module registration. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new Qore module, layout, QPP class or module registration. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No Qore module changed; test/worker entry points use %modern. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated .qc file changed. |
| 8. No `%include` usage (deprecated for modules) | Pass | No deprecated %include is introduced. |
| 9. Copyright 2026 on all new files | Pass | New C/CMake/Python/Qore sources and design/evidence documents carry 2026 copyright; original third-party source notices and bytes remain intact. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new Qore module, layout, QPP class or module registration. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new Qore module, layout, QPP class or module registration. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new Qore module, layout, QPP class or module registration. |
| 13. `%modern` directive present | Pass | All three Qore test/worker entry points explicitly use %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | The qtest and both .qr workers are executable (755). Python/C fixtures use explicit interpreter/compiler entry points. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Qore entry points prepend the local qlib path before requirements. Local QORE_MODULE_DIR and LD_LIBRARY_PATH identify the Debug module/core, with -b --enable-debug in workers and test commands. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project xml and core QUnit use hard requirements; external json uses %try-module and a specific missing-dependency error, never a successful skip. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | Pass | Runtime changes operate on compiler/executor memory and existing parsed nodes; no new filesystem operation. Build copies and standalone fixture inputs are explicit build/test operations. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | Pass | No new runtime networking. Existing checksum-pinned FetchContent selection remains behavior-based; provider tests use verified local source and temporary staging. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No added runtime filesystem/network operation requires a new QoreSandboxManagerHelper. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Workers use ReadOnlyFile only for explicit temporary JSON fixture inputs through the Qore API. Native qtests use in-memory StringInputStream; no direct resource-access bypass. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ loop is added. New loops are in the pure C dependency checker and standalone fixtures, without a Qore ExceptionSink/API dependency. The checker traverses finite source graphs and exact arithmetic; it does not expand occurrence counts. Existing Qore interruption/reuse tests remain in the affected gate. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ cancellation point or deprecated interrupt API is added. This increment does not claim new mid-call cancellation support in the C dependency. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No new C++ cancellation-check frequency applies; C dependency loops retain the dependency execution context described in checks 21–22. |
| 24. No blocking operations without cancellation support | Pass | No new blocking runtime I/O, sleeps or polling. Python subprocesses have bounded deadlines. Compiler graph traversal is iterative; nullable execution avoids enumerating empty iterations. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 34. Response/output types use `private` Fields | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 47. No bare field/option names in prose — must use backticks | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No DataProvider action/app/type, FactoryMap, JNI or JAR change. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Fixes address count feasibility, present-component validation, abstract callbacks and lost counter operations at their source. No fixture conditions, validation bypass, stubs or new TODOs. Existing upstream TODO comments in unchanged surrounding text are retained. The independent native wide-count diagnostic remains explicitly P4-owned under the authorized incremental plan. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Every arena/hash/content allocation is checked; all tables and owned blocks are released on success and failure. Temporary cross-products are freed immediately. Rollback counts/progress share checked allocations and existing teardown. All 134/229/15 measured fault points recover with baseline ownership; final Valgrind finds no losses or memory errors. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Production state belongs to a parser or executor. Published DAG summaries are immutable, parent maps are owned, and borrowed source pointers remain within schema ownership. No mutable global cache; standalone allocator counters are confined to one test process. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Private C structs use size_t, checked limbs, typed native pointers and exact ratio records. C casts occur in C dependency code, with no C++ casts/API changes. Qore workers use typed parameters and ExceptionInfo; no new untyped callback API. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Memoized iterative DAG traversal avoids count expansion and repeated component traversal. Sparse hash intersections avoid pairwise ordinary-name scans; wildcard comparisons are limited to relevant predicates. Temporary arithmetic products are released promptly. Billion-minimum nullable examples and the complete finite oracle finish within their bounded test deadlines. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Malformed count/math/summary input, overflow, unexpected source hashes, absent components and allocation failure are checked. Tests distinguish XSD-SYNTAX-ERROR from PARSE-XML-EXCEPTION and check reuse after failures. Four malformed summary inputs and seven invalid arithmetic operations reject. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | No public API is added. The implemented design documents formulas, ownership, finite-count provenance, callback behavior, execution marks and an executed example. README/release notes/evidence describe behavior and the separate unresolved native count range without claiming phase completion. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP method or method flag changes. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Formatting strings are fixed; size/index/key arithmetic is checked. Base-1e9 products fit uint64_t, arena headers preserve the alignment required by stored types, and no credentials or unbounded input buffer copies are introduced. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 1,000 complete finite marked-language models check 43,630 schema/document rows per mode, with no omitted cases. Python integer/Fraction checks cover 1,399 operations; exact summary fixtures include adjacent 80/81-digit thresholds and required empty all members. The focused 12-schema matrix passes; native Qore regressions check typed declaration values, invalid documents and all/nullable boundaries. |
