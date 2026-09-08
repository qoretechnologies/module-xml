# P2-25 final native fragment audit

Copyright (C) 2026 Qore Technologies, s.r.o.

Scope: remaining native generation/reader changes in src/ql_xml.qpp and
src/QoreXmlReader.h; native fragment/encoding documentation and release bullets;
xml-literal.qtest, independent raw-byte encoding worker/test and durable
xml-element-fragments design. Candidate is isolated on parent 5477680 in
/tmp/wsdl-native-fragment-review. WSDL/consumer code, doc build hygiene,
WebContentUtil and other-repository work are excluded.

Full audit-changes checklist applied, with core module structure, sandboxing and
cooperative cancellation design references. Public schema callback/dependency
ownership changes were already committed in 5477680, reviewed by P2-24-provider.

Original flat XML generation cannot insert retained element trees. The explicit
^xml^ entry preserves and validates a complete document element with its namespace
scope, lexical text and ordered content. XML 1.0 attribute normalization requires
character references for tab/LF/CR. Reader input is already UTF-8; an old encoding
declaration previously decoded it again, and the NUL-terminated API could truncate
input. Explicit encoding and byte length fix those causes.

Final review also reproduced invalid UTF-16 output. Markup was appended as raw
ASCII bytes to a wide-encoding buffer, and the escaping API rejects that buffer.
Generation now uses UTF-8 for non-ASCII-compatible output and converts the completed
result, including markup; ASCII-compatible output retains its direct path. Modern
and deprecated XML APIs have the same encoding behavior. An anonymous namespace
makes the internal fragment class private across external-header configurations.

Normative references: [XML 1.0 character encoding](https://www.w3.org/TR/xml/#charencoding),
[attribute normalization](https://www.w3.org/TR/xml/#AVNormalize),
[namespace defaulting](https://www.w3.org/TR/xml-names/#defaulting).

Validation:

- Debug /usr builds match /usr/bin/qore, without installation. No native compiler
  warnings. nm -D confirms that the final fragment helper is not exported.
- Isolated native suite: 11 cases / 256 assertions. Ten other affected suites pass
  238 cases. Legacy SOAP comparison tests intentionally catch three failing inner
  assertions as their expected TEST-EXCEPTION; all cases succeed.
- Independent encoding test validates 40 XML byte sequences from ten API variants
  across UTF-8, ISO-8859-1 and both UTF-16 byte orders, using Expat and lxml. It checks
  encoding/declarations, references, exact text, attributes, comments and order.
- Isolated both-version catalog survey is recursively identical to parent 5477680
  excluding version metadata: no regression, omission or reassigned finding.
- Native literal Valgrind: zero errors and zero definite/indirect/possible loss.
  The final anonymous-namespace binary repeat is also clean. Existing host DWARF/tool
  diagnostics remain visible and assigned to P9; no suppressions.
- Working-tree final documentation generation passes without warnings/errors.
  The final working P2 repeat passes all 483 cases, including the expanded native
  suite; the separately tested schema callback suite adds four passing cases. Known later-phase corpus/Python failures
  remain tracked and are not counted as passes.

Logs: /tmp/wsdl-p2-25-isolated-{configure,build-final,affected,survey}.log,
/tmp/wsdl-p2-25-independent-encoding.log,
/tmp/wsdl-p2-25-final-literal-vg{,-test}.log,
/tmp/wsdl-p2-25-main-final-build.log, /tmp/wsdl-p2-25-affected-final.log.

| Check | Status | Evidence |
| --- | --- | --- |
| 1. Entry exists in `doxygen/lang/120_modules.dox.tmpl` (for modules in the Qore repo; N/A for external module repos) | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 2. Entry exists in `doxygen/lang/900_release_notes.dox.tmpl` (for modules in the Qore repo; external modules have release notes in their .qm) | Pass | Native 2.3.0 release notes document fragment support, attribute character references, explicit reader lengths/encoding and wide XML output. |
| 3. `qore_user_module()` or `qore_external_user_module()` call in `CMakeLists.txt` | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 4. Module added to QMOD list in `CMakeLists.txt` | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 5. `.qm` file has `@section <lowercasemodname>intro` as first doc section — **must be all lowercase** (e.g., `avrodataproviderintro`, not `AvroDataProviderintro`) | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 6. `%modern` in `.qm` file — no redundant `%new-style`, `%require-types`, `%strict-args`, `%enable-all-warnings` | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 7. No parse directives (`%requires`, `%modern`, `%new-style`) in separated `.qc` files (check OUTSIDE of `@code` blocks only) | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 8. No `%include` usage (deprecated for modules) | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 9. Copyright 2026 on all new files | Pass | New qtest, QR worker, Python regression, design and audit have 2026 notices; changed native source/header already cover 2026. |
| 10. Directory layout: `.qm` inside `qlib/<ModuleName>/` directory (not at `qlib/<ModuleName>.qm` for multi-file modules) | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 11. No second `.qm` for the same module at `qlib/<ModuleName>.qm` | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 12. `ns=Qore::XX` matches the QoreNamespace constructor path | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 13. `%modern` directive present | Pass | xml-literal.qtest uses %modern; the .qr worker receives modern mode automatically. Deprecation warnings are intentionally disabled only to test existing legacy XML API entry points. |
| 14. Executable permission set (`chmod +x`) | Pass | Qtest and QR worker are executable. Python regression is invoked with python3. |
| 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus) | Pass | Qtest prepends local qlib; native module selected through QORE_MODULE_DIR. The QR worker requires only this repository binary module, with no same-repository user module dependency. |
| 16. External module dependencies use `%try-module` — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard `%requires` | Pass | xml is a hard same-repository dependency; QUnit is the required test framework. No optional external Qore module. |
| 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks | Pass | No filesystem operation in new native parsing/generation. Test subprocesses run a fixed script against an explicitly selected local module. |
| 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks | Pass | Fragment parsing uses XML_PARSE_NONET, forbids DOCTYPE and enables no external entity substitution or DTD loading. |
| 19. If filesystem/network ops exist, verify `QoreSandboxManagerHelper` usage | Pass | No new runtime filesystem/network operation; stream/file reader security remains unchanged. |
| 20. No `File::`, `Dir::`, `Socket::`, `HTTPClient::` usage without justification | Pass | Qore tests operate on in-memory strings and sandbox cancellation; Python subprocesses have bounded deadlines. |
| 21. All `for`/`while` loops that could iterate >100 times have `qore_check_cancel()` checks | Pass | New hash/root/namespace traversals check cancellation each iteration; attribute byte scan every 100 bytes. Reader loop uses the existing cancellation-aware read operation. |
| 22. Uses `qore_check_cancel()` (NOT deprecated `qore_check_io_interrupt()`) | Pass | Only qore_check_cancel is used; no deprecated interruption API. |
| 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations | Pass | Every node/hash/namespace step and each 100-byte attribute block satisfy the applicable interval. |
| 24. No blocking operations without cancellation support | Pass | No blocking external operation. Existing libxml2 parser limits and deterministic cancellation/recovery tests retained. |
| 25. Every action has `display_name`, `short_desc` (plain text, <80 chars), `desc` (markdown) | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 26. Every action has `options` populated via `getActionOptionFromFields()` — without this, the action shows an empty, unusable form | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 27. Every action has `output_type` set to a typed data type constant (e.g., `MyResponseDataType`) — not omitted | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 28. DPAT_API actions: provider has `"supports_request": True` and implements `doRequestImpl()` | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 29. DPAT_FIND actions: every option exists in `SearchOptions`, `getRecordTypeImpl()` returns `*hash<string, AbstractDataField>` | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 30. Scheme-based apps (with `"scheme"` in registerApp): actions use `"path"` and do NOT use `"cls"` — having both `scheme` and `cls` causes a runtime error | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 31. Single-key hash slices use trailing comma: `Fields{"key",}` (without trailing comma, `Fields{"key"}` returns the value, not a hash) | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 32. **Typed data type classes exist** for request and response types — inherit `HashDataType`, have `const Fields` hash, call `addQoreFields(Fields)` in constructor, export public constant at bottom (e.g., `public const MyDataType = new MyDataType();`) | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 33. Request/input types use `public` Fields (enables `ClassName::Fields` in action registration) | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 34. Response/output types use `private` Fields | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 35. Each field in data types has `display_name`, `type`, and `desc` (markdown-formatted) | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 36. Input fields have `example_value` where useful (string fields, endpoint URIs, SQL queries, etc.) | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 37. Fields with finite allowed values use `allowed_values` with `AllowedValueInfo` containing both `value` and `display_name` (Title Case, human-readable) — never bare values, never described only in text | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 38. Password/secret fields have `"sensitive": True` | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 39. `groups` uses `AppGroup` enum values from `qlib/DataProvider/AppGroup.qc` | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 40. App `logo` stored as separate file, loaded at module level in `Priv` namespace | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 41. App `desc` uses markdown: bullet list of capabilities, links to project website, business-language explanation of value | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 42. `display_name` is user-friendly ("Apache Avro" not "avro") | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 43. `short_desc` is plain text, under 80 chars, single sentence — no markdown | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 44. `desc` uses markdown: backticks for code/field refs (`` `field_name` ``, `` `True` ``, `` `pdf` ``), `\n\n` for paragraphs, `- ` bullet lists for enumerations, `**bold**` for caveats | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use" | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 46. No bare `True`/`False`/`NOTHING` — must be backtick-wrapped in `desc` | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 47. No bare field/option names in prose — must use backticks | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 48. Long descriptions (>500 chars) use bold section headers and bullet lists | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 49. **Factory registration in Qore repo**: every factory name registered in `qlib/DataProvider/DataProvider.qc` → `FactoryMap` (without this, module loads but doesn't appear in Qorus apps) | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 50. **`getRecordTypeImpl()` signature**: must be `private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options)` — NOT returning `*AbstractDataProviderType` | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 51. **Dependency JARs committed** (for JNI modules): JAR files in `qlib/*/jar/` may be gitignored — use `git add -f` to ensure they're tracked, otherwise CI compilation fails | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 52. JAR install rules in CMakeLists.txt for all dependency JARs | N/A | No new user module, public QPP class, DataProvider registration/metadata, factory or JNI dependency in this increment. |
| 53. **No workarounds**: No TODOs, FIXMEs, stubs, or partially-implemented features | Pass | Complete fragment documents are parsed, never pasted unchecked. Attribute references address XML normalization; explicit UTF-8/byte length fixes double decoding and truncation. Wide output uses an ASCII-compatible markup buffer because the escaping API requires one, then converts the whole result. No data dropping, flag workaround or suppressed memory error. |
| 54. **Exception safety**: C++ uses `ReferenceHolder` for Qore allocations, `std::unique_ptr` for C++ allocations, `*xsink` checked after every fallible operation | Pass | Preserved document outlives the reader and is freed after reset; xmlBuffer uses unique_ptr; Qore strings use SimpleRefHolder/TempEncodingHelper. Sink checks discard partial results and retain original errors. Fragment/encoding/cancellation Valgrind checks have zero errors/lost allocations; the final anonymous-namespace binary repeat is also clean. |
| 55. **Thread safety**: All mutable shared state protected by `std::lock_guard<std::mutex>` or documented as immutable-after-construction | Pass | Fragment reader/document/buffer are owned per call. No shared mutable state. Anonymous namespace gives helper internal linkage even where external Qore headers define DLLLOCAL as empty. |
| 56. **Type safety**: Strongly-typed `code<return(args)>` instead of untyped `code`; `static_cast` instead of C casts; typed hashdecls for results; enums where appropriate | Pass | Bounds-checked int conversion for libxml2 byte length, typed native callbacks/hash values and explicit pointer casts. Test values and result records are typed. |
| 57. **Performance**: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply | Pass | One parse/preserve/serialization per fragment; attribute scan and namespace scans are linear. ASCII-compatible output retains direct generation; only wider encodings convert the complete output once. |
| 58. **Error handling**: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable | Pass | Wrong types, NULs, DOCTYPEs, multiple/missing roots, trailing malformed input, undefined prefixes, encoding failures and cancellation reject with specific errors. Root count includes fragment keys; failed calls permit subsequent successful use. |
| 59. **Documentation**: Doxygen `@param`, `@return`, `@throw` on all public methods; `@par Example` with realistic business scenarios; `@note` for important caveats | Pass | Public native fragment section and realistic shipment example, updated throws, encoding/normalization notes and durable implementation design provided. Working-tree native docs build without warnings; documentation build hygiene remains a separate pending increment. |
| 60. **QPP flags**: `[flags=CONSTANT]` on methods that never throw; `[flags=RET_VALUE_ONLY]` on methods that throw but have no side effects | Pass | Existing XML generator flags remain RET_VALUE_ONLY because generation can throw. No new public QPP function/class or functional domain is introduced. |
| 61. **Security**: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code | Pass | Complete input byte lengths checked before int narrowing; fragments use memory-only parsing with normal limits; original document owns node pointers. No credentials or user-controlled format strings. |
| 62. **Correctness**: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features) | Pass | 11 native cases / 256 assertions cover positive, negative, boundary, cancellation and ten modern/legacy output variants. Forty raw documents/fragments are checked with both Expat and lxml for bytes, lexical content, attributes and ordered mixed content. Isolated affected suites/corpus match parent; all 483 working-tree XML/SOAP cases pass with no warnings/errors. |

Reviewed candidate SHA-256:

- `src/ql_xml.qpp`: `a805ad46a077c7e19912e286cb262cf3e787bbf37f94f9e808cc0b0232d9ed7e`
- `src/QoreXmlReader.h`: `ade2ef061cf4e26265b0e256a4760c46320f8c5a6ac14c9c7b58583b073460da`
- `docs/mainpage.doxygen.tmpl`: `e5240078de60a5e9cfc323652893c6183e06575d8817eb17676840f54f4f8c32`
- `design/xml-element-fragments.md`: `0e41dbc065d52db98e881eef4b8d1c29d2b5ae03cc2f22dc00ec20255671bdfa`
- `test/xml-literal.qtest`: `9b656f34cb4305c92007ad283b1c5e683d5066bc2a3c3d2e667b78a3ce2af6e4`
- `test/wsdl-interop/xml-fragment-encoding.qr`: `72e28c29eae26ef5b03a31fe17236f543c5b570455ecec1b3d7b291a55e3fa92`
- `test/wsdl-interop/test_xml_fragment_encoding.py`: `f1a771d71c70fd1093ed980a12c0edcb1d99bd9126dc51bbff1d24e3deaa5432`
