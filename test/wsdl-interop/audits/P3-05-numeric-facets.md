# P3-05 audit: exact numeric restriction values and consumers

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: WSDL.qm; numeric facet Qore/Python/consumer tests; strict selection and
coverage assertions; current reports; XML mainpage anchor; scalar design,
README and EXECUTION. No C++ or core repository change is included.

The full audit-changes skill was reread before this commit. Applicable sections
of core design/qore-module-structure.md, module-sandboxing-audit-guide.md,
data-provider-checklist.md and data-provider-development-guide.md were checked.
The cooperative-cancellation checklist is N/A for native code in this increment;
Qore computations and the existing bounded subprocess cancellation tests apply.
Every one of the skill's 62 items is recorded below.

Normative basis: XSD 1.0 Second Edition part 2 sections 4.3.4–5 and 4.3.7–12.
Numeric bounds/enumeration compare exact values; patterns constrain normalized
lexical forms. Fractional leading zeros count under this edition's totalDigits
coefficient-and-scale rule. Original fixture bytes and adjudications are retained.

Evidence: focused Qore 10 cases/413 assertions; all 39 affected suites/499 cases
without warnings; independent libxml2/Xerces matrix 1440 documents plus 432
provider rejection checks. Real SOAP 1.1/1.2 bindings and both directions cover
simple content, attributes, lists/unions, providers, reconstruction and examples.
Strict coverage passes 72 descriptions/648 directions; broad failures decrease
from 252 to 220, no new failure rows; exact value stages 556 pass, zero fail.
Current reports match WSDL source SHA-256
7c9596f35c2e17acdc37b9f81b34bb121c28eb7a78a0bfa07571684cb30e4c7a.

The XML documentation used a generic NAMED_ARGS subsection anchor that collided
with the core reference. It now uses xml_named_args. Native XML Doxygen with
FAIL_ON_WARNINGS and WSDL Qdx/Doxygen pass without warnings using normal core tags.
No C++ changed, so Valgrind is not required for this increment. Test environments,
root-cause reproductions and final log paths are recorded in EXECUTION.md.

Full Python discovery: /tmp/wsdl-p3-05-python-verified.log reports 102 tests
with exactly seven tracked P4/P5/P6 failures, no errors/skips/warnings. An earlier
assertion incorrectly assigned the already-passing IntegerSimpleTypePattern
family to P3; the corrected assertion preserves its original P9 ownership. These diagnostics are never counted as passing
conformance, and P3 remains active. No push or installation is performed.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, module layout, QMOD registration or separated implementation file. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 release notes describe exact restriction values, reconstructed providers and validated numeric/list examples. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing external WSDL registration remains correct; no new user or binary module is needed. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, module layout, QMOD registration or separated implementation file. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | The module retains wsdlintro as its first documentation section. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL and the authored Qore tests/workers use %modern; no redundant parse options. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, module layout, QMOD registration or separated implementation file. |
| 8. No `%include` usage (deprecated for modules) | Pass | No deprecated %include is introduced. |
| 9. Copyright 2026 on all new files | Pass | The new tests, worker, audit and updated design carry 2026 notices; third-party corpus notices are unchanged. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, module layout, QMOD registration or separated implementation file. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, module layout, QMOD registration or separated implementation file. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No C++, QPP, native operation or native loop changed. Qore VM cancellation and managed values apply. |
| 13. `%modern` directive present | Pass | Both wsdl-numeric-facets.qtest and numeric-facet-consumers.qr have %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | New qtest, Qore worker and Python test are executable. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Tests prepend local qlib and require WSDL by relative path; explicit environment selects local XML and Debug core. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Repository-owned xml is a hard requirement. External json uses %try-module and raises a dependency error if missing; QUnit is supplied by core. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++, QPP, native operation or native loop changed. Qore VM cancellation and managed values apply. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++, QPP, native operation or native loop changed. Qore VM cancellation and managed values apply. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++, QPP, native operation or native loop changed. Qore VM cancellation and managed values apply. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | No production I/O is added. The worker reads explicit local manifest/WSDL files; Python uses offline validators, subprocess argument lists, deadlines and scoped temporary directories. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++, QPP, native operation or native loop changed. Qore VM cancellation and managed values apply. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++, QPP, native operation or native loop changed. Qore VM cancellation and managed values apply. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++, QPP, native operation or native loop changed. Qore VM cancellation and managed values apply. |
| 24. No blocking operations without cancellation support | N/A | No C++, QPP, native operation or native loop changed. Qore VM cancellation and managed values apply. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No app, action, connection factory, request/response class or dependency JAR is introduced. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No app, action, connection factory, request/response class or dependency JAR is introduced. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No app, action, connection factory, request/response class or dependency JAR is introduced. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No app, action, connection factory, request/response class or dependency JAR is introduced. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No app, action, connection factory, request/response class or dependency JAR is introduced. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No app, action, connection factory, request/response class or dependency JAR is introduced. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No app, action, connection factory, request/response class or dependency JAR is introduced. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No app, action, connection factory, request/response class or dependency JAR is introduced. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No app, action, connection factory, request/response class or dependency JAR is introduced. |
| 34. Response/output types use `private` Fields | N/A | No app, action, connection factory, request/response class or dependency JAR is introduced. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | Pass | Existing XML field names, descriptions, types and requiredness remain supplied through QoreDataField; the numeric subclass adds value equality and retains metadata after reconstruction. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | Pass | Fixed/default attribute examples retain their declared values; generated numeric/list examples are checked by independent validators in both directions. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | Pass | Numeric fields retain typed AllowedValueInfo with value and display_name. Repeated elements use element_allowed_values. Exact equality accepts lexical aliases without dropping the choices. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No app, action, connection factory, request/response class or dependency JAR is introduced. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No app, action, connection factory, request/response class or dependency JAR is introduced. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No app, action, connection factory, request/response class or dependency JAR is introduced. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No app, action, connection factory, request/response class or dependency JAR is introduced. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No app, action, connection factory, request/response class or dependency JAR is introduced. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | Pass | Existing field short descriptions are retained; no long or markdown short_desc is added. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | Pass | Existing XML attribute/simple-content descriptions retain markdown references; no new app description is introduced. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | Pass | Public type documentation uses invoice amounts and describes why lexical precision and field equality matter. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | Pass | No unquoted boolean/NOTHING value is introduced in field desc text. |
| 47. No bare field/option names in prose — must use backticks | Pass | No bare field/option identifier is introduced in field desc prose. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No app, action, connection factory, request/response class or dependency JAR is introduced. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No app, action, connection factory, request/response class or dependency JAR is introduced. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No app, action, connection factory, request/response class or dependency JAR is introduced. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No app, action, connection factory, request/response class or dependency JAR is introduced. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No app, action, connection factory, request/response class or dependency JAR is introduced. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Numeric value constraints are fully implemented without fixture-specific rules, rounding workarounds or validation bypasses. P3 explicitly permits precise unsupported-generation errors. Schema declaration legality and other scalar families remain separate active P3 criteria. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Qore owns allocations. Replacement choice maps are fully validated before publication; failed setter tests prove previous choices survive. Provider snapshots eliminate weak namespace graph lifetime errors. Serialization and independent worker failure/cancellation tests retain cleanup. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Providers use private configuration fixed after construction/reconstruction. Acceptance is read-only. Like QoreDataField, field choice setters are configuration operations before sharing; this contract is documented in the scalar design. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | XsdNumericFacetInfo and AllowedValueInfo preserve typed metadata. Bounds use validated strings and counts use integer sizes. auto is confined to heterogeneous XML/native value interfaces; schema downcasts are guarded. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Decimal canonicalization/comparison and exact grid arithmetic are linear in lexical length per facet. No unbounded increment-by-one search or arbitrary-precision rounding loop is used. Examples validate a bounded set of candidates. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Tests cover nearby/exclusive/negative/zero bounds, native digits, malformed metadata, invalid patterns, empty intervals, missing/optional/null categories inherited from base providers, reconstruction and setter rollback. SOAP/provider/field/sample error categories are asserted. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public hashdecl/provider/field methods document parameters, outputs and applicable errors. Design, examples, README, execution record and release notes are updated. XML anchor collision is fixed; final XML and WSDL documentation is warning-free. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++, QPP, native operation or native loop changed. Qore VM cancellation and managed values apply. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | All format strings are constants. Lexical validation precedes comparison/indexing; no credentials or network access is added. Immutable source fixtures and exact value assertions prevent schema-valid changed values from passing. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Focused Qore passes 10 cases/413 assertions; 39 affected suites total 499 cases. Independent matrix validates 1440 documents with libxml2/Xerces and exact Decimal values/names. Strict gate passes 72 descriptions/648 directions; broad failures decrease 252 to 220 with no new rows. |
