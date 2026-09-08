# P3-01 audit: integer XML lexical validation

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: qlib/WSDL.qm, test/wsdl-integer-lexical.qtest,
test/wsdl-interop/test_integer_lexical.py, test_survey.py, current reports,
README/PLAN/EXECUTION, this audit and design/wsdl-scalar-values.md.
The full audit-changes skill was read before committing and each of its 62
checks was applied. Referenced core module-structure, sandboxing, cancellation
and DataProvider guides were reviewed; this increment adds no provider/action
registration or native XML code.

Normative basis: XML Schema Datatypes Second Edition, integer/unsigned lexical
spaces (3.3.13 and 3.3.21-24) and whiteSpace (4.3.6):
https://www.w3.org/TR/xmlschema-2/#integer,
https://www.w3.org/TR/xmlschema-2/#unsignedLong,
https://www.w3.org/TR/xmlschema-2/#rf-whiteSpace.
The existing P1 normative adjudication retains the Xerces disagreement on
signed unsigned strings; validator acceptance cannot override that lexical rule.

Core prerequisite ea9ddfc51 preserves embedded NUL bytes in substitutions, with
its own complete audit, Debug build, both-engine regressions and clean native
memory results. No C++ changes are part of this XML commit; no additional XML
Valgrind run is required. Existing native XML from the final P2 C++17 build and
local Debug libqore are selected via QORE_MODULE_DIR/LD_LIBRARY_PATH. The core
DataProvider qmod precedes core qlib; in-repository WSDL is required by path.
No install, astparser change or push.

The final acceptance and logs are recorded under P3-01 in EXECUTION.md. All
35 affected Qore suites pass 463 cases. The independent matrix validates 936
documents. Python discovery runs 94 tests with exactly seven later-phase
failures, zero errors/skips; the fourteen survey tests pass. WSDL documentation
is warning-free. Both-version source/corpus comparison confirms only the 32
invalid signed unsigned inputs change behavior, and both-direction coverage
removes exactly 64 prior failures, retaining 296. No valid-input row changes.
The original findings and source fixture hashes remain byte-identical.
P3 precision, range, provider/facet and other scalar behavior remain active;
this completed lexical gate is not represented as full phase acceptance.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL v0.5.8 release notes document integer lexical rejection and XML whitespace rules. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | The existing WSDL single-file module remains registered; no new module is introduced. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | Existing first section remains wsdlintro. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL and the new Qore test use %modern; no redundant directive added. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 8. No `%include` usage (deprecated for modules) | Pass | No include directive added. |
| 9. Copyright 2026 on all new files | Pass | All authored new test/design/audit files carry 2026 notices. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 13. `%modern` directive present | Pass | The new Qore test uses %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | wsdl-integer-lexical.qtest is executable (0755). |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The Qore test prepends local qlib before requiring ../qlib/WSDL.qm; the worker also loads local development WSDL. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | xml is delivered with this project and uses a hard dependency; no new external binary dependency. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | No runtime filesystem/network access is added. Independent tests use temporary offline fixtures, the existing bounded worker and pinned validators. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 24. No blocking operations without cancellation support | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 34. Response/output types use `private` Fields | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 47. No bare field/option names in prose — must use backticks | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | The lexical gate fixes permissive conversion and XML whitespace root causes without changing native field shapes. Native NUL truncation is separately fixed in core ea9ddfc51. Remaining P3 requirements are explicit active work; no stub, fixture-name branch or hidden skip. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Validation uses local scalar values and immutable constants; exceptions occur before conversion and propagate with the existing API error categories. Reconstruction/error-recovery tests pass; no native allocation is changed here. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | The helper map is constant and all validation/normalization values are call-local. No shared mutable state is introduced. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Helper parameters and boolean result are typed; generic input is required to reject incompatible runtime types explicitly. Test schema maps and XsdAbstractType references are typed. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Each lexical expression scans the input with absolute anchors and fixed character classes. Whitespace handling uses a fixed number of linear passes; no per-character copies or recursive matcher. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Empty/missing text, booleans/null/binary/structured values, malformed signs, fractions, exponents, garbage, Unicode digits, controls/NUL and signed unsigned strings fail with the intended category. Valid zero/sign/leading-zero forms and XML whitespace are covered. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Durable scalar design and README give examples and commands; release notes describe changed behavior. Internal helper only; no new public method. Final WSDL Qdx/Doxygen completes with no warnings/errors. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No new module, separated source, QPP class, native code/loop, provider/action/app/Fields registration, factory, JAR or public method flag in this increment. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Absolute lexical anchors and length-preserving core substitution prevent suffix truncation. No credentials or user-controlled format strings; tests preserve original fixture hashes. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 35 affected suites pass 463 cases; 16 new cases make 983 assertions. 936 independent documents cover both real SOAP bindings and directions with exact values/names. Final 94-test Python discovery has only the seven explicitly retained P4/P5/P6 diagnostics; survey tests pass and every corpus result change is an expected invalid-input rejection. |
