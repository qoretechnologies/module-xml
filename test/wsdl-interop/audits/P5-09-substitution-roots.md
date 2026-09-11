# P5-09 audit: selected complete-element roots

Copyright (C) 2026 Qore Technologies, s.r.o.

Audited the final changes from `3e122cf` using the full audit-changes skill and its five referenced guides. The production change is in the existing WSDL Qore module; tests, design and evidence accompany it. No C++ or registration changes.

All 62 items are recorded below. Evidence and exact tested source/runtime hashes are in [P5-09-validation.json](../P5-09-validation.json). Temporary acceptance runner source is embedded there for replay.

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | External module repository; no Qore module catalog entry is added. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL v0.5.8 release notes describe selected roots, providers, samples, part ownership and schema reconstruction. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | The existing WSDL module registration is unchanged; six existing module targets build. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No new module or QMOD-list entry. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | Existing WSDL introduction and module identity are unchanged. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL retains %modern; no redundant parse directives are introduced. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated qc file changes. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include or alternate module entry point is introduced. |
| 9 | Copyright 2026 on all new files | Pass | New Qore/Python tests, design, evidence, audit and JSON inventory carry Copyright 2026. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | The existing single-file WSDL module layout is unchanged. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No duplicate module entry point is introduced. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No QPP class is added. |
| 13 | `%modern` directive present | Pass | Both qtests and the qr worker explicitly use %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | Both qtests, the qr worker and Python matrix are executable (0755). |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Qore tests prepend local qlib before requirements and use relative repository paths. Compiled supplements explicitly import built qmods. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project xml and core QUnit/HttpServer use hard requirements; external json uses %try-module and fails explicitly when missing. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ filesystem changes; native XML and libqore remain unchanged. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ network changes; native XML and libqore remain unchanged. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No new native filesystem or network operations. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production conversion adds no I/O. The worker reads its explicit fixture manifest; bounded HTTP tests use loopback listeners and completion queues. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ loops change. Qore matching loops retain runtime cancellation checks, tested in all source modes. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No native cancellation API changes. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No native cancellation-check frequency changes. |
| 24 | No blocking operations without cancellation support | Pass | No blocking production operation is added. Test queues/counters and subprocesses have deadlines and deterministic cleanup; workers propagate cancellation. |
| 25 | Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No action registration changes. |
| 26 | Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No action option registration changes. |
| 27 | Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No action output registration changes. |
| 28 | DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DPAT_API action or dispatch implementation changes. |
| 29 | DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No find action or search-option changes. |
| 30 | Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No application scheme or class registration changes. |
| 31 | Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No Fields hash slice is added. |
| 32 | **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | Schema-driven providers have dynamic alternatives, not fixed application schemas. XsdElementDataType extends AbstractDataProviderType; existing XsdMessageDataType remains a HashDataType. |
| 33 | Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No static request Fields constant is introduced. |
| 34 | Response/output types use `private` Fields | N/A | No static response Fields constant is introduced. |
| 35 | Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | Pass | Selected Element and Value metadata provide display_name, typed providers and descriptions; union metadata is checked in unit and consumer tests. |
| 36 | Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | Pass | Each element selector supplies an exact QName example; concrete sample values pass provider and independent schema checks. |
| 37 | Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | Pass | Element choices use AllowedValueInfo with an XsdQNameValue and Element {URI}local display label. Existing finite native choices unwrap identity without losing it. |
| 38 | Password/secret fields have `"sensitive": True` | N/A | No password or secret fields. |
| 39 | `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No application groups. |
| 40 | App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No application logos. |
| 41 | App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No application catalog descriptions. |
| 42 | `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No application display names. |
| 43 | `short_desc` is plain text, under 80 chars, single sentence — no markdown | Pass | No explicit short_desc is added; field summaries use the existing QoreDataField helper and short human-readable labels. |
| 44 | `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | Pass | Provider descriptions quote wrapper keys and XsdQNameValue with backticks. Short field descriptions are complete sentences. |
| 45 | Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | Pass | Descriptions explain retaining concrete elements when storing or forwarding messages and checking required fields. |
| 46 | No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | Pass | No bare boolean or NOTHING API values occur in new desc strings. |
| 47 | No bare field/option names in prose — must use backticks | Pass | Wrapper keys and class names in provider prose use backticks. |
| 48 | Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | All new provider desc strings are below 500 characters. |
| 49 | **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No factory registration or cross-repository catalog change. |
| 50 | **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No getRecordTypeImpl signature changes. |
| 51 | **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No JNI dependency or JAR changes. |
| 52 | JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No JAR install rule changes. |
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | The fix resolves actual declarations and assigns complete unordered parts. No fixture-name branches, skipped regressions, validation bypasses or new TODO/FIXME/stubs. Remaining P5-P9 requirements remain explicit. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Scoped QName/type contexts restore after errors; matching uses local state; copy-on-write wrapper conversion preserves caller values. Schema replay restores base context on exceptions, and failed additions preserve message maps. Cancellation and failure/reuse tests pass. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Matching state is per call. Provider member maps snapshot construction-time alternatives; schema additions precede concurrent use. Two concurrent readers test conversion and metadata on one graph. Reconstruction and late-addition snapshots are exercised. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Component/provider maps, occurrence indexes and DataTypeInfo/AllowedValueInfo results are typed. Polymorphic XML values use auto intentionally. HTTP callbacks use code<auto(hash<auto>, auto)>. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Indexed expanded names build candidate edges. Iterative augmenting paths take O(P*E); alternating-cycle uniqueness uses O(P+N+E) work/storage. Tests cover all 27 three-occurrence combinations and a 64-part overlap chain without recursion. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Malformed selectors, extra keys, unknown/blocked/abstract roots, incompatible member values, missing/duplicate/ambiguous parts, unknown part APIs and failed schema additions have specific error assertions. Source modes and compiled HTTP consumers pass. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public selection/provider/part APIs document parameters, returns and errors. Durable design explains wrappers, part matching, snapshots and ownership, with an executed order-quantity example. WSDL Doxygen builds without warnings. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP methods or flags change. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Diagnostics use fixed format strings. Matcher indexes come from bounded input enumeration; selected names resolve in admitted maps. No credentials or production external access are added. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | The exact source passes the 123-suite gate, four source modes, compiled consumers, independent context/value matrix and both-version corpus. Required rejection, typed values and expanded names are checked; corpus failures remain visible. |

Result: {'N/A': 35, 'Pass': 27}. No audit failures remain.

Audit corrections include schema replay ordering, provider member snapshots, explicit empty part presence, header index zero handling, QName-aware independent witness construction and SOAP 1.2 actionless member routing. Final tests ran after these corrections. No workaround, skip or scope reduction was introduced.
