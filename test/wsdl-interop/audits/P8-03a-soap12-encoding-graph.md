# P8-03a SOAP 1.2 encoding graph audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied `/home/david/.claude/skills/audit-changes/SKILL.md` to the uncommitted P8-03a changes on main `develop`
based on 97e8b19. Scope: `qlib/WSDL.qm` (encoding constants and rule selection, the SOAP 1.2 reference context,
getValue, struct member matching, array text keys and serialization styles), `qlib/SoapHandler.qm` (fault codes
and subcodes), `test/soap12-encoding.qtest`, `test/wsdl-interop/encoded-corpus/w3c-soap12.wsdl`,
`design/soap-encoding.md`, and PLAN.md and EXECUTION.md.

All 62 checks are explicitly accounted for:

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | External module repository. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL v0.5.8 and SoapHandler 0.3.4 release notes describe SOAP 1.2 Encoding, the references, nodeType, DataEncodingUnknown, struct member order, array whitespace and the fault options. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No module added. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No module added. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No module added. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | Both modules keep their %modern directive. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No .qc changed. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include usage. |
| 9 | Copyright 2026 on all new files | Pass | test/soap12-encoding.qtest, encoded-corpus/w3c-soap12.wsdl and this record carry the 2026 copyright. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No module added. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No module added. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No C++ or QPP change; the changes are Qore module code in qlib/WSDL.qm and qlib/SoapHandler.qm, and tests. |
| 13 | `%modern` directive present | Pass | The new suite uses %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | The new suite is executable. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The new suite uses %prepend-module-path before relative %requires of WSDL.qm and SoapHandler.qm. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | json uses the %try-module pattern with an explicit MISSING-MODULE failure; QUnit, xml and HttpServer are delivered with Qore and this repository. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ or QPP change; the changes are Qore module code in qlib/WSDL.qm and qlib/SoapHandler.qm, and tests. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ or QPP change; the changes are Qore module code in qlib/WSDL.qm and qlib/SoapHandler.qm, and tests. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ or QPP change; the changes are Qore module code in qlib/WSDL.qm and qlib/SoapHandler.qm, and tests. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | No I/O added to the modules. The suite reads its corpus with ReadOnlyFile and uses HttpServer and HTTPClient on 127.0.0.1 only. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ or QPP change; the changes are Qore module code in qlib/WSDL.qm and qlib/SoapHandler.qm, and tests. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ or QPP change; the changes are Qore module code in qlib/WSDL.qm and qlib/SoapHandler.qm, and tests. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ or QPP change; the changes are Qore module code in qlib/WSDL.qm and qlib/SoapHandler.qm, and tests. |
| 24 | No blocking operations without cancellation support | N/A | No C++ or QPP change; the changes are Qore module code in qlib/WSDL.qm and qlib/SoapHandler.qm, and tests. |
| 25 | Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No DataProvider, factory, application registration or JNI change. |
| 26 | Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No DataProvider, factory, application registration or JNI change. |
| 27 | Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No DataProvider, factory, application registration or JNI change. |
| 28 | DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DataProvider, factory, application registration or JNI change. |
| 29 | DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No DataProvider, factory, application registration or JNI change. |
| 30 | Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No DataProvider, factory, application registration or JNI change. |
| 31 | Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No DataProvider, factory, application registration or JNI change. |
| 32 | **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No DataProvider, factory, application registration or JNI change. |
| 33 | Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No DataProvider, factory, application registration or JNI change. |
| 34 | Response/output types use `private` Fields | N/A | No DataProvider, factory, application registration or JNI change. |
| 35 | Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No DataProvider, factory, application registration or JNI change. |
| 36 | Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No DataProvider, factory, application registration or JNI change. |
| 37 | Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No DataProvider, factory, application registration or JNI change. |
| 38 | Password/secret fields have `"sensitive": True` | N/A | No DataProvider, factory, application registration or JNI change. |
| 39 | `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No DataProvider, factory, application registration or JNI change. |
| 40 | App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No DataProvider, factory, application registration or JNI change. |
| 41 | App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No DataProvider, factory, application registration or JNI change. |
| 42 | `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No DataProvider, factory, application registration or JNI change. |
| 43 | `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No DataProvider, factory, application registration or JNI change. |
| 44 | `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No DataProvider, factory, application registration or JNI change. |
| 45 | Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No DataProvider, factory, application registration or JNI change. |
| 46 | No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No DataProvider, factory, application registration or JNI change. |
| 47 | No bare field/option names in prose — must use backticks | N/A | No DataProvider, factory, application registration or JNI change. |
| 48 | Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No DataProvider, factory, application registration or JNI change. |
| 49 | **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No DataProvider, factory, application registration or JNI change. |
| 50 | **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No DataProvider, factory, application registration or JNI change. |
| 51 | **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No DataProvider, factory, application registration or JNI change. |
| 52 | JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No DataProvider, factory, application registration or JNI change. |
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Each defect is fixed at its root: rule selection replaces the hard-coded URI, the reference context replaces SOAP 1.1-only handling, struct matching follows the encoding data model, and array text keys follow the parser's numbering. SOAP 1.2 arrays are the next increment by plan; nothing is stubbed. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Reference, identifier, nodeType and encoding-style errors raise SOAP-DESERIALIZATION-ERROR before any value is converted. The fault options are typed; the handler casts them only after an instanceof check. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | No shared mutable state: the reference context is per message, and the struct reordering is local to one conversion. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed hash<SoapFaultOptions> arguments, typed code<*list<XsdParticle>(list<string>)> and comparator closures, and typed references in the walk. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | The envelope walk runs once per SOAP 1.2-encoded message. Struct reordering runs only after an ordered match fails and is O(n log n) in the member count. The full suite ran at its previous cost (392 parallel targets in 952 s). |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Each failure names the identifier, attribute value or style concerned and carries the SOAP 1.2 code or subcode the spec defines. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | design/soap-encoding.md (encoding style, structs, SOAP 1.2 Encoding, faults, array text), the module docs of both modules and their release notes, the contract's comment, and the PLAN.md and EXECUTION.md entries. Docs build with no warnings. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP change. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No credentials; constant format strings; loopback listeners only. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | The W3C collection's own messages drive the tests. All six cases fail against HEAD's modules. The full suite fails only on the three core-blocked gates. |

Result: **18 Pass / 44 N/A / zero Fail**.
