# P5-05 native selected-type provider audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Audited 2026-09-11 against parent `f41e327`, using the complete
`/home/david/.codex/skills/audit-changes/SKILL.md` and its referenced module,
sandbox, cancellation and provider design guides. All 62 individual items are
recorded below: **27 Pass, 35 N/A, 0 Fail**.

The change adds explicit schema/message provider factories that retain native
selected types. It includes recursive/restored graphs, finite choices, native
and wrapper metadata, examples, unit and HTTP regressions, an independent
matrix, release notes and durable design. There are no C++ or dependency edits.
The [inventory](../P5-05-validation.json) records source, fixture, artifact and
log hashes, all commands and the original W3C reproducer.

Final verification passes 118 Qore suites, 1203 cases and 58850 reported
assertions. The new unit suite passes 15 cases/521 assertions, and the HTTP
suite passes 1 case/64 assertions and 12 loopback calls, in all four source
modes and AOT. The independent matrix requires 336 rejecting rows and validates
1008 outputs per mode. Original W3C type substitution retains exact values and
Part2 in 8 actual-binding/direction/copy rows. Compiled Cargo and CDA consumers,
module builds, WSDL docs, the invoice example and supplements pass without
warnings. Three caught legacy SOAP comparator negatives are intentional within
their successful suite.

Audit fixes include restoring provider indexes by component identity, retaining
QName choice context, rejecting malformed metadata and anonymous nonidentity
selections, and producing valid abstract/anonymous type metadata examples.
The initial Cargo AOT package omitted bundled schema assets; the corrected
harness stages the existing qmod and unchanged module assets together. No
constructor override or validation skip replaces those tests.

The isolated both-version corpus retains all prior results except the WSDL
digest: 142 selected descriptions/1376 directions pass, with all 68 broader
failures visible. Explicit capture evidence does not replace the default native
projection diagnostic. P5 content semantics and the full P6-P9 scope remain
open. Both remotes were fetched and included; main Qore is at `1c63ff2c5` with unrelated Azure/OpenAPI work in progress.
No push or installation occurred. Native XML/libqore hashes are unchanged;
Qore-only changes do not require a new Valgrind run. PCRE2 JIT remains enabled.

| Item | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | Existing external WSDL module; no Qore catalog module is added. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 release notes document explicit native provider factories, restored graphs, choices and concrete abstract-type examples. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module or build target. Existing WSDL and dependent provider qmod targets are built and exercised. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No new module or build target. Existing WSDL and dependent provider qmod targets are built and exercised. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | The existing lowercase wsdlintro remains the first module section. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL and both new qtests and the matrix worker use %modern without redundant directives. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated qc file is changed. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include or alternate module entry point is introduced. |
| 9 | Copyright 2026 on all new files | Pass | New qtests, worker, Python matrix, evidence and audit carry Copyright 2026; the JSON inventory records it. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | Existing single-file WSDL module layout is unchanged; no duplicate qm file. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | Existing single-file WSDL module layout is unchanged; no duplicate qm file. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No QPP class is added. |
| 13 | `%modern` directive present | Pass | Both new qtests and the qr worker explicitly use %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | Both qtests, the qr worker and Python matrix have executable permissions. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Qore tests prepend local qlib before requires and use relative WSDL/SoapClient/SoapHandler paths. AOT copies explicitly import compiled qmods. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project xml and Qore QUnit/HttpServer are hard requirements; external json uses %try-module and an explicit dependency error. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ or new native filesystem/network operation. Native XML and isolated libqore hashes are unchanged. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ or new native filesystem/network operation. Native XML and isolated libqore hashes are unchanged. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ or new native filesystem/network operation. Native XML and isolated libqore hashes are unchanged. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production provider conversion adds no I/O. Workers read explicit fixture manifests; HTTP tests use bounded loopback calls and deterministic listener readiness. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ loops or cancellation API changes. Qore statements retain runtime interruption checks. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ loops or cancellation API changes. Qore statements retain runtime interruption checks. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ loops or cancellation API changes. Qore statements retain runtime interruption checks. |
| 24 | No blocking operations without cancellation support | Pass | No blocking production operation is added. Tests use queues, counters and on_exit cleanup with bounded deadlines; workers rethrow cancellation. |
| 25 | Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No action or application registration, request dispatch, search options or scheme mapping changes. |
| 26 | Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No action or application registration, request dispatch, search options or scheme mapping changes. |
| 27 | Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No action or application registration, request dispatch, search options or scheme mapping changes. |
| 28 | DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No action or application registration, request dispatch, search options or scheme mapping changes. |
| 29 | DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No action or application registration, request dispatch, search options or scheme mapping changes. |
| 30 | Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No action or application registration, request dispatch, search options or scheme mapping changes. |
| 31 | Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No field-map hash slice is introduced. |
| 32 | **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | These are arbitrary-schema provider adapters, not fixed application request/response schemas with static Fields constants. XsdMessageDataType retains its typed HashDataType interface. |
| 33 | Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | These are arbitrary-schema provider adapters, not fixed application request/response schemas with static Fields constants. XsdMessageDataType retains its typed HashDataType interface. |
| 34 | Response/output types use `private` Fields | N/A | These are arbitrary-schema provider adapters, not fixed application request/response schemas with static Fields constants. XsdMessageDataType retains its typed HashDataType interface. |
| 35 | Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | Pass | New wrapper metadata fields have display_name, typed providers and descriptions. Existing schema-derived field identities and labels are retained. |
| 36 | Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | Pass | The selected-type field has a QName example. Abstract declarations use a permitted concrete type and matching value; examples and their metadata are asserted. |
| 37 | Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | Pass | Native fields retain existing AllowedValueInfo entries and display labels. Numeric, QName, binary and list choice tests cover metadata, equivalence and edits without dropping wrappers. |
| 38 | Password/secret fields have `"sensitive": True` | N/A | No password or secret field is added. |
| 39 | `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No application catalog entry, group, logo or application display name changes. |
| 40 | App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No application catalog entry, group, logo or application display name changes. |
| 41 | App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No application catalog entry, group, logo or application display name changes. |
| 42 | `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No application catalog entry, group, logo or application display name changes. |
| 43 | `short_desc` is plain text, under 80 chars, single sentence — no markdown | Pass | New short field summaries are generated by the existing QoreDataField description helper; explicit provider descriptions are separate from short labels. |
| 44 | `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | Pass | Descriptions use backticks for wrapper keys and method references, and explain retaining derived message fields when storing or forwarding data. No bare boolean or NOTHING value is introduced in desc strings. |
| 45 | Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | Pass | Descriptions use backticks for wrapper keys and method references, and explain retaining derived message fields when storing or forwarding data. No bare boolean or NOTHING value is introduced in desc strings. |
| 46 | No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | Pass | Descriptions use backticks for wrapper keys and method references, and explain retaining derived message fields when storing or forwarding data. No bare boolean or NOTHING value is introduced in desc strings. |
| 47 | No bare field/option names in prose — must use backticks | Pass | Descriptions use backticks for wrapper keys and method references, and explain retaining derived message fields when storing or forwarding data. No bare boolean or NOTHING value is introduced in desc strings. |
| 48 | Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | New description strings are shorter than 500 characters. |
| 49 | **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No factory, record-provider signature or cross-repository registration changes. |
| 50 | **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No factory, record-provider signature or cross-repository registration changes. |
| 51 | **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No JNI dependency or JAR installation changes. |
| 52 | JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No JNI dependency or JAR installation changes. |
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Selection resolves against the receiving schema and validates native fields and XML instance constraints. Recursive definitions are indexed before traversal; restored indexes use restored identities. No fixture special cases, round-trip conversion, skips or validation bypasses. The Cargo AOT harness stages the actual module assets rather than changing constructor options or validation. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Provider construction, type lookup and QName output use scoped thread-local restoration. Copy-on-write values and copied field comparators preserve caller state. Controlled errors and cancellation propagate; malformed saved graphs reject before use. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Factories finish named definitions and soft variants before publication. Validation only reads the graph; on-demand canonical scalar adapters remain private. Concurrent reconstructed-provider tests use barriers. Documentation requires caller metadata edits to finish before concurrent validation. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed component and definition maps, provider classes and DataTypeInfo results constrain graph operations. Polymorphic XML values use auto intentionally. HTTP callbacks declare code<auto(hash<auto>, auto)>. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Construction caches each definition before descending into nested elements; recursive graphs terminate. Restored indexes are rebuilt in one pass, followed by hash lookup. Unused builtin adapters are not eagerly added. Native and soft graphs are shared and field edits use copy-on-write. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Tests cover missing globals, incompatible/unknown selections, malformed wrappers and saved state, required fields, changed receiver content, finite choices, nil wrappers, type variants, copies, cancellation and deterministic concurrent use. The independent matrix requires 336 rejecting rows per conversion path in every mode. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public factories, provider methods and serialized graph metadata document their parameters, returns, failures and ownership. The durable contract and executed invoice example cover provider storage and forwarding. Abstract wrapper examples and anonymous declarations were corrected during audit; final unit/mode checks verify concrete examples and resolved anonymous component identity. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP flags change. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Diagnostics use fixed format strings. Schema lookups and wrapper shapes are checked before use. No credentials or new production external access. Temporary module packages contain the existing compiled modules and unchanged bundled assets. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Final Qore gate, source/AOT unit and HTTP checks, independent type matrix, original W3C case, affected provider consumers and both-version corpus evidence are recorded in P5-05-validation.json. The default diagnostic corpus remains separate from explicit capture coverage. |
