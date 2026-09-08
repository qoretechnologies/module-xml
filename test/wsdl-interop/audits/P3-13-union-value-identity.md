# P3-13 audit: union primitive values and lexical restrictions

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: WSDL Qore implementation, the new Qore/Python regressions, two adjusted
existing graph tests, scalar design, README, release notes and execution evidence.
All 62 audit-changes items are recorded below. Qore module-structure, sandboxing,
cancellation, DataProvider checklist and development guidance were reviewed for
applicability. No native XML source, build rule or external fixture is changed.

The implemented families are decimal/integer, boolean, string and distinct
hexBinary/base64Binary. Union results carry family/value identities independently
of native conversion, retaining lexical input when reserialization would select
a different value. Union patterns and enumeration remain enforced in restrictions,
detached providers, finite field choices, repeated values and generated examples.
The remaining primitive/list/native-input requirements remain required P3 work;
this is not P3 acceptance or a SOAP conformance claim.

Normative references: XSD 1.0 Part 2
[ordered union selection](https://www.w3.org/TR/xmlschema-2/#union-datatypes),
[value-space equality](https://www.w3.org/TR/xmlschema-2/#section-fundamental-facets),
[enumeration](https://www.w3.org/TR/xmlschema-2/#enumeration), and
[whiteSpace](https://www.w3.org/TR/xmlschema-2/#rf-whiteSpace).
Independent libxml2/Xerces validation is paired with primitive-family/value
assertions; schema validity alone is insufficient.

Audit findings fixed before this record:

- Preserve native/lexical primitive identity, own union facets and field comparisons.
- Serialize public atomic metadata without transient obsolete member lists; retain
  associations through provider reordering/removal and reject malformed metadata.
- Validate every restored enumeration entry against its base, including an invalid
  entry following a valid entry (the baseline accepted this metadata).
- Cache ordinary own-facet rejection and propagate unexpected errors, including
  enumeration reporting (the baseline swallowed TEST-CANCELLED).
- Fix the indexed container use-after-free exposed by a malformed boolean metadata
  member in core commit bac32354a, with separate regression, Valgrind and full audit.
- Correct the test documentation environment to select the already fixed local
  JNI module. The installed module still passes Java native frame line -2 into a
  Qore location requiring at least -1; existing JNI commit 0576b97 fixes it.

Final WSDL SHA-256:
`a481f15526cf54cf4b284679c6e41b57cba8500c1fc1088550475fbc0faff37c`.
Runtime: isolated `/tmp/wsdl-core-date/build-debug`, Debug with `/usr` prefix,
SHA-256 `fc3a60454896701c17913c4ed768678959f9788c059be20c334d72a43ab2ac80`.
The final native XML artifact was rebuilt without source changes, SHA-256
`8ec5487ebe937450478fc856e5c02114e5cf9ffaf9201cf70d052907b40f2e12`.
No installation or push was performed.

Validation:

- New Qore regression: 12 cases / 311 assertions, passing from local source and
  the rebuilt WSDL AOT artifact. Positive, negative, boundary, metadata, field
  update and error-cleanup paths are covered.
- All 57 affected XML suites pass: 670 cases / 11001 assertions recorded. The
  existing soap suite intentionally exercises failed assertions internally;
  all its test cases succeed. Per-suite logs and reconstructed totals are in
  `/tmp/wsdl-p3-13-reviewed-checks.json`.
- All 11 independent union methods pass after the final error-propagation fix,
  including both new value-identity methods, existing providers, whitespace,
  schema graphs, both real SOAP bindings and request/response directions.
- Full Python discovery before the final enumeration-reporting guard ran 127
  tests with exactly the same 33 tracked P4/P5/P6 failure signatures and no new
  error or skip. The final guard was then checked with all affected Qore suites
  and all independent union methods. No diagnostic failure is counted as success.
- Final survey and strict coverage are unchanged outside version metadata:
  89 selected WSDLs / 756 directions, zero selected failures, 220 broad failures.
- WSDL, SoapClient and SoapDataProvider AOT builds and WSDL/native documentation,
  including qjar, pass without build/runtime warnings. Docs use the existing
  local fixed JNI and matching isolated reflection/astparser artifacts.
- After the native relink, the 11-case union suite (305 assertions, before the
  final Qore-only enumeration-reporting guard) passed Valgrind: zero errors and
  zero definite/indirect/possible loss, no suppressions. The previously recorded
  DW_AT_abstract_origin reader warning remains a P9 environment finding. No C++
  change in this increment requires an additional Valgrind run.

Logs: `/tmp/wsdl-p3-13-reviewed-*`, `/tmp/wsdl-p3-13-final-python.log`,
`/tmp/wsdl-p3-13-final-valgrind.log`, and the enum-metadata/enum-errors baseline
and fixed logs. The first matrix stdout path collided with its xml.qtest log;
that combined log is preserved, xml.qtest was rerun into its own log, and final
counts were reconstructed from every per-suite QUnit summary. Failed earlier
docs runs and their debugger traces remain separate from the final passing run.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module entry point, separated source, QPP class, app/action registration or JAR dependency. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 release notes describe the implemented primitive families, lexical retention, union facets and field choices. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing WSDL, SoapClient and SoapDataProvider registrations remain valid; their AOT targets build successfully. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module entry point, separated source, QPP class, app/action registration or JAR dependency. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | The existing first mainpage section remains wsdlintro. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL.qm retains %modern; no redundant parse modes added. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module entry point, separated source, QPP class, app/action registration or JAR dependency. |
| 8. No `%include` usage (deprecated for modules) | Pass | No %include added. |
| 9. Copyright 2026 on all new files | Pass | WSDL, changed tests, new Qore/Python tests, durable design and this audit use 2026 notices. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module entry point, separated source, QPP class, app/action registration or JAR dependency. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module entry point, separated source, QPP class, app/action registration or JAR dependency. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module entry point, separated source, QPP class, app/action registration or JAR dependency. |
| 13. `%modern` directive present | Pass | The new and changed qtests use %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | All new/changed qtests are executable (0755). |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Local qlib prepending precedes the relative WSDL requirement in each Qore regression. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | WSDL and xml are this repository's modules; QUnit is delivered by Qore. Existing external dependency handling in the Python worker is retained. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ or QPP changes in this XML increment; core prerequisite was audited and committed separately. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ or QPP changes in this XML increment; core prerequisite was audited and committed separately. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ or QPP changes in this XML increment; core prerequisite was audited and committed separately. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | New conversion, provider and field code performs no File/Dir/Socket/HTTPClient operations. Independent tests use the existing bounded offline worker harness. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ or QPP changes in this XML increment; core prerequisite was audited and committed separately. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ or QPP changes in this XML increment; core prerequisite was audited and committed separately. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ or QPP changes in this XML increment; core prerequisite was audited and committed separately. |
| 24. No blocking operations without cancellation support | Pass | No blocking operation introduced. Qore owns loop cancellation; existing graph tests and new probe/error tests check state restoration. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 34. Response/output types use `private` Fields | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | Pass | New generic field logic preserves schema-generated field metadata. The serializable hashdecl describes internal primitive rules rather than a business record. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | Pass | Existing schema examples and both independent consumer/example matrices remain exercised; new docs include boolean/integer and integer/decimal choices. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | Pass | Choice setters normalize every entry to AllowedValueInfo with value and display_name before constructing maps. |
| 38. Password/secret fields have `"sensitive": True` | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 47. No bare field/option names in prose — must use backticks | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | Generic schema union/field implementation only; no new business action, record type, app, registration, description catalog, secret field or JAR. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | The change preserves lexical values when native conversion changes member selection and compares the implemented families exactly. No heuristic, validator bypass, fixture-specific rule, skip or TODO added. Other datatype families remain explicit subsequent P3 work. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Qore owns temporary values. Scoped on_exit restores nested thread-local contexts, including probe and facet errors. Setters build complete replacement maps before publishing; failed restoration does not expose a partial object. The native index ownership defect exposed by malformed metadata is separately fixed in core bac32354a. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Per-operation state is thread-local. Atomic lookup maps are initialized with provider configuration; public types are documented to be configured before concurrent use. No persistent mutable result cache added. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed trial/identity/atomic hashdecls, typed providers and lists, validated restored metadata, and explicit casts after class checks. No C-style casts or untyped new callbacks. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Shared unions retain contextual memoization, including ordinary facet rejection. Semantic checks occur only at the operation owner; unchanged output text avoids a second read. Enumeration scans are linear; field lookup maps are built once per setter. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Tests cover malformed atomic metadata and whitespace rules, empty/invalid metadata lists, invalid regexes, invalid enum base values, reordering/replacement, missing/invalid values, ordinary directional rejection, unexpected errors and recovery. Enumeration reporting no longer swallows probe failures. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public helper/field methods and atomic metadata are documented; scalar design, README and release notes explain implemented families and examples. WSDL Qdx/Doxygen and Java wrapper steps pass with the previously fixed local JNI module selected. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++ or QPP changes in this XML increment; core prerequisite was audited and committed separately. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No external fetch, credentials, user-controlled format string or unsafe native buffer operation added. Error formatting uses fixed format strings, and metadata shape/type checks precede indexed use. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | New regressions reproduce value changes and missing errors before fixes. Final Qore and AOT tests, 11 independent union methods, affected suites and unchanged both-version corpus reports pass. The broad Python suite retains exactly its 33 tracked later-phase failures. |
