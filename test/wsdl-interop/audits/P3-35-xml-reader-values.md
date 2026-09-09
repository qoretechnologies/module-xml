# P3-35 audit: native reader cursor values

Copyright (C) 2026 Qore Technologies, s.r.o.

The full audit-changes skill and its applicable module-structure, sandboxing and
cooperative-cancellation guides were applied to the exact C++/QPP changes,
Qore/Python regressions, implemented design, examples and release notes.
DataProvider registration checks were individually assessed as not applicable.

Checklist: **25 Pass / 37 N/A / 0 Fail**. The review corrected the cursor
methods' side-effect flags and added an immediate exception check after reading;
final affected checks were rerun. Verification and exact hashes are recorded in
[EXECUTION.md](../EXECUTION.md). No WSDL source or Qore core change is included.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | Existing external binary module; no Qore module index entry. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | Native 2.3.0 release notes describe safe scalar/empty cursor values, sibling boundaries and preserved side effects. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing xml and docs-module targets build against the frozen Debug core with /usr prefix, without warnings/errors. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No user module or QMOD entry added. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No .qm file is changed. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No .qm file is changed. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated .qc file is added or changed. |
| 8. No `%include` usage (deprecated for modules) | Pass | No deprecated %include usage is introduced. |
| 9. Copyright 2026 on all new files | Pass | Authored native files, new qtest, implemented design, evidence and audit carry 2026 notices. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No module layout change. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module file. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No QPP class change. |
| 13. `%modern` directive present | Pass | New qtest, updated fixture driver and executed examples use %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | xml-reader-values.qtest and the updated diagnostic are executable. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The qtest prepends repository qlib; same-repository xml loads from build-debug via QORE_MODULE_DIR. The diagnostic has no in-repo user-module requirement. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | xml is supplied by this repository, QUnit by Qore; the diagnostic guards the external json binary with %try-module and an explicit missing-module error. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | Pass | No filesystem operation is added to production. The generic helper reuses the existing reader and its checked stream I/O. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | Pass | No network operation or resource resolution is added. Test streams supply in-memory documents. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | The production patch adds no filesystem/network operation requiring a sandbox helper. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | The updated diagnostic reads its explicitly named fixture with ReadOnlyFile. Other new Qore tests use in-memory streams and deterministic interruption. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | Pass | The new helper adds no loop and reuses getXmlData/read, which check cancellation during iteration. Existing XML stack finish/depth loops check every 100 iterations. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | Pass | The empty-element fast path calls qore_check_cancel; other paths call the existing cancel-aware read method. No deprecated interruption API. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | Pass | Existing per-read cancellation and XML-stack checks are retained; tests interrupt after conversion has entered a record and allocated partial values. |
| 24. No blocking operations without cancellation support | Pass | Existing stream operations remain cancel-aware. Tests use armed stream callbacks and bounded processes, with no sleeps or polling loops. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 34. Response/output types use `private` Fields | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 47. No bare field/option names in prose — must use backticks | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No DataProvider action, app, catalog, type, field, factory or dependency JAR changes. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | An owned QoreValue helper implements the documented scalar/empty contract and containing-element boundary. No unchecked cast, assertion removal on document APIs, input rewriting, stub or workaround. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | ValueHolder owns completed values until the exception check succeeds; the XML stack owns partial values. Tests preserve original stream exceptions and release interrupted state. Final Valgrind has zero errors and zero definite/indirect/possible loss. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | New state consists only of per-call scalar locals and a value holder; no shared mutable state is introduced. Cursor mutation uses the existing per-reader state. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | The cursor path returns QoreValue while document parsing retains QoreHashNode*. No scalar-to-hash cast is introduced. Tests use typed stream overrides, callbacks and ExceptionInfo catches. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | The helper adds constant-time state checks and ownership transfer without copying completed values or changing traversal complexity. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | The helper checks the read result and pending exception before conversion. Tests cover malformed XML, schema rejection, partial stream errors, interruption, empty/EOF behavior and later recovery. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Both touched QPP methods have parameter/return/throw documentation and cursor-boundary notes. The implemented design and executed scalar-label example document return values, grouping and cursor position. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | Pass | RET_VALUE_ONLY is removed from both cursor-mutating methods. Discarded-result tests verify cursor advancement in AST/IR/JIT/tiered modes without warnings. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No new external resource access, credentials or user-controlled native format strings. Containing-depth checks prevent consuming sibling data; C++ ownership and original exception propagation are tested. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | The saved exact baseline aborts on a scalar value. Final tests verify exact scalar/empty results and cursor boundaries; pinned Xerces independently assesses all 300 native cursor schema cases. Full regression, mode matrix, corpus comparison and Valgrind evidence are in EXECUTION.md. |
