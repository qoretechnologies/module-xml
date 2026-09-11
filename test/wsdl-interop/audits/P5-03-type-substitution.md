# P5-03 instance type substitution audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Audited 2026-09-11 against parent `460349d`, using the complete
`/home/david/.codex/skills/audit-changes/SKILL.md` and its referenced module
structure, sandbox, cancellation and provider design guides. Every individual
item is recorded below: **19 Pass, 43 N/A, 0 Fail**.

The change covers WSDL instance derivation, block/abstract metadata and QName
selection, Qore/Python regressions and documentation. It adds no C++ source,
provider registration or native dependency change. The [validation inventory](../P5-03-validation.json)
records source/artifact/fixture/log hashes and reproducible commands. The
[design](../../../design/wsdl-type-substitution.md) and
[specification evidence](../type-substitution-evidence.md) explain the algorithms
and the root causes of the development failures.

Final verification passes 115 Qore suites (1170 cases/57779 reported assertions),
all four source execution modes, compiled WSDL, the independent matrix and
supplementary consumer/oracle tests. The AOT and affected documentation builds
and executed invoice example pass without warnings. Native XML/libqore hashes
are unchanged; this Qore-only increment requires no new Valgrind run. Ordinary
PCRE2 JIT remains enabled. Three caught legacy SOAP comparator negatives are
intentional within their successful suite, not new failed tests.

The isolated both-version corpus retains every previous result: only its WSDL
version digest changes. All 142 selected descriptions/1376 directions pass;
all 68 broader failures remain visible. Native selected-type retention,
substitution groups, content/nil/identity and P6-P9 requirements remain open.
Both develop remotes were fetched and already included. Main Qore is clean at
`1c63ff2c5`. No push or installation was performed.

| Item | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | Existing external module; no Qore catalog entry changes. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 release notes cover full instance derivation, block/abstract metadata and detached type QName context. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | Existing WSDL module build registration retained. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No module target added. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | Existing lowercase wsdlintro remains first. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | Existing WSDL and new Qore tests use %modern without redundant parse directives. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated qc edits. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include or separated-module layout change is introduced. |
| 9 | Copyright 2026 on all new files | Pass | New Qore/Python tests, worker, design and evidence files carry Copyright 2026; the inventory carries its copyright field. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | Existing single-file module layout retained. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No duplicate module. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No QPP class. |
| 13 | `%modern` directive present | Pass | New qtest and qr worker use %modern; affected existing suites retain it. |
| 14 | Executable permission set (`chmod +x`) | Pass | New qtest, qr worker and Python matrix are executable (0755); affected existing qtests remain executable. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Qore tests prepend local qlib before requires; WSDL uses relative source requirements. Explicit AOT copies require the tested compiled qmod. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project xml and Qore QUnit are hard requirements. External json uses %try-module with an explicit missing-module failure. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ changes; the native XML and libqore hashes remain unchanged. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ or dependency-selection changes. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No native filesystem or network operation requires a new sandbox helper. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production Qore changes perform no I/O. The integration worker reads its explicit fixture manifest with ReadOnlyFile; Python uses isolated temporary paths and bounded subprocesses. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ changes. Qore loop statements already provide runtime cancellation points. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No native cancellation API or deprecated check is introduced. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No new C++ iteration; Qore runtime checks its loop cancellation points. |
| 24 | No blocking operations without cancellation support | Pass | No new blocking production operation. Tests use queue barriers and bounded counter completion; subprocesses have deadlines and workers rethrow cancellation. |
| 25 | Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 26 | Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 27 | Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 28 | DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 29 | DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 30 | Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 31 | Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 32 | **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 33 | Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 34 | Response/output types use `private` Fields | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 35 | Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 36 | Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 37 | Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 38 | Password/secret fields have `"sensitive": True` | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 39 | `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 40 | App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 41 | App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 42 | `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 43 | `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 44 | `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 45 | Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 46 | No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 47 | No bare field/option names in prose — must use backticks | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 48 | Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 49 | **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 50 | **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 51 | **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 52 | JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No provider actions, application registrations, typed provider classes, factories, presentation catalogs or JNI dependencies change. |
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Resolved derivation, effective block and abstract checks replace identity/immediate-only checks. No fixture names, validation bypass or guessed wire prefix is introduced. Remaining P5 content, substitution-group and native retention requirements stay explicitly open. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Scope exits restore source defaults and instance QName context. Selection mutates only a private value, validates optional lookup before assigning a required type, and guards non-hash metadata. Failed construction/conversion reuse and existing cancellation tests pass. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Traversal caches and worklists are local. Control metadata is immutable after construction and returned by value. Builtin selection owns a separate output registry. Queue-synchronized concurrent consumers and serialized schema copies preserve shared metadata. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | XsdSubstitutionMethod enum, typed method sets, XsdTypeSubstitutionPair hashdecl, typed references and typed component/cache lists constrain traversal. Optional selected-type lookup is validated before nonoptional assignment. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Identity is constant-time; reachable pairs are deduplicated on enqueue and base restriction chains cache union members, including absence. No recursive expansion of shared union paths. Tests cover 1000-step complex/unrelated simple chains, 10000 duplicate members and 40 shared union levels. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Malformed/misplaced/empty/default controls, unbound and unknown QNames, forbidden paths, abstract instances, optional absence and selected facets have exact error-category regressions. The matrix requires 336 rejecting rows in each conversion path. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public enum/getters and affected constructors document parameters, returns and failures. Durable design, executed invoice example, release notes, plan/README and specification evidence are updated. WSDL/module docs compile without warnings. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP flags changed. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Diagnostic format strings are constant, QName input is validated before lookup, and worker I/O is limited to its explicit manifest. Typed graph traversal is bounded; no credentials or new runtime external access. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 115 suites pass 1170 cases/57779 reported assertions. The 104-case matrix passes in AST, IR, JIT, tiered and compiled WSDL, with 336 required rejections and 992 independently validated outputs per mode. Both-version corpus results are unchanged except the WSDL digest: 142 selected descriptions/1376 directions have no failure; all 68 broader failures remain visible. |
