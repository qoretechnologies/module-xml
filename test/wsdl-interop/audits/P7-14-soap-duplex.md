# P7-14 SOAP full-duplex audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied `/home/david/.claude/skills/audit-changes/SKILL.md` to the uncommitted changes on
main `develop` based on 6cc6352. Scope: the new `test/soap-duplex.qtest` suite, the
`soap-duplex-peer` driver, the `test_soap_duplex.py` independent gate, the duplex evidence
and validation records, and the durable design addition. No production, C++, module,
DataProvider or installation change belongs to this increment, so Valgrind is not required.
Unrelated `test/cmake/__pycache__/` is excluded.

The audit found and fixed two defects in the new code. A throwing recovery exchange left
its `DuplexPeer` unjoined, leaking the peer thread and its listener; peer ownership now
uses an idempotent `release()` and an exception-safe `stop()` invoked under `on_error`.
Two per-exchange assertions compared compile-time constants and could never fail; the
sizing invariant is now asserted once as an explicit precondition instead. Writing the
suite also exposed two fixture defects of my own: a "held" peer that closed immediately
instead of holding its connection, and a hold reply that wrongly carried the full response
body. Both are corrected, and the suite passes repeatedly with identical counts.

All 62 checks are explicitly accounted for:

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new or changed module, registration, separated class or layout; existing flat modules are untouched. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | N/A | No module behavior changed, so no release note is due; SoapClient and SoapHandler are unmodified. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new or changed module, registration, separated class or layout; existing flat modules are untouched. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No new or changed module, registration, separated class or layout; existing flat modules are untouched. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new or changed module, registration, separated class or layout; existing flat modules are untouched. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No new or changed module, registration, separated class or layout; existing flat modules are untouched. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new or changed module, registration, separated class or layout; existing flat modules are untouched. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include usage introduced. |
| 9 | Copyright 2026 on all new files | Pass | The new qtest, peer driver, Python gate, evidence and validation record all carry 2026 copyright. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new or changed module, registration, separated class or layout; existing flat modules are untouched. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new or changed module, registration, separated class or layout; existing flat modules are untouched. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No C++, QPP, module, DataProvider or installation change; this increment adds tests, evidence and durable design only. |
| 13 | `%modern` directive present | Pass | test/soap-duplex.qtest and test/wsdl-interop/soap-duplex-peer/client.qr both use %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | Both new Qore files are mode 755. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Both prepend the local qlib before relative in-repo requirements, as the user requires for this repo. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | json is an external dependency and uses %try-module; QUnit and the in-repo WSDL/SoapClient modules use hard requirements. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++, QPP, module, DataProvider or installation change; this increment adds tests, evidence and durable design only. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++, QPP, module, DataProvider or installation change; this increment adds tests, evidence and durable design only. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++, QPP, module, DataProvider or installation change; this increment adds tests, evidence and durable design only. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | The qtest peer uses a raw Socket deliberately: the contract under test is a peer that answers before draining, which HttpServer cannot produce, and Qore Socket exposes no buffer control so the exchange is sized past any plausible buffer. The reason is documented on the DuplexPeer class. Client I/O stays on SoapClient. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++, QPP, module, DataProvider or installation change; this increment adds tests, evidence and durable design only. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++, QPP, module, DataProvider or installation change; this increment adds tests, evidence and durable design only. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++, QPP, module, DataProvider or installation change; this increment adds tests, evidence and durable design only. |
| 24 | No blocking operations without cancellation support | N/A | No C++, QPP, module, DataProvider or installation change; this increment adds tests, evidence and durable design only. |
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
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | No TODO, FIXME or stub. The increment adds no production code and no XML workaround for the core buffered-upload defect, which Qore fixed in 8a1c3e5f3. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Peer ownership is exception safe: DuplexPeer::stop() releases a held connection and joins under on_error, so a failing exchange or recovery cannot leak the peer thread or listener; the audit found and fixed a leak where a throwing recovery exchange left its peer unjoined. Qore cleanup uses on_exit/on_error; the Python peers tear down through explicit stop sockets and bounded joins. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | DuplexPeer::release() is idempotent under a Mutex; peer observations are written by the peer thread and read only after join(). The cancellation case clears the sticky cancellation flag in the worker before reporting. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed closures (code<nothing()>, code<nothing(string)>), typed hash<auto> results, hash<ExceptionInfo> catches and typed peer members throughout. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Each exchange streams once; the peer reads with bounded chunk sizes and the gates reuse one client per matrix cell instead of reconnecting per assertion. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Every failure mode is asserted with its exact terminal error, status and peer-side drain state; the peer validates method, declared length and extra request bytes and reports its own failures to the owning test thread. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | The new peer class, its members and each helper carry Doxygen comments; the durable contract is documented in design/soap-envelope-processing.md and the evidence document. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++, QPP, module, DataProvider or installation change; this increment adds tests, evidence and durable design only. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No credentials, no user-controlled format strings; all peers bind to 127.0.0.1 on ephemeral ports and payloads are generated locally. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Full duplex is proven rather than assumed: the peer records that it had read 0 (qtest) or far fewer than the declared length (independent gate) request bytes when its whole response had been written, and the sizes were measured against a serialized reference client that deadlocks at 512 KiB/256 KiB with bounded buffers and 8 MiB/4 MiB with default buffers. |

Result: **16 Pass / 46 N/A / zero Fail** after the fixes above.
