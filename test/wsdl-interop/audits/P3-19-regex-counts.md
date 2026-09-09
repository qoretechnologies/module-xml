# P3-19 audit: structural XSD repetitions

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: WSDL pattern compilation, structural matching and provider metadata;
Qore/Python regressions and the offline direct matcher worker; release notes,
durable scalar design, README, evidence and execution record. The full
62-item audit-changes checklist and applicable sections of its module,
sandboxing, cooperative-cancellation and provider guides were read and applied.
No C++ changed; this increment requires no additional Valgrind run.

Source and AOT execution pass 14 cases / 476 assertions. All 63 affected XML
suites pass 736 cases / 14971 assertions; SOAP deliberately checks three failed
assertions inside passing test cases. AOT and docs builds are clean. Both-version
survey/strict coverage are unchanged outside version fields: 89 selected WSDLs,
756 directions, zero selected failures and 220 tracked broader failures.

The independent matrix covers 48 actual SOAP contracts, exact large strings,
provider/schema reconstruction, negative errors and examples. Its original
validator limits and bounded reference schemas are documented in
[repetition evidence](../regex-counts-evidence.md). Direct structural matching
includes 17056 original/reconstructed verdicts against exhaustive Python and
normative Unicode/class cases. No corpus file or native dependency changed.

Findings fixed before final verification: trailing-empty split semantics for
open maximum counts; slow per-character large-value processing; loss of a
cancellation point in the initial literal fast path; repeated Unicode prefix
scans in grammar parsing. The Unicode example assertion now expects its valid
Greek candidate. Authoring errors in the temporary worker directives/XML test
wrapper and legacy provider constructor were corrected before final testing.
The earlier source test and timeout logs remain as diagnostic evidence.

Final WSDL SHA-256:
`68535d23496662e516943d479686464b448afee2e3521aebc7df42bff6d24476`.
Native XML remains `8ec5487ebe937450478fc856e5c02114e5cf9ffaf9201cf70d052907b40f2e12`.
Evidence is under `/tmp/wsdl-p3-19-`: frozen-hashes.json, exact-checks,
aot-unit, aot-frozen, docs-frozen, exact-survey/coverage and frozen-python.
Main Qore develop is clean at 3e2f47be0; no push, installation or main rebuild.

Final frozen Python discovery completes 146 methods in 571.099 seconds with
exactly the same 33 tracked P4/P5/P6 failure signatures and no errors. All four
new repetition methods pass. Source/test hashes are unchanged throughout the
run. The exact comparison is frozen-python-comparison.json under the evidence
prefix above. P3 acceptance and all P4-P9 requirements remain open.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, module registration, separated source or QPP class. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL.qm release notes describe structural repetitions and preservation of reconstructed and legacy constraints. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module, module registration, separated source or QPP class. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, module registration, separated source or QPP class. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | Existing wsdlintro introduction remains the first section; no new module. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL.qm and the qtest use %modern; the .qr worker enables modern mode by its extension. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, module registration, separated source or QPP class. |
| 8. No `%include` usage (deprecated for modules) | Pass | No %include usage introduced. |
| 9. Copyright 2026 on all new files | Pass | All new Qore/Python workers, tests, evidence and audit files carry 2026 copyright; third-party artifacts are unchanged. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, module registration, separated source or QPP class. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, module registration, separated source or QPP class. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, module registration, separated source or QPP class. |
| 13. `%modern` directive present | Pass | The qtest has explicit %modern; the .qr worker has implicit modern mode. |
| 14. Executable permission set (`chmod +x`) | Pass | The qtest and new executable test scripts have executable permission. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Local module paths precede relative WSDL requirements; AOT verification explicitly selects the rebuilt qmods. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | The external json binary module uses %try-module and a precise missing-module branch; project xml and core QUnit remain required. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ or native filesystem/network operations changed. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ or native filesystem/network operations changed. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ or native filesystem/network operations changed. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production matching performs no I/O. The test worker reads only its explicit temporary manifest with ReadOnlyFile; external processes have bounded deadlines. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ loops or blocking operations changed; Qore cancellation remains runtime-managed. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ loops or blocking operations changed; Qore cancellation remains runtime-managed. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ loops or blocking operations changed; Qore cancellation remains runtime-managed. |
| 24. No blocking operations without cancellation support | N/A | No C++ loops or blocking operations changed; Qore cancellation remains runtime-managed. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 34. Response/output types use `private` Fields | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 47. No bare field/option names in prose — must use backticks | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | XSD quantities are represented exactly and matched structurally. No count cap, waived Qore result, modified fixture or raised test deadline. Existing execution-limit failures are baseline-reproduced and explicitly retained as the next P3 requirement. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Source-only reconstruction validates before publishing immutable nodes. Per-call stacks/caches have automatic ownership; known grammar/backend exceptions alone are caught. Cancellation unwinds and the same object remains usable. Queue/counter test cleanup is deterministic. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Compiled source and postorder grammar nodes are immutable after construction. Matchers, endpoint/predicate caches and literal-comparison offsets are per-call. Four synchronized workers reuse one pattern and compare independent results. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed XsdPatternConstraint union preserves strings plus the final Serializable class. Internal node hashdecl and enum, typed lists/references and exact decimal count strings retain type safety. Heterogeneous JSON is confined to tests. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Grammar indexes Unicode code points once. Explicit stacks and memoized endpoint sets avoid recursion and exponential backtracking. Count work is bounded by input length; nullable zero-progress transitions are discarded. Flat predicates scan directly; root literals compare bounded UTF-8 byte segments. The unchanged SOAP worker deadlines now pass. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | The shared parser validates XSD syntax before backend selection. Reconstruction rejects wrong source types and malformed patterns. Count ordering, empty/nullable languages, large and zero counts, whole-value errors and all affected provider families have precise tests. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public structural constructor/matching/source APIs document input, output, grammar/interruption errors, example and resource caveat. pcre_patterns metadata docs, release notes, durable design, README and normative/oracle evidence are updated. Frozen docs build passes. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++/QPP changes. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Parsed graph edges point only backward and never come from metadata. Width/count comparisons precede int conversion and bounded allocation. Range/lookahead indices are checked. No credentials, raw native buffers or user-controlled format strings; workers use explicit files and bounded subprocesses. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Source and AOT pass 14 cases / 476 assertions; all 63 XML suites pass 736 cases / 14971 assertions. The 48-contract independent matrix passes. Both-version corpus results match P3-18. Final frozen Python runs 146 methods in 571.099 seconds with the same 33 tracked later-phase signatures, no errors and unchanged source/test hashes. |

All 62 items are classified: 19 Pass and 43 N/A, with no failed items.
The separate pre-existing PCRE execution-limit examples are documented and
baseline-reproduced for the next P3 increment. No phase-completion claim is made.
