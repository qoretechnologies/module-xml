# P3-10 audit: union provider validation and traversal

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: union provider conversion, requiredness, reconstruction, per-call shared
graph caches, cancellation, native scalar error translation, Qore/Python
regressions, reports and documentation. No C++ or core Qore edit belongs to this
increment. The core develop checkout was independently observed clean at d70ed3718.

The audit-changes skill was reread before this commit. Its module structure,
sandboxing, cooperative cancellation, DataProvider checklist and actual
data-provider-development-guide.md references were reviewed for applicability.
All 62 checklist items are recorded below.

Audit corrections: shared graph traversal now uses per-call caches; context
objects avoid growing-map copies. NaN/nested collections, signed zeros, number
precision and date timezone spelling retain correct reentrant input identity.
The corpus review exposed raw date parser rejection escaping union trials; date
and binary converters now translate only native input rejection to the directional
SOAP category. The initial eight date/string regressions are eliminated.

Verification: 44 affected Qore suites pass 557 cases; the focused suite passes
11 cases/197 assertions. Qdx/Doxygen is clean. Final Python discovery runs 115 tests
with exactly seven unchanged P4/P5/P6 failures and no new failures, errors, skips
or warnings. Logs: /tmp/wsdl-p3-10-audited-*. No C++ changed.

Strict coverage remains 89 descriptions/756 directions, 664 successful value
checks and no selected/failed/missing value cases. All 220 broad failures, counts,
source hashes and corpus verdicts are unchanged. Existing five-digit date failure
diagnostics now use SOAP-DESERIALIZATION-ERROR; their failures remain visible.
Final WSDL SHA-256: 42cac931187e15f537d92ecea08e9dd291ff13f6ff27a756d627088a63910967.

All items are Pass or N/A. Separate union lexical/value semantics and date parser
findings are explicitly routed in union-providers-evidence.md and EXECUTION.md;
P3 and P4-P9 remain required.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | Existing single-file external WSDL module; no new module, separated file or layout change. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 release notes describe requiredness, repeated-list validation, cancellation, bounded shared traversal and native parser error translation. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing qore_external_user_module registration builds and documents the local WSDL module; Qdx/Doxygen completes cleanly. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | Existing single-file external WSDL module; no new module, separated file or layout change. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | wsdlintro remains the first documentation section. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL uses %modern; no redundant directives or %include were introduced. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | Existing single-file external WSDL module; no new module, separated file or layout change. |
| 8. No `%include` usage (deprecated for modules) | Pass | WSDL uses %modern; no redundant directives or %include were introduced. |
| 9. Copyright 2026 on all new files | Pass | New Qore/Python/evidence/audit files carry 2026 notices; WSDL and the scalar design retain their 2026 notices. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | Existing single-file external WSDL module; no new module, separated file or layout change. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | Existing single-file external WSDL module; no new module, separated file or layout change. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No C++, QPP, native I/O or native loop changes; no new Valgrind run applies. |
| 13. `%modern` directive present | Pass | The new union suite and reused consumer worker use %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | test/wsdl-union-providers.qtest has executable mode 0755. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The union suite prepends local qlib before requiring ../qlib/WSDL.qm; the reused consumer retains its relative requirement. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | QUnit and same-repository xml/WSDL are hard requirements; the reused consumer guards its external json dependency with %try-module. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++, QPP, native I/O or native loop changes; no new Valgrind run applies. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++, QPP, native I/O or native loop changes; no new Valgrind run applies. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++, QPP, native I/O or native loop changes; no new Valgrind run applies. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production changes operate on in-memory values. The offline Python matrices reuse bounded temporary manifests and existing subprocess deadlines; no new production I/O. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++, QPP, native I/O or native loop changes; no new Valgrind run applies. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++, QPP, native I/O or native loop changes; no new Valgrind run applies. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++, QPP, native I/O or native loop changes; no new Valgrind run applies. |
| 24. No blocking operations without cancellation support | N/A | No C++, QPP, native I/O or native loop changes; no new Valgrind run applies. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | Pass | Dynamic hash access intentionally retrieves scalar/cache entries; no single-key slice is mistaken for a record. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 34. Response/output types use `private` Fields | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No finite field-choice metadata is introduced or changed; existing member restrictions remain active and are tested through reconstruction. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 47. No bare field/option names in prose — must use backticks | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No app/action, request/response record, factory, connection or credential change; this is scalar union provider traversal. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No JNI module, new JAR or Java change; the existing pinned Xerces oracle is reused. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No JNI module, new JAR or Java change; the existing pinned Xerces oracle is reused. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | The change fixes union provider requiredness, per-item validation and traversal generically. Native parse rejection is translated at the converter. No production fixture special case, workaround, TODO or stub. Remaining P3 scalar/union findings and P4-P9 remain explicitly required. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Qore owns strong member references and typed contexts. Reconstruction resolves/validates metadata before publication. on_exit removes active entries and restores caller contexts after success, rejection or cancellation; controlled failures and recovery are tested. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Traversal caches are thread-local and live only for one operation. Public members are documented as configured before concurrent use and stable during validation. Optional variants copy the provider; normal acceptance does not mutate member metadata. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed member lists, XsdUnionTrialResult, context classes and typed maps represent results. Reconstruction validates nonempty provider lists and actual boolean optionality. Helpers validate native type codes before precision/list/hash operations; no new untyped callbacks or C casts. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Per-call memoization bounds shared union trials and metadata traversal by graph edges and input comparisons. Context objects avoid growing-map copy-on-write clones. A 28-level shared graph asserts one terminal visit per operation, including rejected NaN inputs in nested collections; cycles reject explicitly. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Tests cover empty/malformed metadata, legacy restoration, omitted and optional values, nested lists, member restrictions, ordered conversion, cycles, NaN, signed zero, number precision, timezone spelling, cancellation and retry cleanup. Native date/binary rejections use directional SOAP errors; unrelated errors propagate. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Changed public conversion/provider APIs document parameters, returns and errors. The class has a realistic example and concurrent-use caveat. Release notes, durable scalar design, README and evidence explain behavior and remaining criteria; Qdx/Doxygen is clean. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++, QPP, native I/O or native loop changes; no new Valgrind run applies. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Literal format strings, size/key checks before collection access, typed metadata validation and explicit cycle rejection. The existing offline oracle resolver is unchanged; no credentials or native memory operations added. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 11 focused cases/197 assertions and all 44 affected suites/557 cases pass. The independent matrix validates 2580 documents and 2784 consumer rows, including exact values, primitive families, item order, expanded names and both real SOAP versions/directions. Strict coverage and all previous failure identities/counts are unchanged; final full Python has exactly seven known later-phase failures. |
