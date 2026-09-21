# W3C assertion ledger audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Applied `/home/david/.claude/skills/audit-changes/SKILL.md` to the uncommitted changes on main
`develop` based on 06eef84. Scope: the pinned current-normative specification sources, the section
extractor, the assertion ledger, its verification gate and the evidence document. No Qore, C++ or
module code changed, so Valgrind is not required.

Two findings came out of building it, both fixed before this commit:

- Section boundaries were first derived from flattened document text, which cannot distinguish a
  heading from a cross-reference to it. That silently attributed the wrong body to Part 1 section
  2.6. Sections are now read from the documents own heading elements.
- An earlier working note recorded that the fault `Role` value constraint had been dropped from the
  Second Edition. It has not; the constraint is in section 5.4.4 and the row now quotes it. The note
  had been taken from the 2003 collection commentary rather than from the current text.

One point for the reviewer: this increment vendors two W3C specification documents into the
repository so the gate can verify quotations offline. They are unmodified and retain their W3C
copyright notice, and the repository already pins W3C schemas the same way, but vendoring whole
specifications is a heavier step than pinning schemas and is called out here deliberately.

All 62 checks are explicitly accounted for:

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | External module repository; the Qore repo module index does not apply. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | N/A | No module behavior changed, so no release note is due. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No module added or changed. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No module added or changed. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No module added or changed. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No .qm added or changed. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No .qc added or changed. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include usage. |
| 9 | Copyright 2026 on all new files | Pass | The new tooling, ledger, sources index and evidence carry 2026 copyright. The two pinned W3C documents are third-party and correctly retain their own 2007 W3C notice; they are redistributed unmodified and their provenance and licence terms are recorded in normative/sources.json. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No module added or changed. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No module added or changed. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No Qore, C++, QPP, module or DataProvider change; this increment adds specification sources, accounting data, a verification gate and documentation. |
| 13 | `%modern` directive present | N/A | No Qore test added; the new gate is Python, matching the existing independent gates in test/wsdl-interop. |
| 14 | Executable permission set (`chmod +x`) | Pass | verify_ledger.py and soap_sections.py are executable and carry a shebang, matching the existing Python gates. |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | N/A | No Qore test or module requirement added. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | The new tooling uses only the Python standard library, so it adds no optional dependency and needs no guard. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No Qore, C++, QPP, module or DataProvider change; this increment adds specification sources, accounting data, a verification gate and documentation. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No Qore, C++, QPP, module or DataProvider change; this increment adds specification sources, accounting data, a verification gate and documentation. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No Qore, C++, QPP, module or DataProvider change; this increment adds specification sources, accounting data, a verification gate and documentation. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | The verifier performs no network or socket I/O. The specifications were retrieved once and are pinned in the repository with digests, so the gate is hermetic and runs offline from any working directory. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No Qore, C++, QPP, module or DataProvider change; this increment adds specification sources, accounting data, a verification gate and documentation. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No Qore, C++, QPP, module or DataProvider change; this increment adds specification sources, accounting data, a verification gate and documentation. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No Qore, C++, QPP, module or DataProvider change; this increment adds specification sources, accounting data, a verification gate and documentation. |
| 24 | No blocking operations without cancellation support | N/A | No Qore, C++, QPP, module or DataProvider change; this increment adds specification sources, accounting data, a verification gate and documentation. |
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
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | No TODO, FIXME or stub. Nothing is claimed as covered that is not mapped: the 26 data model, encoding and RPC assertions are explicitly routed to P8 rather than credited to literal coverage, and the WS-I identifiers are stated as open rather than silently omitted. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | The verifier accumulates problems and reports them together rather than aborting on the first, so one bad row cannot hide the rest; file reads are scoped and no resource is held across the checks. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Single-threaded accounting over immutable inputs; no shared mutable state. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed, explicit structures throughout: each row has a fixed shape, and applicability and phase are checked against closed sets rather than free text. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Sections are parsed once per document and reused across all 140 rows; the test inventory is built once. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Every failure mode is reported with the identifier and the specific defect: a missing or extra row, a duplicate, a quote absent from its section, a mapping to a missing file or a missing case, an unmapped applicable row, an empty rationale, and an out-of-range applicability or phase. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Both new modules carry module docstrings explaining what they enforce and why; the evidence document records the sources, the corrections found and the accounting. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No Qore, C++, QPP, module or DataProvider change; this increment adds specification sources, accounting data, a verification gate and documentation. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No credentials and no network access. The pinned documents are unmodified third-party text whose digests are checked on every run, so a silent edit is detected. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | The gate was checked against deliberate damage - an invented quote, a mapping to a nonexistent case, a mapping to a nonexistent file, a collection-based excuse, an applicable row with no mapping and a deleted row - and reported all six with the correct diagnosis, then passed again once restored. Section extraction reads the documents own heading elements after a text-based pass was found to attribute the wrong body to section 2.6. |

Result: **14 Pass / 48 N/A / zero Fail**.
