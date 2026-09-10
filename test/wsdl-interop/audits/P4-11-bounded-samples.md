# P4-11 audit: bounded structural samples

Copyright (C) 2026 Qore Technologies, s.r.o.

Date: 2026-09-10. Scope: changes after `b1f38c4` in WSDL, the new sample suite
and independent worker/oracle, implemented particle design, README/release notes,
current reports, execution record and this audit/inventory. The full
[audit skill](/home/david/.codex/skills/audit-changes/SKILL.md) was read before
commit, with applicable module structure, sandboxing and cancellation references.
Every checklist item is resolved: **19 Pass / 43 N/A / 0 Fail**.

The [validation inventory](../P4-11-validation.json) records source/artifact/log
hashes, commands, exact execution results and current corpus accounting. The
sampler's shortest/preferred words respect complete groups and explicit resource
budgets. Exact minima are compared before machine conversion or allocation;
empty iterations are never expanded. Original/reconstructed finite languages
are independently enumerated, including every expected schema/generation error.
The native module/library hashes are unchanged; no additional Valgrind run is
required. PCRE2 JIT remains enabled. No install or push was performed.

The 16 existing suites pass 304 cases and 16420 reported assertions. The three
pre-existing caught SOAP comparator negatives remain intentional. Each of four
execution modes passes 10 cases/190 assertions and 19360 oracle rows. The explicit
1180-variant AOT module passes the same 10/190. The executed shipment example and
affected API docs pass without warnings. The 2443-row survey and complete strict
coverage ledger remain unchanged except the WSDL source hash: 130 selected
descriptions/1260 directions pass, while 92 broader failures and 904 unassessed
value/infoset directions stay visible. README's stale pre-P4-10 ledger counts
were corrected to match the already committed report.

This increment implements the complete public structural sampler. The reproduced
flat `WSMessageHelper` repeated-group failure and shared declaration count mutation
remain the next P4 increment; this does not claim P4 or P5-P9 acceptance.

| Check | Status | Evidence |
|---|---|---|
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | External existing module; no Qore module catalog entry changes. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 release notes describe the bounded structural API. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | Existing WSDL CMake registration is retained. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module target. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | Existing wsdlintro remains the first module section. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | Existing WSDL and both new Qore drivers use %modern without redundant parse directives. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated qc changes. |
| 8. No `%include` usage (deprecated for modules) | Pass | No %include is added. |
| 9. Copyright 2026 on all new files | Pass | All new authored files carry 2026 copyright notices; WSDL already carries 2026. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | Existing single-file layout retained. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No duplicate module introduced. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No QPP class added. |
| 13. `%modern` directive present | Pass | The qtest, worker and cancellation child Program use %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | The qtest, Qore worker and Python oracle are executable. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Both source drivers prepend local qlib and require the relative WSDL path; the AOT copy requires the absolute compiled qmod. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project xml and Qore QUnit remain hard requirements; external json uses %try-module with explicit missing-dependency failure. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ filesystem changes. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ network changes. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No native I/O changes. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production changes perform no I/O. The test worker reads the supplied manifest through ReadOnlyFile; Python owns temporary manifests and bounded subprocesses. |
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
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | The public structural sampler implements complete bounded generation for the existing particle graph. No schema relaxation, fixture case or stub is added. Helper integration is the next explicitly tracked P4 increment. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | All summaries and result words are call-local managed Qore values. Exceptions publish no partial sample. Failure/reuse and interruption/reuse are tested. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | No schema member is modified. Four synchronized callers produce independent results and preserve shared occurrence metadata. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Sample summaries use a typed hashdecl and typed name lists. Occurrence bounds remain exact strings until compared against the available integer budget. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Bottom-up summaries process each compiled node once and store two words bounded by B children. O((M+E)*(B+1)) word/edge work and O(M*(B+1)) name references are documented; huge empty repetitions do no count-sized work. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Checks cover invalid limits, empty/impossible words, alternatives, required suffixes, exact and huge repetitions, wildcard namespaces, all groups, shared references, reconstruction and deep graphs with intended error categories. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | The public method documents parameters, results, exceptions, caveats and a shipment example. The design example executes; README, release notes and execution evidence identify the implemented API and remaining P4 work. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP flags changed. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Capacity is checked before addition, counts are clamped before machine conversion/allocation, division occurs only for nonempty words, and internal child indices are asserted. No external service, credential or user-controlled format string is added. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | All four modes pass 10 cases/190 assertions and 19360 complete-language rows each. Sixteen existing suites pass 304 cases/16420 reported assertions; AOT passes 10/190, the executed example and affected docs are warning-free. The 2443-row survey and complete strict coverage ledger are unchanged except the source hash; all 130 selected descriptions/1260 directions pass. The 92 broader failures and 904 unassessed value directions remain visible. |
