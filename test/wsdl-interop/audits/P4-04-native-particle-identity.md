# P4-04 audit: native particle identity

Copyright (C) 2026 Qore Technologies, s.r.o.

Date: 2026-09-10. Scope: final changes after `17c5b40`.
All 62 checks are individually resolved: 20 Pass / 42 N/A / 0 Fail.

The full [audit skill](/home/david/.codex/skills/audit-changes/SKILL.md) and Qore
module-structure, sandboxing and cooperative-cancellation references were applied.
No DataProvider, QPP, JNI or new Qore module registration is involved. Native checks
apply to the C dependency edits embedded in the checked CMake replacement and
`libxml2-particle-identity.inc`; build probes and allocation tests are reviewed too.
No workaround or approval exception was used.

Files: the CMake provider/patch/probes, Makefile distribution list, Qore identity
suite, C allocation fixture and Python provider tests; native release notes, README,
implemented design/example, interop evidence, execution record, native matrix,
validation inventory and this audit. [P4-04-validation.json](../P4-04-validation.json)
records final source/runtime hashes and all 104 suite results. Logs use
`/tmp/wsdl-p4-04-`; provider artifacts are `/tmp/qore-xml-libxml2-test-uqe2ommw`.

Review corrected per-emission identity to per-source-use identity because native
counted-group lowering can emit one source position repeatedly. The final map
reuses that identity. The test fixture is compiled in the library's internal build
context because it exercises private automata functions; the final 26-test provider
run has no compiler warnings. The identity and occurrence Qore suites and standalone
fault-injection fixture pass Valgrind without lost allocations or memory errors.
Reachable LLVM/loader process-lifetime allocations and the known isolated-core
DWARF diagnostic are explicitly described in the evidence, with no suppressions.
Three counted/component native findings remain failing P4-owned diagnostics.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, module layout, QPP class or build registration. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | Native module release notes describe identity preservation and behavior-based system-backport selection. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module, module layout, QPP class or build registration. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, module layout, QPP class or build registration. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new module, module layout, QPP class or build registration. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No Qore module changed; test entry points use %modern. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated .qc file changed. |
| 8. No `%include` usage (deprecated for modules) | Pass | No deprecated %include introduced. |
| 9. Copyright 2026 on all new files | Pass | New C bridge, probes, allocation fixture, Qore test, design and evidence records carry 2026 copyright. Upstream third-party notices and source bytes are preserved. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, module layout, QPP class or build registration. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, module layout, QPP class or build registration. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, module layout, QPP class or build registration. |
| 13. `%modern` directive present | Pass | The qtest and Qore worker explicitly use %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | The new Qore suite is executable (mode 755). C/Python tests run through explicit compiler/interpreter entry points. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The Qore suite prepends local qlib before project/core requirements. QORE_MODULE_DIR and LD_LIBRARY_PATH select local Debug binaries; all test calls use -b --enable-debug. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Only project xml and core QUnit dependencies are introduced, both with hard requirements. No new external binary module dependency. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | Pass | The native correction manipulates compiler-local memory only; no filesystem operation added. CMake build/probe and standalone-test files are explicit build inputs. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | Pass | No runtime network operation added. The existing checksum-pinned FetchContent path is unchanged; provider tests use the verified local source. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No native filesystem/network operation requiring QoreSandboxManagerHelper is introduced. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | The Qore test uses in-memory StringInputStream values; no new File/Dir/Socket/HTTPClient call. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | The C correction adds no unbounded loop. Push/pop and atom equality do bounded map/field work within the existing dependency compiler. Standalone allocation tests enumerate a finite measured fault inventory. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No new native cancellation point or deprecated interrupt API. Existing Qore parser interrupt checks remain active; interruption/reuse passes in all modes. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No new long-running native loop or blocking call; no new cancellation-check frequency is required. |
| 24. No blocking operations without cancellation support | Pass | No new blocking runtime operation. Test processes have bounded completion deadlines; no sleeps or polling are introduced. |
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
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Particle-use identity is corrected at atom equality and compilation provenance, without stubs or fixture conditions. Counter-feasibility and unreachable-component bugs remain explicit P4 diagnostic failures under the authorized incremental plan. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Every map/identity allocation failure is checked before publication. Entry failure frees the identity; parser teardown frees the map on all paths. Parent restoration covers success and error exits. All 327 fault points return to baseline allocations and a fresh run succeeds. Native and Qore Valgrind runs have no errors/lost allocations/suppressions. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | All identity state belongs to one automaton compiler context. Compiled atoms retain numeric IDs only; map teardown does not invalidate runtime data. No mutable global production state or shared cache is added; test allocator counters are confined to one standalone process. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Private C structs hold size_t IDs, checked native pointers and the existing typed atom fields. Callback payloads remain unchanged. Qore tests use typed arguments and ExceptionInfo; no C++/QPP type declarations are introduced. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | A hash of parent ID and particle address reuses emission identities in expected constant time with linear storage. It avoids a linear scan over prior positions. No count expansion or new recursive traversal is introduced beyond the existing automaton builder. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Bounded key formatting, allocation and ID overflow are checked. Unknown source hashes fail configure. Tests distinguish XSD-SYNTAX-ERROR from invalid-document PARSE-XML-EXCEPTION; repeated/failing construction and interrupted reuse pass. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | No public runtime API is added. The private bridge documents ownership and provenance. Native release notes, README, implemented design and executed shared-group example describe the final behavior. Affected docs-module builds without warnings; remaining native diagnostics are explicit. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP method or flag changed. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Compiler-local pointer/parent keys use fixed format strings and checked buffers; source pointers do not escape in output. No credentials, new external I/O or unchecked allocation. Private bridge symbols are hidden in the module dynamic symbol table. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 104 Qore suites pass: 1051 cases / 43671 reported assertions. The final six-case/93-assertion native suite passes all four modes. All 26 provider/distribution tests pass warning-free; nine behavioral probe cases and 327 allocation faults are checked. Three Valgrind runs pass without errors/lost allocations/suppressions. All baseline/coverage records are unchanged; three native matrix failures remain separately owned by P4. |
