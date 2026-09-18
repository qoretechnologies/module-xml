# P6-33 MIME media types and binding-directed bodies

Copyright (C) 2026 Qore Technologies, s.r.o.

## Requirements and root causes

[WSDL 1.1 section 5.3](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_mime:content)
permits a wildcard in either MIME component and omission of the type constraint.
[HTTP media types](https://www.rfc-editor.org/rfc/rfc9110.html#section-8.3.1)
and [parameter syntax](https://www.rfc-editor.org/rfc/rfc9110.html#section-5.6.6)
distinguish token names, case-insensitive type names, quoted values and
parameter-specific value comparison. [RFC 2387](https://www.rfc-editor.org/rfc/rfc2387.html#section-3.4)
defines multipart/related's type parameter as type/subtype;
[XOP section 5](https://www.w3.org/TR/xop10/#identifying_xop_documents) allows
parameters inside application/xop+xml's type value. Nested action values retain case.

The old matcher compared case-sensitive prefixes; the declaration parser split
on every slash. This accepted type suffixes, rejected valid uppercase names and
wildcard major components, and could not process quoted parameters containing
slashes. SOAP/XOP classification shared these faults. MIME decoding discarded
parameters and inferred SOAP/XML or attachment parsing from the wire type even
when the selected binding required an opaque body. Charset extraction retained
quotes and serialization could append a conflicting second charset.

The shared parser now checks complete syntax, compares declared constraints and
preserves metadata. Binding-directed dispatch keeps XML and multipart MIME values
opaque. A typed generic body hash preserves binary values. Exact classification
also exposed SOAP 1.2 serialization's unquoted URI action and the handler's
last-URI-segment routing guess; quoting and exact-action/body-element dispatch
fix those causes.

## Independent and consumer coverage

`regressions/wsdl-media-types/cases.json` contains 91 declaration/wire pairs and
18 SOAP/XOP classification rows. The independent Python runner uses a full HTTP
ABNF expression and Python's MIME parameter parser, separately from Qore's byte
scanner. Cases cover exact names, both wildcards, malformed tokens, whitespace,
quoted pairs and semicolons, empty slots, duplicate/conflicting parameters,
charset semantics, nested type parameters, exact action values and invalid wire
headers. Eight nested XOP type levels exercise the iterative comparator.

The executable Qore suite also covers source services, both saved-service forms,
detached operations, DataProvider acceptance/examples, both wire directions,
failed descriptor updates, alternate encodings and empty bodies. Live HTTP tests
exercise MIME strings including non-XML text with an XML Content-Type, binary
bytes, complete multipart documents and empty multipart uploads. Queues and
bounded request completion replace polling; on-exit cleanup closes listeners.
The existing SoapClient suite covers custom SOAP actions through the real handler.

## Full-corpus deadline

The full strict test's outer 60-second deadline expired even without a concurrent
build. The same 293-WSDL / 2,272-direction run completed successfully in 65.24
seconds with the previously approved 180-second worker bound. The whole gate
also runs independent validators and typed comparisons. The test now explicitly
uses that worker bound and a separate 360-second outer deadline; ordinary worker
defaults and all coverage assertions remain unchanged.

Validation totals and the exact audited file digests are recorded in
[P6-33-validation.json](P6-33-validation.json). This increment does not close P6,
SOAP protocol conformance (P7), attachment processing (P8), or final CI/runtime
acceptance (P9). MIME content preservation does not claim attachment interpretation.
