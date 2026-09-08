# P2-27 final audit: inherited attributes and mixed base construction

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: P2-14/P2-15 Qore construction changes isolated on parent 9ae595e,
new derivation/mixed-base regressions and worker, release notes and implemented
design. Complete audit-changes checklist applied to this candidate, with its
referenced core design guides. No native, unrelated module or other-repo change.

Root causes: inherited attributes were overwritten without required/fixed/type
checks, and complex construction discarded the mixed flags and nested particle
emptiability needed for legal simple-content restrictions. Replacements now
preserve the base constraint; extensions reject duplicate expanded uses. A typed
construction tree resolves all nested group references and the emptiability
predicate before choosing the effective scalar base. This does not implement
ordered instance matching or arbitrary mixed-content preservation.

Requirements: [attribute restriction](https://www.w3.org/TR/xmlschema-1/#derivation-ok-restriction),
[simple-type ancestry](https://www.w3.org/TR/xmlschema-1/#cos-st-derived-ok),
[complex-type mappings](https://www.w3.org/TR/xmlschema-1/#Complex_Type_Definition_details),
[particle emptiability](https://www.w3.org/TR/xmlschema-1/#cos-group-emptiable).
Independent tests explicitly retain libxml2's fixed-constraint, outer-facet and
mixed-flag disagreements; Xerces and Qore enforce the cited requirements.

Validation: /tmp/wsdl-p2-27-{affected,attributes,mixed,survey,docs}.log.
Both new independent suites pass, all 26 affected Qore suites pass 375 cases,
and WSDL documentation is warning-free. Survey covers all 293 descriptions and
1136 messages with no change from the preceding identity commit except versions.
Previously tracked later-phase failures remain failures. No C++ change or new
Valgrind requirement. Native memory/dependency prerequisites are already committed.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, registration, public QPP class or module layout change. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 notes document required/fixed/type restriction, duplicate extension uses, named mixed bases, group references and effective mixed flags. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module, registration, public QPP class or module layout change. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, registration, public QPP class or module layout change. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new module, registration, public QPP class or module layout change. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | Existing WSDL module remains %modern; no legacy parse directives added. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated .qc changes in this increment. |
| 8. No `%include` usage (deprecated for modules) | Pass | No %include added. |
| 9. Copyright 2026 on all new files | Pass | New Qore/QR/Python regressions and audit carry 2026 notices; source and design notices already include 2026. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, registration, public QPP class or module layout change. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, registration, public QPP class or module layout change. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, registration, public QPP class or module layout change. |
| 13. `%modern` directive present | Pass | Both qtests use %modern; the QR worker does as well. |
| 14. Executable permission set (`chmod +x`) | Pass | Both qtests, QR worker and Python regressions are executable. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | New qtests and worker prepend local qlib and require WSDL by a relative path. The isolated candidate is tested against the committed native Debug module. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | xml and WSDL are required repository modules; QR json uses %try-module and descriptive dependency failure; QUnit is the core test framework. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ or QPP change in this increment. Native dependency and memory prerequisites are already committed and audited in 5477680 and 049cf0d. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ or QPP change in this increment. Native dependency and memory prerequisites are already committed and audited in 5477680 and 049cf0d. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ or QPP change in this increment. Native dependency and memory prerequisites are already committed and audited in 5477680 and 049cf0d. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | No new production I/O. Tests use in-memory schemas and existing offline temporary-file/validator helpers, with bounded worker processes. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ or QPP change in this increment. Native dependency and memory prerequisites are already committed and audited in 5477680 and 049cf0d. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ or QPP change in this increment. Native dependency and memory prerequisites are already committed and audited in 5477680 and 049cf0d. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ or QPP change in this increment. Native dependency and memory prerequisites are already committed and audited in 5477680 and 049cf0d. |
| 24. No blocking operations without cancellation support | N/A | No C++ or QPP change in this increment. Native dependency and memory prerequisites are already committed and audited in 5477680 and 049cf0d. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 34. Response/output types use `private` Fields | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | Pass | The existing scalar/attributed simple-content provider receives the resolved inline type and inherited fields; native integer zero, fixed unit, generated examples and reconstructed WebService consumers pass. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | Pass | Existing allowed-value metadata is unchanged; affected attribute consumer suites pass. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 47. No bare field/option names in prose — must use backticks | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No action/app registration, new field descriptions, factory, JNI dependency or packaging change. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Validates inherited attributes and preserves construction information needed for mixed bases. No name-specific workaround, stub or skipped failing case. Runtime ordered/mixed matching remains assigned to P4/P5. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Managed Qore data, scope/finalization guards and on_error restoration retain exception safety. Required/fixed/type checks run before merging replacements; group evaluation restores its active flag and only caches a completed result. Failed-addition and later-success tests pass. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | New metadata and group caches are completed during schema construction. Ancestry memo is per check. Existing immutable-after-construction service sharing is unchanged. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed recursive XsdEmptiabilityInfo, group maps, attribute identity maps and per-pair ancestry cache. Builtin parent relations use known XSD type names; no untyped callback added. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Group result caching avoids exponential traversal of a shared 32-level doubled-reference graph. Attribute replacements index expanded names once; type-pair memo avoids repeated union ancestry work. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Wrong requiredness/fixed/type replacements, duplicate extension uses, incompatible inline types, missing/cyclic groups and illegal mixed flags produce WSDL-ERROR. Optional branches still validate every reference. Exact value and recovery cases pass. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | isEmptiable documents groups/result/errors. WSDL release notes, examples, schema identity design and README describe implemented derivation/mixed metadata. Candidate WSDL docs pass without warnings/errors. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++ or QPP change; no native Valgrind requirement in this increment. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No credentials, external access change or user-controlled format string. Group/type traversal detects cycles; false/zero values and qualified collisions retain their meaning. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 26 affected Qore suites pass 375 cases; new suites add 13 cases/130 assertions. Four independent tests pass 79 schema variants and 68 SOAP documents across actual 1.1/1.2 bindings and both directions. Both-version survey is recursively identical to 9ae595e except version metadata. |

Candidate WSDL SHA-256: `0379fdf581beb7ed47bba8aca78b563f45869f8da9c5d57b52e3121e52c74ca4`.
