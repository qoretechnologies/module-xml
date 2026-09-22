# P8-01 independent encoding sources audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied `/home/david/.claude/skills/audit-changes/SKILL.md` to the uncommitted P8-01 changes on main `develop`
based on 5ec656c. Scope: `test/wsdl-interop/axis-peer/`, `encoded-corpus/`, `encoded_corpus.py`,
`test_axis_peer.py`, `normative/soap12-testcollection.html` and its `sources.json` entry, `.gitattributes`, the
evidence and validation records, PLAN.md and EXECUTION.md. No production code changed.

Two findings were fixed before commit: the temporary directory leaked if the peer build failed (now removed by a
class cleanup registered first), and the Axis server's readiness read had no bound (the server now uses the
shared `endpoint()` helper with its deadline, and silent output is enforced).

All 62 checks are explicitly accounted for:

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | External module repository. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | N/A | No module behavior changed. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No module added. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No module added. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No module added. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No .qm changed. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No .qc changed. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include usage. |
| 9 | Copyright 2026 on all new files | Pass | Every new local file carries the 2026 copyright: test_axis_peer.py, encoded_corpus.py, AxisPeer.java, pom.xml, manifest.json, both READMEs, the evidence and validation records. Pinned third-party files keep their own Apache headers unchanged. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No module added. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No module added. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No production, C++, QPP or module change; P8-01 adds test infrastructure (pinned peer, corpora, gate). |
| 13 | `%modern` directive present | N/A | No Qore test or script changed; the new gate is Python and drives Java only. |
| 14 | Executable permission set (`chmod +x`) | Pass | test_axis_peer.py and encoded_corpus.py are executable, like the other gates and tools. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | N/A | No Qore test or script changed. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Java 17+ and lxml are required, as for the existing CXF gates; all Java dependencies are pinned offline and verified. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No production, C++, QPP or module change; P8-01 adds test infrastructure (pinned peer, corpora, gate). |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No production, C++, QPP or module change; P8-01 adds test infrastructure (pinned peer, corpora, gate). |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No production, C++, QPP or module change; P8-01 adds test infrastructure (pinned peer, corpora, gate). |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | The gate binds its Axis server to the loopback interface on an ephemeral port and uses no public service. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No production, C++, QPP or module change; P8-01 adds test infrastructure (pinned peer, corpora, gate). |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No production, C++, QPP or module change; P8-01 adds test infrastructure (pinned peer, corpora, gate). |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No production, C++, QPP or module change; P8-01 adds test infrastructure (pinned peer, corpora, gate). |
| 24 | No blocking operations without cancellation support | N/A | No production, C++, QPP or module change; P8-01 adds test infrastructure (pinned peer, corpora, gate). |
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
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Nothing is stubbed. Axis sources are compiled unchanged; only the harness is local. The seven not-well-formed W3C messages are recorded as errata, never corrected. The published .sha discrepancy is recorded and SHA-256 is pinned after signature and MD5 verification. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Class cleanup is registered before the build, so a failing build removes its directory. The server runs under the shared endpoint() helper, which reaps it on every path. In Java, sockets and writers use try-with-resources and the server stops in finally. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | RecordingHandler serializes its file appends on the class monitor; the server and client are separate processes. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | The Java harness compiles with -Xlint:all -Werror and no diagnostics, and its handler declares serialVersionUID. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | The gate builds the peer once per class; a full run takes about 3 s after compilation. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Readiness is bounded by endpoint(), and any stderr output fails the gate. The client must print exactly VERIFIED 31 FAILURES 0 with empty stderr. The captured operations must equal the WSDL portType operations exactly. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Both READMEs document provenance, commands and the canonical comparison. encoded-sources-evidence.md, P8-01-validation.json, PLAN.md and EXECUTION.md record the increment and its findings. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP change. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | TLS verification stayed on (explicit system CA bundle). No credentials. The release signature was checked against Apache KEYS in a throwaway GnuPG home. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Four tests pass in 3 + 4 consecutive runs. Negative tests prove detection of a changed JAR and a changed corpus value; an earlier no-op mutation was identified and replaced. W3C extraction reproduces byte for byte, and the ledger verifier passes. |

Result: **14 Pass / 48 N/A / zero Fail**.
