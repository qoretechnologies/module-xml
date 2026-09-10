# P4-02 audit: bounded ordered particle recognition

Copyright (C) 2026 Qore Technologies, s.r.o.

Date: 2026-09-10. Scope: final changes after `47d14ea` listed below.
All 62 checks are individually resolved: 19 Pass / 43 N/A / 0 Fail.

The full [audit skill](/home/david/.codex/skills/audit-changes/SKILL.md) and its
Qore module-structure, sandboxing and cooperative-cancellation design references
were applied. DataProvider registration and native-code sections do not apply.
No user approval exception or workaround was used.

Changed code is `qlib/WSDL.qm`, `test/wsdl-particle-matching.qtest`,
`particle-matching.qr` and `test_particle_matching.py`. Documentation consists of
the implemented particle design, README, matching evidence, execution record,
current/coverage reports, this audit and the P4-02 validation inventory.

The [validation inventory](../P4-02-validation.json) contains the exact final
source/runtime hashes and all 102 suite results. Local logs use
`/tmp/wsdl-p4-02-`. The native module hash is unchanged. The three deliberately
caught comparator assertions in soap.qtest are included in its reported total;
all 20 test cases pass. The independently recorded 22 broad-documentation
warnings remain failing P9 diagnostics, outside the passing affected docs target.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, module layout, QPP class or build registration. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL v0.5.8 release notes document the new structural predicate. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module, module layout, QPP class or build registration. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, module layout, QPP class or build registration. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new module, module layout, QPP class or build registration. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | Existing WSDL module and new test/worker use %modern without redundant directives. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated .qc file changed. |
| 8. No `%include` usage (deprecated for modules) | Pass | No deprecated %include introduced. |
| 9. Copyright 2026 on all new files | Pass | Every new authored source, test, evidence, inventory and audit file carries copyright 2026. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, module layout, QPP class or build registration. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, module layout, QPP class or build registration. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, module layout, QPP class or build registration. |
| 13. `%modern` directive present | Pass | The qtest and Qore worker explicitly use %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | New qtest and Qore worker have executable mode 755. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Both test entry points prepend local qlib before relative WSDL requirements; QORE_MODULE_DIR selects the local XML Debug module. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project XML and core QUnit use hard requirements; the external json dependency uses %try-module and an explicit missing-dependency error. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No native source, filesystem or network operation added. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No native source, filesystem or network operation added. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No native source, filesystem or network operation added. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production recognition is entirely in memory. The test worker explicitly reads its supplied local case manifest. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ change. Qore loop cancellation remains active; the interrupt/reuse case passes in all four execution modes. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ change. Qore loop cancellation remains active; the interrupt/reuse case passes in all four execution modes. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ change. Qore loop cancellation remains active; the interrupt/reuse case passes in all four execution modes. |
| 24. No blocking operations without cancellation support | Pass | No new blocking production operation. Test processes and queue/barrier cleanup use bounded deadlines; no sleep or polling. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 34. Response/output types use `private` Fields | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 47. No bare field/option names in prose — must use backticks | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No DataProvider action/app/type registration, FactoryMap, JNI dependency or JAR installation change. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | The structural predicate is fully implemented without stubs or fixture-specific production behavior. Ordered message integration remains an explicit subsequent P4 increment; its existing corpus failures remain failures under the authorized incremental plan. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Qore owns all local graph and matcher references. Exceptions discard call-local state; malformed reconstructed graphs, cancellation and subsequent reuse are tested. No native allocation changed; Valgrind is not required for this Qore-only increment. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Graphs are finalized before thread sharing. Compilation and recognition caches are local to each call, with no mutable shared match state. Four concurrent workers pass with deterministic start/completion barriers. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Token callbacks use code<bool(int, string)>, graph nodes use typed hashdecls and enum kinds, child names are list<string>, and occurrence counts remain exact decimal strings. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Compilation retains shared group definitions and never expands numeric counts. Tree automata handle ordinary counts; memoized endpoints preserve shared continuations and finite gaps. Documented polynomial bounds cover 10,000 names, 1,000 positions, 80 nested counts and a compact shared DAG. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Tests cover malformed expanded names, namespace mismatches, missing/invalid all members and placement, empty languages, exact count gaps, zero components, missing wildcard state, indirect cycles and unresolved restored references with exact error categories. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Both public methods document return values, matching inputs and relevant errors/caveats. The invoice example executes successfully and affected docs-WSDL builds without warnings. Design, README, release notes, independent evidence and execution record agree on the structural scope. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP method or flag changed. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No credentials or user-controlled format strings. Expanded names and restored wildcard constraints are validated. Count loops are bounded by input length before integer conversion; untrusted schema counts do not allocate expanded graphs. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 102 affected Qore suites pass: 1,031 cases and 43,488 reported assertions. Matching/model/scalar suites and 2,160 bound-part matching rows pass in all four execution modes. Independent validators and normative empty/zero-particle rules determine expected results; exact validator defects are asserted. All 2,411 survey rows and 144 coverage failure records are unchanged; 1,260 strict directions pass. |
