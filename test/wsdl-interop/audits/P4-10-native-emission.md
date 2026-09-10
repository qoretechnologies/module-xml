# P4-10 audit: native particle emission

Copyright (C) 2026 Qore Technologies, s.r.o.

Date: 2026-09-10. Scope: the complete changes after `bd57449` in WSDL, the
serialization suite, SOAP diagnostics, ordering/value workers, implemented design,
README, execution record, current reports, P5 finding and this audit/inventory.
The full [audit skill](/home/david/.codex/skills/audit-changes/SKILL.md) was read
before commit, with the Qore module structure, sandboxing, cancellation and
provider checklist/development references. All **62 checks** are individually
resolved: **19 Pass / 43 N/A / 0 Fail**.

Source SHA-256: `a92e785c691589ca52407c703d9cc924ed488da9e40c5d6ac48c19dc4d80625e`.
The [validation inventory](../P4-10-validation.json) records exact artifacts,
commands/log locations, 110 passing suites, all four execution modes, the
1173-variant AOT module, five executed examples and warning-free affected docs.
Normal PCRE2 JIT remains enabled. No C++ source, native module or libqore changed;
no additional Valgrind run is required. No install or push was performed. Both
fetched origin/develop tips are already contained locally; main Qore is clean.

The serializer allocates complete groups and preserves per-field value order in
ordered XML keys. Exact count-state allocation avoids greedy suffix/count-gap
failures; indexed witnesses avoid repeated word copying. Its general alphabet
bound is documented, and ordered matching retains its separate polynomial bound.
Native canonical allocation and the lossless XsdXmlValue contract are explicit.

Audit found and fixed a P4-09 shared-object deletion: `delete` on an inactive
XsdElement in a temporary provider map destroyed the shared declaration. Active
field projection now uses `remove` and is shared by provider, encoder and decoder.
The regression checks object survival, namespace collisions, reconstruction and
repeated metadata/value calls. Existing SOAP assertions now check complete-particle
diagnostics; an explicitly supplied empty optional wrapper is preserved, while an
omitted wrapper stays absent. Three pre-existing caught comparator negatives in
soap.qtest remain intentional; the suite has no failing case.

All 2443 survey row identities and original provenance remain intact. Twenty-two
serialization failures and four invalid SequenceChoice outputs are fixed; two P5
dynamic-type failures only change diagnostics. Strict coverage passes all 130
selected descriptions/1260 directions. Broader failures decrease from 144 to 92;
904 value/infoset directions remain explicitly unassessed, including 44 newly
reachable outputs. These are not counted as successful value-preservation checks.
P4 samples/shared-count removal and P5-P9 retain their full scope. The existing
builtin explicit-type identity bug is separately [tracked for P5](../p5-native-type-wrapper-finding.md),
not converted into a passing expected rejection.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | External repository; no new Qore module catalog entry. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 release notes describe native particle allocation, ordering and one-occurrence conversion. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | Existing WSDL qmod and documentation registration is retained. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No additional module target is introduced. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | Existing wsdlintro section remains the first module section. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL, the new suite and both Qore workers use %modern; no redundant directives are added. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated qc file changes. |
| 8. No `%include` usage (deprecated for modules) | Pass | No deprecated %include is introduced. |
| 9. Copyright 2026 on all new files | Pass | All authored files carry 2026 notices; modified module and SOAP tests retain 2026. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | Existing single-file WSDL layout is retained. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No duplicate module is introduced. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No QPP class is added. |
| 13. `%modern` directive present | Pass | New Qore test and worker use %modern, including cancellation child Programs. |
| 14. Executable permission set (`chmod +x`) | Pass | New qtest, Qore worker and Python oracle have executable permissions. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Test drivers prepend local qlib before their relative WSDL requirement; AOT verification uses the explicit compiled artifact. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project xml and Qore QUnit are required; external json uses %try-module followed by an explicit missing-dependency failure. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ filesystem changes. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ network changes. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No new native I/O operation. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | The Qore worker reads its supplied manifest through ReadOnlyFile. Python owns temporary manifests and bounded subprocesses; schema metadata uses async_only. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ loops change. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No native cancellation API changes. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No native loop check interval changes. |
| 24. No blocking operations without cancellation support | Pass | Call-local Qore loops retain cancellation; queue barriers, counter completion and subprocess deadlines are bounded. No polling or sleep is added to tests. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 34. Response/output types use `private` Fields | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 38. Password/secret fields have `"sensitive": True` | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 47. No bare field/option names in prose — must use backticks | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | Existing schema field projection only; no registered action/app, presentation catalog, secret, factory or JNI dependency changes. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Exact complete count-vector allocation replaces greedy/flattened scheduling. No fixture special case, arbitrary count cutoff or weakened value check is added. Remaining sample/shared-group and P5 adapters are explicitly phase-owned. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Temporary active-declaration maps remove references without destroying shared objects. Indexed witnesses and result maps are call-local; error and interruption paths publish no partial result. Repeated metadata/encode/decode and cancellation recovery are tested. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Schema declarations remain immutable during these calls. One-occurrence conversion uses local ranges; namespaces are copied by callers. Four synchronized concurrent calls verify independent outputs. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Count states and witness records use typed hashdecls; terminal callbacks have code<bool(int, string)> types. Particle enums and exact decimal count bounds are retained. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | The allocator deduplicates at most product(count+1) vectors per node/frontier; iterations consume supplied children. Compact indexed witnesses avoid repeated word copying and recursive cleanup. The general exponential alphabet bound and separate polynomial ordered matcher are documented. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Tests cover malformed names, absent/empty/impossible content, count gaps, choice/suffix allocation, inactive fields, duplicate aliases, nil/list values, huge counts, all, shared groups and wildcard predicates, with intended exception categories. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public methods have parameter, return, exception, caveat and example documentation. Implemented design, release notes, README and execution evidence are updated; all five design examples and affected API documentation pass. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP method flags change. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Expanded names and graph structure are checked by the compiler/matcher. Count sums check remaining capacity before addition; witnesses use internal indices. No user format string, credential or external service is added. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 110 suites/1113 cases/56270 reported assertions pass without warnings. All four modes pass 43 Qore cases/1787 assertions, 15132 complete-language rows and 248 SOAP value rows with 224 independently valid outputs. Explicit AOT passes 15/1385. Both-version survey preserves every passing stage; strict coverage passes 130 descriptions/1260 directions with 92 broader failures and 904 explicitly unassessed value directions retained. |
