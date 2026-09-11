# P5-10 audit: wildcard attribute instances

Copyright (C) 2026 Qore Technologies, s.r.o.

Audited the final changes from `a2ce739` with the complete audit-changes skill and its five referenced guides. This increment changes the existing WSDL Qore module, tests and documentation; no C++ or module registration changes.

All 62 checklist items are recorded individually. [P5-10-validation.json](../P5-10-validation.json) records source/runtime hashes, command results and five replayable acceptance runners.

| # | Check | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | External module repository; no Qore module catalog entry. |
| 2 | Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL v0.5.8 release notes document wildcard admission, native representations, provider aliases and per-message namespaces. |
| 3 | `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | Existing module registration is unchanged; six registered module targets build. |
| 4 | Module added to QMOD list in `CMakeLists.txt` | N/A | No new module or QMOD-list entry. |
| 5 | `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | Existing lowercase WSDL introduction and module identity are unchanged. |
| 6 | `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL retains %modern without redundant parse directives. |
| 7 | No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No separated qc file changes. |
| 8 | No `%include` usage (deprecated for modules) | Pass | No %include usage or alternate entry point is added. |
| 9 | Copyright 2026 on all new files | Pass | All new authored Qore/Python tests, design, evidence, audit and inventory carry Copyright 2026. |
| 10 | Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | Existing single-file WSDL layout is unchanged. |
| 11 | No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No duplicate module entry point. |
| 12 | `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No QPP class is added. |
| 13 | `%modern` directive present | Pass | All three qtests and the qr worker explicitly use %modern. |
| 14 | Executable permission set (`chmod +x`) | Pass | Three qtests, qr worker and Python matrix are executable (0755). |
| 15 | Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Tests prepend the local qlib before relative in-repository requirements; AOT staging imports explicit built qmods. |
| 16 | External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Project xml and core QUnit/HttpServer use hard requirements. External json uses %try-module with explicit missing-dependency failure. |
| 17 | No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++ filesystem changes; native XML and isolated libqore hashes match P5-09. |
| 18 | No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++ network changes. |
| 19 | If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No native filesystem/network operations are added. |
| 20 | No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Production adds no I/O. Test manifest reads are explicit and independent validators use offline resources. HTTP tests bind loopback listeners with bounded completion and cleanup. |
| 21 | All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++ loops change. Qore cancellation is checked by the runtime and exercised in source/AOT tests. |
| 22 | Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No native cancellation API changes. |
| 23 | Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No native cancellation-check frequency changes. |
| 24 | No blocking operations without cancellation support | Pass | No blocking production operation is added. Queue/counter deadlines and bounded subprocesses implement deterministic test completion; cancellation propagates. |
| 25 | Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No action registration changes. |
| 26 | Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No action option registration changes. |
| 27 | Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No action output registration changes. |
| 28 | DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No DPAT_API registration/dispatch changes. |
| 29 | DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No find action or search-option changes. |
| 30 | Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No application scheme/class registration changes. |
| 31 | Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No Fields hash slice is added. |
| 32 | **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | The new HashDataType subclass describes dynamic schema components, not a fixed application request/response schema; static Fields constants are not applicable. |
| 33 | Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No static request Fields constant. |
| 34 | Response/output types use `private` Fields | N/A | No static response Fields constant. |
| 35 | Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | Pass | The attribute-map field has display_name, type and a description explaining declared versus expanded wildcard names; simple-content fields retain typed metadata. |
| 36 | Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | Pass | Existing declared default/fixed examples remain attached to fields. The documented shipment extension example executes and validates its XML. |
| 37 | Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | Pass | Fixed/enumerated declared fields retain AllowedValueInfo metadata. Simple-content finite choices remain on the scalar field rather than rejecting the containing attribute hash. |
| 38 | Password/secret fields have `"sensitive": True` | N/A | No password or secret fields. |
| 39 | `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No application groups. |
| 40 | App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No application logos. |
| 41 | App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No application catalog descriptions. |
| 42 | `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No application display names. |
| 43 | `short_desc` is plain text, under 80 chars, single sentence — no markdown | Pass | The XML attribute values summary is plain text and under 80 characters. |
| 44 | `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | Pass | New provider prose uses backticks for expanded attribute examples; descriptions are short complete sentences. |
| 45 | Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | Pass | Documentation explains retaining partner attributes and checking declared quantities while forwarding messages. |
| 46 | No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | Pass | No bare boolean or NOTHING values in new provider desc strings. |
| 47 | No bare field/option names in prose — must use backticks | Pass | The expanded attribute example in provider prose is backtick-wrapped. |
| 48 | Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | New provider descriptions are under 500 characters. |
| 49 | **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No factory registration or cross-repository catalog change. |
| 50 | **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No getRecordTypeImpl changes. |
| 51 | **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No JNI dependency/JAR changes. |
| 52 | JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No JAR install rule changes. |
| 53 | **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Wildcard admission uses completed schema constraints and declarations without fixture-name branches, skips or validation bypasses. The separate pre-existing native ID defect is explicitly reproduced and assigned to P5-11 under the execution prompt. |
| 54 | **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | QName output scopes restore after exceptions/cancellation; per-message and native hash state is local/copy-on-write. Registry publication follows successful resolution, failed additions restore the old map, and malformed serialized components reject before use. |
| 55 | **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | SOAP output allocation is per message. Registry configuration precedes concurrent reads. Four simultaneous serializers use distinct partner namespaces; failures/cancellation preserve shared state. Live/saved provider publication and detached lifetime are tested. |
| 56 | **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Resolved wildcard hashdecls/enums and typed declaration/provider maps retain type safety. Polymorphic values use auto intentionally. HTTP callbacks use code<auto(hash<auto>, auto)>. |
| 57 | **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Expanded-name indexes make attribute admission O(D+A), excluding datatype conversion and ID-ancestry checks. There is no per-attribute scan of all global declarations; namespace/native values use copy-on-write. |
| 58 | **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Tests reject malformed names/XML text, duplicate aliases, forbidden namespaces, missing strict declarations, invalid fixed/list/QName values, wildcard-ID conflicts and malformed provider/registry metadata. Caller-added provider fields cannot bypass wildcard checks. |
| 59 | **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | New public provider/registry APIs document parameters, returns and relevant errors. The implemented design explains representations, configuration/snapshot ownership and namespace allocation with an executed shipment example. WSDL Doxygen builds without warnings. |
| 60 | **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No QPP methods or flags change. |
| 61 | **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Diagnostics use fixed format strings. Expanded names and XML characters are validated. Independent schema resources are offline and unknown URIs fail; there are no credentials or new production external accesses. |
| 62 | **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | The exact source passes the 125-suite gate plus registry ownership, four source modes and AOT, HTTP consumers, and a 39-schema independent matrix. The strict corpus gains four required rejections without new failures; all remaining failures stay visible. |

Result: {'N/A': 35, 'Pass': 27}. No audit failures remain.

Audit corrections include provider assignment shortcuts and caller-added fields, alias normalization, default namespace absence, reserved XML prefixes and complete per-message namespace allocation. Tests were rerun after production corrections. Registry lifetime tests additionally verify live publication, serialized snapshots and rollback without changing production code.
