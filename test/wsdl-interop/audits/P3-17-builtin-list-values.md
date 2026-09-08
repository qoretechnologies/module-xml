# P3-17 audit: builtin name grammar and list values

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: WSDL builtin lexical checks, restriction/provider metadata and union value
identity; Qore/Python regressions, worker error reporting and offline range fixture; release notes,
scalar design, README, normative/oracle evidence and execution record.
The full audit-changes skill and applicable module structure, sandboxing,
cooperative cancellation, DataProvider checklist and development-guide rules
were applied. No C++ changed and no additional Valgrind run is required.

The initial four cases fail on committed P3-16. Shared XML name character classes
now enforce the XSD-referenced XML 1.0 Second Edition grammar; builtin list values
compare ordered string items. Own enumeration/pattern/count facets survive
provider reconstruction, optionality and example generation. The final review
also rejects builtin list descriptors in atomic-item metadata. An old compiled
module reproduces acceptance of that corruption; final source/AOT reject it.

Normative requirements, numeric-range provenance and the precise libxml2 empty
builtin-list false positives are documented in
[builtin-list-values-evidence.md](../builtin-list-values-evidence.md).
No Qore verdict is waived; no upstream corpus or pinned validator artifact changed.

Final verification:

- Source and rebuilt AOT: 9 cases / 765 assertions, no diagnostics.
- All 61 affected XML suites: 710 cases / 13507 assertions. The SOAP test
  intentionally tests three failed assertions inside passing cases.
- Five independent methods: 45 binding schemas, 90 actual SOAP contracts,
  1584 input and 828 output binding documents, 9168 consumer results and 5136
  consumer/example documents. Three further schemas check 6054 name boundaries.
  Xerces assesses all 13602 documents; libxml2 has exactly 24 adjudicated input
  false positives, with all Qore rejection and exact-value checks mandatory.
- Final WSDL/SoapClient/SoapDataProvider AOT and WSDL docs build cleanly.
- Final stable Python discovery: 139 methods in 495.285 seconds, exactly the
  same 33 tracked P4/P5/P6 failure signatures and no errors. No implementation
  or test files changed during this run.
- Both-version survey and strict coverage unchanged outside versions: 89 selected
  WSDLs / 756 directions, zero selected failures and 220 broad tracked failures.

Final WSDL SHA-256:
`6288ad0427058ef8c16776e78428408761caf9faba6edac973d749c9e5e3ec68`.
Native XML remains `8ec5487ebe937450478fc856e5c02114e5cf9ffaf9201cf70d052907b40f2e12`.
Range fixture SHA-256:
`fa274f68b6dfe75cc126bb418528dcad84812dd326a1e45c68e43e7652d9e4a0`.
Evidence under `/tmp/wsdl-p3-17-`: baseline/grammar/values unit logs,
independent-first/adjudicated/final, name-boundaries, final-python,
exact-checks.json and per-suite logs, exact-survey/coverage, aot-final,
final-aot-unit, docs-final and native empty-builtin probes.

The preliminary discovery run had one unclassified worker exit 2; stderr was
captured but omitted from CalledProcessError rendering. The standalone list
matrix passes. Its original cause is not recoverable from that log, which is not
used as final verification. WorkerProcessError now includes bounded stderr while
retaining the original process-error API and full output. Fifteen survey tests
pass, including a real failed child, diagnostic bounds and deterministic cleanup.
The final full discovery uses unchanged implementation/test files.

Earlier test authoring errors (field factory spelling, temporary method
reference, outer wrapper member indexing and hashdecl discrimination) were fixed
before final execution. The old-AOT metadata reproducer records its expected
source-hash mismatch warning separately; the rebuilt final AOT has no warning.
The broader P3 regex complement/class gaps remain explicit next work, alongside
remaining date/IEEE/binary/QName/entity/XML-RPC requirements. P3 and P4-P9 are not
claimed complete.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, separated module source or QPP class. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL release notes cover builtin list value identity/facets and Unicode name grammar. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing WSDL/SoapClient/SoapDataProvider AOT targets build successfully; no new module target needed. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, separated module source or QPP class. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | The first section remains wsdlintro. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL.qm retains %modern and no redundant directives. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, separated module source or QPP class. |
| 8. No `%include` usage (deprecated for modules) | Pass | No deprecated %include directive added. |
| 9. Copyright 2026 on all new files | Pass | All new Qore/Python/JSON/Markdown files carry 2026 copyright; normative numeric ranges have provenance. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, separated module source or QPP class. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, separated module source or QPP class. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, separated module source or QPP class. |
| 13. `%modern` directive present | Pass | Both new Qore test/worker files declare %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | The qtest and .qr worker are executable (0755). |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Local qlib prepend precedes relative WSDL requirements in the qtest and worker. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | xml/WSDL are same-repository dependencies; QUnit is delivered by Qore. The worker guards external json using %try-module and a clear missing-module error. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++/QPP changes. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++/QPP changes. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++/QPP changes. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production changes perform no filesystem/network I/O. The offline boundary worker uses ReadOnlyFile only for the supplied test manifest; Python subprocesses have bounded deadlines. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++/QPP changes. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++/QPP changes. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++/QPP changes. |
| 24. No blocking operations without cancellation support | Pass | No blocking production operation added. Qore loops retain runtime cancellation; the new helpers have no mutable traversal state or catch that could swallow cancellation. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 34. Response/output types use `private` Fields | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | Pass | Existing QoreDataField and XsdUnionDataField normalize finite choices to AllowedValueInfo. Tests retain equivalent ordered list choices, reconstruction and invalid-choice errors. |
| 38. Password/secret fields have `"sensitive": True` | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 47. No bare field/option names in prose — must use backticks | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | Generic schema/value providers only; no action/app registration, business request/response type, secret, factory or dependency JAR added. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Fixes raw enumeration comparison, omitted provider facets and missing token grammar. Final review restricts the new text-facet wrapper to builtin lists and rejects list-valued atomic-item metadata. No upstream fixture modification or production workaround. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Qore-managed values remain scoped to the operation; metadata validates before conversion. Error-category tests and existing cancellation/reentry suites pass; no native allocations changed. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Character classes are immutable constants; per-value identity and normalized text are local. No mutable shared state added; WorkerProcessError holds only its failed process result. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed XsdSizedFacetInfo metadata, typed ordered key lists and existing XsdUnionValueIdentity hashdecls; no untyped code callbacks or native casts added. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Token and key construction are linear in input size; class ranges are fixed constants. Existing bounded example generation is retained, with enumeration candidates checked first. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Tests cover empty/invalid characters and native containers, list order/counts, whitespace, schema enumeration declarations, requiredness and contradictory/nested metadata, with exact errors. Failed-worker stderr rendering is bounded and full diagnostics remain on the exception; real child cleanup is tested. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public hashdecl fields and constants are documented; release notes, scalar design/examples, README, normative/oracle evidence and execution record are updated. Final docs build is clean. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++/QPP changes. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No credentials, raw buffers or user format strings. Metadata rejects inconsistent kinds/whitespace and builtin lists masquerading as atomic items. Offline workers bound input size, subprocess execution and diagnostic rendering. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Final source/AOT unit regression passes 9 cases/765 assertions; all 61 XML suites pass 710 cases/13507 assertions. Five independent methods cover 90 real SOAP contracts and 13602 Xerces documents, with exact values and 24 source-adjudicated libxml2 false positives. Full Python/corpus gate results are recorded below. |

All 62 checklist items are classified, with no failed items remaining.
Final comparison evidence is in `/tmp/wsdl-p3-17-stable-python-comparison.json`
and `/tmp/wsdl-p3-17-exact-checks.json`. The earlier worker observation remains
preserved without asserting an unproven cause; the final stable run has no error.
