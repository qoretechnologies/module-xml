# P4-03 audit: exact particle attribution

Copyright (C) 2026 Qore Technologies, s.r.o.

Date: 2026-09-10. Scope: final changes after `e71a61d` listed below.
All 62 checks are individually resolved: 19 Pass / 43 N/A / 0 Fail.

The full [audit skill](/home/david/.codex/skills/audit-changes/SKILL.md), Qore
module-structure, sandboxing and cooperative-cancellation design references were
applied. DataProvider registration and native-code sections do not apply. No
workaround or approval exception was used.

Changed code is `qlib/WSDL.qm`, `test/wsdl-particle-ambiguity.qtest`,
`particle-ambiguity.qr` and `test_particle_ambiguity.py`. Documentation includes
the implemented particle design, README, attribution evidence and native failing
diagnostic inventory, current/coverage reports, execution record, this audit and
[P4-03-validation.json](../P4-03-validation.json). The inventory records final
source/runtime hashes, complete suite results and audit-added test coverage.
Local logs use `/tmp/wsdl-p4-03-`. No native source or binary changed. The three
intentionally caught comparator negatives in soap.qtest retain their existing
accounting; all 20 cases pass. The 22 broad-documentation diagnostics remain
explicit P9 failures, outside the passing affected docs target.

Audit identified missing direct assertions for unused groups, base/extension
boundaries and zero-count absent ambiguous subgraphs. These were added and pass
in AST, IR, JIT and tiered modes; no production change was needed after the full
gate. The construction recovery test had already exposed and verified the fix
for validation after shared occurrence mutation.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, module layout, QPP class or build registration. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL v0.5.8 release notes document construction-time attribution and validateDeterminism(). |
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
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production attribution is entirely in memory. The worker reads only its explicitly supplied local case manifest through core sandboxed ReadOnlyFile. |
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
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Exact weak attribution is implemented without stubs, fixture conditions or count approximation. Independent native defects were root-caused and remain four failing P4-owned records; ordered message integration remains the authorized subsequent P4 increment. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Qore owns temporary maps and exact-integer values. Attribution runs before shared legacy occurrence mutation; the failure/recovery regression preserves existing declarations and allows a subsequent valid schema addition. Cancellation propagates and subsequent reuse succeeds. Native code is unchanged, so no new Valgrind run is required. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Each attribution call owns its program, summaries and overlap cache. No shared lazy cache is introduced. Four concurrent workers use start/completion queues and check all results; the finalized graph remains unchanged. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Rational values and summaries use private typed hashdecls; nodes use existing enums and typed particle maps. Exact decimal count strings never pass through floating point. The arithmetic overload retains bounded base-1e9 limb products. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Symbolic thresholds retain one intrinsic summary per graph node instead of expanding reference paths or numeric counts. Ordinary-name intersections use smaller-set hash lookups and flat choices update in place. Tests cover 1000 choices, 80/81-digit adjacent thresholds and a DAG expanding beyond one billion positions; documented bounds include rational digit costs and wildcard intersections. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Construction rejects competing positions with WSDL-ERROR, including unused groups, extension boundaries and ambiguous groups inside empty languages. Absent zero-count subgraphs are omitted. Valid fixed counts, disjoint namespaces and weak repetition boundaries remain accepted. Existing malformed reconstruction/all/cycle tests pass. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | New public namespace getter documents its return value; void validateDeterminism documents errors and resolution requirements. The invoice example executes with the new method. Affected docs-WSDL builds warning-free. Release notes, implemented design, README and independent evidence match the implemented scope. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP method or flag changed. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No external production I/O, credentials, user-controlled format strings or native buffers. Validated counts and exact arithmetic avoid count expansion. Graph traversal retains existing cycle and range checks; test subprocesses have deadlines. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | The final 103-suite gate passes; two additional audit cases pass in all four modes, bringing the final inventory to 1045 cases / 43578 reported assertions. The 300-expression complete marked-prefix oracle and 12 pinned-validator schemas assert every construction and both-binding bound-part row in all four modes. All 2411 survey rows and 144 coverage failures are unchanged; 1260 strict directions pass. |
