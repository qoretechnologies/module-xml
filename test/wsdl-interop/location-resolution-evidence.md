# P6-05 URI resolution evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

The previous directory helpers split raw URL strings on slashes, including those
inside queries and fragments. They also returned leading-slash references as
filesystem paths before checking an HTTP base. The asynchronous WSDL loader only
set its root directory for local files. These defects prevented HTTP schema
imports from resolving against the actual containing document.

`WSDLLib` now resolves URL components using the algorithm and examples in
[RFC 3986 sections 5.2–5.4](https://www.rfc-editor.org/rfc/rfc3986#section-5.2).
The full-document interface preserves the filename for query-only and
fragment-only references. Directory helpers retain their existing filesystem
contract. HTTP request targets retain queries and omit fragments. Qore's
`parse_url()` includes the query and fragment in `path`; the repair does not
assume that they arrive in separate fields.

`test/wsdl-location-resolution.qtest` covers all 42 RFC normal/abnormal examples,
component boundaries, repeated separators, escaped dot/slash octets, empty
query/fragment components, file URLs, bare filenames with spaces and invalid
references. Six real HTTP scenarios cover synchronous/asynchronous retrieval
with relative, root-relative and network-path schema includes, another nested
include, query slashes and fragments. The peer checks exact request targets.
Each service validates the imported integer element, rejects an invalid value,
and reconstructs and validates again after the HTTP server stops.

The new suite passes 5 cases / 131 assertions. See [validation](P6-05-validation.json)
for the affected suites, frozen runtime, corpus comparisons and documentation
build, and [audit](audits/P6-05-location-resolution.md) for all 62 checks.
The implemented contract is in [design](../../design/wsdl-location-resolution.md).

This increment repairs location resolution and existing XSD retrieval. WSDL
import catalog integration and full-document base propagation for query-only XSD
references remain P6 work. The isolated catalog prototype is not production
import support. No phase boundary or new CI result is claimed; these changes
remain local.
