# P3-20 audit: XSD pattern execution

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: source-retaining WSDL pattern compilation, Thompson state sets, counted
repetition dominance and closure identities; Qore/Python regressions; metadata
and release documentation, durable design, README, evidence and execution record.
The prior repetition document-count accounting is corrected transparently.
All 62 audit-changes items and the applicable module, sandboxing, cancellation
and provider guide sections were reviewed. No XML C++ source changed.

The root cause was full-expression PCRE backtracking exhausting its match budget
before a valid alternative. New constraints match structurally; zero/one and
unbounded repetitions have a source-sized Thompson graph, and general decimal
counts remain unexpanded. Count states before the minimum are retained; later
states can be pruned only when an earlier visit dominates their remaining budget.
Nullable cycles use visited-state deduplication. Per-call subset/character caches
reuse reached transitions, with no shared mutable matcher state.

The six-case Qore regression passes 348 assertions in source and AOT form,
including 10000-character inputs, exact error categories, source reconstruction,
cancellation/reuse and concurrent matches. All 64 affected XML suites pass
742 cases / 15319 assertions. SOAP deliberately tests three assertion failures
inside passing test cases. All three regex suites pass AOT (32 cases / 1812
assertions), and four AOT language methods check 32296 exact verdicts. AOT and
WSDL documentation builds are clean.

The independent matrix checks 60 actual SOAP contracts, 540 input and 264 emitted
binding documents, 3360 consumer result rows and 1888 provider/example documents.
Original Xerces checks every document. The 48 named libxml2 internal-limit results
are unassessed; 668 separately identified globally equivalent schema/document
jobs are mandatory in both validators. The portability audit restricts recognized
errors to the exact reduced lexical strings and accepts correct libxml2 verdicts
when fixed. No fixture, payload, backend source or execution budget was changed.
See [execution evidence](../regex-execution-evidence.md) for source/probe hashes
and the equivalence proof. Two direct language methods add 15240 verdicts.

Both-version survey and strict coverage match P3-19 outside version fields:
89 selected WSDLs / 756 directions, zero selected failures and 220 tracked broad
failures. Final frozen discovery completes 150 methods in 686.339 seconds with
the same 33 tracked P4/P5/P6 failure signatures, zero errors and unchanged
source/test hashes. The earlier 682.036-second frozen run is retained separately.

The next IEEE preflight independently exposed Qore's uninitialized empty
string-to-float result. Core commit 9dab82749 fixes it with its own 62-item audit,
20 suite runs / 116 cases / 3628 assertions and clean affected Valgrind checks
using the already authorized PCRE interpreter test control. The existing
Valgrind DWARF reader warning remains a P9 environment item. Main Qore is clean;
no push, installation or main-checkout build occurred.

Final WSDL SHA-256:
`767dc84affb55d4800155e443d927a078e7dac3ec7269faf64e497b40ec69274`.
Final Debug core SHA-256:
`c8b0739f796b93c0f056cbf2a37050d6902de45c3e9361ed3565754ac5549afb`.
Evidence prefix `/tmp/wsdl-p3-20-`: final-checks, final-survey/coverage,
frozen-python/comparison/hashes, execution-accounting-final, aot-runtime-final,
aot-tests, aot-final and docs-final. No runtime/source changes occurred during
the final discovery run. P3 and all P4-P9 acceptance requirements remain open.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, module registration, separated source or QPP class. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL release notes describe source-retaining state-set execution and continued legacy metadata support. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module, module registration, separated source or QPP class. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, module registration, separated source or QPP class. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | Existing wsdlintro introduction remains the first section; no new module. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL.qm and the Qore regression use %modern; no redundant parse directives are added. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, module registration, separated source or QPP class. |
| 8. No `%include` usage (deprecated for modules) | Pass | No %include usage introduced. |
| 9. Copyright 2026 on all new files | Pass | New Qore/Python tests, evidence and audit carry 2026 copyright; third-party artifacts are unchanged. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, module registration, separated source or QPP class. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, module registration, separated source or QPP class. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, module registration, separated source or QPP class. |
| 13. `%modern` directive present | Pass | The new Qore regression has explicit %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | The new qtest and Python script are executable (mode 755). |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The local qlib path precedes the relative WSDL requirement. AOT copies explicitly load the final rebuilt qmods. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | The new qtest requires project xml and core QUnit. Existing shared Python worker guards the external json module; no dependency was added. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ or native filesystem/network operations changed. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ or native filesystem/network operations changed. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ or native filesystem/network operations changed. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production matching performs no I/O. Python tests use existing explicit temporary manifests, offline validators and bounded subprocesses. |
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
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Thompson fragments and exact counted matching implement the XSD languages without count caps, backend-limit retries, altered fixtures or raised deadlines. Named libxml2 internal errors remain unassessed and original Xerces/equivalent-schema checks remain mandatory. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Source-only reconstruction validates before publishing the program. Graphs are immutable after construction and transient caches have per-call automatic ownership. Cancellation unwinds and the same object is reusable; queue/counter cleanup uses bounded synchronization. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Grammar and automaton graphs are immutable after construction. Subsets, transitions, predicates, endpoints and work stacks are per-call. Four synchronized workers share one pattern and assert independent positive/negative outcomes. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Internal state/frontier hashdecls, existing node-kind enum and typed lists/maps represent all matcher data. Public XsdPatternConstraint retains its typed legacy/object union. Heterogeneous JSON is confined to test transport. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Thompson state sets merge paths instead of backtracking, with source-sized graphs and input-reached transition caching. Numeric bounds are never expanded. General repetition prunes dominated count/offset states after the minimum; exhaustive count holes remain preserved. The 10000-character schema/provider test passes unchanged deadlines. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | The shared XSD parser validates every new source and reconstruction; no backend error-message parsing is used in production. Existing malformed source/metadata checks remain passing. New negative tests assert SOAP and provider error categories, nullable/empty behavior and count minima. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Existing public API docs remain complete; pcre_patterns metadata docs and release notes now describe source retention. Durable design, README, normative/oracle evidence and execution record describe the final algorithms and old metadata behavior. Final docs build and local links are clean. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++/QPP changes. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Graphs derive only from validated source; metadata cannot inject transitions. Numeric bounds are compared before int conversion, and graph size is proportional to grammar size. No user-controlled format string, credentials, native buffer or production I/O is introduced. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | All 64 affected XML suites pass 742 cases / 15319 assertions. The new 60-contract matrix and 15240 direct language verdicts pass, as do existing count/Unicode checks. AOT passes 32 cases / 1812 assertions and 32296 direct original/reconstructed verdicts. Both-version corpus results match P3-19. Final frozen discovery runs 150 methods in 686.339 seconds with the same 33 tracked later-phase signatures, zero errors and unchanged source/test hashes. |

All 62 checks are classified: 19 Pass, 43 N/A, no failures.
