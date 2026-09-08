# P3-08 audit: list lexical forms and ordered values

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: WSDL list conversion/restrictions/providers/fields/examples, focused Qore
regressions, independent list matrices, oracle diagnostic severity, strict list
value assertions and reports, release/design documentation and execution evidence.
No C++ change or core repository edit belongs to this commit.

The full audit-changes skill was reread. Applicable guidance was reviewed in
qore-module-structure.md, module-sandboxing-audit-guide.md,
cooperative-cancellation.md, data-provider-checklist.md and
data-provider-development-guide.md (the actual filename of the referenced
development guide). Every one of the 62 checklist items is recorded below.

Audit corrections include empty-list key initialization, scalar-versus-list
field formatting, preserved public WSDL part names, provider metadata checks,
invalid native list input error categories, retained boolean pattern tokens,
validated samples and the missing lexical parameter documentation. The oracle
harness now records warnings independently of validity; named list and namespace
reference diagnostics are documented in list-values-adjudication.md.

Verification: 42 affected Qore suites pass 533 cases; the focused suite passes
12 cases / 165 assertions. Qdx/Doxygen passes without diagnostics. Full Python
discovery runs 110 tests with exactly the seven unchanged tracked P4/P5/P6
failures, zero new failures, errors, skips or warnings. All 62 audit items are
Pass or N/A; no audit failure remains.
Strict coverage passes 89 descriptions / 756 directions with 664 successful
value assessments, zero failed/missing value checks and no selected failures.
The 220 broad failure rows are unchanged; all original survey rows and corpus
hashes are unchanged. Final module SHA-256 is
4fb454d9a3b93d41b8a075667a6dca064ffa39974c668ab3dcfdbb04035b936e.
Logs use /tmp/wsdl-p3-08-final-* and /tmp/wsdl-p3-08-completed-*; the latter
reports and documentation follow the documentation-only parameter correction.
No new Valgrind run is required because no C++ changed.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | Existing single-file external WSDL module; no new module or layout change. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 release notes describe ordered list enumeration, retained whole-list patterns, native item boundaries, field updates and validated examples. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing qore_external_user_module registration builds and documents WSDL; Qdx/Doxygen validation uses the local module. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | Existing single-file external WSDL module; no new module or layout change. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | wsdlintro remains the first documentation section. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL uses %modern; no redundant parse directives were introduced. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | Existing single-file external WSDL module; no new module or layout change. |
| 8. No `%include` usage (deprecated for modules) | Pass | No %include was introduced. |
| 9. Copyright 2026 on all new files | Pass | All authored Qore/Python/adjudication/audit files have 2026 notices; modified Java/module/design files retain their 2026 notices. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | Existing single-file external WSDL module; no new module or layout change. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | Existing single-file external WSDL module; no new module or layout change. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No C++, QPP, native I/O or native loop changes. |
| 13. `%modern` directive present | Pass | New list suite and the shared consumer worker use %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | New list suite and existing consumer worker have executable mode 0755. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Both Qore files prepend local qlib before the relative WSDL requirement; xml belongs to this project. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | External json is guarded by %try-module; QUnit is supplied by Qore and xml by this repository. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++, QPP, native I/O or native loop changes. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++, QPP, native I/O or native loop changes. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++, QPP, native I/O or native loop changes. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production changes perform in-memory validation. The test worker reads authored manifests/WSDL with ReadOnlyFile; Python/Java use bounded offline manifests and subprocess deadlines. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++, QPP, native I/O or native loop changes. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++, QPP, native I/O or native loop changes. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++, QPP, native I/O or native loop changes. |
| 24. No blocking operations without cancellation support | N/A | No C++, QPP, native I/O or native loop changes. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | Pass | No single-key hash slice is used as a record; dynamic facet and choice access intentionally retrieves scalar entries. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 34. Response/output types use `private` Fields | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | Pass | XsdListDataField exposes AllowedValueInfo records with ordered native values and lexical display names. Whole/repeated choice replacements publish only validated metadata; restored fields compare exact item values. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 47. No bare field/option names in prose — must use backticks | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No app/action, request/response record, connection factory, credentials or dependency JAR is introduced; scalar restriction metadata is not an application catalog. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No JNI module or new dependency JAR. The existing pinned Xerces test JAR remains unchanged; Java worker compilation uses -Xlint:all -Werror. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No JNI module or new dependency JAR. The existing pinned Xerces test JAR remains unchanged; Java worker compilation uses -Xlint:all -Werror. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | List rules implement XSD lexical boundaries, ordered item equality and whole-list patterns without fixture-specific production branches. All remaining P3 scalar/union criteria and P4–P9 remain required. Oracle warning severity is corrected generically and named reference defects are explicitly assessed. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Qore-managed values own item metadata and providers. Reconstruction validates before publication and rebuilds transient membership/count state. Failed field updates and schema additions preserve prior state. Cancellation propagates during item conversion; Java diagnostics are local to each operation and subprocess temporaries are cleaned on failure/cancellation. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Runtime providers read private restriction metadata and membership maps. Optional variants are newly constructed. Schema and field configuration-before-sharing is documented; per-operation Java diagnostics have no shared mutable collector. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | XsdListItemInfo, XsdListFacetInfo and XsdListConversionInfo type metadata/conversion results; exact XsdFacetCount remains in use. Category and optionality checks protect reconstruction. Lists retain native atomic values or validated lexical tokens as required by patterns. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Ordered length-prefixed value keys support hashed finite-choice membership without pairwise list comparisons. Each conversion traverses items linearly per derivation level; generated pattern/length candidates remain bounded. No per-item schema graph is retained. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Tests cover invalid lexical items/declarations, empty lists versus empty items, wrong native categories, order changes, precision boundaries, malformed metadata, failed choice updates, cancellation, optionality, repeated occurrences and impossible examples. Oracle decoding rejects malformed/empty warning encodings and warning-bearing unreachable records. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public metadata/provider/field methods have Doxygen parameters, returns, throws and examples; validateFacets documents its lexical argument. Updated design, README, release notes and adjudication explain representation and generation bounds. Qdx/Doxygen is clean after the documented parameter correction. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++, QPP, native I/O or native loop changes. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Diagnostics use literal format strings. Native item boundaries and metadata categories are validated; generated allocations are bounded. The oracle still prohibits DTD/network resolution and treats errors/fatal errors as rejection, retaining warnings separately. No credentials were added. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Two matrices check 18 cases across 54 schemas/108 actual SOAP contracts each; 576 inputs, 276 binding outputs and 2288 consumer/example documents are independently assessed. 4176 consumer rows include both directions, versions, copies and element/message providers. Exact item/order assertions supplement Xerces/libxml2 validation; strict List coverage detects value loss. |
