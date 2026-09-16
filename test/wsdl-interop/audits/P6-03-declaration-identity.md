# P6-03 declaration identity audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied `/home/david/.codex/skills/audit-changes/SKILL.md` to the final increment.
All five previously read guides were verified byte-identical: `qore-module-structure.md`,
`module-sandboxing-audit-guide.md`, `cooperative-cancellation.md`,
`data-provider-checklist.md` and `data-provider-development-guide.md`.
No C++ changes; Valgrind is not required for this Qore-only increment.

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, QPP class, registration or layout change. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | N/A | No new module, QPP class, registration or layout change. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module, QPP class, registration or layout change. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, QPP class, registration or layout change. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | Existing WSDL module retains wsdlintro; no module registration change. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL.qm retains %modern; no redundant directives introduced. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, QPP class, registration or layout change. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include or separated module introduced. |
| 9 | Copyright 2026 on all new files | Pass | Authored Qore/Python tests, fixture JSON, design and evidence carry 2026 copyright. Vendored W3C schema retains its original notice. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, QPP class, registration or layout change. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, QPP class, registration or layout change. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, QPP class, registration or layout change. |
| 13 | `%modern` directive present | Pass | The new Qore suite uses %modern; Python is a separate unittest harness. |
| 14 | Executable permission set (`chmod +x`) | Pass | test/wsdl-declaration-identity.qtest has executable mode 0755. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Local qlib is prepended before the relative WSDL.qm require. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Hard requires are QUnit from core and xml/WSDL delivered by this repository; no new external binary dependency. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ code, native I/O or native cancellation loops changed. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ code, native I/O or native cancellation loops changed. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ code, native I/O or native cancellation loops changed. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production validation reads the supplied XML string; no new filesystem/network access. Independent tests use committed fixtures and existing pinned offline Xerces support. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ code, native I/O or native cancellation loops changed. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ code, native I/O or native cancellation loops changed. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ code, native I/O or native cancellation loops changed. |
| 24 | No blocking operations without cancellation support | N/A | No C++ code, native I/O or native cancellation loops changed. |
| 25 | Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 26 | Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 27 | Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 28 | DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 29 | DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 30 | Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 31 | Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 32 | **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 33 | Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 34 | Response/output types use `private` Fields | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 35 | Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 36 | Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 37 | Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 38 | Password/secret fields have `"sensitive": True` | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 39 | `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 40 | App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 41 | App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 42 | `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 43 | `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 44 | `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 45 | Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 46 | No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 47 | No bare field/option names in prose — must use backticks | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 48 | Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 49 | **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 50 | **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 51 | **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 52 | JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No DataProvider action, app, field metadata, factory or JNI packaging changes. |
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Invalid roots and duplicate declarations are rejected before grouping overwrites identity. Empty maps are initialized at construction. This bounded increment completes declaration identity; imports, QName references and operation signatures remain explicit subsequent P6 requirements, with no stub or bypass added. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Reader and frame objects are scoped to validation; exceptions abandon only the current graph. Duplicate/invalid-name failures followed by valid parses succeed. Saved graph reconstruction revalidates retained source. Existing cancellation/lifecycle suites pass. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Name sets belong to one validation invocation and are never shared. Parsed service maps are published during construction and retain the existing read-only-after-construction contract. No global mutable cache added. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Frames have string kind and hash<string,bool> names; the depth map stores WsdlDeclarationFrame objects. Optional name values are checked before normalization. ServiceInfo/PortTypeInfo keep typed empty maps. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Single reader traversal and per-owner hash lookup avoid repeated scans. Mutable frame objects avoid copying growing nested name hashes. The complete enterprise/partner test passes with parent/current 738.264/739.238 seconds. The initial 600-second diagnostic timeout remains recorded; collector cost is routed to the separate Qore investigation, not hidden or claimed fixed. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Wrong root namespaces, missing/invalid NCNames, duplicates, alias/whitespace collisions, independent owner scopes and empty components have positive/negative checks with WSDL-ERROR. Operation names remain eligible for legal overloads; signature resolution is a separate P6 requirement. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Class documentation, release notes, durable design with an inventory example, exact fixture provenance and runnable evidence are included. The WSDL documentation target completes without warnings/errors. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP methods or flags changed. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Fixed diagnostic format strings, local reader state, no credentials or new resource retrieval. Names are validated with the existing XML NCName lexical helper. No unchecked native storage introduced. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Nine focused Qore cases cover names/root/duplicates/scopes/saved empty graphs. Twenty-five pinned WSDL schema cases independently verify validity. Thirty-one affected suites, the complete enterprise/partner case, and both-version native/legacy corpus reports preserve prior results. Broader WSDL grammar/import/binding semantics are not claimed complete. |

All 62 checks: **18 Pass / 44 N/A / zero Fail**.
See [validation](../P6-03-validation.json) and [evidence](../declaration-identity-evidence.md).
