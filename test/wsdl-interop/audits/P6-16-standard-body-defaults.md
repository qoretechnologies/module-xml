# P6-16 standard body defaults and binding-pattern audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied `/home/david/.codex/skills/audit-changes/SKILL.md` to WSDL, SoapDataProvider,
regression fixtures/tests and documentation. Reviewed module structure,
sandboxing, cancellation and the DataProvider checklist/development guide.
No C++ or DGC implementation changed.

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module or build registration. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | N/A | No new module or build registration. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module or build registration. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No new module or build registration. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | WSDL and SoapDataProvider retain their lowercase introduction sections. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | Both module entries use %modern. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | Pass | SoapRequestDataProvider.qc contains no parse directives. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include added. |
| 9 | Copyright 2026 on all new files | Pass | New tests and design/evidence files carry 2026 copyright. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | Pass | SoapDataProvider retains its separated-module directory layout. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | Pass | No duplicate module entry. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 13 | `%modern` directive present | Pass | All changed Qore tests use %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | All changed/new qtests are executable. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Tests prepend local qlib before requiring repository modules by relative path. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Core dependencies and this repository’s xml module use hard requires; no new external module. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | No new production I/O. Tests use repository fixtures and bounded loopback HTTP with Queue completion and on_exit cleanup. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 24 | No blocking operations without cancellation support | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 25 | Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 26 | Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 27 | Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 28 | DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | Pass | Existing SoapRequestDataProvider advertises supports_request and implements doRequestImpl; the new data-dependent request type retains that path. |
| 29 | DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 30 | Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 31 | Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 32 | **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | Pass | The envelope uses HashDataType with schema-derived XsdMessageDataType body fields. Types depend on each WSDL operation, so a single exported static type constant cannot represent this contract. |
| 33 | Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 34 | Response/output types use `private` Fields | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 35 | Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | Pass | Both envelope fields have display_name, type and desc. |
| 36 | Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 37 | Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 38 | Password/secret fields have `"sensitive": True` | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 39 | `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 40 | App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 41 | App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 42 | `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 43 | `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 44 | `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | Pass | New field descriptions are concise Markdown-compatible prose without code literals. |
| 45 | Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | Pass | Descriptions explain Body and Header values to send. |
| 46 | No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 47 | No bare field/option names in prose — must use backticks | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 48 | Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 49 | **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 50 | **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | Pass | The existing record-type method retains the prescribed hash<string, AbstractDataField> signature. |
| 51 | **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 52 | JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No action/application registration, static field catalog, finite values, secret fields, factory or JNI packaging changes. |
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Default selection follows WSDL 1.1. Explicit maps fix overwrite and serializer lookup precedence at their causes. Unsupported concrete patterns reject before publication. HTTP argument errors validate at the URI serializer; the separate Mime root cause is fixed in Qore ac5cfb171. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Validation precedes binding-map mutation. Native serialization modifies local values; per-call provider descriptors do not change shared schema. Server cleanup runs on every exit. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Binding metadata is constructed before publication; decoding and envelope type construction use local maps. No new global mutable state. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Pattern checks use WsdlOperationPattern; selections remain typed string lists; HTTP callbacks have explicit parameter and return types. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Overlap checks use hash membership, linear in body parts. Pattern checks are constant-time. Per-call envelope descriptors reuse the existing message schema construction contract. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Tests cover omitted/explicit selections, both SOAP styles and versions, both directions, malformed maps and conflicting headers, missing parts, nil/empty records, saved/imported graphs, manual bindings, HTTP clients/handlers/providers, and invalid URL argument types. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public serialization docs, module/native release notes and durable selection/header/pattern docs describe the final contract and examples. No DGC architecture changes. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++ changes; native sandboxing, cancellation and QPP checks do not apply. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No new unmanaged buffers, production I/O or credentials. All format strings are constant. Schema checks run before transport. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Focused standard-default and interaction-pattern regressions reproduce prior defects and pass. The final 164-suite gate passes 1647 cases / 82855 reported assertions; all 14 corpus commands have expected outcomes, with unchanged semantic results. |

All 62 checks: **27 Pass / 35 N/A / zero Fail**.

See [validation](../P6-16-validation.json) and [evidence](../standard-body-defaults-evidence.md).
