# P3-43 audit: native sample instances

Copyright (C) 2026 Qore Technologies, s.r.o.

The full audit-changes skill and its module-structure, sandboxing, cancellation,
DataProvider checklist and development guides were applied to the final changes.
All 62 checks are resolved: **19 Pass / 43 N/A / 0 Fail**.

Review fixed nested subclass dispatch and the unknown-message diagnostic.
Exception/cancellation recovery, thread isolation and callback-count regressions
pass. The final documentation-only edit was followed by new-suite, example,
Doxygen and report checks. See [verification evidence](../sample-instances-evidence.md)
and `/tmp/wsdl-p3-43-final-manifest.json` for exact tested artifacts.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, separated source, QPP class, layout or module registration. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 release notes describe native sample validation and the explanatory choices contract. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing WSDL external registration is unchanged; final docs-module build succeeds without warnings/errors. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, separated source, QPP class, layout or module registration. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new module, separated source, QPP class, layout or module registration. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | Existing WSDL and the new qtest use %modern; no redundant directives added. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, separated source, QPP class, layout or module registration. |
| 8. No `%include` usage (deprecated for modules) | Pass | No %include directive introduced. |
| 9. Copyright 2026 on all new files | Pass | New test, design, evidence and audit have 2026 notices; WSDL already includes 2026. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, separated source, QPP class, layout or module registration. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, separated source, QPP class, layout or module registration. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, separated source, QPP class, layout or module registration. |
| 13. `%modern` directive present | Pass | The new qtest uses %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | test/wsdl-sample-instances.qtest is executable. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The test prepends ../qlib and requires ../qlib/WSDL.qm; the recorded environment selects local xml and frozen core dependencies. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project xml and core QUnit use hard requirements; no new optional external binary dependency introduced. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++/QPP, native I/O, loop or method flags changed. Native xml hash is unchanged; no new Valgrind run required. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++/QPP, native I/O, loop or method flags changed. Native xml hash is unchanged; no new Valgrind run required. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++/QPP, native I/O, loop or method flags changed. Native xml hash is unchanged; no new Valgrind run required. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | No production I/O added. Embedded offline WSDLs and bounded Queue/Counter barriers are used in tests. The example reads a caller-supplied local WSDL. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++/QPP, native I/O, loop or method flags changed. Native xml hash is unchanged; no new Valgrind run required. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++/QPP, native I/O, loop or method flags changed. Native xml hash is unchanged; no new Valgrind run required. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++/QPP, native I/O, loop or method flags changed. Native xml hash is unchanged; no new Valgrind run required. |
| 24. No blocking operations without cancellation support | N/A | No C++/QPP, native I/O, loop or method flags changed. Native xml hash is unchanged; no new Valgrind run required. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 34. Response/output types use `private` Fields | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 47. No bare field/option names in prose — must use backticks | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No DataProvider action, field, app, factory, metadata, description or JNI dependency changed in this increment. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Candidate validation reuses schema instance conversion. Bounded generation errors are explicitly allowed by P3. Choices retains its documented explanatory shape; retained XML still validates. No fixture conditional or workaround. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | on_exit restores child context even when a subclass throws before base entry. Private namespaces and output scopes unwind on failure; controlled errors, actual interruption and recovery pass. No partial multipart result is returned. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Child context is thread-local. Four simultaneously pending child calls assert unique worker results and exactly one serialization per thread. Shared schema is unchanged. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Concrete helper/element/context types, typed exception hashes and code<nothing()> callbacks; existing public auto value contract retained. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | One schema traversal per root; exactly three callbacks for three repeated leaves and one per concurrent root. Child context allocation is constant per call and avoids repeated subtree validation. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Schema rejection maps to XSD-SAMPLE-ERROR; callback/cancellation errors propagate. Tests assert error categories and ENTITY reason. Unknown-name diagnostic now identifies both requested and known names. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public changed methods document parameters, return values, errors and choices. Class @par Example and durable catalog example execute successfully; README, release notes and design explain bounded generation. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++/QPP, native I/O, loop or method flags changed. Native xml hash is unchanged; no new Valgrind run required. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No production I/O, raw buffer, credential or user-controlled format string added. choices never disables retained XML checks. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 94 suites/966 cases/36,510 reported assertions pass; new suite 9/138 in all modes. Independent ENTITY/QName matrices and unchanged complete reports verify preserved values. Exactly two known P6 failures remain reported; no skips added. |
