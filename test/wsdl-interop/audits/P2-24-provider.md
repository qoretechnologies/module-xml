# P2-24 final audit: verified libxml2 provider and error ownership

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: CMake provider/probes/catalog correction, Makefile support-file packaging,
README/native release notes, the schema callback hunks in src/ql_xml.qpp,
new Python/C provider tests and xml-schema-callbacks.qtest. This exact candidate
is validated on committed XML parent 4879ed6 in /tmp/wsdl-libxml-provider-review.
The remaining P2 XML-value/consumer and documentation changes, WebContentUtil,
core AOT/Jina and astparser work are excluded.

Full audit-changes skill applied; references read: core module structure,
module sandboxing and cooperative cancellation design guides. Provider metadata
and new module/QPP class registration checks are not applicable.

Root causes:

- Installed libxml2 2.12.10 returns escaped namespace URI text. Actual reader
  namespace identity controls AUTO/SYSTEM selection, including distribution
  backports. BUNDLED uses the verified 2.15.4 archive (latest stable checked
  2026-09-08), SHA-256
  `98087fd181d9070724f3fbc65c7377db03038eb92bd882374daff44940138821`.
- The old schema warning callback ignored its exception context, printing a
  secondary skipped-import warning after an application import exception.
  Error/warning callbacks now share the actual sink and preserve its first error;
  a warning with no pending exception retains its existing reporting behavior.
- A new negative callback test exposed a separate libxml2 2.15.4 ownership bug.
  xmlResolveFromCatalog saves xmlError by value, accumulates a catalog error,
  then overwrites it with the saved record without freeing its owned strings.
  A standalone C reproduction loses 100 bytes/3 blocks without Qore. A GDB
  watchpoint identifies the overwrite at parserInternals.c:2356. The corrected
  build-tree copy calls xmlResetError(lastError) before restoration. The pinned
  original file hash is checked; unexpected source overrides fail, and a source
  already containing the fix is accepted. No supplied source is modified.
  The C regression also checks prior-error state and reports live allocation
  counts after complete cleanup. It fails on pristine upstream and passes with
  the ownership correction. Upstream master inspected on 2026-09-08 still has
  the same overwrite. No external report was submitted.

References: [GNOME release archive](https://download.gnome.org/sources/libxml2/2.15/),
[libxml2 error API](https://gnome.pages.gitlab.gnome.org/libxml2/html/xmlerror_8h.html),
[upstream catalog resolution implementation](https://github.com/GNOME/libxml2/blob/master/parserInternals.c).
Private static linkage retains original notices and hides libxml2 symbols;
upstream install rules are excluded. Autotools retains explicit system selection.
The system provider is screened for namespace identity; supported-system catalog
cleanup remains part of P9 environment validation.

Final validation (2026-09-08):

- 13 real CMake integration tests pass (20.569 seconds), including fixed/changed
  source overrides and source immutability. No build/compiler warnings.
- Standalone catalog regression: 873 allocations/frees, zero Valgrind errors or
  lost allocations. Namespace probe: runtime 21504, PASS, zero errors/loss.
- Isolated provider plus callback candidate: ten suites / 238 cases pass before
  the catalog correction and again after it. No Qore warnings/errors. The callback
  suite passes all 4 cases / 10 assertions under Valgrind with zero errors/loss.
  The existing xml suite also passes 25 cases / 189 assertions with zero errors/loss.
- Full working P2: all 482 cases pass again after the catalog correction. Existing
  native literal/value/context and HTTP/SOAP consumer memory runs have zero errors
  or lost allocations after core prerequisite 1e52a0a44.
- Both-version catalog survey on the isolated provider matches parent 4879ed6
  recursively except version metadata, including the final catalog-corrected build. Full P2 corpus retains its prior 360 broad
  failures and zero strict failures with unchanged owners; full Python retains
  the same 15 later-phase failures among 92 tests. These are not counted as passes.
- Debug builds use /usr and local binary paths. No install or push. Existing
  Valgrind DWARF/tool warnings and the independently reproduced host glibc failed-
  pthread_create leak remain explicitly assigned to P9 in EXECUTION.md. The final
  native documentation target builds without warnings/errors. The soap suite
  deliberately catches three TEST-EXCEPTION comparison assertions in its negative
  tests; its assertion counter reflects those expected throws, with all cases passing.

Logs: /tmp/wsdl-p2-24-provider-catalog-tests.log,
/tmp/wsdl-p2-24-catalog-cleanup-original.log,
/tmp/wsdl-p2-24-catalog-cleanup-vg.log,
/tmp/wsdl-p2-24-isolated-{catalog-build,affected-final,survey-final}.log,
/tmp/wsdl-p2-24-isolated-schema-fixed-vg{,-test}.log,
/tmp/wsdl-p2-24-affected-catalog-final.log.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | Native 2.3.0 release notes describe provider selection, catalog ownership correction and original import exception propagation. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | Pass | Existing external binary module registration links the selected target. The namespace probe is EXCLUDE_FROM_ALL; provider support files are in Autotools EXTRA_DIST. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 8. No `%include` usage (deprecated for modules) | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 9. Copyright 2026 on all new files | Pass | All new CMake, C, Python and Qore files and this audit have 2026 notices; original libxml2 notices remain complete. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 13. `%modern` directive present | Pass | New xml-schema-callbacks.qtest uses %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | New qtest is executable (100755). C and Python regressions use the documented compiler/Python entry points. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | New qtest prepends repository qlib. QORE_MODULE_DIR selects the isolated Debug binary and local qlib; no new same-repository user module dependency. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | xml is a same-repository hard dependency; QUnit is the required core test framework. No optional external Qore module is added. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | Pass | Runtime callback changes add no filesystem operation. CMake performs authorized dependency/build I/O; tests use temporary directories and in-memory schema/catalog input callbacks. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | Pass | No runtime network operation added. FetchContent uses the authorized HTTPS archive with TLS verification and a pinned SHA-256. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | Pass | No new production filesystem/network API. Existing XML resource callbacks retain their sandbox implementation. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Qore regression uses in-memory streams. Python launches bounded configure/build subprocesses and uses isolated temporary artifacts. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | Pass | Changed callback formatting retries only to resize its output buffer; fixed probe documents and catalog regression have bounded loops. Qore read loops retain native reader cancellation checks. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | Pass | No deprecated interruption API added. Runtime cancellation behavior remains in XmlReader; no new long-running production operation. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | Pass | Fixed C probe/test inputs are tiny; no unbounded production traversal is introduced. |
| 24. No blocking operations without cancellation support | Pass | No new blocking runtime I/O. Test subprocesses have explicit deadlines. Build downloads use FetchContent; cross-run verification requires an emulator. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 34. Response/output types use `private` Fields | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 47. No bare field/option names in prose — must use backticks | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Behavioral namespace selection follows the user instruction. The catalog fix releases owned temporary error strings at their upstream overwrite site, without changing parsing/error semantics. No namespace repair shim, entity expansion flag, suppression, fixture-specific production branch or source mutation. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Schema error strings use SimpleRefHolder and transfer ownership to the sink. Both callback signatures receive the same live ExceptionSink. The bundled catalog temporary is reset before restoring its saved error. Standalone allocation accounting and Valgrind verify cleanup; final Qore checks are recorded below. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | No mutable shared runtime state added. Callback context is the existing per-parser sink. C allocation counters belong to a single-thread test process; dependency patching writes only each build tree. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Native callbacks match libxml2 void* signatures with internal static_cast. Qore regression members, callbacks and exceptions are typed. C literal lengths fit int; allocator and I/O callbacks use the library types. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | No new data-path scan or copy. Dependency source copying occurs at configure time; configure_file avoids changing the compile input on an identical reconfigure. Provider checks operate on tiny fixed inputs. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Invalid/missing provider, wrong source version, changed unrecognized source, unavailable system library and cross-compiling limitations fail explicitly. Already-fixed source is accepted; negative schema/import/document tests verify exact exception categories and successful recovery. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | README provides provider, offline, cross-build, pin-update and verification commands, build-tree patch scope and source-override restrictions. Native release notes updated. No public runtime method/signature added. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No new user module, QPP class/API, provider registration/metadata, factory or JNI packaging in this increment. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Pinned HTTPS archive/hash, verified patch input, private hidden static target and preserved third-party notices. No credentials, dynamic format strings or user-input-sized buffers added. Offline source trees remain unchanged. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | Namespace probe checks named/decimal/hex references and literal entity-looking text. Provider tests cover selection/switching/backports/install/offline/cross/error cleanup. C allocation regression fails on pristine 2.15.4 and passes with the one-line ownership fix. Final runtime/corpus evidence below. |

Reviewed candidate file SHA-256 (isolated parent plus exact provider candidate):

- `.gitignore`: `8ea47c636ad91638d6ae184001c187a9d7acf4a61a3db6bf27481f2f70973db8`
- `CMakeLists.txt`: `7003e737298faf79e05fa31b28eef3d3ff520dcaa30e16c869ab62f51232ed33`
- `Makefile.am`: `257ea19204ea4f63b3300b296e54058d1506827656a6010cd34bdf7d4bd4c257`
- `README`: `3de022c2adad723c6a6d7ac9a608248814c3d2cf800661440d735dc8e70804c0`
- `docs/mainpage.doxygen.tmpl`: `ac2be631d4f9fdc6537917bc672156c4dfa9cae4a891c8fde6c7b5ae8e03f558`
- `src/ql_xml.qpp`: `69c24aa36ceae347e40a2d228036d039b2715ef572d1cb18a1f43f4f0cd1f2a2`
- `cmake/QoreXmlLibXml2.cmake`: `86514f6f93ba123758b91ac01cff349fc882b4fb320f862b8941727d91774ef2`
- `cmake/QoreXmlLibXml2CatalogFix.cmake`: `97dadebf6a42899e4ebd6e077a19502abd2396051e20e466729f640714363590`
- `cmake/system-libxml2/CMakeLists.txt`: `ce6643bf71f85e4f75e97dad6bbfa03cee8a14a07267edb9c13b2e9bfed8b5cd`
- `cmake/libxml2-namespace-probe.c`: `255b230498990f7e4bb0a23dbeb036d0f13b9678f741ff297ea32dc05fd74adf`
- `cmake/libxml2-NOTICES.txt`: `c3b86c489cf68d34748bfd4f0e854ff3dd11d8f5e15216c2aa44f636f958a5d4`
- `test/cmake/test_libxml2_provider.py`: `0ca1c3f28426179d53e60702e24afaefd3530946de74e3e84a7a2aa49215c659`
- `test/cmake/libxml2_catalog_cleanup.c`: `3c37c04e814585a0945f04e1972ea063aca86aa091a48e2313ace7581cc36996`
- `test/xml-schema-callbacks.qtest`: `7be6a78794c00509d4191fa007c5b45d65181eda33a8f96b9a27ae2ebbf2603a`
