# Independent HTTP MIME tree peer

Copyright (C) 2026 Qore Technologies, s.r.o.

`nested.wsdl` is a local two-part WSDL 1.1 contract with a nested related entity. The inner entity offers opaque `text/xml` and schema-bound XML alternatives. The other outer entity carries binary media. Neither test direction uses an external service.

`test_mime_entity_tree.py` uses Python's standard email parser/writer to validate Qore output and produce independent input. It checks explicit root identity, entity order, nested XML and exact binary bytes, Base64 and quoted-printable transfer encodings, source/saved/detached operations, live Qore client and handler exchanges, and malformed-input recovery. Readiness uses events and pipe notifications with bounded deadlines; no sleeps or polling are needed.

From the repository root:

```sh
QORE_MODULE_DIR=build-debug:qlib python3 -B test/wsdl-interop/test_mime_entity_tree.py -v
QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug test/wsdl-mime-entity-tree.qtest
```

The contract follows [WSDL 1.1 sections 5.2–5.6](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_mime:multipartRelated) and the related root semantics of [RFC 2387](https://www.rfc-editor.org/rfc/rfc2387.html). The tests require the installed Qore Mime delimiter and related-writer fixes.
