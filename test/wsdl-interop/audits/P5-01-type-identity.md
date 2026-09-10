# P5-01 audit: native type identity and annotation ownership

Copyright (C) 2026 Qore Technologies, s.r.o.

Date: 2026-09-10. Scope: the exact changes after `ca181ff` in WSDL,
its new unit/integration tests, implemented design, release notes, README,
plan/finding/execution records and current validation reports.
The entire [audit skill](/home/david/.codex/skills/audit-changes/SKILL.md)
was read before committing; its module, sandbox, cancellation and provider
references were reviewed. All **62 checks resolve: 19 Pass / 43 N/A / 0 Fail**.
The [validation inventory](../P5-01-validation.json) records hashes, commands,
fixtures, artifacts, individual checks and explicit remaining scope.

Root-cause fixes accept declared-type identity, preserve selected annotation
namespaces and metadata, avoid delegated anonymous/base annotations and nested
simple-content hashes, and select complex instance types before checking derived
attributes. Immediate complex extensions use resolved base components. The tests
reject unrelated/malformed/unbound type identities and invalid values/counts,
and retain cancellation, custom-conversion counts and concurrent schema reuse.
Same-element data QName collisions with type/instance prefixes pass independent
schema and expanded-value checks in both actual SOAP bindings and directions.

The final source passes 112 Qore suites, 1144 cases and 56907 reported assertions.
Three intentionally caught legacy SOAP comparator negatives remain part of that
suite's successful result. The focused suite passes 11/342 in AST, IR, JIT,
tiered and explicit AOT. The final integration matrix passes all five modes:
224 rows, 72 required serialization errors and 416 independently valid outputs
per mode. Compilation produces 1189 variants; affected docs and the executed
invoice example are warning-free. No authored C++ or native runtime artifact
changed, so no new Valgrind run is required.

All 2455 survey rows and strict outcomes are unchanged: 142 descriptions/1376
directions selected without failure, 68 broader failures and 812 unassessed
value/infoset directions still visible. Full P5 derivation controls, selected-type
retention and other content semantics remain required, followed by P6-P9. The
known P6 dual-binding diagnostic and P9 broad-doc/debug-info findings are not
counted as passes. No install or push was performed.

Audit/development findings were fixed: invalid test container/map syntax and raw
binary/list expectations were corrected to existing API contracts; anonymous
simple values no longer name a base type as themselves; QName comparisons use
expanded identity, not arbitrary prefix spellings. An initial non-existent QName
suite filename was corrected and is superseded by the full passing gate. The
broad QName test's 240-second outer deadline was below its established 338-419
second runtime; the corrected 900-second aggregate gate passes in 360.851 seconds
without changing its 300/180-second child limits. That aborted run is recorded
as a runner failure, never a passing test, and correctly prevented the initial
corpus invocation until all prerequisites passed.

| Check | Status | Evidence |
|---|---|---|
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | Existing external module; no Qore catalog entry changes. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 release notes describe native type identity, expanded complex dispatch and annotation/content ownership. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | Existing WSDL module build registration retained. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No module target added. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | Existing lowercase wsdlintro remains first. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | Existing WSDL and new Qore tests use %modern without redundant parse directives. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated qc edits. |
| 8. No `%include` usage (deprecated for modules) | Pass | No %include or separated-module layout change is introduced. |
| 9. Copyright 2026 on all new files | Pass | All new authored test, worker, Python and design files carry a 2026 copyright statement. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | Existing single-file module layout retained. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No duplicate module. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No QPP class. |
| 13. `%modern` directive present | Pass | The Qore suite and integration worker explicitly declare %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | The qtest, qr worker and Python integration test have executable mode 0755. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Tests prepend local qlib before a relative WSDL %requires; the AOT copy explicitly requires the compiled qmod. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project xml and Qore QUnit are hard requirements. External json uses %try-module with an explicit missing-module failure. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ filesystem edits. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ network edits. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No native I/O. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production edits perform no external I/O. The integration worker reads its supplied manifest with ReadOnlyFile; Python owns temporary paths and bounded child processes. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ loop edits. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No native cancellation API edit. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No native loop interval edit. |
| 24. No blocking operations without cancellation support | Pass | No new blocking production operation. Tests use queue barriers, counter completion and bounded process deadlines, without sleeps or polling. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 34. Response/output types use `private` Fields | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 47. No bare field/option names in prose — must use backticks | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Identity, annotation ownership and existing immediate-complex dispatch have implemented root-cause fixes. No fixture names, validator relaxations, stubs or workarounds are added. Full remaining P5 semantics retain their explicit plan ownership. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Qore-managed values and local metadata are exception safe; existing scoped instance namespaces restore on every return and exception. Cancellation propagates unchanged and failed conversion/decoding permits reuse. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Only the supplied output registry acquires prefixes. Shared type components and owned namespace mappings are read-only during conversion; synchronized callers verify unchanged shared state. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Helpers use XsdAbstractType, XsdQNameValue and Namespaces; XML metadata uses heterogeneous hash<auto>. Native lists preserve their occurrence/value distinction. Tests construct mixed containers without narrowed hash assignments. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Identity and immediate-base checks use constant component operations. Each occurrence is converted once, and annotation/attribute processing remains linear in the supplied metadata. No ancestry backtracking or conversion retry is introduced. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Unit and integration regressions require exact errors for invalid values, facets, counts, incompatible components, unbound/malformed type QNames and missing derived attributes. Nil, empty, anonymous, list/union and cross-registry builtin cases are checked. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Changed public entry points document parameters, results/errors and examples; implemented design, README and release notes describe identity and annotation ownership. The invoice example executes; affected API docs build without warnings. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP flags changed. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Diagnostics use constant format strings. QName lookup validates lexical namespace identity, and direct extensions compare resolved bases. No credentials, raw I/O or unchecked native memory access is introduced. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Final production source passes 112 suites/1144 cases/56907 reported assertions; the 11-case/342-assertion focused suite passes four source modes and explicit AOT. The final 224-row matrix passes all five with 72 exact expected errors and 416 independently valid outputs per mode. Complete original survey rows and isolated strict ledger results are unchanged; no regression or missing row is hidden. |
