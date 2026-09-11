# P5-02 type final audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Audited 2026-09-11 against parent `d223ed4`, using the complete
`/home/david/.codex/skills/audit-changes/SKILL.md` and its referenced module
structure, sandbox, cancellation and provider design guides. All 62 individual
items resolve: **22 Pass, 40 N/A, 0 Fail**.

The change covers WSDL construction metadata/resolution, the native dependency's
anonymous-type defaults, configure behavior detection, tests and evidence. It
adds no QPP class or provider action. The [validation inventory](../P5-02-validation.json)
records exact source/artifact/fixture/log hashes and commands. The
[implemented design](../../../design/wsdl-type-final.md) and
[specification adjudications](../type-final-evidence.md) explain the corrected
semantics and independent-validator disagreements.

Final verification includes 114 Qore suites (1157 cases/57498 reported assertions),
34 provider tests, the 87-schema matrix in all five execution modes, AOT and
warning-free affected documentation, and the isolated both-version corpus.
Native probe, native final suite and reader cancellation/lifecycle suite have
zero Valgrind errors and no lost blocks. PCRE2 JIT is disabled only for Valgrind.
The final corpus changes only the recorded WSDL version digest: 142 selected
WSDLs/1376 directions have no failure and 68 broader findings remain unchanged.
The three caught legacy SOAP comparator negatives remain intentional; the
corrected supplementary runner filename is recorded separately from passes.

P5 remains open for instance block/abstract, full dynamic derivation,
substitution, content and identity requirements. No work is removed from P6-P9.
No push or installation was performed. Both develop remotes were fetched and
already included; main Qore remains clean at `1c63ff2c5`.

| Item | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | Existing external module; no Qore catalog entry changes. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 and XML 2.3.0 release notes cover type final exclusions, source defaults and corrected native provider selection. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | Existing WSDL module build registration retained. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No module target added. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | Existing lowercase wsdlintro remains first. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | Existing WSDL and new Qore tests use %modern without redundant parse directives. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated qc edits. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include or separated-module layout change is introduced. |
| 9 | Copyright 2026 on all new files | Pass | All new authored CMake, C probe, Qore/Python test, worker, design and evidence files carry Copyright 2026. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | Existing single-file module layout retained. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No duplicate module. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No QPP class. |
| 13 | `%modern` directive present | Pass | Both qtest suites and the qr integration worker declare %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | Both qtest files, the qr worker and the Python matrix have executable mode 0755. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Qore tests prepend local qlib before requires; WSDL uses relative source requirements. Explicit AOT copies require the tested compiled qmod. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project xml and Qore QUnit are hard requirements. External json uses %try-module with an explicit missing-module failure. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | Pass | The native correction only initializes three component flags; its probe operates on in-memory schemas. No runtime filesystem access is introduced. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | Pass | No native network operations are introduced. The source archive remains pinned and CMake retains TLS/hash verification. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No native filesystem or network operation requires a new sandbox helper. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production Qore changes perform no I/O. The integration worker reads its explicit fixture manifest with ReadOnlyFile; Python uses isolated temporary paths and bounded subprocesses. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | Pass | The native correction has no loop. The new standalone C probe has exactly 3 by 4 cases; no introduced native loop can exceed 100 iterations. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No native cancellation API is changed or needed for three flag assignments. No deprecated cancellation API is introduced. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No new unbounded native iteration; the standalone behavior probe has 12 bounded cases. |
| 24 | No blocking operations without cancellation support | Pass | No new blocking production operation. Tests use queue/counter completion and bounded subprocess deadlines; native reader cancellation and cleanup regressions pass under Valgrind. |
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
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Final construction properties are retained and enforced without production fixture names or validation exceptions. XSD 1.0 normative mappings adjudicate oracle disagreements. Remaining P5 instance/element controls retain explicit plan ownership. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Qore scope exits restore source defaults, constructor metadata is owned and copied, and failed schema addition/replacement permits reuse. The native correction allocates nothing. Native probe, native unit and reader cancellation/lifecycle suites have zero Valgrind errors and zero lost blocks. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Type final sets are immutable after construction and returned by value. Source defaults restore on every exit. Concurrent serialized copies and independent consumers verify unchanged shared metadata. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | New public XsdDerivationMethod enum, typed hash<string,bool> sets and XsdAbstractType parameters avoid untyped controls. Native flags use existing integer representations; C probe pointers, bounds and snprintf results are checked. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Final membership checks are constant size. Source token parsing is linear. Existing resolved union graphs are reused without expanding repeated dependency paths; no new graph search or conversion retry. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Explicit/empty/default controls, invalid methods and whitespace, prohibited derivations, anonymous forms, schema scopes and failed reuse are tested. The final matrix requires exact WSDL-ERROR and XSD-SYNTAX-ERROR results for 86 invalid binding descriptions. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | New metadata methods and affected constructors document inputs/results and caveats. Durable design, executed invoice example, root/interoperability READMEs and both release notes are updated; affected docs build without warnings. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP flags changed. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Constant format strings and bounded snprintf output; checked parser/schema allocations and matching frees in the probe. No credentials or new runtime external I/O. Pinned input/output hashes reject unknown dependency sources. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | All 114 suites pass 1157 cases/57498 reported assertions. The final 87-schema matrix passes in AST, IR, JIT, tiered and AOT with 86 required construction errors and 352 independently validated outputs per mode. Both-version survey and isolated strict coverage preserve every prior result; 142 selected descriptions/1376 directions have no failure. Normative adjudications retain oracle disagreements as disagreements. |
