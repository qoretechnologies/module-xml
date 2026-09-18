# WSDL URI constraints and XSD absolute URI content (P6-35)

Copyright (C) 2026 Qore Technologies, s.r.o.

WSDL construction previously accepted relative or explicitly empty target
namespaces and absolute HTTP operation locations. The grammar's `xs:anyURI`
types alone cannot enforce the opposite context-specific rules. Construction now
checks these rules after lexical normalization, including imported documents.
Qore's URI mapping supplies classification without changing stored spelling.

The independent matrix also exposed a native datatype gap: libxml2's general
RFC 3986 parser accepts a bare scheme, although XSD 1.0's RFC 2396 lexical contract
requires an absolute URI to have a hierarchical or opaque part. The shared native
datatype validator now rejects missing content before a fragment, releases its
parsed URI on rejection, and preserves prior allocation-error propagation. URI
resolution keeps its separate RFC 3986 behavior. The checksum-verified build-tree
correction leaves the downloaded source intact. CMake's behavior probe exercises
16 values through direct conversion, DOM and streaming validation with recovery.

Requirements and independent adjudication:

- [WSDL 1.1 sections 2.1.1 and 4.5](https://www.w3.org/TR/2001/NOTE-wsdl-20010315):
  supplied target namespaces are absolute; HTTP operation locations are relative.
  Omitted namespaces and explicitly empty operation locations remain supported.
- [XSD 1.0 anyURI](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#anyURI) and
  [RFC 2396 collected grammar](https://www.rfc-editor.org/rfc/rfc2396#appendix-A):
  `a:` and `a:#fragment` are invalid datatype values; `a:/`, `a:?`, `a://` and
  `a: #fragment` have the required content. Scheme-specific URI restrictions are
  separate from datatype validity.
- Pinned Xerces assesses all 33 WSDL documents and the expanded 89-document
  URI/language matrix. Of the WSDL documents, 13 pass the published grammar but
  violate explicit WSDL absolute/relative rules; two bare-scheme values also fail
  grammar validation. These are classified semantic negatives, not oracle failures.
- The WSDL suite checks source, both saved-service forms, detached operations,
  imports, exact expanded component identity, providers/examples, both message
  directions and 21 real HTTP exchanges. The URI/language suite additionally
  checks native validation, saved schemas/providers, native and retained decoding,
  serialization rejection and primitive union identity.

Reproduction from the repository root:

```sh
export QORE_MODULE_DIR=build-debug:qlib:/home/david/src/qore/git/qore/qlib
qore -b --enable-debug test/wsdl-uri-constraints.qtest
qore -b --enable-debug test/xml-uri-values.qtest
qore -b --enable-debug test/wsdl-uri-language.qtest
python3 -B test/wsdl-interop/test_uri_constraints.py -v
python3 -B test/wsdl-interop/test_uri_language.py -v
```

See [validation inventory](P6-35-validation.json),
[full audit](audits/P6-35-uri-constraints.md),
[WSDL grammar design](../../design/wsdl-core-grammar.md),
[HTTP binding design](../../design/wsdl-http-mime.md) and
[datatype design](../../design/wsdl-uri-language-values.md).
Artifacts, including baseline failures, are under `/tmp/xml-wsdl-uri-constraints/`.
The native probe passes Valgrind with zero errors and no exit allocations. The
Qore URI suite has zero errors and zero definite, indirect or possible leaks with
`QORE_PCRE2_NO_JIT=1`, Qore's documented memory-checking setting; LLVM execution
mode remains unchanged and no suppressions are used. Initial PCRE2-JIT runs are
retained separately: they report a conditional-read diagnostic originating from
the QUnit reporter's call-stack string, and no lost allocations. Ordinary Qore,
HTTP, independent-peer and corpus tests keep PCRE2 JIT enabled.
This increment does not claim complete HTTP URI resolution or P6 acceptance;
binding combinations, MIME multipart and attachment replay remain required before
P7–P9.
