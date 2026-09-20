# P7-12 transport audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied `/home/david/.codex/skills/audit-changes/SKILL.md` to main develop based on
2ad12f9. Scope: two Qore peers, one Python matrix, durable transport documentation
and test evidence. No production code, C++, DataProvider or DGC change. Unrelated
`test/cmake/__pycache__/` is excluded. All 62 checks are explicitly accounted for.

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No production module, module layout, installation entry or separated class change. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | N/A | No production module, module layout, installation entry or separated class change. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No production module, module layout, installation entry or separated class change. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No production module, module layout, installation entry or separated class change. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No production module, module layout, installation entry or separated class change. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No production module, module layout, installation entry or separated class change. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No production module, module layout, installation entry or separated class change. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include or new module directives introduced. |
| 9 | Copyright 2026 on all new files | Pass | New Qore/Python peers and evidence carry 2026 copyright. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No production module, module layout, installation entry or separated class change. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No production module, module layout, installation entry or separated class change. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No C++ or QPP change; native ownership, cancellation, sandbox enforcement and flags are not modified. |
| 13 | `%modern` directive present | Pass | Both Qore peers use %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | Both peers and the Python gate are executable. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Peers prepend local qlib before relative in-repo requirements. Compiled derivatives select the freshly built qmods. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | External json uses %try-module; same-repo XML and bundled core dependencies use hard requirements. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ or QPP change; native ownership, cancellation, sandbox enforcement and flags are not modified. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ or QPP change; native ownership, cancellation, sandbox enforcement and flags are not modified. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++ or QPP change; native ownership, cancellation, sandbox enforcement and flags are not modified. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Bounded loopback I/O and read-only fixture access are required for independent transport testing. Owned sockets, listeners and processes have deterministic teardown. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ or QPP change; native ownership, cancellation, sandbox enforcement and flags are not modified. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++ or QPP change; native ownership, cancellation, sandbox enforcement and flags are not modified. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++ or QPP change; native ownership, cancellation, sandbox enforcement and flags are not modified. |
| 24 | No blocking operations without cancellation support | N/A | No C++ or QPP change; native ownership, cancellation, sandbox enforcement and flags are not modified. |
| 25 | Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 26 | Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 27 | Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 28 | DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 29 | DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 30 | Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 31 | Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 32 | **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 33 | Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 34 | Response/output types use `private` Fields | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 35 | Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 36 | Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 37 | Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 38 | Password/secret fields have `"sensitive": True` | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 39 | `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 40 | App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 41 | App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 42 | `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 43 | `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 44 | `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 45 | Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 46 | No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 47 | No bare field/option names in prose — must use backticks | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 48 | Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 49 | **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 50 | **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 51 | **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 52 | JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No DataProvider, application registration, JNI dependency or factory change. |
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | The real receive event remains the cancellation barrier. EOF and exact error checks remain intact; no client close workaround, skipped case, or increased deadline hides a core failure. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Worker completion is collected before shared results are read; the worker clears its sticky cancellation flag before publishing results. A background-returned thread ID supports cleanup even if readiness fails. Processes are reaped; servers, selectors and sockets close on exceptional exits. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Queues and Counter completion protect worker/main-thread communication; Python queues carry replies, observations and errors. Server selectors have one owning worker. Service graphs are immutable during calls. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | The invocation closure is code<nothing()>, processor arguments use SoapNodeHeader, and exception catches use ExceptionInfo. Requests and responses are explicitly validated. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Finite small messages and matrices, capped request/reply accumulation, no readiness polling or retries. Each interrupted exchange has exactly one recovery call. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Tests cover all four response truncation points, both receive framings for cancellation, three request truncation points, both SOAP versions and operation patterns, graph/value modes, exact callback counts, and recovery. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Evidence records the test contract, commands, compiled-mode procedure and limits. Durable design describes existing transport boundaries; no new public API or release behavior requires release notes. DGC is unchanged. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++ or QPP change; native ownership, cancellation, sandbox enforcement and flags are not modified. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Only loopback ephemeral ports and fixed test payloads are used. Request/reply size and I/O/process deadlines are bounded. No credentials, mutable shared transport configuration, or user-controlled format strings. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Six affected native Qore suites pass: **38 cases / 2,223 assertions**. Three independent Python gates pass, including all **432 new transport exchanges**. The full new matrix also passes with freshly compiled WSDL, SoapClient and SoapHandler modules (another 432 exchanges). Both peer scripts pass astparser without diagnostics. Installed Qore is `25346118e`. Audit: **16 Pass / 46 N/A / zero Fail**. |

**16 Pass / 46 N/A / zero Fail.** No unresolved finding remains in this increment.
Valgrind is not required because there are no C++ changes. Remaining P7/P8/P9 scope
is recorded in PLAN.md and is not claimed complete by this audit.
