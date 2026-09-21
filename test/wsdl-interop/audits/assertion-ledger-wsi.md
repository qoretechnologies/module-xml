# WS-I profile requirement ledger audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied `/home/david/.claude/skills/audit-changes/SKILL.md` to the uncommitted changes on main
`develop` based on 1205ae7. Scope: the WS-I requirement extractor, the pinned requirement extracts,
the 353 new ledger rows, the extended verifier and the documentation. No Qore, C++ or module code
changed, so Valgrind is not required.

Findings from building it:

- A digest of the published profile HTML is not reproducible. The documents are served through a CDN
  that rewrites contributor addresses per response, so two downloads have identical length and
  different bytes. Pinning the extracted requirement statements instead is both reproducible and
  86 KB rather than 2.7 MB.
- Keying extraction off the `<a name=...>` anchor silently drops `R4005` and `R5010`, whose anchors
  sit on the preceding rationale paragraph. Keying off the statement's own leading identifier finds
  every requirement in both profiles.
- `R9999` is the specification's own notational example, not a requirement.
- An earlier revision of the rule table was written through a non-raw Python string, which turned
  every `\b` in a pattern into a literal backspace and silently stopped those rules matching. The
  requirement that every row match a rule is what exposed it; the patterns were repaired and checked.
- Running the mapped suites the P7 sweep did not cover surfaced two long-standing failing methods in
  `test_soap_container_whitespace.py`. They are recorded in the ledger under `known_defects` and
  called out in the evidence and execution records rather than absorbed.

All 62 checks are explicitly accounted for:

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | External module repository. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | N/A | No module behavior changed. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No module added or changed. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No module added or changed. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No module added or changed. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No .qm added or changed. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No .qc added or changed. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include usage. |
| 9 | Copyright 2026 on all new files | Pass | The new extractor, ledger rows and documentation carry 2026 copyright. The pinned WS-I extracts are derived from third-party documents; their titles, source URLs and extraction method are recorded so the derivation is traceable to the published profiles. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No module added or changed. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No module added or changed. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No Qore, C++, QPP, module or DataProvider change; this increment adds pinned requirement extracts, accounting data, extraction and verification tooling, and documentation. |
| 13 | `%modern` directive present | N/A | No Qore test added. |
| 14 | Executable permission set (`chmod +x`) | Pass | wsi_requirements.py is executable with a shebang, matching the other Python gates. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | N/A | No Qore test or module requirement added. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | The tooling uses only the Python standard library. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No Qore, C++, QPP, module or DataProvider change; this increment adds pinned requirement extracts, accounting data, extraction and verification tooling, and documentation. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No Qore, C++, QPP, module or DataProvider change; this increment adds pinned requirement extracts, accounting data, extraction and verification tooling, and documentation. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No Qore, C++, QPP, module or DataProvider change; this increment adds pinned requirement extracts, accounting data, extraction and verification tooling, and documentation. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | The verifier and extractor perform no network I/O. The profiles were retrieved once and their requirement statements are pinned, so the gate runs offline from any directory. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No Qore, C++, QPP, module or DataProvider change; this increment adds pinned requirement extracts, accounting data, extraction and verification tooling, and documentation. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No Qore, C++, QPP, module or DataProvider change; this increment adds pinned requirement extracts, accounting data, extraction and verification tooling, and documentation. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No Qore, C++, QPP, module or DataProvider change; this increment adds pinned requirement extracts, accounting data, extraction and verification tooling, and documentation. |
| 24 | No blocking operations without cancellation support | N/A | No Qore, C++, QPP, module or DataProvider change; this increment adds pinned requirement extracts, accounting data, extraction and verification tooling, and documentation. |
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
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | No TODO, FIXME or stub, and nothing is claimed that is not backed. The 49 WS-Addressing requirements are recorded as gaps rather than excluded; the two still-failing P6 container methods are recorded under known_defects rather than omitted; and the ledger states plainly that accounting is not acceptance. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | The extractor and verifier read files under explicit paths and report accumulated problems together rather than aborting on the first one. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Single-threaded processing over immutable inputs. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Closed sets for applicability, coverage and phase; rows have a fixed shape and the verifier rejects an unknown source, coverage or phase. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Each profile is parsed once and each suite inventory built once for all 493 rows. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Failures are reported per identifier with the specific defect, including a quote absent from its pinned statement, a coverage and applicability disagreement, a gap with nothing missing stated, a covered row with no mapping and a routed row still against P7. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | The extractor documents why the raw HTML cannot be pinned and why the anchor cannot be trusted; the evidence document records the accounting, the gaps and the known defects. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No Qore, C++, QPP, module or DataProvider change; this increment adds pinned requirement extracts, accounting data, extraction and verification tooling, and documentation. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No credentials and no network access at verification time. Contributor email addresses in the source documents are stripped during extraction rather than carried into the repository. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Every mapped case was checked to exist, and the eleven mapped suites the P7 sweep did not already cover were run: ten pass and the eleventh has two long-standing failing methods that are now recorded as known defects. The verifier was negative-tested a second time with seven WS-I defects injected and reported all seven correctly. |

Result: **14 Pass / 48 N/A / zero Fail**.
