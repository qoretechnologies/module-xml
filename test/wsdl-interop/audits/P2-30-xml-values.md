# P2-30 final audit: retained XML values and consumers

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: complete retained XML carrier/context plus WSDL/schema/provider/client/
handler integration, isolated on parent 9fb341c. Three new Qore suites, two workers,
three independent tests, implemented XML-value design, README and release notes.
Native XML generation/reader/dependency code was already committed and audited in
5477680 and 049cf0d. Unrelated documentation/build and other-repository work is excluded.

The full audit-changes checklist and referenced module structure, sandboxing,
cancellation and DataProvider guides apply. The original native representations
lose lexical spelling, namespace scope and ordered XML; the additive final class
retains authoritative XML plus separate inherited language/space/base context.
Consumers validate through existing decode/encode paths while preserving native
API defaults. Serializable/provider reconstruction retains source ownership and
rebuilds views. XML Base resolves components directly because libxml2's ASCII URI
helper cannot preserve XML Base LEIRIs.

Requirements: [XML Infoset](https://www.w3.org/TR/xml-infoset/#infoitem.element),
[namespace scoping](https://www.w3.org/TR/REC-xml-names/#scoping),
[XML Base](https://www.w3.org/TR/2009/REC-xmlbase-20090128/),
[RFC 3986 resolution](https://www.rfc-editor.org/rfc/rfc3986#section-5.2),
[XML language/space](https://www.w3.org/TR/REC-xml/#sec-lang-tag), and
[SOAP 1.1 document restrictions](https://www.w3.org/TR/2000/NOTE-SOAP-20000508/#_Toc478383494).

Validation: /tmp/wsdl-p2-30-{affected,independent,survey,coverage,docs}.log.
All 447 affected Qore cases pass without warnings/errors. The independent tests
complete six generic XML value documents, 80 inherited-context documents and 192
consumer documents; the existing encoding test additionally checks 40 raw outputs.
The sole independent consumer failure is the already-root-caused P5 required-wildcard
example defect: native generation emits empty content for required xs:any. Both
validators reject the same 16 examples; no rejection is called a passing test.
Other independent value/context/infoset assertions complete successfully. The
execution prompt explicitly permits independent later-phase findings to remain
failing while P2 representation work proceeds.

The both-version 293-WSDL/1136-message survey is recursively identical to 9fb341c
excluding version metadata; strict selected failures are zero. All 360 broad
failures remain with no missing/skipped stages. Native memory gates are resolved
by committed provider/core prerequisites; no native change or new Valgrind
requirement applies to this increment. No installation/push/astparser work.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | WSDL 0.5.8, SoapClient 1.0.4 and SoapHandler 0.3.4 document opt-in retained values, XML context, literal parts and one-way behavior. Client/handler Version constants match their modules. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | Pass | Existing modules use %modern with no redundant legacy directives. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 8. No `%include` usage (deprecated for modules) | Pass | No %include or separated module layout introduced. |
| 9. Copyright 2026 on all new files | Pass | New design, Qore tests, workers, Python regressions and this audit carry 2026 notices; changed modules already include 2026. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 13. `%modern` directive present | Pass | Qtests use %modern. The .qr workers use modern mode automatically (the consumer worker also declares it). |
| 14. Executable permission set (`chmod +x`) | Pass | Qtests and QR workers have executable bits; Python regressions use python3. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | New tests/workers prepend local qlib before relative WSDL/SoapClient/SoapHandler requires. Candidate qlib and committed native Debug XML are selected explicitly; core LD_LIBRARY_PATH selects the tested runtime. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | Same-repository XML/user modules are hard dependencies. The optional consumer json worker uses %try-module with a descriptive missing-module error. Core QUnit and HttpServer remain required test support. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | N/A | No C++/QPP change. Qore loops and XmlReader use existing cooperative cancellation; no new blocking production operation. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | N/A | No C++/QPP change. Qore loops and XmlReader use existing cooperative cancellation; no new blocking production operation. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | N/A | No C++/QPP change. Qore loops and XmlReader use existing cooperative cancellation; no new blocking production operation. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | No new direct production File/Dir/Socket/HTTPClient operation. SoapClient/Handler use their existing transport. Integration fixtures use local HTTP with bounded deadlines, queue completion and deterministic cleanup; independent workers are offline. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | N/A | No C++/QPP change. Qore loops and XmlReader use existing cooperative cancellation; no new blocking production operation. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | N/A | No C++/QPP change. Qore loops and XmlReader use existing cooperative cancellation; no new blocking production operation. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | N/A | No C++/QPP change. Qore loops and XmlReader use existing cooperative cancellation; no new blocking production operation. |
| 24. No blocking operations without cancellation support | N/A | No C++/QPP change. Qore loops and XmlReader use existing cooperative cancellation; no new blocking production operation. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No action request/response HashDataType or Fields catalog is introduced. XsdXmlValueDataType is a specialized QoreDataType for the existing ObjectType contract; typed SoapXmlMessageInfo describes the opt-in return structure. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 34. Response/output types use `private` Fields | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | Pass | The XML object provider has typed NameDescInfo metadata with name/display_name/short_desc/desc. Native provider field metadata remains unchanged. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | Pass | Schema/provider/client examples demonstrate complete invoice/order elements with retained lexical values. XML examples reuse native generation; the required-wildcard generator failure remains a tracked P5 diagnostic. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | Pass | Provider short_desc is a plain sentence fragment under 80 characters without Markdown. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | Pass | Provider desc uses Markdown backticks around XsdXmlValue and describes retained values and schema checks. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | Pass | Provider text explains accepting complete XML without losing values, namespace bindings or order. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | Pass | New provider description contains no bare True/False/NOTHING. |
| 47. No bare field/option names in prose — must use backticks | Pass | The class name in the provider description is backtick-wrapped; no bare option/field reference. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No new user module/layout/registration, native class, DataProvider action/app/Fields declaration, factory or JNI dependency in this increment. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | An explicit immutable representation addresses information native hashes lose. Existing conversion checks are reused without relaxing them; complete native scalar/particle/wildcard semantics remain tracked in P3/P4/P5. No fixture branch, stub, suppression or hidden failure. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Managed Qore values and final immutable carrier. Serializable revalidates authoritative XML/context and reconstructs transient state. Provider strongly retains the source-backed schema. Validation uses a namespace copy, rethrows cancellation unchanged and publishes no partial result. Malformed-state, detached-schema and recovery tests pass. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Carrier has no mutators; returned strings/maps are copy-on-write and each reader is independent. Provider validation allocates prefixes in a private namespace copy. No new shared mutable cache. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Typed SoapXmlMessageInfo and URI component hashdecls, typed part/header/context maps and explicit bool options. Runtime carrier/provider/input state checks reject wrong types. URI resolution distinguishes absent from empty components. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | Component merging/dot removal is linear and preserves unresolved relative parents. Immediate-child extraction scans source XML and emitted subtrees without per-sibling ancestor rescans; 4096 siblings, depth 128 and a 4096-segment path are exercised. Cancellation/recovery is tested. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Malformed XML/state/context, wrong roots/types, conflicting sibling contexts, duplicate/missing parts and invalid options reject with documented categories. One-way calls preserve NOTHING. SOAP DTD/PI checks and injected cancellation remain explicit. Native scalar/example failures are retained under later-phase ownership. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public APIs document parameters/results/errors, examples and representation limits. Durable XML-value design and README explain lexical/context fidelity, Serializable/providers, native defaults and client/handler opt-in. All three candidate module docs build without warnings/errors. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | N/A | No C++/QPP change. Qore loops and XmlReader use existing cooperative cancellation; no new blocking production operation. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | SOAP retained values reject DTDs/PIs; namespace identity is checked before conversion. No new external-resource parsing flag, credentials or dynamic format string. Serialized state cannot override cached identity; inherited context cannot overwrite authored payload attributes. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 34 affected Qore suites pass 447 cases, including 38 carrier/context/consumer cases with 862 assertions and actual HTTP. Independent XML values/context and raw encoding tests pass. The consumer oracle checks 192 documents, with only the already-root-caused 16 P5 required-wildcard examples rejected. Corpus/strict results retain all failures and no missing/skipped cases. |

Candidate production SHA-256:

- qlib/WSDL.qm: `8a929d64f4e58443e0164e944a3f568d4ddc75a360c9d4c0629d7a13caae657e`
- qlib/SoapClient.qm: `18c525099ec75b1b0b52f35354e1d08d116440b46bfdd4e77636ae9ab0ff21d5`
- qlib/SoapHandler.qm: `bdd26f9e3985af4b839d6d5c4c9da70530ccf71b428df2e4b2fd573e06bbbe5c`
