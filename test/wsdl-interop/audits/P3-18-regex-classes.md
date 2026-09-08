# P3-18 audit: XSD regex character sets and grammar

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: existing WSDL regex translation and sample generation; Qore and Python
regressions and an offline worker; release notes, durable scalar design, README,
normative/oracle evidence and execution record. The full audit-changes skill and
its applicable design guides were read and applied. No C++ changed; Valgrind is
not required for this increment.

The final source and AOT regression passes 12 cases / 988 assertions. All 62
XML suites pass 722 cases / 14495 assertions, including the SOAP suite's three
intentional failed-assertion checks inside passing cases. AOT and docs builds
are clean. Both-version survey and strict coverage match P3-17 outside versions:
89 selected descriptions / 756 directions, zero selected failures and 220
tracked broad failures. Final frozen Python discovery runs 142 methods in
588.793 seconds with exactly the same 33 tracked P4/P5/P6 failure signatures
and no errors. All three new independent regex methods pass. Implementation
and test hashes remain unchanged throughout the final run.

Normative decisions, source hashes, exact libxml2/Xerces defects and separately
identified equivalent schemas are in [regex evidence](../regex-classes-evidence.md).
Qore input rejection and exact values remain mandatory on every original schema.
No corpus source, pinned JAR or production native code changed.

The audit caught a new no-pattern sample regression before committing: bounded
character search must require an actual pattern facet. Its reduced date case
changed 2026-09-09 to a; the guard and reconstructed date/string/integer regression
now preserve the supplied examples. Two intermediate full Python runs were
explicitly interrupted to finish audit fixes and portable oracle assertions;
only the final frozen run may be used for the commit gate. A temporary probe's
method-name typo and a reversed QUnit assertLt argument were corrected before
final testing; their preliminary logs are retained.

Final WSDL SHA-256:
`d64c20533b0a156965bb3e9905f71462f4d00e1c07e6d6fcad40035f3c504fe2`.
Native XML remains `8ec5487ebe937450478fc856e5c02114e5cf9ffaf9201cf70d052907b40f2e12`.
Evidence is under `/tmp/wsdl-p3-18-`: frozen-hashes.json, exact-checks,
final-unit-guarded, aot-final-unit, docs-final, exact-survey/coverage and frozen-python.
The current P3 increment does not claim phase acceptance; remaining regex backend
limits, primitive/date/IEEE/binary/QName/XML-RPC and all P4-P9 criteria remain open.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, module registration, separated source or QPP class. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | External-module release notes in WSDL.qm describe grammar/set fixes and bounded sample search. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module, module registration, separated source or QPP class. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, module registration, separated source or QPP class. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | Existing wsdlintro introduction remains the first section; no new module. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL.qm and the qtest use %modern; the .qr worker enables modern mode by its extension. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, module registration, separated source or QPP class. |
| 8. No `%include` usage (deprecated for modules) | Pass | No %include usage introduced. |
| 9. Copyright 2026 on all new files | Pass | All authored files carry 2026 copyright; third-party artifacts are unchanged. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, module registration, separated source or QPP class. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, module registration, separated source or QPP class. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, module registration, separated source or QPP class. |
| 13. `%modern` directive present | Pass | The qtest has explicit %modern; the .qr worker has implicit modern mode. |
| 14. Executable permission set (`chmod +x`) | Pass | The qtest and new executable test scripts have executable permission. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Local module paths precede relative WSDL requirements; AOT verification explicitly selects the rebuilt qmods. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | The external json binary module uses %try-module and a precise missing-module branch; project xml and core QUnit remain required. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ or native filesystem/network operations changed. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ or native filesystem/network operations changed. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ or native filesystem/network operations changed. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Only the test worker reads its explicit temporary manifest through ReadOnlyFile; production regex code performs no I/O. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ loops or blocking operations changed; Qore cancellation remains runtime-managed. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ loops or blocking operations changed; Qore cancellation remains runtime-managed. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ loops or blocking operations changed; Qore cancellation remains runtime-managed. |
| 24. No blocking operations without cancellation support | N/A | No C++ loops or blocking operations changed; Qore cancellation remains runtime-managed. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 34. Response/output types use `private` Fields | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 47. No bare field/option names in prose — must use backticks | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No provider action/app registration, business data type, option catalog, factory or dependency JAR changed. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | XSD syntax and set semantics are implemented directly. No upstream source is modified and no Qore verdict is waived. Existing backend compilation limits remain explicit required P3 work, not completion credit. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Per-call strings/lists have automatic ownership. Generation catches only known syntax/backend errors; cancellation and unexpected errors propagate. Sandbox cancellation is cleared on exit and recovery is tested. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Character tables and escape definitions are immutable; parser stacks, counters and candidates are local to each call. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed string/int lists, references and XsdSimpleType casts; heterogeneous JSON worker records are confined to the test boundary. No untyped code callbacks or native casts introduced. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Nested subtraction uses an explicit parent stack and joins output pieces once. The 2000-level test bounds translated size. Sample repetition is bounded before conversion/multiplication and empty atoms do not loop. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Malformed escapes, groups, classes and counts fail at schema construction. Both conversion directions and providers assert precise errors. Empty syntax/value sets, Unicode endpoints, counts and no-pattern examples are covered. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | toPcre documents parameters, return, errors, example and backend limits. Sample API describes bounded candidates accurately. Release notes, durable design, README and normative/oracle evidence are updated; final docs build is clean. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++/QPP changes. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Input lookahead checks bounds; exact count comparison precedes native conversion. No raw buffers, credentials or user-controlled format strings; fixture workers have bounded execution and deterministic temporary cleanup. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Source/AOT pass 12 cases/988 assertions; 62 XML suites pass 722 cases/14495 assertions. The 156-contract matrix and all three new Python methods pass. Full discovery has the same 33 tracked P4/P5/P6 signatures and no errors; both-version corpus results are unchanged. |

All 62 checks are classified, with no failed items remaining. The exact final
comparison is `/tmp/wsdl-p3-18-frozen-python-comparison.json`. P3 acceptance
and all P4-P9 requirements remain open. Main Qore develop is clean at 3e2f47be0.
