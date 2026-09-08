# Qore map result and optional type audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Full 62-item skill checklist for four runtime files, three regression files, release notes and the implemented design. Reviewed against the module structure, sandboxing, cooperative cancellation, and DataProvider checklist/development guides; no DataProvider registration changes apply.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, separated module source or QPP class. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | Qore 3.0 release notes describe map result inference and optional folding. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module, separated module source or QPP class. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, separated module source or QPP class. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new module, separated module source or QPP class. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No new module, separated module source or QPP class. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, separated module source or QPP class. |
| 8. No `%include` usage (deprecated for modules) | N/A | No new module, separated module source or QPP class. |
| 9. Copyright 2026 on all new files | Pass | All four new files carry 2026 copyright; the changed IR source now carries it too. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, separated module source or QPP class. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, separated module source or QPP class. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, separated module source or QPP class. |
| 13. `%modern` directive present | Pass | Both Qore regression files declare %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | OptionalMapTypeFolding.qtest is executable (0755); the .qr fixture is data read by the runner. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Local qlib path precedes relative QUnit.qm and FsUtil.qm requirements. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Only repository-owned QUnit/FsUtil dependencies; native fixture uses the matching local Qore library. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | Pass | Runtime edits add no filesystem calls; native test compilation uses the existing build and a temporary output. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | Pass | No network operations in the changes. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No runtime filesystem or network operations introduced. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | The test writes fixtures and compiler output in TmpDir, closes File with on_exit, and reads companion fixtures. Necessary local test setup only. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | Pass | Shared native map checks cancellation at each 100 items; bounded native setup loop uses the same cadence. The interpreter delegates to this loop. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | Pass | Only qore_check_cancel is used; no deprecated interrupt checks added. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | Pass | Every 100 iterations in the tight native loops. |
| 24. No blocking operations without cancellation support | Pass | No blocking runtime operations added. Tests use synchronous compiler/child process completion. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 34. Response/output types use `private` Fields | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 47. No bare field/option names in prose — must use backticks | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No DataProvider actions, types, app metadata, factories or JAR dependencies changed. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Fixes map result inference and the two common-type folding root causes; no XML coercion workaround, stub or fixture special case. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | ReferenceHolder owns input and partial native output; accessor and checked append errors are checked; interpreter retains exception routing and cleanup. Native cancellation and invalid-member paths tested under Valgrind. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Result/type state is per invocation; the existing immutable append-mode switch and synchronized type caches are reused. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Runtime type metadata follows actual values and preserves optional hashdecls; incompatible values stop narrowing. Tests use typed hashdecls/lists and typed method dispatch. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | One incremental pass, no second map or copied input; removes duplicated IR interpreter loop. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Empty and missing values, heterogeneous types, unrelated declarations, invalid member after a valid item, cancellation and recovery are covered. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Internal helper documents arguments, ownership, result and exception sink; durable design includes a typed identity example; release notes updated. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP methods added or changed. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No credentials, user-controlled format strings or raw buffer indexing; native ABI memcpy uses a size assertion; list access is bounded. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | AST/IR/JIT and source-stripped AOT agree for optional hash/int/list values, iterator/map-select, empty input, repeated NOTHING, both operand orders and negative inputs. Both native append paths tested. |

Validation evidence (2026-09-08):

- Debug runtime build uses `/usr` prefix and local `LD_LIBRARY_PATH`; no installation. Native library SHA-256: `67f2c22aaaac71cec3a75b19b5417e0231d6d999fca55125fe36c87bd29057df`. Final subsequent source differences are comments only.
- New regression: three cases, 28 assertions; AST, IR, JIT, source-stripped AOT, both append paths and native deterministic cancellation. `/tmp/wsdl-p3-15-core-unit-complete.log`; repeated from the main checkout in `/tmp/wsdl-p3-15-main-core-unit.log`.
- Eleven affected existing core suites passed, including hashdecl propagation, specialized map access, optional AOT dispatch and soft types: `/tmp/wsdl-p3-15-core-regressions-final.log`.
- Native map fixture and XML AOT integration: Valgrind reports zero errors, zero definite/indirect/possible loss, no suppressions. `/tmp/wsdl-p3-15-core-valgrind.log`, `/tmp/wsdl-p3-15-aot-valgrind.log`; deterministic native cancellation in `/tmp/wsdl-p3-15-cancel-valgrind.log`. The known DWARF `DW_AT_abstract_origin` reader warning remains separately tracked for P9; it is not a memory error.
- Final runtime passes all 59 affected XML suites (691 cases, 12497 recorded assertions), compiled union-list integration (11 cases, 251 assertions), and unchanged both-version survey/strict coverage (zero selected failures). `/tmp/wsdl-p3-15-core-final-*` and `/tmp/wsdl-p3-15-aot-items-final.log`.

All 62 items are classified; no failed audit items remain. Only the nine named, tested files are eligible for the Qore commit.

Committed in Qore `develop` as `3e2f47be0`; main checkout clean afterward. No push.
