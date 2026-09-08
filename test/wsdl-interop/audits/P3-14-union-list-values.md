# P3-14 audit: atomic list members in unions

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: WSDL Qore conversion and provider metadata, new Qore/Python tests,
release notes, scalar design, README, oracle adjudication and execution evidence.
The full audit-changes skill was reread and all 62 items are recorded below.
Its module-structure, sandboxing, cooperative-cancellation, DataProvider checklist
and development guide were reviewed for applicability. No native source changed.

XSD 1.0 [list values](https://www.w3.org/TR/xmlschema-2/#list-datatypes),
[ordered union selection](https://www.w3.org/TR/xmlschema-2/#union-datatypes) and
[enumeration](https://www.w3.org/TR/xmlschema-2/#rf-enumeration) require ordered
item value comparisons. The baseline changes boolean-list values into string-list
values, rejects equivalent decimal list choices, and casts native provider lists
directly to string. The initial new regression fails all six cases. Binary list
coverage additionally reproduces a leaked PARSE-HEX-ERROR instead of selection of
the valid base64 member. Each root cause is fixed without relaxing item validation.

The known libxml2 empty-list enumeration null-value defect also affects unions.
Both 2.12.10 and private 2.15.4 reproduce it. The independent matrix records exactly
the named schema compiler diagnostics and counts affected documents as unassessed;
The additional base64 punctuation false positives are also root-caused and counted;
Qore, Xerces and strict Python base64 reject those tokens. No production verdict
is waived. Xerces and exact primitive-value assertions apply to every document. See
[list-values-adjudication.md](../list-values-adjudication.md).

Verification:

- Source and rebuilt AOT regression: 10 cases / 214 assertions, no diagnostics.
- All 58 affected XML suites: 680 cases / 12246 recorded assertions, all cases pass.
  The soap suite intentionally tests three failed assertions internally. The P3-13
  aggregate had omitted that suite's 1031 assertion count; its original 57 logs
  actually contain 12032 assertions. Historical logs/reports are preserved.
- New independent matrix: 24 schemas and 48 actual SOAP contracts, 588 input and
  312 emitted binding documents; 3520 consumer results and 2048 emitted/example
  documents. Xerces assesses all 2948 documents. Libxml2's known empty-list defect
  leaves three schemas and 72/176 documents unassessed in the two matrices; its
  base64 grammar yields exactly 12 input false positives and no output disagreement.
- Full Python discovery: 129 methods, with 33 tracked P4/P5/P6 failure signatures
  identical to P3-13, plus the 12 new libxml2 false positives before their precise
  adjudication. The affected two-method matrix then passes after adjudication;
  no production code changed after the full run. All 13 union methods have passing
  final results when the affected rerun is included. No broad acceptance is claimed.
- Both-version survey and strict coverage are identical to P3-13 outside versions:
  89 selected WSDLs / 756 directions, zero selected failures, 220 broad failures.
- WSDL/SoapClient/SoapDataProvider AOT and native/WSDL docs including qjar pass
  without warnings or errors. No C++ changes: Valgrind is not required here.

Final WSDL SHA-256: `01f96dbb5449251b09ddc3d2c9a4a739bdfba686ccc4ce6988a67dc25137f0b6`.
Native XML SHA-256 remains `8ec5487ebe937450478fc856e5c02114e5cf9ffaf9201cf70d052907b40f2e12`.
Evidence: `/tmp/wsdl-p3-14-{final-unit,aot-identity,aot,docs,final-checks,final-python,
reviewed-independent,survey,coverage}.log`, `final-checks.json`,
`python-comparison.json`, and baseline/expanded-test/reorder/oracle probe logs.
The initial new test accidentally shadowed QUnit's errors() summary method and
read _hash from an object record; both test authoring errors were corrected.
The reorder assertion now respects xs:integer's documented noncanonical-string
representation while explicitly checking the reordered primitive key.

P3 remains in progress. Union-valued list items and the remaining date/IEEE/QName/
anyURI/entity/binary-grammar/native-ambiguity/regex requirements still need their
separate implementation increments; the next union-item reproducer is recorded
in EXECUTION.md. This commit does not complete a phase or claim SOAP conformance.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module entry point, separated source, QPP class or JAR dependency. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 release notes describe atomic list union values, lexical input, retained spellings and exact choices. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing WSDL, SoapClient and SoapDataProvider targets compile the updated module; no new registration is needed. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module entry point, separated source, QPP class or JAR dependency. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | The first WSDL mainpage section remains wsdlintro. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL.qm retains %modern and adds no redundant parse modes. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module entry point, separated source, QPP class or JAR dependency. |
| 8. No `%include` usage (deprecated for modules) | Pass | No %include directive added. |
| 9. Copyright 2026 on all new files | Pass | New Qore/Python regressions and this audit carry 2026; existing WSDL/design documentation retains 2026. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module entry point, separated source, QPP class or JAR dependency. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module entry point, separated source, QPP class or JAR dependency. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module entry point, separated source, QPP class or JAR dependency. |
| 13. `%modern` directive present | Pass | The new Qore regression uses %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | wsdl-union-list-identity.qtest is executable (0755). |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Local qlib prepending precedes the relative ../qlib/WSDL.qm requirement. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | WSDL/xml belong to this repository; QUnit is delivered by Qore. No external binary dependency added. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++/QPP changes in this increment. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++/QPP changes in this increment. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++/QPP changes in this increment. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | New production helpers perform no File/Dir/Socket/HTTPClient operations. The existing offline worker harness owns fixture I/O. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++/QPP changes in this increment. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++/QPP changes in this increment. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++/QPP changes in this increment. |
| 24. No blocking operations without cancellation support | Pass | No blocking operation added. Qore loop cancellation and scoped union traversal cleanup remain active; probes test unexpected and cancellation-category exceptions. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 34. Response/output types use `private` Fields | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 38. Password/secret fields have `"sensitive": True` | Pass | Finite union list choices still normalize to AllowedValueInfo with value/display_name through XsdUnionDataField; list keys now retain item primitive families and order. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 47. No bare field/option names in prose — must use backticks | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | Generic schema/provider value conversion only; no business action, app, route, request/response field definition, registration, secret or JAR changed. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Native and lexical list conversion uses actual member constraints and ordered primitive identities. No heuristic, production validator bypass, fixture-specific production branch, stub or TODO. Unsupported identity families remain explicit required P3 work. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Qore owns temporary lists/maps. Existing on_exit contexts restore on success/error; malformed detached metadata never publishes a partial provider. Failed field choice setters preserve the existing map. No C++ ownership changes. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | List metadata maps are initialized during configuration/restoration. Public types must be configured before concurrent use. Conversion caches stay per-thread/per-operation; no persistent result cache. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Public XsdUnionListInfo and atomic hashdecls, typed provider maps and string lists; restored shape, provider identity, category, mandatory items and whitespace rules are validated. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | List conversion/key construction is linear in item/text size. Length-prefixed keys avoid collisions. Existing shared-graph memoization remains active and is covered by graph tests; no benchmark claim. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Positive, negative and boundary tests cover empty/single lists, order, numeric equality, binary family selection, native item boundaries, lexical facets, invalid metadata, member reordering/pruning, legacy metadata and error recovery. Matching binary parser errors alone permit fallback. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | New public metadata is documented; module prose, durable design and README include the boolean-list ambiguity example and detached behavior. Oracle evidence records exact unassessed libxml2 cases without weakening Qore or Xerces checks. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++/QPP changes in this increment. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No credentials, external fetch, unsafe buffer or user-controlled format string added. Native list items and serialized shapes are checked before conversion/index use. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Final source/AOT suite passes 10 cases / 214 assertions; all 58 affected suites and both independent list-union matrices pass. Survey/strict coverage are unchanged. Full discovery retains the same 33 later-phase failures; adjudicated oracle false positives are explicitly counted and the affected matrix was rerun. |
