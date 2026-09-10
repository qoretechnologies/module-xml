# Remote develop integration audit: anyAttribute scalar values

Copyright (C) 2026 Qore Technologies, s.r.o.

Merged origin/develop c1403ef after fetching the requested remote fix. The full
audit-changes skill and its module structure, sandboxing, cancellation and
DataProvider references were applied to the final merge changes. All 62 checks
are listed: 19 Pass, 43 N/A, 0 Fail.

The remote change fixes runtime hash narrowing that discarded or rejected
attributes when wrapping scalar content. Its positive test originally declared
an element-only complex type, which conflicts with the local P3 text-validation
rule. The positive fixture now declares mixed=true. A separate element-only
attribute-wildcard fixture retains negative coverage in both directions;
serialization now applies the same XML-whitespace rule as deserialization.
The upstream widening and its string/non-string attribute assertions are retained.
These are authored test fixtures, not modifications to the pinned W3C corpus.

Evidence: /tmp/wsdl-p3-45-merge-features-native-validation.log,
/tmp/wsdl-p3-45-full-gate-reviewed.log, /tmp/wsdl-p3-45-survey-final.json and
/tmp/wsdl-p3-45-coverage-final.json. The ongoing XML-RPC native work is not part
of this merge commit; the affected full-suite run uses that local module build
and the separately committed Qore HTTP encoding prerequisite 38e8e0e52.
The two existing P6 binding-version tests remain diagnostic failures.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, class, layout, registration, or dependency. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 notes document retained mixed-content attributes and matching element-only output checks. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing WSDL external module registration is unchanged; module documentation builds. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, class, layout, registration, or dependency. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new module, class, layout, registration, or dependency. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | Existing module and updated suite use %modern. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, class, layout, registration, or dependency. |
| 8. No `%include` usage (deprecated for modules) | Pass | No %include introduced. |
| 9. Copyright 2026 on all new files | Pass | Updated tests and new audit carry copyright 2026; WSDL already has 2026 copyright. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, class, layout, registration, or dependency. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, class, layout, registration, or dependency. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, class, layout, registration, or dependency. |
| 13. `%modern` directive present | Pass | soap-features.qtest uses %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | The updated qtest retains executable permissions. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The suite prepends ../qlib and requires local WSDL and SoapHandler files. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project XML and core QUnit/Mime dependencies retain hard requirements. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | This merge changes Qore schema code and tests only; no native I/O changes. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | This merge changes Qore schema code and tests only; no native I/O changes. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | This merge changes Qore schema code and tests only; no native I/O changes. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Added tests are offline; existing suite integration uses its existing bounded test setup. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ loop or blocking operation changes; Qore VM cancellation applies. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ loop or blocking operation changes; Qore VM cancellation applies. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ loop or blocking operation changes; Qore VM cancellation applies. |
| 24. No blocking operations without cancellation support | N/A | No C++ loop or blocking operation changes; Qore VM cancellation applies. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No provider action, app, field, factory, or JNI change. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No provider action, app, field, factory, or JNI change. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No provider action, app, field, factory, or JNI change. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No provider action, app, field, factory, or JNI change. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No provider action, app, field, factory, or JNI change. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No provider action, app, field, factory, or JNI change. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No provider action, app, field, factory, or JNI change. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No provider action, app, field, factory, or JNI change. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No provider action, app, field, factory, or JNI change. |
| 34. Response/output types use `private` Fields | N/A | No provider action, app, field, factory, or JNI change. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No provider action, app, field, factory, or JNI change. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No provider action, app, field, factory, or JNI change. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No provider action, app, field, factory, or JNI change. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No provider action, app, field, factory, or JNI change. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No provider action, app, field, factory, or JNI change. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No provider action, app, field, factory, or JNI change. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No provider action, app, field, factory, or JNI change. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No provider action, app, field, factory, or JNI change. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No provider action, app, field, factory, or JNI change. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No provider action, app, field, factory, or JNI change. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No provider action, app, field, factory, or JNI change. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No provider action, app, field, factory, or JNI change. |
| 47. No bare field/option names in prose — must use backticks | N/A | No provider action, app, field, factory, or JNI change. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No provider action, app, field, factory, or JNI change. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No provider action, app, field, factory, or JNI change. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No provider action, app, field, factory, or JNI change. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No provider action, app, field, factory, or JNI change. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No provider action, app, field, factory, or JNI change. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | The upstream hash widening is retained. Positive scalar fixtures declare mixed content; attribute wildcards do not bypass element-only text validation. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Only managed Qore values change; elementContent checks a local copy before serialization. Rejection preserves caller data. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | No shared state added; schema instances retain existing immutable metadata and local serialization values. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | The helper adds a typed string error-category argument. Existing typed hashes and checked complex-type casts are retained. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | The existing linear text-fragment helper is shared with serialization; no new search or unbounded candidate generation. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Both directions reject non-whitespace scalar/text/CDATA for element-only types, including an attribute wildcard. XML formatting whitespace and valid mixed scalars pass. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Release notes and test comments distinguish mixed content from attribute wildcards. Seven independent native XSD assertions verify the authored test declarations and output. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP method changes in the merge. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No new I/O, credentials, input-controlled formatting, or raw memory operations. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | soap-features passes 55 cases / 213 assertions, including seven native XSD assertions. The 2,411 survey rows and all 144 diagnostic failure identities are unchanged; strict coverage remains 130 WSDLs / 1,260 directions with zero selected failures. |
