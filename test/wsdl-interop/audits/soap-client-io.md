# SoapClientIo async I/O client audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied `/home/david/.claude/skills/audit-changes/SKILL.md` to the uncommitted changes on main
`develop` based on 887d2d2. Scope: the new `qlib/SoapClientIo` module (module file, client class and
connection provider), its `test/soap-client-io.qtest` suite, and the CMakeLists.txt and Makefile.am
registration. `SoapClient` is deliberately untouched, so no existing API changes. No C++, QPP or
DataProvider change, so Valgrind is not required. Unrelated `test/cmake/__pycache__/` is excluded.

The audit found four defects in the new code, all fixed and retested:

- `SoapIoConnection` did not override `getConnectionSchemeInfoImpl()`, so the base class recursed
  until the thread stack was exhausted. The override now returns the connection scheme.
- `close()` replaced the connection manager while another thread could be issuing a request. The
  manager is now swapped under a `Mutex` and read through `getManager()`; the retired manager is
  closed outside the lock so in-flight requests are never blocked by it.
- `username` and `password` options were accepted and silently dropped, which would have sent
  unauthenticated requests to a protected service. Credentials from options or the endpoint URL now
  produce a Basic authorization default header, with a test asserting the exact header value and its
  absence when no credentials are supplied.
- Three `@ref` cross-references to the `SoapClient` module produced Doxygen warnings. They are now
  plain text, because a documentation link does not justify declaring a module dependency that does
  not exist.

Registering the module also exposed that the existing `XmlRpcClientIo` module was missing from
`Makefile.am` entirely; it is registered alongside `SoapClientIo`.

All 62 checks are explicitly accounted for:

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | External module repository; the Qore repo module index does not apply. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | Release notes for the new external module are in its own .qm under @section soapclientio_relnotes. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | qore_external_user_module("qlib/SoapClientIo" "WSDL") added to CMakeLists.txt. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | Pass | qlib/SoapClientIo added to the QMOD list, and to Makefile.am USER_SPLIT_MODULES with its own moddir/DATA rules; the same Makefile.am gap for the existing XmlRpcClientIo was fixed in passing. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | The first doc section is @section soapclientiointro, all lowercase. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | SoapClientIo.qm uses %modern with no redundant %new-style, %require-types, %strict-args or %enable-all-warnings. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | Pass | Neither SoapClientIo.qc nor SoapIoConnection.qc contains any parse directive. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include usage. |
| 9 | Copyright 2026 on all new files | Pass | All four new files carry 2026 copyright. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | Pass | The module is a directory module at qlib/SoapClientIo/ with the .qm inside it. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | Pass | No qlib/SoapClientIo.qm exists. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No C++ or QPP change; the new module is pure Qore and adds no native allocation, DGC or sandbox surface. |
| 13 | `%modern` directive present | Pass | test/soap-client-io.qtest uses %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | test/soap-client-io.qtest is mode 755. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | The test prepends the local qlib before its relative in-repo requirements. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | QUnit, HttpServer and the in-repo WSDL/SoapHandler/SoapClientIo modules use hard requirements; no external optional dependency was introduced. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ or QPP change; the new module is pure Qore and adds no native allocation, DGC or sandbox surface. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ or QPP change; the new module is pure Qore and adds no native allocation, DGC or sandbox surface. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ or QPP change; the new module is pure Qore and adds no native allocation, DGC or sandbox surface. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | The client performs no direct socket or HTTPClient I/O: SOAP traffic goes through HttpClientIo::HttpClientConnectionManager. Remote WSDL retrieval uses the WSDL module's own HTTP client, which is documented on the constructor. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ or QPP change; the new module is pure Qore and adds no native allocation, DGC or sandbox surface. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ or QPP change; the new module is pure Qore and adds no native allocation, DGC or sandbox surface. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ or QPP change; the new module is pure Qore and adds no native allocation, DGC or sandbox surface. |
| 24 | No blocking operations without cancellation support | N/A | No C++ or QPP change; the new module is pure Qore and adds no native allocation, DGC or sandbox surface. |
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
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | No TODO, FIXME or stub. SoapClient is untouched, so nothing is half-migrated; the new module is a complete client for its documented scope. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | close() swaps the manager under a lock and closes the retired one outside it, so no in-flight request is blocked and no manager is leaked; the constructor acquires no resource that can leak on a validation throw, since every option is validated before the manager is created. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | The audit found the connection manager being replaced in close() while another thread could be issuing a request; mgr is now swapped under a Mutex and read through getManager(). All other state is immutable after construction. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed members (WSDL::WebService, WSDL::SoapProcessingNode, HttpClientIo::HttpClientConnectionManager), typed hashdecl results and hash<ExceptionInfo> catches; the response is decoded through the typed hash<WSDL::SoapNodeResult> node result. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | One request per call through a pooled connection manager; response decoding reuses the shared WSDL decoders rather than re-parsing, and the fault path reuses the envelope it already parsed instead of parsing twice. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Conflicting and missing WSDL options, unknown services and ports, unsupported ports, request-only options on the response path, non-SOAP-1.2 bindings, and xml_values combined with preserve_types all reject before any I/O; HTTP status handling distinguishes a SOAP fault from a transport error. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Every public method has Doxygen with @param, @return and @throw plus @par Example where useful; the module mainpage documents features, usage and release history. The documentation build is clean after replacing three cross-module @ref links that would have required a spurious SoapClient dependency. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++ or QPP change; the new module is pure Qore and adds no native allocation, DGC or sandbox surface. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | The audit found that username/password options would be silently dropped, sending unauthenticated requests to a protected service; credentials from options or the endpoint URL now produce a Basic authorization default header, covered by a test asserting the exact header and its absence when no credentials are given. No credentials are hard-coded. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | The new suite drives a real SoapHandler over the new transport across SOAP 1.1/1.2, source/saved-object/saved-data graphs and native/retained values, and covers faults, one-way operations, SOAP 1.2 response retrieval, option rejection, credentials and the connection provider. It also proves the async transport satisfies the full-duplex contract recorded in P7-14: a raw peer writes a complete 4 MiB response having read none of the 8 MiB request body, and the exchange completes. The suite passes identically against the source module and the AOT-compiled qmod. |

Result: **24 Pass / 38 N/A / zero Fail** after the fixes above.
