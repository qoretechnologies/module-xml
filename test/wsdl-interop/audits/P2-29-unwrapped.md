# P2-29 final audit: bare document argument ownership

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: P2-20 argument selection isolated on parent 7771dde, new focused Qore
suite, independent Python/QR check, release notes and implemented documentation.
The complete audit-changes checklist and referenced core design guides were applied.
No native, carrier/consumer, unrelated module or other-repository change.

Root cause: selecting unwrapped values inspected only the flat element map;
wildcard-only and nested-choice-only records appeared empty. Selection also
needed ownership boundaries to preserve separately addressed headers/parts.
The implementation recognizes parsed choice/element-wildcard fields for one
selected part, reserves other wrappers and preserves legacy message containers.
Ambiguous multipart records require explicit part/element wrappers.

Requirements: the compatible Qore value contract and WSDL 1.1
[SOAP body](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_soap:body)/
[header parts](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_soap:header),
plus [XSD zero/zero particle absence](https://www.w3.org/TR/xmlschema-1/#element-element).
No complete ordered-particle or general wildcard runtime claim is made.

Validation: /tmp/wsdl-p2-29-{affected,independent,survey,docs}.log.
All 409 affected Qore cases and the independent test pass without warnings/errors.
Both independent validators accept all 60 documents with exact infoset/value
assertions. The 293-WSDL/1136-message survey is recursively unchanged except
versions; known later-phase failures remain failures. No native changes.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 notes describe bare choice/wildcard fields, legacy message containers and explicit multipart ownership. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL remains %modern with no redundant parse directives. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 8. No `%include` usage (deprecated for modules) | Pass | No %include or separated source layout introduced. |
| 9. Copyright 2026 on all new files | Pass | New qtest/worker/Python/audit files have 2026 notices; source and design notices already include 2026. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module/layout/registration, C++/QPP class, DataProvider action/app/type declaration, description, factory or JNI dependency in this increment. |
| 13. `%modern` directive present | Pass | The new qtest and QR worker use %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | Qtest, QR worker and Python regression are executable. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Qtest/worker prepend local qlib and require WSDL relatively. Explicit environment selects the isolated candidate and committed native Debug XML. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | xml/WSDL are required repository modules; QR json uses %try-module with a descriptive missing dependency failure. QUnit is the core framework. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No native change; Qore loops use runtime cancellation. No new blocking production operation. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No native change; Qore loops use runtime cancellation. No new blocking production operation. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No native change; Qore loops use runtime cancellation. No new blocking production operation. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | No production I/O added. Worker reads only its supplied temporary contract; Python runs offline validators and bounded Qore processes. |
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
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Argument selection recognizes choices/element wildcard slots and reserves other part/header values. No fixture-specific branch, stub or scope reduction. Full particle/wildcard matching remains explicitly tracked P4/P5 work. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Only managed Qore values and copy-on-write hashes. Original caller input remains unchanged; selection removes values only from the local serialization copy. Negative request followed by valid request and reconstructed schema tests pass. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Parsed wildcard metadata is established during construction. Selection maps/hashes belong to each call; no new shared mutable state. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed string/bool field and reserved-name maps; existing hash<auto> carries heterogeneous XML values. Explicit NT_NULL/exists handling preserves False, zero and empty strings. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Builds a field map once per selected part, then scans the input once. Other part/header names use hash lookups. No unbounded repeated copying or new recursion. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Ambiguous multipart bare values require wrappers; attribute wildcards and zero/zero particles cannot consume child fields. Nested choices retain negative exclusivity tests and header wrappers remain separate. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | hasElementWildcard/isEmpty/serializeDocument document scope/results. Release notes, README and durable schema design include examples and limits. WSDL docs generate without warnings/errors. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No native change; Qore loops use runtime cancellation. No new blocking production operation. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No new I/O, secret or user-controlled format string. Wildcard selection cannot absorb explicitly reserved header/other-part wrappers; output namespace names are handled by the committed generator. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 31 affected Qore suites pass 409 cases. The new suite passes six cases/116 assertions; independent lxml/Xerces validation covers 60 documents through both actual bindings/directions and reconstructed services. Names/order/values/header placement are asserted. Survey is recursively identical to 7771dde except versions. |

Candidate WSDL SHA-256: `7adfda3b7c5338dbf85d2fb6b64ee4365a6a7c46652c6819e086ae4773f5dbbd`.
