# Concrete binding extension ownership

Copyright (C) 2026 Qore Technologies, s.r.o.

The previous compiler removed namespace prefixes before reading operation and
body declarations. It accepted SOAP 1.2 bodies in SOAP 1.1 bindings, HTTP operation
metadata in SOAP bindings and duplicate operation extensions. Duplicate SOAP
bodies raised an internal type exception; duplicate HTTP mappings were ignored.

The structure scanner now carries the enclosing protocol namespace into concrete
operation and message frames. It checks expanded names and declaration counts
before grouping. SOAP version/protocol mismatches, duplicate protocol/operation/
body declarations, duplicate or conflicting URL mappings and output URL encodings
raise `WSDL-ERROR`. Prefix aliases, default namespaces and absent SOAP operation
extensions remain supported. Unknown optional payloads stay opaque.

[WSDL 1.1 sections 3.2 and 4.2](https://www.w3.org/TR/2001/NOTE-wsdl-20010315)
describe the protocol-specific extension structures; HTTP URL mappings belong to
input messages. The individual extension schemas leave cross-protocol ownership
and contextual cardinality to component processing. All 65 fixture documents pass
pinned Xerces grammar validation. Independent namespace-aware Python inspection
classifies 24 supported documents and 41 invalid combinations; the latter are
explicit schema-valid semantic negatives, not schema rejections.

The positive omitted-action tests also exposed missing route registration for
document type-parts. `getTopLevelRequestNames()` now includes selected type-part
wire names alongside element declarations. Tests verify selected type-part routes,
reject an unselected type-part before callbacks, and then send another valid
request. This fixes the route owner instead of inventing an action.

The 67-case Qore matrix passes 1,924 assertions through local/imported source,
both saved-service forms, detached operations, provider examples and both request
and response conversion. It makes 156 successful HTTP calls and six rejected
unselected-route calls across SOAP 1.1, SOAP 1.2 and HTTP POST.

```sh
QORE_MODULE_DIR=build-debug:qlib:/tmp/xml-http-part-values/runtime:/home/david/src/qore/git/qore/qlib \
  qore -b --enable-debug test/wsdl-binding-extension-ownership.qtest
python3 -B test/wsdl-interop/test_binding_extension_ownership.py -v
```

The module path selects the current built Qore Mime fix documented in
[the preceding evidence](http-part-presence-evidence.md); Qore's working tree and
installation remain unchanged. [Validation](P6-37-validation.json) records the
full affected gate, corpus comparison, source hashes and logs under
`/tmp/xml-binding-extension-ownership/`. [Audit](audits/P6-37-binding-extension-ownership.md)
records all 62 checks. No C++ changes require Valgrind.

MIME multipart child grammar and alternative compilation remain separate required
P6 work; this increment does not claim complete binding or protocol conformance.

The final gate passes all 29 Qore suites (1,337 cases / 30,613 assertions)
and all 11 supplements. All 16 corpus commands meet expected outcomes; six semantic
reports match P6-36. Legacy P5 projection losses keep their expected diagnostic
status 1 and are not counted as conformance successes.
