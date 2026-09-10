# P4-08 audit: ordered child value conversion

Copyright (C) 2026 Qore Technologies, s.r.o.

Date: 2026-09-10. Scope: final changes after `09f5f68` in `qlib/WSDL.qm`,
`soap.qtest`, `wsdl-xml-consumers.qtest`, `wsdl-particle-values.qtest`, the
`particle-values.qr` / `test_particle_values.py` worker and oracle,
`test_compositor_context.py`, implemented design, README, current reports,
execution record, this audit and [P4-08-validation.json](../P4-08-validation.json).
The full [audit skill](/home/david/.codex/skills/audit-changes/SKILL.md) and its
module-structure, sandboxing and cancellation references were applied;
DataProvider registration/development guidance was checked for applicability.
All 62 checks are individually resolved: **19 Pass / 43 N/A / 0 Fail**.

Review fixed an ambiguous-local-name regression: direct component callers must
supply expanded identities when declarations share a local name. Metadata now
accepts only actual numbered value/CDATA/comment keys. The core AOT failure was
reduced to a private typed constructor called by a static factory with instance
member operands; Qore commit `72890415a` fixes its lexical access context and has
its own complete audit. The isolated debug core includes the latest upstream
container retyping/deferred-constant fixes and matches main native sources.

Final source SHA-256 is
`09a262f40a5368071e7fa1171348556a3fd9c88da91f9341171b48030a11b18f`.
The 108-suite gate passes **1,087 cases / 54,665 reported assertions**, without
warnings. The existing three intentionally caught comparator negatives in
`soap.qtest` retain their established reporting. All 16 mode checks pass: per
mode, three Qore suites total 33 cases/706 assertions, and independent lxml and
Xerces check 248 rows, 124 input verdicts and 112 outputs. Original/reconstructed
schemas, both real SOAP bindings/directions, local HTTP, required empty wrappers,
nil/list occurrences, encode-only constraints and scope cleanup are covered.

The compiled WSDL module contains 1,157 variants; its affected suite passes
11 cases/107 assertions. Both its Valgrind run and the reduced core constructor
run report zero errors and zero lost bytes without suppressions. Only Valgrind
uses the already approved PCRE2 no-JIT switch, with Qore signals disabled and
Qore debugging enabled. The existing GCC DWARF reader warning and 22 broad
documentation diagnostics remain recorded P9 work; affected documentation and
ordinary tests emit no warnings. All three design examples execute successfully.

Both-version survey retains original hashes and every stage, with 32 decoding
failures now passing and no formerly passing-stage regression. All 64 changed
coverage failures move from decode to the newly reachable native serializer;
none is counted as passing. Four retain original P2 primary labels for mixed
content, whose runtime behavior is already explicitly assigned to P5. Strict
coverage passes 130 selected descriptions/1,260 directions in the full 293-case
ledger, with 144 failures still visible. Its unchanged 60-second worker deadline
expired during concurrent gates; the complete unchanged command then passed in
isolation (66.316 seconds including validators). No case, timeout or output
criterion was changed. The survey harness (15 methods), compositor harness
(two methods) and affected documentation pass.

Native particle serialization, independent field cardinality and sample
integration remain P4 work. P5-P9 retain the full original scope, including
860 explicitly unassessed value/infoset directions. Logs use
`/tmp/wsdl-p4-08-verified-`; source/binary hashes and complete validation rows are
in the inventory. No system install or push was performed.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | External repository; no new installed module. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 release notes describe ordered conversion, retained XML validation and required wrappers. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module or build registration. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new QMOD target. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new module documentation section. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL and all new/changed Qore test drivers use %modern without redundant directives. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated .qc source is changed. |
| 8. No `%include` usage (deprecated for modules) | Pass | No deprecated %include is introduced. |
| 9. Copyright 2026 on all new files | Pass | New tests, worker, inventory and audit carry copyright 2026; changed module/design notices retain 2026. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | Existing module layout is unchanged. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No duplicate module. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new QPP class. |
| 13. `%modern` directive present | Pass | Qore suites and worker use %modern, including generated integration descriptions. |
| 14. Executable permission set (`chmod +x`) | Pass | All changed/new qtest files and the Qore worker are executable (0755). |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Tests prepend local qlib before relative WSDL/SoapClient/SoapHandler requirements; the worker requires ../../qlib/WSDL.qm. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project xml and QUnit dependencies remain hard requirements. The external json worker dependency uses %try-module and fails explicitly when missing. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No native source change in this XML increment; Qore prerequisite audited separately. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No native source change in this XML increment; Qore prerequisite audited separately. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No native I/O change. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Test-only file access reads a temporary manifest. Local HTTP tests exercise actual SoapClient/SoapHandler contracts with bounded requests and deterministic cleanup; no new production I/O capability is added. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ loop is changed. Qore cancellation remains active, with cancellation/reuse coverage passing. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No native cancellation API is introduced or replaced. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No new native loop needs a cancellation interval. |
| 24. No blocking operations without cancellation support | Pass | Owned workers have bounded deadlines; HTTP requests and thread queue synchronization are bounded. Existing cancellation/reuse suites pass. The complete strict worker passes in isolation without modifying its deadline. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 34. Response/output types use `private` Fields | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 47. No bare field/option names in prose — must use backticks | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Ordered matching precedes native projection, with one real declaration per position and no shared range mutation. Required wrappers follow their own occurrence constraints. Native serialization/metadata/samples and P5 behavior remain explicitly owned later work; no fixture special case, weakening or skipped failure. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Retained validation owns a namespace copy and restores its previous thread-local scope with on_exit, including failures and interruption. Failed conversions publish no partial result; constructor cleanup is fixed/audited in Qore 72890415a. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Matching/field accumulation belongs to each call. Namespace allocation never reaches shared schema state. Four deterministic concurrent callers verify native/retained scope isolation. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed particle/element maps and name lists identify declarations; occurrence values use explicit list<auto> so nil and list-valued children retain their shapes. Malformed names and ambiguous local aliases are rejected. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Name indexing and field accumulation are linear in declarations/input size beyond the already bounded particle matcher. Child conversion occurs once per accepted position; retained validation avoids whole-flat-subtree re-encoding. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Tests reject incomplete/overfull/wrong-order groups, wrong namespace identities, malformed child names, empty occurrence lists, unknown metadata, ambiguous local aliases and encode-only value violations with intended error categories. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | The implemented particle design, three executed examples, public occurrence API documentation, README and release notes describe exact conversion and retained XML behavior. Current coverage counts were synchronized with the ledger. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No DataProvider action/app registration, typed action fields, discovery factory or JNI dependency is changed. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Complete matching runs before child conversion. Existing root/DOCTYPE checks remain active. Tests preserve upstream bytes and use an explicit documented SOAP fixture derivative; no untrusted format string or credential is added. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 108 suites/1087 cases/54665 reported assertions pass without warnings. Three affected suites and the 248-row independent matrix pass in all four source modes. AOT 1157 variants, real SOAP 1.1/1.2 HTTP, both directions/reconstruction, strict corpus, and Valgrind pass. |
