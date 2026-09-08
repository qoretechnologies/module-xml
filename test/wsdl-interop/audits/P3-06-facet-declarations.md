# P3-06 audit: numeric facet declarations

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: WSDL.qm, numeric facet declaration/value tests, independent declaration
matrix and adjudication, scalar design, README, execution record and current
reports. No C++ or core repository change is part of this commit.

The complete audit-changes skill was reread. Applicable module structure,
sandboxing, cancellation and DataProvider design guidance was reviewed. The
checklist below records all 62 checks individually. The implementation adds
no app, action or request/response data record; those DataProvider-specific
checks are N/A rather than requirements to register the scalar count typedef.

Normative basis and every observed compiler disagreement are recorded in
[facet-declarations-adjudication.md](../facet-declarations-adjudication.md).
The independent tests retain exact Decimal and expanded-name assertions where
one schema compiler rejects valid input. Invalid Qore declarations must fail
with their intended exception category, regardless of validator disagreement.

Audit findings fixed: inherited/builtin opposite bound consistency; repeated
exclusive endpoints outside base enumeration/digit value spaces; qualified
facet attributes and ordered grammar; malformed numeric provider metadata;
preservation of the existing simpleContent grammar error category. Regression
reproductions and final test evidence are recorded in EXECUTION.md.

Final verification: 40 affected Qore suites / 509 cases pass without warnings.
Focused declarations pass 10 cases / 176 assertions; numeric values pass 10 cases /
420 assertions. Full Python discovery runs 103 tests with exactly the same seven
tracked P4/P5/P6 failures as P3-05, zero errors/skips/warnings. The new independent
matrix passes all 172 schema expectations, 344 contract parses and 608 exact-value
input/output documents, with the adjudicated oracle disagreements recorded.

WSDL Qdx/Doxygen completes without warnings. Both-version survey and strict
coverage retain identical counts, failure rows and stage accounting to P3-05:
220 broad failures; 72 selected descriptions / 648 directions; zero selected
failures or failed exact-value stages. Both committed reports identify source
SHA-256 028eb787df869635f643f65f75f31a5168b49b71dfc8a31f5320aec5673fbe2c.
Final logs use the /tmp/wsdl-p3-06-*-reviewed naming recorded in EXECUTION.md.
No C++ changed, so this increment requires no new Valgrind run. All 62 checklist
items have Pass or N/A status; there are no unresolved audit failures.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module or module-layout change; WSDL is an existing external single-file module. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 release notes describe numeric declaration validation and exact arbitrary-size counts. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing qore_external_user_module WSDL registration remains correct; there is no new module. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module or module-layout change; WSDL is an existing external single-file module. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | WSDL keeps wsdlintro as its first documentation section. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL and both updated Qore tests use %modern without redundant parse directives. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module or module-layout change; WSDL is an existing external single-file module. |
| 8. No `%include` usage (deprecated for modules) | Pass | No deprecated %include is introduced. |
| 9. Copyright 2026 on all new files | Pass | Authored tests, adjudication, audit and documentation carry 2026 notices; third-party files are unchanged. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module or module-layout change; WSDL is an existing external single-file module. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module or module-layout change; WSDL is an existing external single-file module. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No C++ or QPP changes. Qore VM loop cancellation and managed values apply; no new native blocking operation is introduced. |
| 13. `%modern` directive present | Pass | wsdl-facet-declarations.qtest and wsdl-numeric-facets.qtest contain %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | Both Qore suites and the new Python test have executable permissions. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Qore tests prepend local qlib before requiring ../qlib/WSDL.qm; the worker uses the repository development module. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | xml is delivered by this repository and QUnit by core. The reused survey worker guards external json with %try-module. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ or QPP changes. Qore VM loop cancellation and managed values apply; no new native blocking operation is introduced. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ or QPP changes. Qore VM loop cancellation and managed values apply; no new native blocking operation is introduced. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ or QPP changes. Qore VM loop cancellation and managed values apply; no new native blocking operation is introduced. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production changes perform no new filesystem or network operations. Python uses isolated temporary fixtures and bounded existing subprocess/oracle helpers. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ or QPP changes. Qore VM loop cancellation and managed values apply; no new native blocking operation is introduced. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ or QPP changes. Qore VM loop cancellation and managed values apply; no new native blocking operation is introduced. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ or QPP changes. Qore VM loop cancellation and managed values apply; no new native blocking operation is introduced. |
| 24. No blocking operations without cancellation support | N/A | No C++ or QPP changes. Qore VM loop cancellation and managed values apply; no new native blocking operation is introduced. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 34. Response/output types use `private` Fields | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 47. No bare field/option names in prose — must use backticks | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No app/action registration, request/response record, field presentation, connection factory or dependency JAR is changed; these rules do not apply to scalar facet metadata. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Implemented numeric declaration rules follow XSD 1.0 without fixture-specific production code or machine-width clamping. Named oracle defects do not change production expectations. Other scalar requirements remain active P3 work. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Qore-managed values own all state; streaming grammar frames are local, namespace scopes unwind, and XmlReader attribute traversal restores its element with on_exit. Failed-addition tests verify registry and fixed-facet reconstruction rollback. Cancellation exceptions are rethrown. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Grammar frames belong to one parse. Declaration finalization completes before publication; private fixed facets and provider snapshots are read-only during acceptance. Existing schema configuration-before-sharing contract remains in force. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | XsdFacetCount is union<int,string>; grammar frames use a hashdecl and an enum. Numeric facet snapshots remain typed. Dynamic XML nodes are checked before interpretation and downcasts are guarded. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Streaming grammar takes one pass with depth-proportional state. Count comparison is linear in decimal length. Ancestor constraints are checked during dependency finalization; no iterative search proportional to a numeric count is introduced. Example conversions occur only after a bounded comparison. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Focused tests cover missing/duplicate/unknown facets, wrong namespaces, malformed values/fixed attributes/patterns, inapplicable facets, exact contradictory/inherited/fixed constraints, huge counts, reconstruction, samples and rollback. Existing simpleContent grammar keeps WSDL-ERROR; facet failures use XSD-SIMPLETYPE-ERROR. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | New public count type and changed count members document representation and since version. Schema API documents facet failures. Scalar design, README, normative adjudication and release notes describe behavior and examples; Qdx/Doxygen validation is recorded below. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++ or QPP changes. Qore VM loop cancellation and managed values apply; no new native blocking operation is introduced. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Format strings are constant. Integer/count lexical validation precedes canonical comparison. No credentials, network fetches or user-controlled executable code are added. XML annotations remain opaque application content. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Focused Qore, affected suites, independent 172-schema/344-contract/608-document declaration matrix and existing numeric value matrix verify exact values and error categories. Final evidence and report hashes are recorded below. |
