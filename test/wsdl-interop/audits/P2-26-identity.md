# P2-26 final audit: document and message namespace identities

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: combined independently tested P2-11/P2-12/P2-13 identity changes after
049cf0d. Includes WSDL name helpers/field indexing/message part scopes, SoapHandler
routing, three new Qore suites, workers/independent regressions, documentation and
release notes. The initial incomplete XML carrier from historical snapshots is
excluded; the complete carrier and its consumer integration are a later P2 commit.
Native sources, WebContentUtil, schema-constraint increments and other repos are
excluded. Candidate: /tmp/wsdl-schema-identity-review.

The full audit-changes skill and its referenced module structure, sandboxing,
cancellation and DataProvider guides were applied to this exact candidate.
Root causes were destructive prefix stripping before schema matching, local-name
map collisions before resolution, and message parts resolving outside their
actual XML namespace scope. The implementation retains expanded identities until
compatible public field names or wire names are selected.

Requirements: [XML Namespaces scoping/defaulting](https://www.w3.org/TR/REC-xml-names/#scoping),
[XSD element validity](https://www.w3.org/TR/xmlschema-1/#cvc-elt), and
[WSDL 1.1 messages/body/header parts](https://www.w3.org/TR/2001/NOTE-wsdl-20010315).

Validation is recorded in the accompanying P2-26 execution entry. No C++ changes;
Valgrind is not required for this increment. Native prerequisites have their own
committed audits. Eight independently invalid integer cases remain P3 failures,
four nested-choice exclusivity cases remain P4 failures, and two actual binding
selection cases remain P6 failures. They are not counted as passing identity tests.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 and SoapHandler 0.3.4 release notes describe namespace matching, collision-safe fields, message scopes/examples and retained routing input. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | Existing single-file modules use %modern; no redundant directives added. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 8. No `%include` usage (deprecated for modules) | Pass | No %include directive introduced. |
| 9. Copyright 2026 on all new files | Pass | Every new regression/worker/Python file and audit has a 2026 notice. Existing module and design notices include 2026. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 13. `%modern` directive present | Pass | All qtests use %modern; .qr workers explicitly use it as well. |
| 14. Executable permission set (`chmod +x`) | Pass | New qtests and QR workers have executable permissions. Python files use the documented python3 entry point. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Qtests prepend local qlib before relative WSDL/SoapHandler requires; worker requires are relative. QORE_MODULE_DIR selects the committed native Debug module and isolated candidate user modules. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | xml and repository user modules are hard dependencies. Optional external json dependencies in QR workers use %try-module; QUnit is the required core test framework. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++/QPP change. Qore loops use runtime cooperative cancellation; no new blocking production operation. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++/QPP change. Qore loops use runtime cooperative cancellation; no new blocking production operation. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++/QPP change. Qore loops use runtime cooperative cancellation; no new blocking production operation. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | No new production I/O. SoapHandler regression uses its existing local HTTP service with bounded request deadlines and lifecycle teardown; Python fixtures are offline with bounded workers and validators. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++/QPP change. Qore loops use runtime cooperative cancellation; no new blocking production operation. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++/QPP change. Qore loops use runtime cooperative cancellation; no new blocking production operation. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++/QPP change. Qore loops use runtime cooperative cancellation; no new blocking production operation. |
| 24. No blocking operations without cancellation support | N/A | No C++/QPP change. Qore loops use runtime cooperative cancellation; no new blocking production operation. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 34. Response/output types use `private` Fields | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | Pass | Existing dynamic provider field metadata is retained; final map keys distinguish expanded identities. Provider reconstruction/type/value tests cover element and part fields. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | Pass | Generated examples use the same collision-safe field or WSDL part names as providers, include all multipart values and validate independently. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | Pass | Existing allowed values stay on their resolved type; no bare new enumeration metadata introduced. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 47. No bare field/option names in prose — must use backticks | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No new module/layout/registration, public QPP class, DataProvider action/app/type declaration, factory, description or JNI dependency in this increment. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Resolves names before matching/indexing instead of stripping namespace identity. No fixture-specific production branch, stub or weakened assertion. Known P3/P4/P6 failures remain executable failures under the explicit phase-routing rule. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Managed Qore values with copy-on-write. on_exit restores namespace scope; on_success publishes fully constructed types; resolution guards restore schema state after errors. Original caller input/base field maps remain unchanged in negative/reconstruction tests. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | New field maps are selected during schema finalization. Runtime expansion/restoration operates on local values; routing uses a separate hash. No new shared cache or global mutable state. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed element maps, prefix/identity maps, counts and ArgInfo hashdecls. Internal field lookup asserts complete resolution. Existing heterogeneous XML content uses hash<auto> intentionally. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Linear field indexing and unique-identity counts. Mutable scope stack avoids copying every ancestor binding to descendants. Repeated alias lists are promoted once then appended; 4096 values and deep scopes are covered. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Wrong/unbound/reserved namespaces, malformed expanded keys, duplicate parts, ambiguous public aliases and missing required fields raise specific existing error categories. Subsequent valid calls and original input remain intact. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public name helpers document inputs/results/errors and examples. Design and README explain local versus expanded field keys, part names and namespace scoping. Candidate WSDL/SoapHandler documentation is generated with warnings enabled. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++/QPP change. Qore loops use runtime cooperative cancellation; no new blocking production operation. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | XML names are validated as NCNames and reserved namespace bindings are rejected. Prefix allocation reserves existing declarations and lexical references. No new external resource access, secrets or user-controlled format strings. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Positive/negative namespace, collision, provider, examples, reconstructed schema and real HTTP checks pass. Independent lxml/Xerces document names, order and values are asserted in both actual SOAP bindings and directions. Corpus and later-phase failure evidence below. |

Candidate production SHA-256:

- qlib/WSDL.qm: `db6ca5d8a7cad7f074edb4c68393b62a3a3e0d62cd3d440fcde738ca4650b73a`
- qlib/SoapHandler.qm: `c7331ab3c93d8a36a6a04090dfc192bd6a164f5ab3eb3f8db3c122e019309385`
