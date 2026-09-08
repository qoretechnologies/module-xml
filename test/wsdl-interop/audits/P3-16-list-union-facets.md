# P3-16 audit: list-owned facets with union-valued items

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: WSDL metadata/schema/provider conversion and field reconstruction,
new Qore/Python regressions, release notes, scalar design, README and execution
evidence. The full audit-changes skill was reread. Module structure, sandboxing,
cooperative cancellation, DataProvider checklist and development-guide rules were
reviewed for applicability; every item is recorded below. No C++ changed.

Root cause: list facet metadata described only atomic item types. Lists whose
items were unions fell through to literal enumeration comparison in schema
conversion and lost whole-list enumeration/pattern checks in detached providers.
The six-case initial regression fails on the committed baseline. The fix captures
ordered identities during actual base conversion, applies lexical patterns to
collapsed original tokens, and shares captures through inherited restrictions.
Field corruption testing also exposed a missing item-descriptor check during
XsdListDataField reconstruction; the added hook rejects it immediately.

Normative references: XSD 1.0 Part 2 [list datatypes](https://www.w3.org/TR/xmlschema-2/#dt-list),
[enumeration](https://www.w3.org/TR/xmlschema-2/#rf-enumeration),
[pattern](https://www.w3.org/TR/xmlschema-2/#rf-pattern) and
[whitespace](https://www.w3.org/TR/xmlschema-2/#rf-whiteSpace).
No new oracle adjudication applies. The existing libxml2 empty-list enumeration
compiler defect remains separately unassessed there, with Xerces and exact empty
values still required for those documents. No corpus file or pinned artifact changed.

Verification:

- Final source and compiled AOT regression: 10 cases / 245 assertions, including
  enclosing unions and schema/provider failure cleanup, with no diagnostics.
- All 60 affected XML suites pass (700 cases / 12689 recorded assertions); the
  expanded final suite adds one case and 53 assertions, for combined final evidence
  of 701 cases / 12742 assertions. Original logs and aggregate remain unchanged.
  The soap suite intentionally exercises three failed assertions internally.
- New independent matrix: nine cases, 27 schemas, 54 SOAP contracts, 516 input and
  204 output binding documents, 3184 consumer results and 1520 output/example
  documents. All 2240 documents are checked by Xerces, plus exact typed values;
  libxml2 checks all except its existing empty-list enumeration compiler defect.
- Both-version survey and strict coverage unchanged outside versions: 89 selected
  WSDLs / 756 directions, zero selected failures, 220 broad tracked failures.
- Final full Python discovery: 133 methods, with exactly the same 33 tracked
  P4/P5/P6 failure signatures as P3-15. No new failures or missing cases.
- WSDL/SoapClient/SoapDataProvider AOT and WSDL docs/qjar builds pass without
  warnings or errors. No C++ changes; no new Valgrind run is required.

WSDL SHA-256: `3e3fc3b3c003502c5e8f81b59476360eed49e56283dcf2d17b6eb07ede248d0d`.
Native XML remains `8ec5487ebe937450478fc856e5c02114e5cf9ffaf9201cf70d052907b40f2e12`.
Evidence: `/tmp/wsdl-p3-16-{baseline-unit,reviewed-unit,reviewed-aot-unit,
field-metadata-baseline,field-metadata-fixed,final-checks,final-python,
independent-first,final-survey,final-coverage,aot-final,docs}.log` and report JSON.
The test runner initially bound a method reference to a temporary provider, and
expected native strings after valid integer conversion; both test authoring
assumptions were corrected. The final tests assert preserved typed values and
valid output. A later test helper syntax error was corrected before execution.

P3 remains active. Builtin NMTOKENS/IDREFS/ENTITIES list identity in unions is the
next reproduced case, alongside remaining primitive/date/IEEE/binary/QName/entity/
regex and XML-RPC requirements. All P4-P9 requirements remain in scope.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, separated source or QPP class. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL release notes describe list-owned facets on union items, retained tokens and reconstructed fields. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing WSDL/SoapClient/SoapDataProvider qmod targets rebuilt successfully. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, separated source or QPP class. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | First module section remains wsdlintro. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL.qm retains %modern without redundant directives. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, separated source or QPP class. |
| 8. No `%include` usage (deprecated for modules) | Pass | No deprecated %include directives added. |
| 9. Copyright 2026 on all new files | Pass | New Qore/Python tests and audit record carry 2026 copyright. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, separated source or QPP class. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, separated source or QPP class. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, separated source or QPP class. |
| 13. `%modern` directive present | Pass | New Qore regression declares %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | wsdl-list-union-facets.qtest is executable (0755). |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Local qlib prepend precedes relative ../qlib/WSDL.qm requirement. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | xml/WSDL belong to this repository; QUnit is delivered by Qore. No external binary dependency added. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ changes in this XML increment. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ changes in this XML increment. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ changes in this XML increment. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production helpers add no filesystem or network operations; independent tests reuse the offline fixture/worker harness. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ changes in this XML increment. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ changes in this XML increment. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ changes in this XML increment. |
| 24. No blocking operations without cancellation support | Pass | No blocking operations added; Qore loop cancellation and on_exit restore schema and provider captures after second-item failures. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 34. Response/output types use `private` Fields | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | Pass | XsdListDataField retains AllowedValueInfo value/display_name normalization, ordered primitive keys, repeated choices and atomic replacement validation. |
| 38. Password/secret fields have `"sensitive": True` | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 47. No bare field/option names in prose — must use backticks | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Extends the atomic-only list metadata root cause. Own facets use captured actual base conversion, and field reconstruction validates descriptors. No fixture or validator waiver added. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Capture ownership restores thread state on all exits; inherited wrappers reuse bounded intervals. Schema/provider cancellation, unexpected and binary-error categories are asserted, followed by recovery. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Schema list capture is thread-local; provider captures use target identity, call depth and scoped intervals. Existing public graph configuration must precede concurrent use. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed item/conversion metadata; optional builtin is exclusive with union-item mode, mandatory union providers required. Restored field metadata is checked before publication. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Actual item validation occurs once through the inherited base conversion; each facet wrapper makes a linear pass for its own list tokens and identity. No exponential graph traversal introduced. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Ordered enumeration and duplicates, inherited patterns/counts/item facets, invalid declarations, native boundaries, empty/optional values, metadata corruption, field updates, reentry and cleanup covered. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public metadata fields, release notes, durable scalar design and examples, README and execution record updated; WSDL docs/qjar build passes. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP changes. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No credentials, raw buffers or user-controlled format strings. Capture count is checked before indexed lexical access; restored descriptors validated. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Independent selected-family and exact Decimal values plus pinned validators cover 54 actual SOAP contracts, both directions, attributed/repeated values, reconstructed consumers and examples. Source and AOT agree, including enclosing unions. |

All 62 items are classified, no failed audit items remain. Final comparison and combined-suite evidence are in `/tmp/wsdl-p3-16-{python-comparison,reviewed-checks}.json`.
