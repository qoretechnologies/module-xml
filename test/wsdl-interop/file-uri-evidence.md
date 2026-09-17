# P6-08 local file URI evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

The file URI increment fixes the distinction between URI references and literal
filesystem paths. The previous implementation recognized schemes only with
`://`, concatenated the parsed file authority and path, and retained only a
directory base for local documents. As a result, `file:/absolute` and
`file://localhost/absolute` failed, escaped filenames were opened literally,
fragments became filename characters, and nested escaped imports lost their URI
context. The final seven-case regression suite fails on the isolated pre-change
source and passes on the new source with 291 assertions.

[RFC 8089 sections 2–4](https://www.rfc-editor.org/rfc/rfc8089#section-2) define
absolute paths, the localhost authority and filesystem name encoding.
[RFC 3986 section 2.4](https://www.rfc-editor.org/rfc/rfc3986#section-2.4) requires
separating URI components before decoding octets; section 5.2 governs relative
references. The new helper applies that separation at the file retrieval
boundary. Existing `file://relative/path` locations remain literal relative
paths; other file authorities retain that legacy interpretation and do not
select remote hosts.

`test/wsdl-file-uris.qtest` covers:

- Absolute, empty-authority, localhost and case-varied URI forms, with and without
  fragments; synchronous text/binary retrieval and all three WSDL loaders.
- UTF-8 filenames, spaces, hashes, question marks, percent signs, plus signs and
  literal percent-looking filenames; bare and legacy relative paths stay literal.
- Nested WSDL imports, XSD includes, namespace-bound message parts, cycles and
  canonical aliases. Source files are removed before saved graphs are rebuilt;
  typed validation and graph fingerprints remain equal.
- Added schema files retaining their own URI while restoring an active HTTP
  context, and inline WSDL roots recognized through canonical containing paths.
- Explicit file document-location options and older relative cache keys, including
  reconstruction after the caller-supplied cache is cleared.
- Missing absolute paths, queries (including empty queries), malformed escapes,
  NUL, invalid localhost authority, unescaped URI spaces and missing resources.

The existing callback regression tests exposed the need to select `try_import`
using the original reference and local resource kind after URI canonicalization.
That routing is fixed for WSDL and XSD. Inline-root cycle detection compares
canonical containing directories; local schema additions retain source URIs.
The existing document-location test now expects canonical file origins.

Final validation is recorded in [P6-08-validation.json](P6-08-validation.json):
36 affected Qore suites pass 464 cases / 7,547 reported assertions (including the
seven existing intentionally caught SOAP comparator assertions); the full
enterprise/partner suite passes 5 cases / 85 assertions. Both documentation
targets pass, and the installed astparser parses the full WSDL module with zero
errors. Pinned WSDL4J, the declaration/reference matrices, contract tests and
33 survey/coverage tests pass. Both-version native coverage retains 2,096
successful valid directions; legacy coverage retains 2,084 successes and its
12 documented projection losses; 176 invalid-source directions are rejected.

No C++ code changes or new runtime dependency are involved. All 62 audit items
are recorded in [the audit](audits/P6-08-file-uris.md). Durable behavior is in
[resource resolution](../../design/wsdl-location-resolution.md).
HTTP redirect-effective bases and the rest of the P6 binding matrix remain open;
this increment does not claim P6 completion.
