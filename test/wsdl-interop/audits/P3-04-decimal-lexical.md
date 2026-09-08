# P3-04 audit: exact decimal values and native formatting

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: WSDL.qm, wsdl-decimal-lexical.qtest, decimal-consumers.qr,
test_decimal_lexical.py, strict selection/coverage assertions, current reports,
README/EXECUTION and design/wsdl-scalar-values.md. The full audit-changes skill
and applicable module-structure, sandboxing and DataProvider design guides were
consulted. All 62 checklist items are recorded below. Core changes are already
committed and separately audited; this increment changes no XML C++.

Normative basis: [XSD 1.0 decimal](https://www.w3.org/TR/xmlschema-2/#decimal).
Native binary inputs use an explicit shortest round-trip binding policy, similar
to [BigDecimal.valueOf(double)](https://docs.oracle.com/en/java/javase/24/docs/api/java.base/java/math/BigDecimal.html#valueOf(double)).
Original decimal text remains exact. Neither the MPFR display heuristic nor a
float cast may discard authored digits. Ordinary canonical inputs retain native
float output when their decimal spelling survives a subsequent serialization;
other inputs remain strings. This is documented as a binding policy, not as
universal XPath casting or binary arithmetic becoming exact decimal arithmetic.

Validation:

- Focused Qore: 5 cases / 380 assertions, including 2000-digit strings,
  native extrema/subnormal/nonfinite values, optionality, Serializable copies,
  provider lists and attributed/CDATA simple content.
- All 38 affected Qore suites: 489 cases, debugging enabled, no warnings.
- Independent matrix: 784 documents, actual SOAP 1.1/1.2 contracts and both
  directions, exact Decimal values/expanded names plus pinned Xerces. All
  documents are also checked with libxml2; its known 24-digit pre-parser limit
  produces 80 explicitly adjudicated disagreements on this older version.
  Newer libxml2 may accept all of them. No document or missing stage is skipped.
- Strict gate: 63 descriptions / 576 directions, zero selected failures.
  Broad coverage: 252 failure rows versus 264 on the parent, no new failures.
  All eight old decimal value losses and four decimal-pattern input failures
  are resolved. Current value stages: 484 ok, zero failed, 324 unreachable,
  1464 unassessed. Original corpus bytes/hashes/findings are unchanged.
- Full Python discovery: 100 tests, exactly seven tracked P4/P5/P6 failures,
  zero errors/skips/warnings. These diagnostic failures remain visible and are
  not represented as passing conformance.
- Final WSDL Qdx/Doxygen passes without warnings. Qore 3.0 is required for the
  formatter committed as core 20422dedf. Its independent native/float oracles,
  IR/AST and Valgrind evidence are in core's round-trip-formatting.md audit.
  The focused XML decimal suite also passes Valgrind with zero errors or
  definite/indirect/possible loss. The pre-existing DW_AT_abstract_origin reader
  warning remains a P9 environment finding and is not suppressed.

The execution record lists exact commands, runtime dependency selection and
/tmp/wsdl-p3-04-final-* / python-reviewed / independent / valgrind logs. This
closes base decimal conversion only. Numeric bounds/digit facets, general value
enumeration and the other P3 acceptance criteria remain active; P4 has not
started. No installation or push was performed.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, separated .qc file, directory layout or QMOD registration. Existing WSDL remains a single-file external user module. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 release notes document exact decimal input, validated providers, native round-trip formatting and the new Qore 3.0 minimum. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | The existing WSDL CMake registration is unchanged. No additional binary/user module is added. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, separated .qc file, directory layout or QMOD registration. Existing WSDL remains a single-file external user module. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | The first existing documentation section remains wsdlintro. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL and both Qore tests/workers use %modern; no redundant parse options are added. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, separated .qc file, directory layout or QMOD registration. Existing WSDL remains a single-file external user module. |
| 8. No `%include` usage (deprecated for modules) | Pass | No deprecated %include directive is introduced. |
| 9. Copyright 2026 on all new files | Pass | The new qtest, consumer, Python test and audit, plus the modified design document, carry 2026 notices. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, separated .qc file, directory layout or QMOD registration. Existing WSDL remains a single-file external user module. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, separated .qc file, directory layout or QMOD registration. Existing WSDL remains a single-file external user module. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | This XML commit has no native code, operation, loop or QPP flags. The Qore formatter dependency is separately tested and audited in core 20422dedf. |
| 13. `%modern` directive present | Pass | The qtest and decimal-consumers.qr use %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | The qtest and consumer script have executable permission. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The qtest and worker prepend local qlib before relative WSDL requirements. Test environments select the local XML binary, Debug core and explicitly compiled DataProvider dependency snapshot. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | xml is supplied by this repository and is required directly. The consumer uses %try-module for external json, with a clear dependency error rather than a skipped test. QUnit is a core-provided module. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | This XML commit has no native code, operation, loop or QPP flags. The Qore formatter dependency is separately tested and audited in core 20422dedf. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | This XML commit has no native code, operation, loop or QPP flags. The Qore formatter dependency is separately tested and audited in core 20422dedf. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | This XML commit has no native code, operation, loop or QPP flags. The Qore formatter dependency is separately tested and audited in core 20422dedf. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | No production I/O is added. The consumer reads the explicitly supplied local WSDL. Independent checks use offline schemas, argument-list subprocesses, bounded deadlines and temporary-directory cleanup. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | This XML commit has no native code, operation, loop or QPP flags. The Qore formatter dependency is separately tested and audited in core 20422dedf. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | This XML commit has no native code, operation, loop or QPP flags. The Qore formatter dependency is separately tested and audited in core 20422dedf. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | This XML commit has no native code, operation, loop or QPP flags. The Qore formatter dependency is separately tested and audited in core 20422dedf. |
| 24. No blocking operations without cancellation support | N/A | This XML commit has no native code, operation, loop or QPP flags. The Qore formatter dependency is separately tested and audited in core 20422dedf. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 34. Response/output types use `private` Fields | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 38. Password/secret fields have `"sensitive": True` | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 47. No bare field/option names in prose — must use backticks | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | XsdDecimalDataType is an atomic scalar type, not a record or app/action. No Fields constant, options, catalog, factory, request/response type or dependency JAR is introduced. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | The helper implements a complete base decimal binding, without fixture-specific conversion, rounding workarounds or stubs. NOTHING-returning scalar metadata methods implement the atomic type contract. Unfinished P3 facets and later-phase diagnostics remain explicitly tracked. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | All new allocations are managed Qore values. Conversion exceptions propagate and do not mutate the supplied value/provider. The consumer and Python workers have scoped lifetimes and deterministic subprocess cleanup. Native cancellation/unchanged-destination checks are in the core formatter audit. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Decimal conversion uses call-local values. Provider requiredness is private, initialized on construction/deserialization and copied for optional/mandatory variants; there is no mutable global state. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | The provider exposes typed category maps, AbstractDataProviderType interfaces and typed field declarations. auto is needed only for the documented heterogeneous native input and float/string output contract; validated string values reach float conversion. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Lexical validation uses a bounded-alternative anchored decimal regex and linear whitespace/string processing. Float reconstruction formatting is bounded by binary64 output size. Native arbitrary-precision formatting uses the separately audited logarithmic candidate search and cancellable output expansion. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Positive, negative and boundary tests cover XML whitespace, empty/control/Unicode/trailing/exponent inputs, nonfinite values, wrong native types, omission versus null and optionality. SOAP serialization/deserialization, provider type and missing-value categories are asserted. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | The new public type and methods document parameters, results, errors and realistic invoice examples. Durable design describes the exact string/native value contract; README, execution record, release notes and reports are current. Final Qdx/Doxygen is warning-free. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | This XML commit has no native code, operation, loop or QPP flags. The Qore formatter dependency is separately tested and audited in core 20422dedf. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No credentials, user-controlled format strings, unchecked indexes or new network access. Decimal regex validation precedes permissive numeric conversion. Schema and independent-value checks reject changed values, not only malformed output. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | The focused suite passes 5/380 and all 38 affected suites pass 489 cases. The independent matrix checks 784 documents using Xerces plus exact Decimal values and records the existing libxml2 limit. Strict selection passes 63 descriptions/576 directions, all eight old decimal value losses are resolved, and no new broad failure row appears. |
