# WSDL redirect resource metadata

Copyright (C) 2026 Qore Technologies, s.r.o.

P6-10 consumes the installed Qore 3.0 FileLocationHandler resource API. No Qore
source or native XML code changes are required. The durable implementation is in
[resource location resolution](../../design/wsdl-location-resolution.md).

WSDLLib, SoapClient and WsdlPollOperation now carry effective retrieval URIs from
root and dependency responses into the WSDL catalog and schema parser. Requested
and intermediate redirect URIs map directly to final resource identities. Source
bytes and aliases survive serialization, while response headers and cookies do
not enter graph state. Import/include namespace checks remain per edge.

The resource APIs return bytes with charset metadata. Shared text decoding uses
BOM precedence, then transport charset, then XML declaration/signature detection
and the UTF-8 default, following [RFC 7303](https://www.rfc-editor.org/rfc/rfc7303#section-3.2).
Binary calls preserve the resource bytes. Local schema files use the same decoding.

## Focused regressions

`test/wsdl-redirect-locations.qtest` runs ten cases and 284 assertions:

- Root and nested WSDL/XSD redirects in synchronous, SoapClient and asynchronous
  loaders; all five redirect statuses; relative/absolute Location, queries,
  fragments, root cycles and schema cycles. Actual request targets are checked.
- Intermediate root aliases, duplicate imports through a second redirect,
  configured request headers, and offline reconstruction after stopping the peer.
- Required namespaces on WSDL and XSD imports after redirected cache reuse.
- Redirect loops and missing targets, followed by successful reads with the same
  configured client.
- Twelve encoding combinations, including non-ASCII content, transport/declaration
  disagreement, BOM precedence, UTF-16/32 byte order with and without BOMs, default
  UTF-8, saved text and exact binary retrieval.
- Failed incremental schema additions restore aliases, dependencies and caller
  context; the next valid addition fetches the resources again and saves offline.
- Different content at an already retained effective WSDL/XSD URI rejects in
  both synchronous and asynchronous loaders.
- Empty, BOM-only and unknown-encoding resources reject with parser/encoding
  exceptions, followed by a successful load.
- Custom resource handlers with known and unknown effective locations preserve
  containing filenames and query-only schema references, then reconstruct with
  the handler explicitly disabled. Literal data:// XML bypasses URL authority parsing.

Review caught implementation errors before acceptance: alias lookup left
an asynchronous schema cache key pointing to the requested URI, causing repeat
fetches; and asynchronous completion could replace previously retained content.
The final code updates the effective cache key and rejects conflicting content
before replacement. Unknown custom-handler metadata retains the requested full
URI instead of degrading to a directory base. Custom-handler dispatch bypasses
HTTP URL parsing, preserving literal data:// XML without a broad catch/retry.

The 37-suite broad gate passes 474 cases / 7,835 reported assertions. All six
corpus reports retain P6-09 semantic results. After the dispatch correction,
the focused redirect and five affected loader/integration suites were rerun;
validation retains both source fingerprints. Corpus paths are local files or
HTTP and are unchanged by custom-handler dispatch.

The [validation inventory](P6-10-validation.json) records exact commands, source
hashes and logs for the broader Qore/corpus gate, documentation and astparser.
The [audit](audits/P6-10-redirect-resources.md) covers all 62 skill checks.
No Valgrind run is required because this increment changes no C++.

P6 remains open for operation overloads, abstract input/output names, binding
selection and the rest of its binding/contract matrix. P7–P9 remain open.
No push or new image pipeline is part of this increment.
