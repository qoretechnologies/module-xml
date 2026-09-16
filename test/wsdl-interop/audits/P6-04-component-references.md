# P6-04 component reference audit

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
| 9 | Copyright 2026 on all new files | Pass | New authored test, reference fixture JSON, independent Python test, design and evidence carry 2026 copyright. The pinned upstream WSDL schema is unchanged. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, QPP class, registration or layout change. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, QPP class, registration or layout change. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, QPP class, registration or layout change. |
| 13 | `%modern` directive present | Pass | The new Qore suite uses %modern; Python is a separate unittest harness. |
| 14 | Executable permission set (`chmod +x`) | Pass | test/wsdl-declaration-identity.qtest has executable mode 0755. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Local qlib is prepended before the relative WSDL.qm require. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | The external json binary dependency uses %try-module with a precise MISSING-MODULE error. QUnit/HttpServer from core and xml/WSDL/SoapClient/SoapHandler delivered here use hard requires. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ code, native I/O or native cancellation loops changed. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ code, native I/O or native cancellation loops changed. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ code, native I/O or native cancellation loops changed. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production changes add no I/O. Tests read committed JSON through ReadOnlyFile and exchange messages with ephemeral local HTTP listeners; queues and clients have bounded deadlines, with on_exit server cleanup. |
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
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Expanded declaration identities and deferred reference resolution remove the local-name fallback before construction. Namespace scopes fix header prefix resolution. Whitespace is normalized in both declaration identity and the constructed namespace container. No silent skip, name rewriting workaround or stub is added. Imports and complete binding semantics remain explicit P6 work. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Reader, typed reference list and declaration maps are local to a construction call. Missing/malformed references reject before schema retrieval or object publication. NamespacePrefixHelper restores operation/input-output/header scope on all exits. Invalid cases are followed by valid parses and saved graph reconstruction. Existing cancellation/lifecycle suites pass. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Reference tables are construction-local. Existing namespace helpers restore nested input maps; published services retain the documented read-only-after-construction contract. No shared mutable cache or persistent reference-state object is added. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | WsdlComponentReference is a typed private hashdecl with kind, identity and origin strings. Declaration lookup uses hash<string,bool>; reader frames retain typed binding context. HTTP callback signatures and captured queues are typed. Missing optional strings are checked before lexical normalization. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | One ordered reader pass collects declarations and references; one linear reference pass uses hash lookups. There is no repeated global component scan. Namespace scoping uses the existing restoration mechanism. The separate previously documented Qore collector-cost investigation remains a P9 runtime concern and is not claimed fixed. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Wrong namespaces cannot borrow a same-local-name message/port type/binding. Missing targets reject even in empty bindings. Required attributes, malformed/unbound QNames, default/no namespace, local prefixes, forward references, separate symbol spaces, faults/headerfaults and whitespace have positive/negative tests. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Class documentation and module release notes describe expanded-name reference semantics. Durable design includes a scoped partner authorization header example and source retention. Evidence separates lexical schema validity from component resolution and broader P6 import/binding gaps. WSDL docs build without warnings/errors. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP methods or flags changed. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Fixed diagnostic formats, validated QNames, no credentials or new production I/O. Component references are validated before dependency retrieval. Source and reference fixtures are pinned, and independent tests fail on missing results. Local HTTP endpoints use bounded timeouts and deterministic cleanup. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | The focused suite passes 8 cases / 103 assertions including saved services and actual SOAP 1.1/1.2 HTTP exchanges. The shared 21-document matrix separates pinned Xerces lexical verdicts from independent expanded-reference inventory verdicts. Seven contract unit tests and affected SOAP/provider suites pass. Corpus comparisons and final large-description results are recorded in the validation inventory. |

All 62 checks: **18 Pass / 44 N/A / zero Fail**.
See [validation](../P6-04-validation.json) and [evidence](../component-references-evidence.md).
