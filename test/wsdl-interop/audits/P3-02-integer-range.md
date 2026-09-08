# P3-02 audit: exact integer ranges and providers

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: qlib/WSDL.qm, wsdl-integer-range.qtest, the attribute-consumer assertion,
integer-consumers.qr, test_integer_range.py, test_coverage.py, strict selection,
current reports, README/EXECUTION, this audit and design/wsdl-scalar-values.md.
The full audit-changes skill was read before this commit; all 62 checks follow.
Referenced core module structure, sandboxing, cancellation, DataProvider checklist
and development guides were reviewed. No native XML code or module registration
is changed. The new scalar provider does not introduce an app/action or record.

Normative basis: [XSD 1.0 integer and its derived types](https://www.w3.org/TR/xmlschema-2/#integer),
including signed and unsigned value bounds in sections 3.3.13-3.3.25. Existing P1
adjudication retains the specification-based unsigned lexical decisions and
libxml2 arbitrary-number precision limitation. Xerces acceptance alone does not
override the specification; every valid output also requires exact Python integer
comparison. No original corpus byte or historical finding was changed.

Core prerequisite 860603291 has its own full audit, Debug /usr build, 116 IR/AST
cases / 1664 assertions, three Valgrind suites with zero errors/lost memory, and
AOT exact-constant verification. It fixes MPFR raw integer digits, boxed removal
ownership and typed foreach cleanup. It is committed develop without a push;
unrelated core development and astparser were preserved. No additional XML
Valgrind run is required for this Qore-only increment. The existing P9 tool/runtime
findings remain explicit and are not represented as passing environment acceptance.

Final checks and logs are detailed in the P3-02 entry of EXECUTION.md:

- The new test passes 16 cases / 980 assertions, including reconstructed-state
  rejection/recovery. The other 35 affected suites pass, for 479 cases total.
  Final native/module paths and --enable-debug are used. The first reconstructed
  state test incorrectly expected serialize() to return a hash; using the typed
  serializeToData() API fixes the test, whose final rerun passes.
- The independent matrix checks 1200 documents in 26 actual SOAP bindings,
  both directions, attributes/simple content, providers, generated examples and
  original/reconstructed services. Ninety-six known libxml2 input disagreements
  are explicitly asserted; exact values and Xerces verdicts are mandatory.
- Python discovery runs 96 tests: exactly seven existing P4/P5/P6 failures,
  zero errors and no skips. Updated test_coverage expectations require the
  newly preserved integer values and all 64 adjudicated output disagreements.
- Both-version survey changes exactly sixteen previously clamped output
  verdicts to the original input's known libxml2 precision rejection. All other
  rows are identical. Adjudicated coverage resolves 32 value-loss failures,
  adds none and retains 264 failures. Strict selection expands to 60 descriptions
  and 536 message-direction cases, zero selected failures; missing/skipped
  stages remain zero and unassessed infoset work remains explicit (1492).
- WSDL Qdx/Doxygen and the documented provider example pass without warnings or
  errors. The durable scalar contract documents mixed int/string output and
  preserves the bounded NT_INT metadata relied on by existing consumers.

P3 remains active: this audited increment does not certify other scalar facets,
particles, bindings or SOAP protocol behavior assigned to remaining work.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 release notes document exact ranges, large strings, provider validation and integer examples. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing WSDL single-file registration remains in CMakeLists.txt; no new user module. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | Existing first module section remains wsdlintro. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL, the qtest and consumer worker use %modern without redundant new directives. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 8. No `%include` usage (deprecated for modules) | Pass | No deprecated %include directive is added. |
| 9. Copyright 2026 on all new files | Pass | All new authored tests/worker/audit and changed design documentation carry 2026 notices. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 13. `%modern` directive present | Pass | The new test and worker use %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | wsdl-integer-range.qtest is executable; the modified attribute-consumer qtest retains its executable mode. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Both Qore tests and the worker prepend local qlib before relative WSDL requirements. Runtime module paths select the tested native XML and core DataProvider qmod. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | xml is shipped with this project and is required directly. The external json binary module uses %try-module in the worker, raising an explicit missing-dependency error; no skip. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Only the offline consumer worker reads manifest/WSDL paths with builtin ReadOnlyFile. The library adds no I/O. Python temporary fixtures and pinned Xerces use bounded subprocess deadlines and existing cleanup. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 24. No blocking operations without cancellation support | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | Only a scalar datatype is added; no new request/response HashDataType or Fields registration is required. The scalar provider is integrated and tested in existing record/list consumers. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 34. Response/output types use `private` Fields | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 47. No bare field/option names in prose — must use backticks | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Exact string range comparison precedes numeric conversion. Large integers retain exact strings, and providers receive original list items. No fixture-name behavior, skip, suppression or workaround. Remaining P3/P4-P9 failures stay explicit. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Validation uses local values and constant maps; errors occur before conversion. Serializable member types and names are validated. Optional/mandatory variants copy state before mutation. Recovery after invalid serialized state and native prerequisite cleanup are tested. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Builtin maps are constant; helper state is call-local. Datatype/requiredness are private and stable after construction/reconstruction; variant construction mutates only a new copy. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Helper parameters, bounds lists and provider APIs have explicit types; heterogeneous values are necessary to reject incompatible runtime input types. Serialized-state tests use hash<SerializationInfo>. Worker manifests use list<hash<auto>> with named protocol fields. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Canonicalization and comparison use a fixed number of linear string passes and constant-sized bound lookups. There is no per-digit integer accumulation or quadratic concatenation. Native formatting is proportional to emitted text. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Tests reject malformed syntax, fractions/nonfinite inputs, wrong native types, out-of-range boundaries, missing required values and invalid reconstructed members with the intended category. Optional NOTHING differs from NULL. All thirteen builtin bounds and large exact inputs pass. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | All new public provider methods have return/parameter/error docs as applicable; the class and durable scalar design provide an invoice/order identifier example. Return-type changes and list conversion policy are documented. Qdx/Doxygen and the extracted example pass without warnings/errors. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No new module, separated source, QPP class, native operation/loop, app/action/field registration, factory, JAR or QPP method flag in this increment. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Numeric conversion cannot truncate/overflow before range checks. Canonical inputs are validated before comparison; error format strings are constant. No credential or untrusted source interpolation into commands. Original corpus hashes and baseline findings remain unchanged. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Final focused tests pass 16/980; all 36 affected suites account for 479 successful cases after the final focused rerun. Independent Python/Xerces checks validate 1200 documents with exact values. Final 96-test discovery has only seven tracked P4/P5/P6 failures, no errors/skips. The expanded strict gate passes 60 descriptions/536 directions and resolves 32 value-loss failures without adding failures. |
