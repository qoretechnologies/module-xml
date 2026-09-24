# P9a-06 non-anonymous response endpoints audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied `/home/david/.claude/skills/audit-changes/SKILL.md` to P9a-06 on `develop` based on 3c39aee. Scope: `WsaReceivedMessage`, `WsaReplyReceiver` and the receiver argument of `WsAddressingHelper::clientRequest()` in `qlib/WSDL.qm`; `setResponseEndpointAuthorizer()`, delivery and `SoapReplyHandler` in `qlib/SoapHandler.qm`; the `reply_receiver` option in `qlib/SoapClient.qm` and `qlib/SoapClientIo`; `test/soap-addressing-decoupled.qtest`; `design/soap-addressing.md`; and `EXECUTION.md`.

All 62 checks are explicitly accounted for:

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | External module repository. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | Release notes of WSDL v0.5.8, SoapHandler 0.3.4, SoapClient v1.0.4 and SoapClientIo v1.0 describe the non-anonymous response endpoints, WsaReplyReceiver, SoapReplyHandler and the reply_receiver option; the addressing sections of the three modules are updated. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No module added. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No module added. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No module added. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | The changed .qm files keep %modern. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | Pass | qlib/SoapClientIo/SoapClientIo.qc gains no parse directives. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include usage. |
| 9 | Copyright 2026 on all new files | Pass | test/soap-addressing-decoupled.qtest carries the 2026 copyright. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No module added. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No module added. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No C++ or QPP change; the changes are Qore module code in qlib/WSDL.qm, qlib/SoapHandler.qm, qlib/SoapClient.qm and qlib/SoapClientIo, a test and documentation. |
| 13 | `%modern` directive present | Pass | test/soap-addressing-decoupled.qtest uses %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | test/soap-addressing-decoupled.qtest is executable. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The test uses %prepend-module-path before its relative %requires of the in-repository modules. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | QUnit, xml and HttpServer are delivered with Qore; in-repository modules use relative %requires. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ or QPP change; the changes are Qore module code in qlib/WSDL.qm, qlib/SoapHandler.qm, qlib/SoapClient.qm and qlib/SoapClientIo, a test and documentation. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ or QPP change; the changes are Qore module code in qlib/WSDL.qm, qlib/SoapHandler.qm, qlib/SoapClient.qm and qlib/SoapClientIo, a test and documentation. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ or QPP change; the changes are Qore module code in qlib/WSDL.qm, qlib/SoapHandler.qm, qlib/SoapClient.qm and qlib/SoapClientIo, a test and documentation. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | HTTPClient is used by SoapHandler only to deliver to endpoints that the configured authorizer approved (the approved opt-in against the SOAP Binding section 7 risk); only http and https addresses are used; the tests use loopback servers. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ or QPP change; the changes are Qore module code in qlib/WSDL.qm, qlib/SoapHandler.qm, qlib/SoapClient.qm and qlib/SoapClientIo, a test and documentation. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ or QPP change; the changes are Qore module code in qlib/WSDL.qm, qlib/SoapHandler.qm, qlib/SoapClient.qm and qlib/SoapClientIo, a test and documentation. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ or QPP change; the changes are Qore module code in qlib/WSDL.qm, qlib/SoapHandler.qm, qlib/SoapClient.qm and qlib/SoapClientIo, a test and documentation. |
| 24 | No blocking operations without cancellation support | Pass | Waiting for a decoupled reply is bounded by the client timeout (WSA-REPLY-TIMEOUT) on a blocking queue, not polling; deliveries use the configured connection and response timeouts; interruption exceptions are rethrown. |
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
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | No stubs: both server and client sides of non-anonymous response endpoints are complete and tested. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Expectations are cancelled by on_exit on every client path; the receiver releases entries on wait and cancel; delivery failures are caught and logged without leaking the connection (the HTTPClient is local). |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | WsaReplyReceiver guards its maps with a Mutex; the handler reads its authorizer and timeout under the read lock and sets them under the write lock. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | The authorizer is a typed code<bool(hash<auto>, hash<WsaEndpointReference>)>; received messages use the WsaReceivedMessage hashdecl. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | One HTTP request per delivered reply; correlation is a constant-time map lookup. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Refusals produce the WS-Addressing faults; receiver misuse raises WSA-RECEIVER-ERROR, missing replies WSA-REPLY-TIMEOUT, invalid options SOAP-CLIENT-ERROR or SOAP-CLIENT-IO-ERROR; all are asserted. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | All new classes, methods and options are documented with examples; design/soap-addressing.md gains the non-anonymous endpoint section; docs build without warnings. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP change. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | The handler contacts no address that its configuration did not approve; non-HTTP schemes are never used; reference parameters are sent only to the endpoint that supplied them. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | soap-addressing-decoupled.qtest: 6 cases, 101 assertions, repeated runs stable, SOAP 1.1 and 1.2, both clients; the related addressing, handler and client suites pass. The full suite shows no new failures. |

Result: **20 Pass / 42 N/A / zero Fail**.
