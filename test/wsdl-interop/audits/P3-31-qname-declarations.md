# P3-31 audit: QName enumeration declaration identity

Copyright (C) 2026 Qore Technologies, s.r.o.

All 62 audit-changes entries and the referenced module structure, sandboxing,
cooperative cancellation and DataProvider guides were reviewed against the
final changes. Scope is declaration capture/validation, its Qore/Python tests,
implemented design, release notes, current reports and evidence. No XML C++
source or new provider API changes are included.

The mode matrix exposed a separate core JIT defect: recursive StoreClosure
reused its caller's local schema value. It was root-caused, fixed and committed
in Qore develop as `f135ddac7`, with its own complete audit and native/Qore
Valgrind evidence. XML cases retain their original order and JIT stays enabled.
All affected XML gates were rerun against the corrected isolated Debug library.
The pre-existing detached-type namespace lifetime issue is explicitly assigned
to the next P3 increment in the evidence file, before wire/provider integration.

The independent matrix retains the exact Xerces `xmlns:Name` disagreement
in all three declaration models. The XML Infoset definition excludes that
binding; Qore and libxml2 reject the original inputs. The pinned Xerces bytecode
confirms the reserved-prefix lookup defect. No invalid fixture is reclassified
as a valid schema and no test hides the disagreement.

Checklist: **20 Pass / 42 N/A / 0 Fail**. Final tests and source
hashes are recorded in [EXECUTION.md](../EXECUTION.md). No push or installation.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | Existing external single-file module; no new module, separated source or namespace registration. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 release notes document scoped QName enumeration declarations and inherited restrictions. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing WSDL, SoapDataProvider, SoapClient and SoapHandler qmod targets and WSDL Qdx/Doxygen build cleanly; no new registration needed. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | Existing external single-file module; no new module, separated source or namespace registration. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | Existing wsdlintro section remains the first module introduction. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL.qm and the new test use %modern; no redundant directives. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | Existing external single-file module; no new module, separated source or namespace registration. |
| 8. No `%include` usage (deprecated for modules) | Pass | No deprecated %include added. |
| 9. Copyright 2026 on all new files | Pass | All new authored code, tests, evidence and audit files carry 2026 notices. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | Existing external single-file module; no new module, separated source or namespace registration. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | Existing external single-file module; no new module, separated source or namespace registration. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No QPP class or method added or modified. |
| 13. `%modern` directive present | Pass | New Qore suite uses %modern; Python-generated workers retain the existing modern/debug-enabled harness. |
| 14. Executable permission set (`chmod +x`) | Pass | New qtest and Python test are executable. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The qtest prepends local qlib before its relative WSDL requirement; the worker uses the local source and compiled variants explicitly use build-debug qmods. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | XML is this repository's binary module and QUnit is supplied by Qore. Existing independent worker guards its external json dependency. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ change in this XML increment. Qore statement/loop cancellation remains active and is tested; the dependency core fix has its own complete audit. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ change in this XML increment. Qore statement/loop cancellation remains active and is tested; the dependency core fix has its own complete audit. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ change in this XML increment. Qore statement/loop cancellation remains active and is tested; the dependency core fix has its own complete audit. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | No production I/O added. Tests use offline cached includes, bounded workers and deterministic queue barriers. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ change in this XML increment. Qore statement/loop cancellation remains active and is tested; the dependency core fix has its own complete audit. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ change in this XML increment. Qore statement/loop cancellation remains active and is tested; the dependency core fix has its own complete audit. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ change in this XML increment. Qore statement/loop cancellation remains active and is tested; the dependency core fix has its own complete audit. |
| 24. No blocking operations without cancellation support | N/A | No C++ change in this XML increment. Qore statement/loop cancellation remains active and is tested; the dependency core fix has its own complete audit. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 34. Response/output types use `private` Fields | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 47. No bare field/option names in prose — must use backticks | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No provider action/app, request/response field catalog, factory registration, credential or JAR change. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Complete declaration checks at active scope capture and resolved base validation; no fixture exceptions in production, tolerance, speculative metadata fallback or placeholder. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Transient literal capture is removed on every finalization exit. Validated identity index is published only after all inherited checks pass. Failed additions roll back and cancellation propagates. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Construction state belongs to each schema/type; completed indexes are read only. Concurrent independent copies pass, and the existing contract requires adding documents before sharing a schema. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed XsdQNameDeclarationLiteral hashdecl, optional URI, typed reference output, and nested namespace/local boolean indexes. Heterogeneous XML input retains its established hash representation. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Each literal retains one URI rather than the entire namespace map. Namespace/local indexes avoid delimiter encoding and linear enumeration searches; work is proportional to literals times inheritance depth. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Tests assert XSD-SIMPLETYPE-ERROR for invalid grammar, unbound prefixes and invalid inherited restrictions; forward/inline, rollback, duplicate, default, large and non-QName cases pass. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Implemented value design, README, release notes and independent evidence explain declarations, pattern inheritance, reconstruction and remaining ordinary wire/provider work. No new public API. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP class or method added or modified. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Fixed format strings, exact namespace keys, no credentials or new resource access. Original corpus, pinned validator JAR and generated source hashes remain unchanged. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 79 suites/853 cases/31947 assertions, 248 mode/zone cases/5816 assertions, 31 compiled cases/727 assertions and the 396-contract independent declaration matrix pass. The full Python gate retains exactly two known P6 failures; complete corpus differences are only WSDL source hash. |
