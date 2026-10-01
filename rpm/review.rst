XML RPM qualification review
============================

Copyright 2026 Qore Technologies, s.r.o.

Scope: portable XML recipe and isolated test runner; private libxml2 occurrence
bounds data-flow correction; XML response media types; concrete proxy defaults,
child dispatch and DAV namespace; strict API reference generation.

Validation: 304 Debug package suites and WebDAV CLI checks pass. Litmus passes
all 106 cases against Qore XML without Apache exceptions. Expanded mounted
GET/PROPFIND/COPY/MOVE/DELETE regression: four suites / 86 assertions. Native
particle/range/WSDL regressions under Valgrind: 23 cases / 1350 assertions,
zero memory errors or definite/indirect lost bytes, using PCRE2's upstream
Valgrind instrumentation with JIT enabled. Optimized native compilation has no
GCC occurrence-bound warning; three patch tests cover idempotence, unchanged
upstream input and rejection of unexpected/missing sources. All 18 native and
user-module API references pass with warnings treated as errors.

Logs: qore-packaging/results/xml-functional-7.log, xml-webdav-16.log,
xml-proxy-17.log, xml-valgrind-3.log, xml-release-1.log and xml-docs-2.log.
Live Salesforce and separately provisioned Java peer checks remain external
gates. Final committed RPMs and installed tests remain separate qualification;
no final RPM success is asserted here.

.. list-table:: Full audit checklist
   :header-rows: 1

   * - Check
     - Status
     - Evidence

   * - 1. Entry exists in doxygen/lang/120_modules.dox.tmpl (for modules in the Qore repo; N/A for external module repos)
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 2. Entry exists in doxygen/lang/900_release_notes.dox.tmpl (for modules in the Qore repo; external modules have release notes in their .qm)
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 3. qore_user_module() or qore_external_user_module() call in CMakeLists.txt
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 4. Module added to QMOD list in CMakeLists.txt
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 5. .qm file has @section <lowercasemodname>intro as first doc section — must be all lowercase (e.g., avrodataproviderintro, not AvroDataProviderintro)
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 6. %modern in .qm file — no redundant %new-style, %require-types, %strict-args, %enable-all-warnings
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 7. No parse directives (%requires, %modern, %new-style) in separated .qc files (check OUTSIDE of @code blocks only)
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 8. No %include usage (deprecated for modules)
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 9. Copyright 2026 on all new files
     - Pass
     - All new files and changed WebDAV sources/tests have 2026 notices.

   * - 10. Directory layout: .qm inside qlib/<ModuleName>/ directory (not at qlib/<ModuleName>.qm for multi-file modules)
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 11. No second .qm for the same module at qlib/<ModuleName>.qm
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 12. ns=Qore::XX matches the QoreNamespace constructor path
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 13. %modern directive present
     - Pass
     - Both changed Qore tests use %modern.

   * - 14. Executable permission set (chmod +x)
     - Pass
     - Both changed qtest files retain executable mode.

   * - 15. Uses %prepend-module-path  before %requires for in-repo modules (Qore and Qore modules only; not Qorus)
     - Pass
     - Development tests retain local module lookup. RPM tests are copied outside the checkout; explicit native preload and 17-module path validation select built/installed artifacts.

   * - 16. External module dependencies use %try-module — except modules delivered with the project itself (Qore ex: DataProvider, ConnectionProvider, QUnit, etc.) which use hard %requires
     - Pass
     - No new external binary import in these tests; the existing Litmus driver requires the system executable explicitly during RPM qualification.

   * - 17. No filesystem operations (fopen, open, creat, unlink, remove, rename, mkdir, rmdir, stat, chmod) without sandbox checks
     - Pass
     - No new native filesystem operation; the parser patch uses already-validated particle bounds.

   * - 18. No network operations (connect, bind, socket, getaddrinfo, gethostbyname) without sandbox checks
     - Pass
     - No new native network operation.

   * - 19. If filesystem/network ops exist, verify QoreSandboxManagerHelper usage
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 20. No File::, Dir::, Socket::, HTTPClient:: usage without justification
     - Pass
     - Filesystem and loopback HTTP operations are required integration fixtures; temporary roots and on_exit server cleanup isolate them.

   * - 21. All for/while loops that could iterate >100 times have qore_check_cancel() checks
     - Pass
     - No new unbounded native loop; the bounds correction changes one expression.

   * - 22. Uses qore_check_cancel() (NOT deprecated qore_check_io_interrupt())
     - Pass
     - No cancellation API changed or deprecated interrupt call introduced.

   * - 23. Check frequency: every 100 iterations for tight loops, every 10 for expensive iterations
     - Pass
     - No new native loop needing cancellation cadence.

   * - 24. No blocking operations without cancellation support
     - Pass
     - No new blocking native operation; test child processes have explicit timeouts and existing server teardown.

   * - 25. Every action has display_name, short_desc (plain text, <80 chars), desc (markdown)
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 26. Every action has options populated via getActionOptionFromFields() — without this, the action shows an empty, unusable form
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 27. Every action has output_type set to a typed data type constant (e.g., MyResponseDataType) — not omitted
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 28. DPAT_API actions: provider has "supports_request": True and implements doRequestImpl()
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 29. DPAT_FIND actions: every option exists in SearchOptions, getRecordTypeImpl() returns *hash<string, AbstractDataField>
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 30. Scheme-based apps (with "scheme" in registerApp): actions use "path" and do NOT use "cls" — having both scheme and cls causes a runtime error
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 31. Single-key hash slices use trailing comma: Fields{"key",} (without trailing comma, Fields{"key"} returns the value, not a hash)
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 32. Typed data type classes exist for request and response types — inherit HashDataType, have const Fields hash, call addQoreFields(Fields) in constructor, export public constant at bottom (e.g., public const MyDataType = new MyDataType();)
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 33. Request/input types use public Fields (enables ClassName::Fields in action registration)
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 34. Response/output types use private Fields
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 35. Each field in data types has display_name, type, and desc (markdown-formatted)
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 36. Input fields have example_value where useful (string fields, endpoint URIs, SQL queries, etc.)
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 37. Fields with finite allowed values use allowed_values with AllowedValueInfo containing both value and display_name (Title Case, human-readable) — never bare values, never described only in text
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 38. Password/secret fields have "sensitive": True
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 39. groups uses AppGroup enum values from qlib/DataProvider/AppGroup.qc
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 40. App logo stored as separate file, loaded at module level in Priv namespace
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 41. App desc uses markdown: bullet list of capabilities, links to project website, business-language explanation of value
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 42. display_name is user-friendly ("Apache Avro" not "avro")
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 43. short_desc is plain text, under 80 chars, single sentence — no markdown
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 44. desc uses markdown: backticks for code/field refs ( field_name ,  True ,  pdf ), \n\n for paragraphs, -  bullet lists for enumerations, bold for caveats
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 45. Descriptions use plain business language relating to common challenges — not just technical "what" but "why" and "when to use"
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 46. No bare True/False/NOTHING — must be backtick-wrapped in desc
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 47. No bare field/option names in prose — must use backticks
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 48. Long descriptions (>500 chars) use bold section headers and bullet lists
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 49. Factory registration in Qore repo: every factory name registered in qlib/DataProvider/DataProvider.qc → FactoryMap (without this, module loads but doesn't appear in Qorus apps)
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 50. getRecordTypeImpl() signature: must be private *hash<string, AbstractDataField> getRecordTypeImpl(*hash<auto> search_options) — NOT returning *AbstractDataProviderType
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 51. Dependency JARs committed (for JNI modules): JAR files in qlib/*/jar/ may be gitignored — use git add -f to ensure they're tracked, otherwise CI compilation fails
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 52. JAR install rules in CMakeLists.txt for all dependency JARs
     - N/A
     - No new module/class, DataProvider action/type/registration or Java dependency; documentation-only provider edits do not change those contracts.

   * - 53. No workarounds: No TODOs, FIXMEs, stubs, or partially-implemented features
     - Pass
     - Reads validated particle minOccurs/maxOccurs instead of dummy initialization or warning suppression. Strict docs remain enabled, and Litmus is mandatory.

   * - 54. Exception safety: C++ uses ReferenceHolder for Qore allocations, std::unique_ptr for C++ allocations, *xsink checked after every fallible operation
     - Pass
     - The parser correction adds no allocations. CMake verifies input/output digests and writes into the build tree; unexpected source content aborts before patch output.

   * - 55. Thread safety: All mutable shared state protected by std::lock_guard<std::mutex> or documented as immutable-after-construction
     - Pass
     - Proxy dispatch adds no shared state; each child derives its own request context, authentication and lock preconditions. Parser bounds remain request-local.

   * - 56. Type safety: Strongly-typed code<return(args)> instead of untyped code; static_cast instead of C casts; typed hashdecls for results; enums where appropriate
     - Pass
     - Proxy helper returns *hash<HttpResponseInfo>; constructors use concrete DummyWebDavHandler defaults. Qore tests and response hashes retain declared types.

   * - 57. Performance: No O(n²) where O(n) is possible; no unnecessary copies; coordinate descent uses incremental residuals not full matrix multiply
     - Pass
     - One child lookup and dispatch per mounted request; no new quadratic operation or data copy.

   * - 58. Error handling: All inputs validated (dimensions, empty data, unfitted models); C++ I/O handles EAGAIN/EINTR if applicable
     - Pass
     - Patch mismatch/missing-source negative cases pass. Missing proxy routes reject, missing Litmus is fatal for packaging, and module preflight rejects missing/wrong artifacts.

   * - 59. Documentation: Doxygen @param, @return, @throw on all public methods; @par Example with realistic business scenarios; @note for important caveats
     - Pass
     - Release notes explain charset/proxy changes. Proxy class docs give a mounted-path example; RPM docs cover private library maintenance, archive exclusions, test/installed commands and external gates. Strict API docs pass.

   * - 60. QPP flags: [flags=CONSTANT] on methods that never throw; [flags=RET_VALUE_ONLY] on methods that throw but have no side effects
     - Pass
     - No QPP signature/flag or public native API changed.

   * - 61. Security: No user-controlled format strings; no buffer overflows; bounds checking on array indices; no credentials in code
     - Pass
     - Private parser does not replace system libxml2. Source bundles exclude credentials/restricted fixtures, and proxy child dispatch enforces child authorization/preconditions. XML bytes and charset agree.

   * - 62. Correctness: Algorithms verified against reference implementations; edge cases tested (empty data, single sample, all-zero features)
     - Pass
     - All 304 suites, 106 Litmus tests, 86 targeted assertions and 1350 Valgrind assertions pass; optimized native build and strict docs pass.
