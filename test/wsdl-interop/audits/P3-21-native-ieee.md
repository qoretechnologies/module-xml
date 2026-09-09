# P3-21 audit: native IEEE scalar conversion

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: the new binary-module convert_xsd_float API, its C++ implementation,
CMake/autotools registration, public Qore/native/rational regressions, native
release notes, implemented design, README and execution evidence. No WSDL source
or main Qore code changes belong to this increment. All 62 skill items and the
applicable module-structure, sandboxing and cancellation design guides were reviewed.
DataProvider registration checks do not apply to this native value API.

The existing WSDL preflight establishes binary64 conversion for both IEEE types,
permissive lexical prefix acceptance and incorrect underflow/overflow handling.
This separately testable native prerequisite supplies strict direct conversion;
WSDL scalar/provider/facet integration remains outstanding. The native algorithm
and normative references, including W3C R-214's double exponent correction, are
in [the native design](../../../design/xml-ieee-conversion.md).

Decimal text parses directly at the target precision with the classic locale,
under a saved/restored nearest-rounding environment. Native binary32 conversion
compares the original value with exact midpoints; it does not first narrow a
number/int or render a native float as approximate decimal text. Public calls
preserve signed zero, use gradual underflow and accept only the XSD special
spellings. Explicit scans check cancellation every 100 bytes.

Review corrections: float stream overflow may produce infinity or a clamped
finite value; both are accounted for. The native test harness now owns its boxed
large integers through ValueHolder (the initial 960-byte loss was in temporary
test arguments). Its comma-locale facet has stack ownership on exceptional exits.
The Qore concurrency test owns a thread pool: a closure-completion counter with
detached workers did not guarantee native TLS cleanup before process exit and
initially left one 368-byte DTV allocation visible to Valgrind. No production
conversion allocation was implicated, and no suppression or timing retry was added.

Final checks: 5 public cases / 597 assertions across AST, IR, JIT and tiered
(20 cases / 2388 assertions); 1380 native checks over four rounding modes and
classic/comma C++ locales; 3144 exact-rational reference values. Native C++ and
AST/IR Valgrind runs have zero errors and no definitely/indirectly/possibly lost
allocations. Qore Valgrind uses the previously authorized QORE_PCRE2_NO_JIT=1
control. The existing core DWARF reader warning remains the recorded P9 environment
item; it is not hidden or claimed fixed.

All 64 existing XML suites pass 742 cases / 15319 assertions. SOAP intentionally
checks three failed assertions inside passing cases. Both-version survey and strict
coverage match P3-20 outside version fields: 89 selected WSDLs / 756 directions,
zero selected failures and 220 tracked broad failures. The 150-method full Python
run with 33 tracked P4/P5/P6 failures remains the preceding P3-20 baseline; this
native-only increment runs the three new Python methods and both corpus drivers.
There is no new phase boundary or claim that the remaining full suite passes.
Native/AOT/documentation builds and combined-unit syntax compilation are clean.

Evidence prefix: /tmp/wsdl-p3-21-. Final production conversion evidence is in
reviewed-checks, reviewed-xml-checks, reviewed-corpus-checks, reviewed-build-docs,
reviewed-survey/coverage, lifecycle-checks, cpp-owned-locale-checks, unity-syntax
and final-hashes. Main Qore remains clean on develop at 9dab82749; no push,
installation or main-checkout build occurred.

Final native XML SHA-256: `e5f15836d1d3b1577d223fcff29fa59ce916192c229cac579eb3343ed3c0ac02`.
Final Debug core SHA-256: `c8b0739f796b93c0f056cbf2a37050d6902de45c3e9361ed3565754ac5549afb`.

Checklist result: **25 Pass, 37 N/A, 0 Fail**.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | External repository; no Qore builtin module-list entry applies. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | External binary-module release notes in docs/mainpage.doxygen.tmpl describe the new conversion API. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | CMake adds XsdFloat.cpp to the existing xml target and an explicit native test target. Autotools source/header and single-compilation-unit lists include it; the combined unit passes syntax compilation. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new user module, separated .qc source or QPP class is introduced. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new user module, separated .qc source or QPP class is introduced. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No new user module, separated .qc source or QPP class is introduced. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new user module, separated .qc source or QPP class is introduced. |
| 8. No `%include` usage (deprecated for modules) | Pass | No %include is introduced. |
| 9. Copyright 2026 on all new files | Pass | All new C++/Qore/Python/design/audit files carry 2026 copyright. Existing ql_xml.qpp already carries 2026. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new user module, separated .qc source or QPP class is introduced. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new user module, separated .qc source or QPP class is introduced. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new user module, separated .qc source or QPP class is introduced. |
| 13. `%modern` directive present | Pass | xsd-float.qtest explicitly uses %modern; ieee-conversion.qr obtains modern semantics from the .qr extension. |
| 14. Executable permission set (`chmod +x`) | Pass | The qtest, .qr worker and Python driver are executable. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Qore tests prepend the repository qlib directory before requirements; QORE_MODULE_DIR selects this repository build-debug binary, verified by its final hash. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project xml and core QUnit are hard requirements. The external json module uses %try-module with an explicit missing-dependency error. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | Pass | Production conversion performs no filesystem operations; test input files are handled by the Qore test worker. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | Pass | No native network operations are introduced. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No production filesystem/network operation requires a sandbox manager. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | The test worker reads its explicit temporary JSON manifest with ReadOnlyFile. This is test input transport, not a production resource-access path. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | Pass | The three input-length loops check qore_check_cancel every 100 bytes. The native rounding search has at most 31 iterations; native harness loops have fixed small bounds. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | Pass | Only qore_check_cancel is used; there is no deprecated interruption API. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | Pass | All input scans check every 100 iterations. Conversion also checks at entry and after standard-library decimal parsing. |
| 24. No blocking operations without cancellation support | Pass | No external blocking I/O or wait is introduced in production. Native comparisons are bounded; test workers use queues with deadlines and an owned pool for teardown. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 34. Response/output types use `private` Fields | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 47. No bare field/option names in prose — must use backticks | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No provider action, app, field schema, option catalog, factory or dependency JAR is changed. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | The complete native API implements the requested IEEE conversion directly. It does not retry failed backends, cap lexical lengths/exponents, change fixtures or apply display heuristics. WSDL integration is explicitly the next increment, not reported as fixed here. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | ReferenceHolder owns number references and strings, ValueHolder owns boxed test integers, and streams/environment guards use automatic ownership. The test locale facet is stack-owned with nonzero refs. Cancellation/error paths restore state. Final Valgrind has zero errors and no lost allocations. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | All production mutable state is per call. Only the current thread floating-point environment is temporarily changed and restored. Four synchronized pool workers verify independent conversions with deterministic teardown. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Strong C++ scalar types, enum-class lexical states, static_cast and typed Qore lists represent conversion data. Heterogeneous QoreValue/JSON is confined to the public scalar dispatch and test transport. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Lexical validation and trimming are linear in input bytes. Exact native binary32 choice needs at most 31 comparisons, with no decimal rendering or exponent-sized allocation. The standard-library parser consumes the actual input; no expanded exponent text is generated. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Complete lexical validation precedes parsing; every parse must reach EOF. Illegal types, NUL, missing digits, trailing garbage, non-XML whitespace and special spellings have category assertions. Float/double overflow, underflow and signed zero are covered. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | The public QPP function documents parameters, result, lexical/conversion/cancellation errors, rounding semantics and a measurement example. Native design, README, release notes and execution evidence describe the implemented API and limits. Final native/user documentation build is clean. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | Pass | convert_xsd_float is RET_VALUE_ONLY and NAMED_ARGS: it can throw, has no external side effects and restores the thread floating-point state. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Length-checked byte access, bounded endpoints and constant format strings; no credentials, external resource access or user-controlled executable text. The JSON worker treats all cases as data. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | The public regression passes 5 cases / 597 assertions in AST, IR, JIT and tiered modes. Native host-state/cancellation verification passes 1380 checks. Three independent rational tests check 3144 values. All 64 existing XML suites pass 742 cases / 15319 assertions, and both-version corpus results remain unchanged. |
