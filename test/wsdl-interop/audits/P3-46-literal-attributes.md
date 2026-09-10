# P3-46 audit: literal scalar attributes and HTTP consumers

Copyright (C) 2026 Qore Technologies, s.r.o.

The complete audit-changes skill and its module structure, sandboxing, cancellation
and DataProvider references were reviewed against the final diff. The provider
reference named development-guide resolves to data-provider-development-guide.md
in the core repository. No provider registration or native implementation changed.

All 62 checks are resolved: 18 Pass / 44 N/A / 0 Fail.

See [evidence](../literal-attributes-evidence.md). Audit review retained the original
synthetic reference hash and literal contract as a negative case, added an actual
encoded-reference positive, and fixed the new Python worker invocation to select
each requested execution mode explicitly. The final affected SOAP rerun passes
all 20 cases. Original corpus files and all diagnostic expectations are preserved.
P3 phase acceptance and P4-P9 remain separate, unfinished gates.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8 release notes describe literal scalar attributes and encoded reference contexts. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | WSDL retains %modern; no redundant parse directives. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 8. No `%include` usage (deprecated for modules) | Pass | No deprecated %include directive introduced. |
| 9. Copyright 2026 on all new files | Pass | All new test/evidence/audit files and touched source/design files carry 2026 copyright. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 13. `%modern` directive present | Pass | Both affected qtests use %modern. |
| 14. Executable permission set (`chmod +x`) | Pass | Both affected qtests are executable. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Tests prepend local qlib and require WSDL/SoapClient/SoapHandler by relative paths. Runtime module paths select local Debug XML and isolated core. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Same-repository XML and core dependencies use hard requirements. The reused external-json survey worker guards its dependency with %try-module. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Only new I/O is test I/O: loopback HTTP listeners bound before clients, bounded queue/socket/subprocess deadlines, on_exit server cleanup, and managed temporary fixtures. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 24. No blocking operations without cancellation support | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 34. Response/output types use `private` Fields | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 47. No bare field/option names in prose — must use backticks | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | The binding supplies reference context from body.encoded; schema attributes are not renamed or special-cased. The old invalid literal-reference expectation now rejects; an actual encoded contract retains positive lookup/recovery coverage. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Reference maps and projected bodies are local values; no shared object is partially updated. Exceptions propagate. Negative client/handler/lookup cases verify reuse; no native ownership changed. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | No shared mutable runtime state introduced. HTTP test callbacks communicate through queues and each server stops on scope exit. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | New reference/body variables are typed hashes; scalar callbacks have typed request/response signatures. Dynamic schema values intentionally use auto. The worker mode is validated before script construction. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Literal messages avoid the encoded-reference traversal. Encoded traversal complexity is unchanged. Independent fixture/stage checks are bounded and do not omit cases. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Both bindings and directions check unsigned overflow, malformed scalar input, missing references, invalid handler responses and recovery. Exact error categories are asserted; literal URIs including empty values remain schema data. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public getValue parameter/return/error docs, WSDL release notes, durable scalar designs, README and evidence are updated. Doxygen and all three extracted Qore examples pass without diagnostics. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No new module, QPP class, native code, provider/action/app, factory, JAR, or method flag. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | No credentials or input-controlled formats added. The temporary worker uses a fixed validated mode, shlex-quoted executable and shell argument forwarding; all fixture data remains in files. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 98 affected Qore suites / 1001 successful cases / 40146 reported assertions pass. New 3/1336 suite and 52-document independent matrix pass in AST/IR/JIT/tiered. All 2411 survey rows and 144 diagnostic failures are unchanged; 1260 strict directions pass. |
