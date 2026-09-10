# P4-13 audit: ordered corpus and phase acceptance

Copyright (C) 2026 Qore Technologies, s.r.o.

Date: 2026-09-10. Scope: changes after `e8ea3b6` in corpus workers,
independent particle observations/tests, strict selection/coverage, README,
current reports, phase plan/execution evidence and this audit/inventory.
The complete [audit skill](/home/david/.codex/skills/audit-changes/SKILL.md)
was read before commit; its module structure, sandboxing, cancellation and
provider references were considered. **62 checks: 16 Pass / 46 N/A / 0 Fail**.

The [inventory](../P4-13-validation.json) records all source/artifact/log hashes,
SOAP 1.2 derivative hashes, individual checks and full corpus transitions.
The new worker regression fails before the parser flag change and passes after
it. Ordered input reaches the existing complete-particle validator unchanged.
Native values are compared per field occurrence; retained XML is compared in
full original order. Every string, element, attribute and count in the selected
tree is observed; only element-only indentation is ignored. Independent schema
validation remains mandatory. No original fixture is changed or rejected valid
case relabeled as a passing expectation.

Eighteen Qore suites pass 333 cases/16941 reported assertions; three intentionally
caught SOAP comparator negatives are unchanged. Three reference and 16 harness
methods pass. Each of four modes checks 240 corpus rows, eight mandatory invalid
source rejections and 696 independently valid native/retained outputs. Full
coverage unit tests retain exactly the two previously routed P6 binding-selection
assertions as failures. All current-phase checks, including strict completeness,
pass without warnings. The initial stale strict-count assertion was updated for
the expanded selection; a misspelled orchestration test path was corrected and
the actual provider suite rerun. Neither diagnostic is counted as a test pass.

The final isolated strict run passes 142 selected descriptions/1376 directions.
All 120 P4-owned directions have complete outcomes: 116 preserve required values
and four reject invalid source content. Broader failures fall 92 to 68, removing
exactly 24 P4 decode failures. All older successful survey rows are identical;
12 formerly failing decode rows and their 12 new valid outputs account for the
2455-row survey. The 812 remaining unassessed value/infoset directions are not
counted as conformance passes. P4 is complete; P5-P9 remain fully required.
No production module or native artifact changes, rebuild, install or push.

| Check | Status | Evidence |
|---|---|---|
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | External existing module; no Qore module catalog entry changes. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | N/A | Only the test harness and phase evidence change; the WSDL API release notes from P4-12 remain current. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | Existing WSDL CMake registration is retained. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module target. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | Existing wsdlintro remains the first module section. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No qm module changes; test script parse directives are checked in item 13. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated qc changes. |
| 8. No `%include` usage (deprecated for modules) | N/A | No module include/layout changes. |
| 9. Copyright 2026 on all new files | Pass | All new authored Python/Qore/evidence files carry 2026 copyright notices. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | Existing single-file layout retained. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No duplicate module introduced. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No QPP class added. |
| 13. `%modern` directive present | Pass | Both the updated probe.qr and new particle-corpus.qr use %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | Qore workers and executable Python test drivers have mode 755; particle_reference.py is an imported helper. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Both workers prepend local qlib before a relative WSDL source requirement; source/artifact hashes remain pinned. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project xml remains required; external json uses %try-module with an explicit missing-dependency exception. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ filesystem changes. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ network changes. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No native I/O changes. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Workers read only the supplied local manifests/files through ReadOnlyFile. Corpus bytes are hash checked; temporary directories and subprocesses are owned by Python. No production I/O changes. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ loops changed. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No native cancellation API changes. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No native loop interval changes. |
| 24. No blocking operations without cancellation support | Pass | New Qore loops keep runtime cancellation points; explicit cancellation exceptions propagate. Workers have bounded subprocess deadlines and deterministic teardown; final gates use process-completion events. |
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
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | The caller now supplies ordered XML to the existing strict validator. No input reordering, fixture modification or relaxed rejection is introduced. All P4-owned cases are selected with value assertions; remaining P5-P9 failures stay visible. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Temporary resources and subprocesses use scoped cleanup. New worker failure rows are complete and cancellation propagates. Observation state is call local and iterative; failures publish no partial successful comparison. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | No mutable shared state is added. Observation and worker results are local; schema reconstruction is tested independently for every corpus direction. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Qore manifest/result values and SoapXmlMessageInfo are typed. Python predicates validate exact assertion keys, names, leaf inventory and ordering modes before use. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Iterative observation visits each XML element once, with stable per-parent name sorting only for the explicit native contract; O(N log N) worst-case time and O(N) storage. Each schema is compiled once per family and reused. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Mutation tests catch lost/extra nodes, string changes, reordered occurrences, namespace changes, attributes, non-whitespace container text, nested scalar content, invalid paths and malformed assertions. Every worker row and source rejection is required. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | README documents reproducible commands, both ordering contracts, exact SOAP 1.2 derivative/provenance and P5/P6 distinctions. Phase acceptance and remaining failures are recorded without new public API claims. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP flags changed. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Original WSDL/schema/message digests are verified; new manifests contain only offline test inputs. No credentials or unsafe format strings are added. Missing/duplicate rows cannot improve counts. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | All four modes pass 240 complete corpus rows and 696 independently validated outputs, with exact native/retained comparisons. Eighteen Qore suites, reference/harness tests and isolated strict coverage pass; only two previously routed P6 diagnostic assertions remain failing. |
