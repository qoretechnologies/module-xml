# P3-45 audit: XML-RPC character data

Copyright (C) 2026 Qore Technologies, s.r.o.

The full audit-changes skill and its module structure, sandboxing, cancellation
and DataProvider design references were applied to the exact final XML-RPC
changes. All 62 items are resolved: 25 Pass / 37 N/A / 0 Fail.

Audit and regression review fixed duplicate-member ownership, expanded empty
value/response boundaries, trailing XML validation, invalid XML characters,
legacy encoding-wrapper offsets, and the optional logger path. The native
module was rebuilt in build-debug with prefix /usr and tested through local
module paths without installation. Qore prerequisite 38e8e0e52 and remote XML
merge aec7c38 have their own committed audits.

See [evidence](../xmlrpc-text-evidence.md), the implemented
[contract](../../../design/xmlrpc-character-data.md), and
/tmp/wsdl-p3-45-final-manifest.json for final source/runtime hashes and log paths.
The final docs rebuild produces the same native module hash as the Valgrind runs.
The diagnostic corpus still retains its 144 failures assigned to later phases;
all 1,260 selected directions pass. P3 acceptance and P4-P9 remain pending.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, QPP class, layout, registration, or dependency. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | Native 2.3.0 and XmlRpcHandler release notes describe character data, encodings, empty values and missing-logger faults. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing native XML target and user-module registrations are retained; Debug native and docs-module builds pass. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, QPP class, layout, registration, or dependency. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new module, QPP class, layout, registration, or dependency. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | XmlRpcHandler retains %modern; no redundant directives added. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | Pass | The separated ClientIo source adds no parse directives. |
| 8. No `%include` usage (deprecated for modules) | Pass | No %include introduced. |
| 9. Copyright 2026 on all new files | Pass | Every new test, worker, design, evidence and audit carries 2026 copyright; touched native copyright dates updated. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, QPP class, layout, registration, or dependency. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, QPP class, layout, registration, or dependency. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, QPP class, layout, registration, or dependency. |
| 13. `%modern` directive present | Pass | The new qtest and peer worker use %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | xmlrpc-text.qtest and the Qore peer worker are executable. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Tests prepend local qlib before hard local XmlRpcHandler/ClientIo requirements; runtime paths select the local XML module. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project XML and core dependencies use hard requirements; the external json module is guarded with %try-module. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | Native changes process in-memory XML; no new filesystem or network operation. Existing native HTTPClient policy checks are unchanged. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | Native changes process in-memory XML; no new filesystem or network operation. Existing native HTTPClient policy checks are unchanged. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | Native changes process in-memory XML; no new filesystem or network operation. Existing native HTTPClient policy checks are unchanged. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | New I/O is confined to tests: ephemeral loopback HTTP, explicit listener/control readiness, bounded socket/subprocess deadlines, and managed temporary fixture files. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | Pass | Character scans check cancellation every 100 iterations; collection serialization checks each value; character collection and document completion use cancellation-aware read calls. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | Pass | New checks use qore_check_cancel, including through the reader wrappers; no deprecated interrupt API. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | Pass | Tight loops check at most every 100 iterations; expensive per-value/per-node operations check on every advance. |
| 24. No blocking operations without cancellation support | Pass | No new blocking native operation; HTTP/socket/queue test calls and subprocesses have bounded deadlines and cleanup. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 34. Response/output types use `private` Fields | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 47. No bare field/option names in prose — must use backticks | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No DataProvider action, app, field, factory, or JNI change. ClientIo edits only update existing exception documentation. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Fixes shared text, boundary, ownership and encoding causes. No fixture-specific branch or validation bypass. Existing empty-value and numeric/date contracts are explicit, not newly invented policies. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Character collectors and conversions use ReferenceHolder; serializer buffers have scoped ownership. Duplicate assignments discard replaced values. Eight affected Valgrind runs have zero errors and zero definite/indirect/possible loss. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Reader, serializer and character-validation state is local to the operation. No new mutable shared native state. Test handlers use existing request dispatch and scoped callback state. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Native pointers retain specific Qore node types, sizes use size_t, and character codepoints are unsigned. New Qore callbacks and test collections use explicit types; dynamic protocol values remain auto intentionally. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Character processing is linear with bounded scans and a single final wide-encoding conversion. Character collection appends complete chunks; collection traversal does not rescan earlier members. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Tests cover empty/whitespace values, adjacent nodes, all output flags, four encodings, nested content, malformed/trailing XML, conversion failures, signed bounds, duplicate keys, cancellation, error recovery and logger-free faults. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public function/client exception docs, release notes, README and implemented design describe behavior. Doxygen and the extracted UTF-16 example pass; final documentation rebuild leaves the native binary hash unchanged. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | Pass | Pure generation/parsing functions retain RET_VALUE_ONLY. Existing native client network flags and signatures are unchanged; new reader helpers are internal C++ methods. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | XML character bounds are checked before output; encoding errors propagate. No input-controlled format string, credentials or new raw-buffer arithmetic. Invalid XML cannot return a completed partial value. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 97 affected suites / 998 cases / 38,810 reported assertions pass. Text suite 13/226 and four peer methods pass in all four execution modes. Independent decoding checks 272 generated documents and 34 HTTP value/fault exchanges; diagnostic corpus records are unchanged. |
