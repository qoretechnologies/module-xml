# P3-09 audit: boolean lexical restrictions

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: boolean restriction declarations, lexical retention in schema/provider
conversion, defaults, fixed attribute/field value equality, generated examples,
Qore regressions, independent SOAP matrices, reports and documentation. No C++
change or Qore core repository edit belongs to this commit.

The audit-changes skill was reread before this commit. Applicable guidance in
qore-module-structure.md, module-sandboxing-audit-guide.md,
cooperative-cancellation.md, data-provider-checklist.md and
data-provider-development-guide.md was reviewed (the latter is the actual name
of the skill's referenced development guide). All 62 checklist items are below.

Audit corrections: the inherited-default path now validates restriction patterns;
fixed boolean comparisons use truth values for both runtime attributes and schema
references/restrictions; copied field documentation no longer suggests boolean
enumeration is a legal XSD facet. Test method references retain strong provider
variables for their full assertion lifetime.

Verification: 43 affected Qore suites pass 546 cases with no warnings; the focused
suite passes 13 cases/184 assertions. Qdx/Doxygen is clean. Full Python discovery
runs 113 tests with exactly the seven unchanged tracked P4/P5/P6 failures and no
new failures, errors, skips or warnings. Final affected, docs, survey, coverage
and boolean matrix runs include the default-path audit correction. The full Python
run is /tmp/wsdl-p3-09-final-python.log; other final evidence uses
/tmp/wsdl-p3-09-completed-* (focused output is also in the affected suite log).

Strict coverage passes 89 descriptions/756 directions with 664 successful value
checks and no selected, failed-value or missing-value cases. All 220 broad failure
rows and every original survey/coverage case record are unchanged. Final WSDL
SHA-256: e04a9cc66988dce2898b29e020905075e4432c5f9c4f5f9710ec11d04b8d1427.
No C++ changed, so no new Valgrind run applies. All audit items are Pass or N/A.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | Existing single-file external WSDL module; no new module or layout change. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 release notes describe retained boolean patterns, forbidden facet rejection, fixed attribute/field value equality and exhaustive valid examples. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing qore_external_user_module registration builds and documents WSDL; Qdx/Doxygen validation uses the local module. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | Existing single-file external WSDL module; no new module or layout change. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | wsdlintro remains the first documentation section. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL uses %modern; no redundant parse directives were introduced. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | Existing single-file external WSDL module; no new module or layout change. |
| 8. No `%include` usage (deprecated for modules) | Pass | No %include was introduced. |
| 9. Copyright 2026 on all new files | Pass | New Qore/Python/evidence/audit files carry 2026 notices; WSDL, design and shared Python matrix retain their existing 2026 notices. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | Existing single-file external WSDL module; no new module or layout change. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | Existing single-file external WSDL module; no new module or layout change. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No C++, QPP, native I/O or native loop changes. |
| 13. `%modern` directive present | Pass | The new boolean suite uses %modern; the reused consumer worker already uses %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | test/wsdl-boolean-facets.qtest and the shared consumer worker have executable mode 0755. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The boolean suite prepends local qlib before requiring ../qlib/WSDL.qm; the shared consumer uses its existing relative requirement. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | The new suite requires QUnit and same-repository xml/WSDL. The shared worker guards its external json dependency with %try-module. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++, QPP, native I/O or native loop changes. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++, QPP, native I/O or native loop changes. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++, QPP, native I/O or native loop changes. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production changes validate in-memory values only. Python writes bounded temporary schema/message manifests and uses the existing offline validator and consumer subprocess deadlines; no new production I/O. |
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
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | Pass | XsdBooleanDataField resolves choices to AllowedValueInfo with value/display_name and compares true/false value keys. Both whole-field and repeated-element replacements validate before publishing state; tests cover rollback and reconstruction. |
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
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No JNI module, new JAR, dependency or Java change; the existing pinned Xerces oracle is reused unchanged. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No JNI module, new JAR, dependency or Java change; the existing pinned Xerces oracle is reused unchanged. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Boolean applicability and lexical/value separation implement the XSD rules generically. No fixture-specific production condition, workaround, TODO or stub is introduced. Remaining P3 union/scalar criteria and P4–P9 stay explicitly required. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Qore-managed strong base providers and typed metadata retain ownership. Reconstruction validates before publication; setters resolve all choices and maps before assignment. Controlled cancellation propagates unchanged. The audit fixed the inherited-default path so it cannot bypass this restriction. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Acceptance reads private metadata and does not mutate shared state. Optional variants construct new providers. Design documentation requires schema/field configuration to finish before sharing with concurrent consumers. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | XsdBooleanFacetInfo carries a typed name and compiled pattern list; boolean providers validate the base family during construction/reconstruction. Lexical validation precedes native conversion. No new untyped callbacks or C casts. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Normalized boolean lexical candidates have at most five characters. Validation is linear in input whitespace and derivation/pattern counts. Finite choices use hashed true/false keys; example generation exhausts four fixed candidates after the supplied default. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | The focused suite covers forbidden facets, invalid lexical/native values, whitespace/CDATA/comments, inherited pattern alternatives/intersections, metadata rejection, optional/repeated providers, defaults, fixed references/restrictions, choice rollback, cancellation and impossible examples. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | New public metadata/provider/field APIs document parameters, returns, errors and examples. The audit corrected copied enumeration wording because enumeration is forbidden on boolean. Release notes, scalar design, README and normative evidence explain the representation; Qdx/Doxygen is clean. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++, QPP, native I/O or native loop changes. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Literal diagnostic format strings, strict boolean lexical validation, bounded example search, typed reconstruction checks and unchanged offline oracle resolution. No credentials, native memory operations or user-controlled format strings added. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 13 focused cases/184 assertions and 43 affected suites/546 cases pass. The independent matrices check 2320 documents and 3104 consumer rows with exact boolean/item/order/name/version assertions. Twenty invalid schemas reject in both processors and all 40 Qore SOAP contracts. Strict coverage and all prior corpus records remain unchanged. |
