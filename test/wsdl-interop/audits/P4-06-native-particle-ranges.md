# P4-06 audit: exact native occurrence ranges

Copyright (C) 2026 Qore Technologies, s.r.o.

Date: 2026-09-10. Scope: final intended changes after `35e54e3`.
All 62 checks are individually resolved: **20 Pass / 42 N/A / 0 Fail**.

The full [audit skill](/home/david/.codex/skills/audit-changes/SKILL.md) and its
module-structure, sandboxing and cooperative-cancellation references were applied.
Data-provider checklist/development-guide scope was checked; no provider code,
new Qore module, QPP class or JNI asset changes. C dependency replacements,
helpers, probes and standalone fixtures were reviewed together. The
[validation inventory](../P4-06-validation.json) records final hashes and tests.

Review checked exact bounds through all six schema counter-construction paths,
finite-versus-unbounded fast paths, source-range validation before absent
component removal, descriptor transfer/cleanup, every schema token increment,
rollback storage and both diagnostic snapshots. The executor fixture was expanded
to exercise 80/81-digit boundaries, finite INT_MAX, separate counter offsets,
unbounded saturation and diagnostic independence; it was rebuilt and rerun under
Valgrind after the full provider gate. No production source changed afterward.

Changed files include the native provider range fix and helpers, behavior probe,
source distribution, C/Python/Qore regressions, implemented design/example,
README/release notes, current range report, validation/execution records and this
audit. The historical failing report and upstream source hashes remain intact.
No Qore/WSDL production source changes or system installation were made. P4
continues with ordered message conversion, metadata and samples; P5–P9 retain
all original requirements and separately recorded diagnostics.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new Qore module, layout, QPP class or module registration. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | Native 2.3 release notes describe exact occurrence bounds, finite/unbounded counters, rollback and behavior-based provider detection. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new Qore module, layout, QPP class or module registration. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new Qore module, layout, QPP class or module registration. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new Qore module, layout, QPP class or module registration. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No Qore module changed; test/worker entry points use %modern. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated .qc file changed. |
| 8. No `%include` usage (deprecated for modules) | Pass | No deprecated %include is introduced. |
| 9. Copyright 2026 on all new files | Pass | New C/CMake/Qore sources, design and reports carry 2026 copyright. Original third-party source notices and hashes remain unchanged. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new Qore module, layout, QPP class or module registration. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new Qore module, layout, QPP class or module registration. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new Qore module, layout, QPP class or module registration. |
| 13. `%modern` directive present | Pass | The new xml-particle-ranges.qtest explicitly uses %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | The new qtest is executable (755); Python/C fixtures use explicit interpreter/compiler entry points. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The new qtest prepends the local qlib path before requirements. Commands use local Debug module/core paths and -b --enable-debug. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | The new qtest requires project xml and core QUnit directly; it adds no external binary dependency. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | Pass | Runtime changes operate on compiler/executor memory and existing parsed nodes; no new filesystem operation. Build copies and standalone fixture inputs are explicit build/test operations. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | Pass | No new runtime networking. Existing checksum-pinned FetchContent selection remains behavior-based; provider tests use verified local source and temporary staging. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No added runtime filesystem/network operation requires a new QoreSandboxManagerHelper. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | The new qtest uses in-memory StringInputStream. It introduces no File/Dir/Socket/HTTPClient access. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ loop is added. The pure C dependency helpers operate on decimal digits and limbs without a Qore ExceptionSink/API dependency. They never expand occurrence values. Existing interruption/reuse suites pass in the affected gate. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ cancellation point or deprecated interrupt API is added. This increment does not claim new mid-call cancellation support in the C dependency. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No new C++ cancellation-check frequency applies; C dependency loops retain the dependency execution context described in checks 21–22. |
| 24. No blocking operations without cancellation support | Pass | No new blocking runtime operation, sleep or polling. Test subprocesses have bounded deadlines. Exact counter increments and comparisons use storage proportional to bound digits. |
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
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | The native lexical/sentinel defect is fixed through parsing, compilation and execution. Numeric maxima remain finite, including the old sentinel itself. No rounding, fixture special cases, numerical cap, validation bypass or TODO is introduced. Remaining ordered WSDL conversion is explicitly P4-owned under the incremental plan. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Bounds, attribute content and counter/runtime allocations are checked. Automata own descriptors until successful transfer to compiled regexps; existing teardown frees every descriptor. Counter values/progress/diagnostics share checked allocations. All 6 executor and 6 schema-bridge failure points restore baseline ownership and allow fresh reuse. Prior checker/executor fixtures (229/15 points) and Valgrind pass. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Bounds are immutable after compilation. Mutable counters, progress and diagnostic snapshots belong to individual executors. Source-node/count-source pointers stay under schema ownership. No mutable global runtime cache is added; test allocator state is process-local. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | C helpers use explicit lexical/bounds structs, size_t offsets, uint32_t limbs and checked uint64_t integer conversion. Casts occur in C dependency sources, not C++. Qore tests have typed inputs/results and ExceptionInfo error handling. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Decimal normalization/comparison and limb conversion are linear in input digits. Runtime counters use fixed capacity and small finite bounds keep integer fields. Unbounded saturation at the minimum is language-equivalent and avoids overflow. No occurrence expansion; large nullable cases and the complete oracle finish within bounded deadlines. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Lexical input and min<=max are checked before absent-particle removal; all-group restrictions remain enforced. Five invalid counter configurations, 33 malformed lexical positions, source-hash guards, DOM/reader schema-versus-document error categories and allocation recovery pass. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | No public method is added. The exact-range design documents source provenance, bound adjustment, nullable/unbounded semantics, ownership, storage cost and an executed batch example. README, native release notes, current/historical reports, validation and execution status are updated without claiming P4 completion. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP method or method flag changes. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | All formatting strings are fixed. Bound capacities, descriptor allocations and cumulative snapshot storage use checked size arithmetic. Limb values fit uint32_t and conversion uses checked uint64_t. Private execution tests verify distinct offsets, resets, rollback and diagnostic copies; Valgrind detects no invalid access. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | All 881 generated boundary cases match Python integer expectations; 1,000 complete finite models pass 43,630 DOM/reader rows in each of four execution modes. The focused range suite passes 8 cases/534 assertions per mode. Actual private execution is seeded at 80/81-digit boundaries, including unbounded operation and finite INT_MAX. All 16 historical range requirements now pass with identical fixture hashes. |
