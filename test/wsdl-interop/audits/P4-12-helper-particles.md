# P4-12 audit: complete native helper samples

Copyright (C) 2026 Qore Technologies, s.r.o.

Date: 2026-09-10. Scope: changes after `f687c55` in WSDL, its sample suite,
new independent SOAP sample matrix, implemented design, README/release notes,
current reports, worker finding, execution record and this audit/inventory.
The full [audit skill](/home/david/.codex/skills/audit-changes/SKILL.md) and its
module structure, sandboxing, cancellation and both provider references were
read. All **62 checks resolve: 19 Pass / 43 N/A / 0 Fail**.

The [validation inventory](../P4-12-validation.json) records exact source,
artifact and log hashes, commands and individual checks. The helper produces
complete named particles with bounded total elements and preserves shared
occurrence metadata. Typed complex parts and public nested/reentrant hooks
retain their existing return contracts. Runtime context restoration covers
failure, interruption and concurrent calls.

Audit failures were fixed before commit. Graph visitation initially reversed
native field order; reverse child pushing restores schema order. A public
override could bypass construction accounting with a larger subtree; the final
converted-output traversal now counts it without a second value conversion.
The new constructor option has its missing exception documentation. A suspected
multiple-root fragment issue was disproved by the native writer's single-root
contract; separate siblings, malformed fragments and reuse are tested. Early
test-only return diagnostics are superseded by warning-free final runs.

All 111 suites pass 1133 cases/56558 reported assertions; replacing the sample
row with its final seven extra fragment checks gives 56565 assertions. The final
sample suite passes 19/243 in AST, IR, JIT, tiered and explicit AOT. Each source
mode also passes 15132 independently enumerated ordering rows, the 248-row value
matrix (224 independently validated outputs), and the 208-row generated sample
matrix (32 required budget errors, 352 independently validated outputs). The
1186-variant AOT build, affected docs, shipment example and 15 harness methods
are warning-free. Native hashes are unchanged; no Valgrind rerun is required.

All 2443 survey rows and isolated strict ledger outcomes are unchanged: 130
selected descriptions/1260 directions pass, while 92 broader failures and 904
unassessed value/infoset directions stay visible. The
[worker ordering finding](../p4-worker-order-finding.md) owns 24 remaining P4
decode failures and is the next increment. P4 and P5-P9 remain open. Concurrent
main Qore work is preserved; no install or push was performed.

| Check | Status | Evidence |
|---|---|---|
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | External existing module; no Qore module catalog entry changes. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 notes describe complete native examples, typed complex parts, total-element budgets and immutable group declarations. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | Existing WSDL CMake registration is retained. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module target. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | Existing wsdlintro remains the first module section. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | Existing WSDL, updated sample qtest and new Qore worker use %modern without redundant parse directives. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated qc changes. |
| 8. No `%include` usage (deprecated for modules) | Pass | No %include is added. |
| 9. Copyright 2026 on all new files | Pass | All new authored files carry 2026 copyright notices; WSDL already carries 2026. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | Existing single-file layout retained. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No duplicate module introduced. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No QPP class added. |
| 13. `%modern` directive present | Pass | The qtest, integration worker and existing cancellation child Program use %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | The qtest, Qore worker and Python oracle are executable. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The qtest and worker prepend local qlib before requiring relative WSDL source; the AOT copy explicitly loads the compiled artifact. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project xml and Qore QUnit remain hard requirements; external json uses %try-module with explicit missing-dependency failure. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ filesystem changes. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ network changes. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No native I/O changes. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production changes perform no external I/O; XmlReader counts supplied fragment text in memory. The worker reads its manifest through ReadOnlyFile; Python owns temporary files and bounded subprocesses. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ loops changed. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No native cancellation API changes. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No native loop interval changes. |
| 24. No blocking operations without cancellation support | Pass | Qore loops keep runtime cancellation checks. Tests use bounded queue barriers/counter completion and subprocess deadlines; no sleep or polling. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 34. Response/output types use `private` Fields | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 47. No bare field/option names in prose — must use backticks | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No DataProvider action, data type, app, factory, presentation catalog or JNI dependency changes. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Complete named-particle helper integration and removal of shared count mutation are implemented. No fixture branch, weakened validator or stub is added. Remaining worker-order acceptance and P5-P9 are explicitly tracked. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Managed call-local budgets and context use on_exit restoration after nested/reentrant callbacks, recursion failure and interruption. Shared declarations are indexed without deletion or mutation. Output is checked before return. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Thread-local consume-once child contexts preserve independent root budgets. Four synchronized callers and same-helper reentrant callbacks pass. Shared group declarations retain min/max 1/1 after reconstruction and generation. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Declaration maps, name lists, occurrence values and call contexts are typed. Heterogeneous pending/value lists are explicitly constructed to avoid homogeneous runtime inference. Exact particle ranges retain their existing string representation. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Active declarations are traversed once by identity, preserving schema order. Construction reserves children before callbacks; output counting reserves pending elements before expansion. The helper uses the documented complete structural sampler and count-vector allocator bounds; the latter can be exponential in distinct supplied names, as documented, and adds no derivation backtracking. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Positive integer options, complete group budgets, empty/recursive types, typed parts, namespace collisions, XSD list occurrences, override subtrees, independent sibling fragments and malformed fragments have specific expected errors. No partial sample is returned. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public constructor and element generator document parameters, results/errors and instance/explanatory caveats. Implemented design documents the per-part budget and callback boundary; the shipment example executes and affected API docs are warning-free. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP flags changed. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Limits are checked before decrement/allocation; pending XML nodes reserve remaining capacity, and embedded fragments use the existing single-document-element contract. Internal attributed positions are asserted; no credentials, external network access or user-controlled format strings are introduced. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Final source passes 111 existing/new suites, four execution modes, explicit AOT, independent model ordering and SOAP value/example matrices, docs/example, survey harness and isolated strict coverage. Final seven fragment assertions are rerun in all four modes and AOT. |
