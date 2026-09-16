# P5-21 character whitespace audit

Copyright (C) 2026 Qore Technologies, s.r.o.

The audit-changes skill and all five referenced guides were consulted for the
final diff. The C++ change propagates one private boolean parse flag and retains
character entries at node finalization. WSDL enables it at instance boundaries.
The initial broad run identified an overbroad declaration-parser edit and an old
XML-view grouping expectation; both were corrected before the final stable run.
The independent matrix explicitly checks the established legacy inferred-string
annotations separately from character preservation; it does not claim type
annotation absence in that compatibility mode. No main Qore change or workaround.

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, class, app registration or provider metadata in this increment. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 and native XML 2.3 release notes describe the whitespace flag and schema-aware instance behavior. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing WSDL and native XML CMake registrations retained; both actual documentation targets pass. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, class, app registration or provider metadata in this increment. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | Pass | Existing first WSDL documentation section remains wsdlintro. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL uses %modern; no redundant directives added. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, class, app registration or provider metadata in this increment. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include added. |
| 9 | Copyright 2026 on all new files | Pass | All new tests, worker, design/evidence and audit documents have 2026 copyright. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, class, app registration or provider metadata in this increment. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | Pass | Only the existing single WSDL.qm module entry remains. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new QPP class; the flag is exported in the existing Qore::Xml namespace. |
| 13 | `%modern` directive present | Pass | Both new and both updated qtests and the new worker use %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | All four affected qtests and the independent worker/test are executable. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Local qlib precedes relative WSDL requirements; runtime tests use the frozen new XML qmod and frozen Qore modules. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Same-repository XML/WSDL and Qore libraries are hard requirements; external JSON in the worker uses %try-module with explicit missing-module failure. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | Pass | C++ diff only adds a local parse flag and changes whitespace finalization; no filesystem operation added. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | Pass | No native network operation added. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No native filesystem or network operation added. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production changes parse supplied strings. Tests use bounded localhost HTTP via Qore classes and temporary fixture files for the independent worker. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | Pass | No loop added in C++; existing read/checkDepth/takeValue cancellation points still cover retained whitespace paths. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | Pass | Cancellation remains qore_check_cancel; no deprecated calls added. New interruption/retry test passes. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | Pass | No new loop cadence; read and stack traversal keep existing checks, including checks before finish returns early. |
| 24 | No blocking operations without cancellation support | Pass | No new blocking native operation; actual HTTP tests retain bounded timeouts and on_exit teardown. |
| 25 | Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No new module, class, app registration or provider metadata in this increment. |
| 26 | Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No new module, class, app registration or provider metadata in this increment. |
| 27 | Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No new module, class, app registration or provider metadata in this increment. |
| 28 | DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No new module, class, app registration or provider metadata in this increment. |
| 29 | DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No new module, class, app registration or provider metadata in this increment. |
| 30 | Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No new module, class, app registration or provider metadata in this increment. |
| 31 | Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No new module, class, app registration or provider metadata in this increment. |
| 32 | **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No new module, class, app registration or provider metadata in this increment. |
| 33 | Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No new module, class, app registration or provider metadata in this increment. |
| 34 | Response/output types use `private` Fields | N/A | No new module, class, app registration or provider metadata in this increment. |
| 35 | Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No new module, class, app registration or provider metadata in this increment. |
| 36 | Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No new module, class, app registration or provider metadata in this increment. |
| 37 | Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No new module, class, app registration or provider metadata in this increment. |
| 38 | Password/secret fields have `"sensitive": True` | N/A | No new module, class, app registration or provider metadata in this increment. |
| 39 | `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No new module, class, app registration or provider metadata in this increment. |
| 40 | App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No new module, class, app registration or provider metadata in this increment. |
| 41 | App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No new module, class, app registration or provider metadata in this increment. |
| 42 | `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No new module, class, app registration or provider metadata in this increment. |
| 43 | `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No new module, class, app registration or provider metadata in this increment. |
| 44 | `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No new module, class, app registration or provider metadata in this increment. |
| 45 | Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No new module, class, app registration or provider metadata in this increment. |
| 46 | No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No new module, class, app registration or provider metadata in this increment. |
| 47 | No bare field/option names in prose — must use backticks | N/A | No new module, class, app registration or provider metadata in this increment. |
| 48 | Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No new module, class, app registration or provider metadata in this increment. |
| 49 | **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No new module, class, app registration or provider metadata in this increment. |
| 50 | **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No new module, class, app registration or provider metadata in this increment. |
| 51 | **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No new module, class, app registration or provider metadata in this increment. |
| 52 | JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No new module, class, app registration or provider metadata in this increment. |
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Fix is an explicit parser capability, used by schema-aware instance consumers. Default parsing remains documented and tested; no injected xml:space attribute or fixture special case. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | New C++ state is a non-owning bool. Existing RAII and stack cleanup own retained strings. Malformed/interrupt/retry tests and four clean Valgrinds verify cleanup. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Flag state is private to each parser stack and inherited per child; no mutable global or shared schema state added. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Boolean stack fields, existing typed APIs, typed Qore callbacks and declarations; flags use a distinct integer bit. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Constant work to propagate the flag; preservation avoids the indentation-removal pass. Repeated 1/32/1024-child cases retain complete ordered fields. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Malformed XML, invalid schema content and invalid integers reject with exact categories. xml:space reset and reader cursor boundaries are tested. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public flag documents semantics, default behavior, example and since; WSDL API/design docs cover ordered whitespace keys. Native and WSDL docs build without diagnostics. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | Only a QPP constant is added; callable method flags are unchanged. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No format strings, indexing, credentials or I/O policies changed by native code. New test callbacks use bounded queues and local ephemeral listeners. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Final 193 suites/97,747 assertions pass with stable sources and no unexpected diagnostics; seven caught soap comparator assertion failures retain the accepted baseline. Independent 288-conversion/306-document matrix, mutation comparison and original corpus character checks pass. Four Valgrinds have zero errors/lost bytes. |

All 62 checks: **27 Pass / 35 N/A / zero Fail**.
