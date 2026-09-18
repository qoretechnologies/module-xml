# HTTP and MIME declaration grammar evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

The 187-document matrix covers five HTTP and two MIME leaf declaration contexts.
It tests required attributes, namespace ownership, empty content, comments and
processing instructions, lexical whitespace, schema-instance attributes, explicit
part omission, GET/POST and extension namespace aliases.

The prior implementation accepted 93 invalid declarations and rejected two valid
MIME part references with surrounding whitespace in the initial 179-document
matrix. Attribute/content checks were missing for these extension nodes; the
compiler also used the original token spelling for message-part lookup. The
stream checker and known-attribute projection address those causes.

All 187 documents have independent Xerces assessments using unchanged schemas
from `https://schemas.xmlsoap.org/wsdl/http/` and
`https://schemas.xmlsoap.org/wsdl/mime/`, with original notices and pinned hashes.
The corrected core WSDL grammar is loaded before the extension schemas. The
resources are local; no schema hints or imports are fetched by the test.

Exactly seven rows have different module and validator acceptance. Each has an
incomplete xsi:schemaLocation pair. XSD 1.0 Structures section 4.3.2 requires
namespace/location pairs; Xerces accepts these unused hints. The matrix records
that semantic rejection separately from schema validity and asserts every identity.

The Qore regression exercises original services, both saved forms, detached
operations, provider acceptance/examples and request/response values. A separate
case runs 24 real HTTP calls through normalized verbs, operation/endpoint locations,
MIME part references and URL replacement. Eight declaration variants each run
through source, serialized and data-serialized services without overriding the
service's endpoint URL. Wrong response media types reject.

This matrix concerns direct leaf declarations. The published MIME multipart schema
has separate discrepancies against the WSDL text; it is not used to infer correct
multipart behavior here. Multipart grammar, binding combinations and attachment
interoperability retain their separate plan requirements.

## Reproduction

```sh
QORE_MODULE_DIR=build-debug:qlib:/home/david/src/qore/git/qore/qlib \
  qore -b --enable-debug test/wsdl-http-mime-grammar.qtest
python3 -B test/wsdl-interop/test_wsdl_http_mime_grammar.py -v
```

See [the implemented design](../../design/wsdl-http-mime-grammar.md).
