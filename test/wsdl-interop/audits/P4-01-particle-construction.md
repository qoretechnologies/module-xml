# P4-01 audit: ordered particles and native occurrence values

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied the complete audit-changes skill to the final changes, including its
module structure, sandboxing and cooperative-cancellation design references.
All 62 checks are individually resolved: 21 Pass / 41 N/A / 0 Fail.

Review corrected the remaining SOAP array construction path, added exact count
and Serializable validation, preserved default occurrence compatibility, strengthened
worker completeness/error diagnostics, and fixed missing source-distribution inputs.
The final tests include both native APIs, independent schema validators, reconstruction,
all four Qore execution modes and affected existing clients/providers.

See [validation inventory](../P4-01-validation.json),
[independent evidence](../particle-counts-evidence.md), and
[execution record](../EXECUTION.md) for runtime hashes, counts and remaining criteria.
The native C fallback retains its pre-existing integer counter capacity; the new
WSDL declaration model stores exact strings. The standalone dependency's scan has
no Qore runtime dependency or new mid-attribute cancellation callback.

The full documentation target has 22 independent diagnostics recorded under P9;
affected WSDL/native targets pass without warnings. Known P4/P5/P6 compatibility
failures remain visible, including the four nested-choice diagnostics. No new
production regression is accepted as a pass, and P4 acceptance is not claimed.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, QPP class, module layout, registration or binary dependency. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 and native XML 2.3.0 release notes describe the implemented metadata and occurrence corrections. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing module targets are retained; local Debug native, runtime probe and affected documentation targets build successfully. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, QPP class, module layout, registration or binary dependency. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new module, QPP class, module layout, registration or binary dependency. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL retains %modern; no redundant parse directives introduced. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated .qc source changed. |
| 8. No `%include` usage (deprecated for modules) | Pass | No deprecated %include introduced. |
| 9. Copyright 2026 on all new files | Pass | All new source, tests, design, evidence, diagnostic and audit files carry 2026 copyright; upstream notices and source bytes are preserved. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, QPP class, module layout, registration or binary dependency. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, QPP class, module layout, registration or binary dependency. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, QPP class, module layout, registration or binary dependency. |
| 13. `%modern` directive present | Pass | Both qtests and both Qore workers use %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | Both qtests and both Qore workers have executable mode 755. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Local qlib is prepended before requirements; WSDL requirements are relative; QORE_MODULE_DIR selects the local Debug XML module. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project XML and core modules use hard requirements; both JSON workers guard the external json module with %try-module. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | Native changes are standalone libxml2 C parsing and CMake probes, with no new runtime filesystem operation. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No new native network operation. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No added filesystem/network capability; existing schema-load sandbox boundaries remain unchanged. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | New file reads are limited to explicit test manifests. Production source conversion is in memory and adds no I/O. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No Qore C++ loop changed. Standalone libxml2 C scans one XML attribute linearly without a Qore dependency; the construction loops use Qore cancellation points. The native design records cancellation boundaries and long-input tests. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | Pass | No deprecated interrupt API added; existing schema-entry/read qore_check_cancel boundaries remain active and interruption/reuse tests pass. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No Qore C++ polling loop added. Standalone libxml2 has no Qore cancellation callback inside an attribute; this boundary is documented explicitly. |
| 24. No blocking operations without cancellation support | Pass | No new blocking production operation. Test workers have bounded subprocess deadlines; no sleep or polling was added. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 34. Response/output types use `private` Fields | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 47. No bare field/option names in prose — must use backticks | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No DataProvider action/app/type registration, FactoryMap, JNI or JAR installation change. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Root causes are ordered-source regrouping, duplicate declaration construction, occurrence lexical scanners and zero-particle admission. This increment fully implements construction metadata and native corrections; existing P4 runtime failures remain failing diagnostics under the authorized incremental plan. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Qore construction uses scoped namespace/finalization restoration and managed references. Native lexical parsing allocates nothing; zero-count declarations remain owned by the schema arena. Probe, occurrence and existing reader Valgrind runs report zero errors and zero definite/indirect/possible leaks without suppressions. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Native scan state is local. Particle resolution is documented as construction-time mutation before thread sharing; returned children are copy-on-write. No global mutable cache introduced. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Particle kinds use an enum, declaration/visit records use typed hashdecls, and children/elements/groups have explicit object types. Decimal strings retain exact counts. C casts are confined to standalone C dependency/probe code. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | The source adapter appends directly without accumulated-list copies. Particle storage scales with declaration positions and references, without count expansion. Group definitions are shared; iterative traversal avoids repeated element construction. Tests cover 1,000 positions, 80 nested groups and 81-digit compositor counts. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Tests cover malformed terms/counts, reversed ranges, empty groups, all restrictions, missing/unknown/cyclic references, imports, reconstruction errors and interruption/recovery. Native schema and document errors retain distinct expected categories. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | New public APIs have parameter/return/error documentation and an executed invoice example. Implemented model/native design, release notes, README and independent evidence are present. Affected Doxygen targets are warning-free; 22 unrelated full-doc diagnostics are explicitly assigned to P9 without suppressions. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP method or functional-domain flag changed. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Native decimal accumulation checks overflow before multiplication. Probe buffers check snprintf bounds. No credentials, untrusted format string or new I/O capability. Serialized model members are type/range checked. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 101 affected Qore suites pass: 1,020 cases and 43,196 reported assertions. Four execution modes pass the new and affected context suites and both independent matrices. The 880 native rows and 80 model rows retain specification-based values and exact validator disagreements. All 2,411 baseline survey rows and 144 coverage failure records are unchanged; all 1,260 strict directions pass. |
