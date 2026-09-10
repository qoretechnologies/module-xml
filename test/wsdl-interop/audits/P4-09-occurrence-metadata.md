# P4-09 audit: exact occurrence metadata

Copyright (C) 2026 Qore Technologies, s.r.o.

Date: 2026-09-10. Scope: final changes after `6ebdd39` in `qlib/WSDL.qm`,
`wsdl-particle-occurrences.qtest`, `particle-occurrences.qr`,
`test_particle_occurrences.py`, implemented particle design, README, execution
record, current reports, this audit and [P4-09-validation.json](../P4-09-validation.json).
The full [audit skill](/home/david/.codex/skills/audit-changes/SKILL.md) was read
before committing. Its module structure, sandboxing, cancellation and provider
checklist/development references were checked for the affected APIs.
All **62 checks** are individually resolved: **19 Pass / 43 N/A / 0 Fail**.

The final WSDL source SHA-256 is
`9c849ab51f6cc77abe9227f7a335337e24cb42e7dc74a1ec0b68f270e94b4b0b`.
Provider metadata uses complete particle minima/maxima and moves enum choices to
item choices when the containing particle repeats. Shared element counts are not
used by this path. The reviewed implementation distinguishes an impossible
language from accepted empty content, preserves namespace identities, and keeps
whole-particle validation authoritative for correlated fields and count gaps.

The provider tests exposed the Qore missing optional soft-list/default dispatch
bug, fixed and separately audited in `f1dd175f0` on main Qore develop. Its nine
checks pass 75 cases/2875 assertions; the new 5-case/129-assertion suite passes all
four execution modes and an explicit AOT-module run. The DataProvider-qmod target
was rebuilt from matching changed source. Its six relevant class sources and
five existing provider regression files match main Qore. Main development builds
were preserved. No C++ source changed; native XML and libqore hashes are unchanged,
so no new Valgrind run is required. Normal PCRE2 JIT remains enabled.

The XML gate passes **109 suites / 1098 cases / 54884 reported assertions**, with
no warnings. Three affected Qore suites pass **28 cases / 402 assertions per mode**.
Complete finite languages independently check **1000 models / 2530 rows per mode**,
including 235 required schema rejections and both copies of 765 valid models.
The existing independent value matrix passes **248 rows / 124 input verdicts /
112 outputs per mode**, using pinned lxml and Xerces. Both actual SOAP bindings
and directions expose the new provider metadata, including reconstruction.
The compiled WSDL module has 1162 variants and passes 11 cases/219 assertions.
Affected docs, four WSDL examples, the SoftList example and qdx extraction, and
all 15 survey-harness methods pass without warnings.

The both-version survey preserves **all 2443 stage rows/verdicts** and original
input/source/catalog hashes. Strict coverage passes **130 descriptions / 1260
directions** on the first isolated run. All 293 cases, 144 broader failure records
and stage accounting are unchanged, including 860 unassessed value/infoset
directions. Current reports only change source-version metadata.

Both remotes were fetched with no additional commits to merge. No install or
push was performed. P4 native serialization, legacy shared group mutation removal,
and sample generation remain explicit next work. P5-P9 retain the full original
scope, including the previously recorded broad documentation/debug-information
items. Logs and exact hashes are recorded in the inventory.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | External repository; no new module catalog entry. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 release notes describe exact named-element ranges and whole-particle provider shape. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | Existing WSDL module/qmod registration is unchanged. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new QMOD target. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | Existing wsdlintro documentation section is unchanged. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL and the new Qore test/worker use %modern without redundant directives. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated .qc file is changed in this repository. |
| 8. No `%include` usage (deprecated for modules) | Pass | No deprecated %include is introduced. |
| 9. Copyright 2026 on all new files | Pass | New suite, workers, inventory and audit carry 2026 notices; changed design/module notices retain 2026. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | Existing single-file WSDL layout is unchanged. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No duplicate module is added. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No QPP class is added. |
| 13. `%modern` directive present | Pass | New qtest and worker use %modern, including the child Program used for cancellation. |
| 14. Executable permission set (`chmod +x`) | Pass | New qtest, Qore worker and Python oracle have mode 0755. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Both Qore drivers prepend local qlib before relative WSDL requirements; generated child Program labels resolve its relative requirement in the test directory. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project xml and Qore QUnit are hard dependencies. External json uses %try-module with an explicit missing-dependency error. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ or filesystem operation is changed. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ or network operation is changed. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No new native external-resource operation requires a sandbox helper. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | The worker reads its owned JSON manifest through ReadOnlyFile. Python owns its temporary manifests; service metadata tests use async_only and make no remote request. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ loop is changed. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No native cancellation API is changed. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No native loop needs a new check interval. |
| 24. No blocking operations without cancellation support | Pass | Call-local Qore loops retain cancellation. Queue barriers and worker subprocesses have bounded deadlines; strict coverage passes in isolation without changing its deadline. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 34. Response/output types use `private` Fields | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 38. Password/secret fields have `"sensitive": True` | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 47. No bare field/option names in prose — must use backticks | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | Schema-derived field metadata only; no registered action/app, new request/response schema class, factory, presentation catalog, secret or JNI dependency is introduced. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Exact language extrema replace shared-declaration counts for provider metadata. No fixture special case, approximation, omitted model or weakened validation is introduced. Legacy native serialization/sample work remains explicitly tracked in P4. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Projection publishes only a complete local result; malformed graphs and interruption permit reuse. Provider construction mutates local maps. Qore f1dd175f0 fixes optional list/default dispatch without swallowing item validation errors. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | No projection cache or shared mutation is introduced. The checked declaration graph is immutable during use, and returned maps use copy-on-write storage. Four synchronized concurrent calls verify independent results. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Public XsdParticleOccurrenceRange uses exact string counts and optional maximum. Typed node/field/summary maps and enum dispatch preserve identity and distinguish NOTHING from an empty map. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Child-before-parent DAG summaries visit each node once without expanding numeric counts or shared groups. O(mk) map work/storage plus digit arithmetic is documented; a shared 2^70 graph and huge decimal limits pass. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Tests cover impossible/empty languages, absent zero-count components, optional/unbounded repetitions, namespace collisions, cyclic/unresolved graphs, invalid enum values, cancellation and reuse with intended error categories. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public range/record documentation, four executed WSDL examples, README, release notes, execution record and current reports are updated. Affected WSDL docs build without warnings; the core prerequisite has its own executed example/docs/audit. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP method or flags are changed. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Canonical occurrence values are validated by the existing graph compiler; child-before-parent assertions protect summary indexing. No untrusted format string, credential or external service dependency is added. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 109 suites/1098 cases/54884 assertions pass. All four modes pass 28 Qore cases/402 assertions plus 2530 complete-language rows and 248 independent value rows. Explicit AOT passes 11/219. Both-version survey preserves all 2443 rows and original hashes; strict coverage passes 130 descriptions/1260 directions with all 144 broader failures unchanged. |
