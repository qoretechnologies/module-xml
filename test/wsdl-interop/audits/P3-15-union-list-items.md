# P3-15 audit: union-valued list items

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: WSDL conversion/provider metadata, two Python files and one Qore regression,
scalar design, release notes, README, validator adjudication and execution records.
The full audit-changes skill was reread before this commit. Module structure,
sandboxing, cooperative cancellation, DataProvider checklist and development guide
were reviewed for applicability. All 62 checks are recorded below.

XSD 1.0 lists contain ordered atomic values. An item union chooses its first
accepting member; boolean and decimal values remain distinct, while integer and
decimal values share their primitive family. The baseline cannot describe a list
whose item selects a union member, losing the identity needed for enclosing union
enumerations and finite field choices. Capturing the actual selected item identity
fixes this across schema/provider conversion and restriction wrappers, without
calling user validators again to infer a selection.

The precise Xerces LIST_DT/LISTOFUNION_DT enumeration false negative is adjudicated
in [list-values-adjudication.md](../list-values-adjudication.md), with original
source artifact hash, source locations and normative references. Exactly 48 binding
and 128 consumer documents have that false negative; libxml2 and independent typed
values remain mandatory. Empty-list enumeration compilation in libxml2 remains a
separate counted defect, with Xerces and exact empty values required. No production
waiver, upstream fixture edit or validator artifact modification is introduced.

Verification:

- Source and rebuilt AOT regression: 11 cases / 251 assertions, no diagnostics.
- All 59 affected XML suites: 691 cases / 12497 recorded assertions, every case
  passes. The soap suite intentionally exercises three failed assertions internally.
- New independent matrix: 18 schemas, 36 actual SOAP contracts, 408 input and
  180 emitted binding documents, 1248 consumer/output/example documents. Xerces
  assesses all 1836 documents; exact false negatives are counted above. libxml2's
  empty-list defect leaves three schemas and 72/176 documents unassessed.
- Full final-runtime Python discovery: 131 methods; the 33 tracked P4/P5/P6 failure
  signatures are unchanged. No new failure or reduced coverage; no phase claim.
- Both-version survey/strict coverage identical outside versions to P3-14:
  89 selected WSDLs / 756 directions, zero selected failures, 220 broad failures.
- WSDL/SoapClient/SoapDataProvider AOT and WSDL docs/qjar builds pass without
  warnings or errors. Native XML is unchanged.
- AOT integration exposed Qore map specialization and optional common-type folding
  defects, fixed separately in Qore develop commit `3e2f47be0`, without pushing.
  Its full audit is [P3-15-qore-map-types.md](P3-15-qore-map-types.md).
  Core and compiled XML Valgrind runs have zero errors, zero definite/indirect/
  possible loss and no suppressions. The known DWARF reader diagnostic remains
  tracked for P9, separately from memory errors.

WSDL SHA-256: `c0bc371468726c34941e844ba9e951848fbd469358e21ce7a851c7e40e53e581`.
Native XML SHA-256: `8ec5487ebe937450478fc856e5c02114e5cf9ffaf9201cf70d052907b40f2e12`.
Evidence: `/tmp/wsdl-p3-15-core-final-{checks,survey,coverage}.{log,json}`,
`/tmp/wsdl-p3-15-python-core-final.log`, `/tmp/wsdl-p3-15-python-core-comparison.json`,
`/tmp/wsdl-p3-15-{aot,docs,aot-items-final,aot-valgrind,independent-reviewed}.log`.

P3 remains active. List-own facets for union-valued items are the next independently
reproduced root cause, followed by the remaining scalar requirements. All P4-P9
requirements remain in scope. This increment does not complete a phase.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, separated source or QPP class. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL release notes describe union-item list identities and reconstructed providers. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing WSDL/SoapClient/SoapDataProvider qmod targets rebuilt successfully. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, separated source or QPP class. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | First module section remains wsdlintro. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL.qm retains %modern without redundant directives. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, separated source or QPP class. |
| 8. No `%include` usage (deprecated for modules) | Pass | No deprecated %include directives added. |
| 9. Copyright 2026 on all new files | Pass | New tests and audit records carry 2026 copyright. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, separated source or QPP class. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, separated source or QPP class. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, separated source or QPP class. |
| 13. `%modern` directive present | Pass | New Qore regression declares %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | wsdl-union-list-items.qtest is executable (0755). |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Local qlib prepend precedes relative ../qlib/WSDL.qm requirement. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | xml/WSDL belong to this repository; QUnit is delivered by Qore. No external binary dependency added. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ changes in this XML increment; separate required Qore fix audited independently. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ changes in this XML increment; separate required Qore fix audited independently. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ changes in this XML increment; separate required Qore fix audited independently. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production helpers add no filesystem or network operations; independent tests reuse the offline fixture/worker harness. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ changes in this XML increment; separate required Qore fix audited independently. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ changes in this XML increment; separate required Qore fix audited independently. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ changes in this XML increment; separate required Qore fix audited independently. |
| 24. No blocking operations without cancellation support | Pass | No blocking operations added; Qore loops retain cancellation and on_exit restores capture state after unexpected errors. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 34. Response/output types use `private` Fields | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | Pass | XsdUnionDataField retains AllowedValueInfo value/display_name normalization; ordered primitive identities govern finite list choices and atomic setter failure. |
| 38. Password/secret fields have `"sensitive": True` | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 47. No bare field/option names in prose — must use backticks | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | Generic schema/provider conversion only; no business action/app/field registration, secret, factory or JAR changed. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Actual conversions publish primitive identities without replaying validators. Compiler defects fixed at their Qore roots. Exact oracle defect adjudication does not relax production validation. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Scoped capture restores thread state on all exits; second-item cancellation/unexpected/binary-error categories propagate and later calls recover. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Captures are thread-local and reentrant; per-target depth excludes nested provider probes. Public member graphs must be configured before concurrent use, documented in design. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed capture classes/hashdecls and optional identities; restored metadata checks provider identity, union flag type, mandatory items and mutually exclusive descriptors. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | One capture per actual item, linear ordered identity construction, shared-graph traversal caches reused. 28-level diamond tests bound terminal invocation counts. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Empty lists, omitted/whitespace/nested items, restricted item/list members, metadata corruption, cycles and failure cleanup covered. Error categories are asserted. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | New public metadata field is documented; existing conversion API contracts retained. Design, examples, release notes, README, adjudication and execution evidence updated; docs/qjar build passes. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP changes. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No credentials, format strings or raw memory operations; metadata/index accesses validated and cyclic graphs rejected. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Independent ordered primitive-family/Decimal assertions and pinned validators cover real SOAP 1.1/1.2 bindings, both directions, schema/provider reconstruction and examples; no source fixture modified. |
