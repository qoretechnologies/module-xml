# P3-03 audit: boolean lexical values and list whitespace

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: WSDL.qm, wsdl-boolean-lexical.qtest, boolean-consumers.qr,
test_boolean_lexical.py, current reports, README/EXECUTION and
design/wsdl-scalar-values.md. The full audit-changes skill was read and all 62
items were reviewed against this diff. The referenced core module-structure,
sandboxing, cooperative-cancellation and DataProvider checklist/development
guides were consulted for the applicable module, scalar type and test paths.
No native code, module registration, app/action or record type is changed.

Normative basis: [XSD 1.0 boolean](https://www.w3.org/TR/xmlschema-2/#boolean)
and [list datatypes](https://www.w3.org/TR/xmlschema-2/#list-datatypes).
The four boolean lexical forms and fixed list whitespace collapse govern XML
input. The native zero/one policy is documented as a binding policy; it does
not claim to implement XPath numeric truth casting.

The focused test failed three cases on the parent implementation. Its final
version passes 5 cases / 281 assertions. The independent matrix exercises 616
documents (356 input, 132 serialized, 128 provider/example) with both libxml2
and Xerces, actual SOAP 1.1/1.2 bindings, both directions, simple content,
attributes, lists/unions and Serializable reconstruction. Exact boolean values
and expanded names supplement schema validation. The test oracle caught an
initial erroneous invalid-list expectation; it was corrected to a malformed
item. Strict validation exposed TAB/LF/CR list tokenization, whose root cause
was fixed before the final checks. The full run exposed a CDATA regression; ordered scalar text projection fixes it, and the retained XML context test passes all 80 independent document checks. No known failure was hidden or skipped.

All 37 affected Qore suites pass (484 cases) with --enable-debug and local
module paths. A committed DataProvider export from core 860603291 is compiled under /tmp/wsdl-core-deps so concurrent source edits cannot invalidate its AOT artifact. The final runner checks all warning capitalization. Qdx/Doxygen passes without warnings/errors. Both-version survey
and complete coverage retain identical rows/counts to P3-02; only source
metadata differs. Strict selection remains 60 descriptions / 536 directions,
zero selected failures; the 264 remaining broad failures, 1492 unassessed
infoset checks and eight decimal value failures stay explicit. This increment
does not complete P3 or certify the P4-P9 behavior. No C++ changed, so a new
Valgrind run is not applicable. Existing P9 tool/runtime findings remain open.

The decimal standards/heuristic investigation is recorded in EXECUTION.md;
no decimal or global Qore rounding policy is implemented in this commit.
Final Python discovery runs 98 tests with exactly seven tracked P4/P5/P6 failures, zero errors/skips and no warnings. The final focused rerun adds native MPFR nonfinite and nonboolean numeric rejection checks and passes 5/281. Logs are recorded alongside the execution entry.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, separated .qc file, directory module or QMOD registration is added; the existing single-file WSDL module retains its layout and registration. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | Existing WSDL 0.5.8 notes describe the strict boolean input policy and provider list validation. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing WSDL registration in CMakeLists.txt is unchanged; no new module is introduced. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, separated .qc file, directory module or QMOD registration is added; the existing single-file WSDL module retains its layout and registration. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | The first existing module section remains wsdlintro. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL, the new qtest and worker use %modern without redundant new directives. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, separated .qc file, directory module or QMOD registration is added; the existing single-file WSDL module retains its layout and registration. |
| 8. No `%include` usage (deprecated for modules) | Pass | No deprecated %include directive is introduced. |
| 9. Copyright 2026 on all new files | Pass | Every new authored test/worker/audit and modified design document carries a 2026 notice. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, separated .qc file, directory module or QMOD registration is added; the existing single-file WSDL module retains its layout and registration. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, separated .qc file, directory module or QMOD registration is added; the existing single-file WSDL module retains its layout and registration. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No native QPP class or namespace registration changes. |
| 13. `%modern` directive present | Pass | The new qtest and worker both use %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | wsdl-boolean-lexical.qtest has mode 0755. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The qtest and worker prepend local qlib before relative WSDL requirements. Runtime paths select the tested XML binary and core DataProvider qmod. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | xml is provided by this project and is required directly; the external json binary uses %try-module with an explicit missing-dependency error, not a skip. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++/QPP source, native operation, native loop or method flag changes. Qore execution retains its built-in cancellation and allocation cleanup. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++/QPP source, native operation, native loop or method flag changes. Qore execution retains its built-in cancellation and allocation cleanup. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++/QPP source, native operation, native loop or method flag changes. Qore execution retains its built-in cancellation and allocation cleanup. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Library changes add no I/O. The offline worker reads only the supplied local WSDL through builtin ReadOnlyFile; subprocesses use argument lists and deadlines, with temporary-directory cleanup. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++/QPP source, native operation, native loop or method flag changes. Qore execution retains its built-in cancellation and allocation cleanup. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++/QPP source, native operation, native loop or method flag changes. Qore execution retains its built-in cancellation and allocation cleanup. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++/QPP source, native operation, native loop or method flag changes. Qore execution retains its built-in cancellation and allocation cleanup. |
| 24. No blocking operations without cancellation support | N/A | No C++/QPP source, native operation, native loop or method flag changes. Qore execution retains its built-in cancellation and allocation cleanup. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 34. Response/output types use `private` Fields | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 38. Password/secret fields have `"sensitive": True` | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 47. No bare field/option names in prose — must use backticks | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | Only the existing scalar XsdBooleanDataType changes; no app/action, request/response record, Fields constant, options, factory, presentation catalog or JAR is introduced. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Exact boolean validation replaces permissive parsing; list preconversion is disabled through the provider API. Ordered text/CDATA is projected before scalar validation, and XML list collapse precedes tokenization. No special fixture names, workaround, skip or suppression; remaining P3-P9 work stays explicit. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Validation uses call-local values. Exceptions occur before returning a converted result; recovery after invalid values is tested. Inherited optional/mandatory variants copy state, and Serializable original/reconstructed consumers pass. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | No new mutable shared state; text fragments remain call-local and the retained XML carrier is not changed. The helper is stateless, and provider variants retain inherited copy semantics. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Boolean helper and provider methods have explicit parameter/return types. Heterogeneous auto inputs are necessary to reject invalid runtime categories. Worker protocol results are named hashes and tests check native bool results. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | A fixed number of linear whitespace passes precedes constant boolean comparisons and linear list splitting. No per-character concatenation, quadratic loop or new unbounded native operation. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Empty/invalid/case-variant/trailing-data/control-character strings, null, structured/binary values, nonfinite/fractional/nonzero-or-one numbers and missing required provider values receive the intended error categories. Legal whitespace, zero/one, empty lists and optional omission pass. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public added/changed provider methods document parameters, return values and errors as applicable. Class/design examples show false and yes behavior and provider lists. Qdx/Doxygen passes without warnings/errors; consumers exercise generated SOAP examples. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++/QPP source, native operation, native loop or method flag changes. Qore execution retains its built-in cancellation and allocation cleanup. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Format strings are constant; runtime strings are validated before boolean conversion. No new credentials, filesystem/network authority or user-controlled shell syntax. Historical corpus/findings remain unchanged. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Focused Qore regression passes 5 cases / 281 assertions; all 37 affected suites pass (484 cases). Independent libxml2/Xerces tests cover 616 documents in both bindings/directions. Survey and coverage differ from P3-02 only in source metadata; strict scope 60/536 passes and all 264 remaining failures are retained. |
