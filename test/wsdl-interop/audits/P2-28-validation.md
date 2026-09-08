# P2-28 final audit: schema reference and declaration validation

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: P2-16 through P2-19 construction fixes isolated together on parent
8b8c3d1. WSDL source, four new Qore/Python suites and three workers, three
Qore-authored encoding-import fixtures, release notes and design documentation.
The full audit-changes checklist and its referenced core design guides apply.
No native/consumer/carrier/WebContentUtil/other-repository changes are included.

Root causes: source permission was conflated with globally loaded components;
field maps lost conflicting declarations before resolution; anyAttribute's
boolean discarded namespace and processing constraints; element constructors
accepted contradictory context/type properties and missed resolved ID constraints.
The fixes retain and validate these properties during schema construction.

Requirements: XSD 1.0 [src-resolve](https://www.w3.org/TR/xmlschema-1/#src-resolve),
[src-import](https://www.w3.org/TR/xmlschema-1/#src-import),
[element consistency](https://www.w3.org/TR/xmlschema-1/#cos-element-consistent),
[wildcard subset](https://www.w3.org/TR/xmlschema-1/#cos-ns-subset),
[element declarations](https://www.w3.org/TR/xmlschema-1/#src-element), and
[complex type properties](https://www.w3.org/TR/xmlschema-1/#ct-props-correct).
Independent matrices explicitly assert libxml2/Xerces disagreements against those
requirements; no validator disagreement is skipped or converted into a pass.
General instance particles, wildcard processing and ID/reference binding remain
assigned to P4/P5; this increment implements schema construction constraints.

Validation: /tmp/wsdl-p2-28-{affected,references,elements,wildcards,declarations,survey,docs}.log.
All 403 affected Qore cases and eight new independent tests pass without warnings
or errors. The full 293-description/1136-message both-version survey has identical
counts and classifications. SOAPEncodedArray, already invalid, now reports its
unimported WSDL-namespace QName earlier with the same WSDL-ERROR category. Every
other row is identical apart from versions; the complete report matches the
historical P2-19 report excluding versions. No C++ change/Valgrind requirement.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 notes describe import permissions, declaration consistency, wildcard construction, declaration properties and ID constraints. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL remains %modern with no redundant parse directives. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 8. No `%include` usage (deprecated for modules) | Pass | No %include or separated source layout introduced. |
| 9. Copyright 2026 on all new files | Pass | New test/worker/audit files and all modified authored fixtures carry 2026 notices; upstream corpus bytes are unchanged. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 13. `%modern` directive present | Pass | All updated/new Qore tests and QR workers use %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | All qtests and QR workers are executable; Python regressions use python3. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Qtests/workers prepend local qlib and require WSDL relatively. Existing soap-features test retains its relative repository dependency. Candidate qlib and committed native Debug module are selected explicitly. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | xml/WSDL are hard repository dependencies; optional QR json dependencies use %try-module. QUnit remains the required framework. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No native change; Qore loops use runtime cancellation. No new blocking production operation. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No native change; Qore loops use runtime cancellation. No new blocking production operation. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No native change; Qore loops use runtime cancellation. No new blocking production operation. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Only construction logic changed in production. Test imports resolve from in-memory/offline maps or temporary files; the three authored SOAP fixtures now declare required encoding imports. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No native change; Qore loops use runtime cancellation. No new blocking production operation. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No native change; Qore loops use runtime cancellation. No new blocking production operation. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No native change; Qore loops use runtime cancellation. No new blocking production operation. |
| 24. No blocking operations without cancellation support | N/A | No native change; Qore loops use runtime cancellation. No new blocking production operation. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 34. Response/output types use `private` Fields | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 47. No bare field/option names in prose — must use backticks | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Checks source-local permission and retained identities before maps lose information. Wildcard metadata implements the XSD 1.0 algebra and preserves non-expressible errors. No fixture-name branch, suppression or passing classification for later-phase failures. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Permission and declaration-presence scopes restore on_exit. Checks run before final maps are published; group/type guards restore on errors. ID ancestry follows resolved objects without an expired borrowed namespace. Failure recovery and detached/reconstructed schemas pass. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Metadata completes during schema construction; getters return managed copy-on-write hash views. No mutable process-global state or new runtime cache. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Public wildcard enums and XsdAttributeWildcardInfo represent constraint/processing choices. Typed identity maps and constrained-element lists retain resolved objects; boolean declarations validate all XSD lexical spellings. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Element consistency indexes each expanded identity; completed group maps/cache prevent exponential shared-reference traversal. Import-cache keys distinguish namespace presence, avoiding invalid permission reuse. ID traversal detects revisits. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Wrong/unimported QNames, contradictory/empty declarations, conflicting types, impossible wildcard combinations, weaker restrictions, ID value constraints and multiple ID uses fail with specific schema/namespace errors. Zero/zero absence and optional presence are distinct. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public metadata getters/enums/hashdecl and constructor options are documented. Schema design, examples, README and release notes explain implemented constraints. WSDL documentation is warning-free. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No native change; Qore loops use runtime cancellation. No new blocking production operation. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No new production I/O or secret/format-string exposure. Import permission cannot be borrowed from another source; invalid namespace contexts restore on exit. Cycle and shared-graph tests pass. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 30 affected Qore suites pass 403 cases, including 28 new cases / 266 assertions. Eight independent tests pass 235 schema graphs (470 actual binding parses) and 180 SOAP documents with exact values/names/provider/reconstruction checks. Survey counts are unchanged; one already-invalid source now fails earlier on its missing import. |

Candidate WSDL SHA-256: `9889e6946ad10449ab3d71e5c1217606004f6335f29dc222d8145a057e868b00`.
