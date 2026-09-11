# P5-04 portable native type capture audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Audited 2026-09-11 against parent `c0b4633`, using the complete
`/home/david/.codex/skills/audit-changes/SKILL.md` and its referenced module
structure, sandbox, cancellation and provider design guides. All 62 individual
items are recorded below: **19 Pass, 43 N/A, 0 Fail**.

The change implements explicit native type capture in WSDL, SoapClient and
SoapHandler, with QName wrappers that resolve against receiving schemas.
Qore/Python regressions, API release notes, an executed example, durable design
and evidence accompany the change. It adds no C++, provider registration or
native dependency changes. The [inventory](../P5-04-validation.json) records
source/artifact/fixture/log hashes and reproducible commands.

Final verification passes 116 Qore suites (1187 cases/58265 reported assertions),
all four source modes and compiled versions of all three changed modules.
The 105-case independent matrix requires 336 rejecting rows and validates 1008
outputs per mode. The original W3C case additionally verifies exact derived
values and type identity in eight actual binding/direction/copy rows.
All affected documentation targets, the example and supplementary regressions
pass without warnings. Three caught legacy SOAP comparator negatives remain
intentional within their successful suite. Native XML/libqore hashes are
unchanged; no C++ edits require a new Valgrind run. Ordinary PCRE2 JIT is enabled.

The isolated both-version corpus preserves every previous result; only the WSDL
digest changes. All 142 selected descriptions/1376 directions pass, and all 68
broader failures remain visible. The original default projection still loses
selected types; explicit capture evidence does not replace that diagnostic.
Provider integration and the remaining P5-P9 requirements are open. An independent
operation handle lifetime defect is reduced against committed source and assigned
to P6; current consumers retain the service owner. Both remotes were fetched and
already included. Main Qore is clean at `1c63ff2c5`. No push or install occurred.

| Item | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | Existing external module; no Qore catalog entry changes. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8, SoapClient 1.0.4 and SoapHandler 0.3.4 release notes document explicit portable native type capture. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | Existing WSDL, SoapClient and SoapHandler module build registrations retained; all three AOT and documentation targets pass. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No module target added. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | Existing lowercase wsdlintro, soapclientintro and soaphandlerintro remain first. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | All three existing modules and the new Qore tests use %modern without redundant directives. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated qc edits. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include or separated-module layout change is introduced. |
| 9 | Copyright 2026 on all new files | Pass | New Qore/Python tests, worker, design, evidence, lifetime finding and audit carry Copyright 2026; the inventory has its copyright field. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | Existing single-file module layout retained. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No duplicate module. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No QPP class. |
| 13 | `%modern` directive present | Pass | New qtest and qr worker use %modern; affected existing suites retain it. |
| 14 | Executable permission set (`chmod +x`) | Pass | New qtest, qr worker and Python matrix are executable (0755); affected existing qtests remain executable. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Qore tests prepend local qlib before requires and use relative WSDL/SoapClient/SoapHandler source paths. AOT copies explicitly require all three compiled qmods. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project xml and Qore QUnit/HttpServer are hard requirements. External json uses %try-module with an explicit missing-module error. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ changes; the native XML and libqore hashes remain unchanged. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ or dependency-selection changes. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No native filesystem or network operation requires a new sandbox helper. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production conversion adds no I/O. SoapClient options are checked before existing HTTP dispatch. Tests read only explicit fixture manifests and use loopback listeners with deterministic readiness and bounded calls. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ changes. Qore loop statements already provide runtime cancellation points. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No native cancellation API or deprecated check is introduced. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No new C++ iteration; Qore runtime checks its loop cancellation points. |
| 24 | No blocking operations without cancellation support | Pass | No new blocking production operation. HTTP tests use listener readiness, queue results and on_exit server.stop(); concurrent tests use barriers and bounded counter completion. Worker subprocesses have deadlines and rethrow cancellation. |
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
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Portable QName wrappers resolve against receiver definitions and repeat existing validation; default return shapes stay compatible. Whole-root extraction, header flattening and incorrect wrapper acceptance in scalar-only contexts are fixed at their actual boundaries. No fixture exceptions or validation bypass. The independent pre-existing operation graph lifetime defect is reduced against c0b4633 and explicitly assigned to P6 under the execution prompt. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Optional output maps and capture flags are scoped and restored on all exits. Shared input is copy-on-write, optional type lookup is validated before required assignment, and metadata access checks hash type. Error reuse and cancellation tests pass. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Capture and output maps are thread-local with nested scope restoration. Schema maps are read by value and canonical builtin lookup uses a private registry. Queue-synchronized consumers preserve namespace state and independent capture choices. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed component maps and optional RAII scope objects constrain resolution; XsdQNameValue carries expanded names. HTTP callbacks use code<auto(hash<auto>, auto)> with an explicit auto-return closure. Polymorphic native values require auto. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Expanded-name lookup uses hash keys and identity is constant-time; derivation reuses the bounded component graph. Nested element calls allocate scopes only for explicit overrides. Values and maps use copy-on-write; no new unbounded traversal or quadratic scan. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Unknown/wrong-namespace types, changed receiver derivation/facets/block, extra/nested wrappers, invalid attribute/simple-content wrappers, custom builtin identity, nil/repeated values and conflicting client/handler options have exact error tests. Each matrix requires 336 decoding and manual-serialization rejection rows. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Changed public capture/map arguments document parameters, returns, failures and examples; client/handler options and mutual exclusion are documented. Durable design has an executed invoice example. All three module documentation targets pass without warnings. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP flags changed. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Diagnostics use constant format strings; expanded-name lookup validates selected values. No credentials or new production external access. Tests use only owned temporary manifests and loopback endpoints with deadlines. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 116 suites pass 1187 cases/58265 reported assertions. The 105-case matrix passes AST, IR, JIT, tiered and AOT with 840 rows, 336 required rejecting rows and 1008 independently valid outputs per mode. Original W3C type substitution passes 8 actual-binding/direction/copy rows with exact values/type and 24 outputs. Both-version diagnostic and strict corpus results are preserved, with all 68 broader failures visible. |
