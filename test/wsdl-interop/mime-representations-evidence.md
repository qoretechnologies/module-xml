# Direct MIME representation selection evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

[WSDL 1.1 sections 5.2–5.6](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_mime)
define MIME alternatives and distinguish opaque content from schema-bound XML.
The previous compiler stored one content/XML description, rejected distinct XML
part alternatives and form/content combinations, and preferred opaque content
at runtime. A concrete reproducer requested `text/xml` through HTTP headers but
serialized the plain string `hello`, relabeling it as XML. Repeated XML declarations
of the same part were already equivalent; the defect concerns distinct mappings.

Direct HTTP declarations now retain content-by-part, XML-by-part, and whole-form
representations. Stable selectors identify them independently of prefix/order.
Content-Type chooses exactly one format or an explicit selector resolves overlap.
The user approved explicit selection for ambiguous formats. No validation failure
falls back to a different representation. Headers participate before serialization,
client and handler options select each direction, and legacy fields/native values
remain compatible. Equivalent repeated media declarations retain a usable default.

An independent ISO-8859-1 exchange found HTTPClient re-encoding the serialized
string to its configured default. SoapClient now sends HTTP binding bytes after
the binding's charset conversion. UTF-16 input then exposed generic charset
retagging after byte-order resolution. MIME content uses Qore's BOM-aware binary
conversion, while XML uses the existing resource decoder. Neutral UTF-16 XML
output includes its required BOM under [RFC 7303](https://www.rfc-editor.org/rfc/rfc7303)
and generic UTF-16 text follows [RFC 2781](https://www.rfc-editor.org/rfc/rfc2781).

The fixture matrix has 17 descriptions: content/XML combinations, duplicate and
reversed declarations, distinct content or XML parts, form/content choices, and
wildcard overlaps. Python ElementTree independently maps selectors and part/media
metadata, pinned Xerces checks grammar, and WSDL4J reports all declarations. The
published MIME schema's required-part rule rejects the two general-WSDL form
examples; this known schema/profile difference is recorded rather than weakening
validation or modifying pinned bytes.

The Qore suite passes 20 cases / 6,940 assertions through local/imported services,
both saved-service forms, detached operations, provider examples, 204 live HTTP
calls, concurrent selectors and post-error recovery. Negative cases cover invalid
HTTP headers, unavailable/ambiguous selectors, wrong roots, charset conflicts,
incompatible options and malformed saved maps. Forty-eight independent HTTP
exchanges cover both directions, source/saved services, overlapping/non-overlapping
formats and UTF-8/ISO-8859-1/UTF-16 wire encodings, including external little-endian
UTF-16 bodies.

All 32 affected Qore suites pass (1,547 cases / 51,937 assertions),
plus 13 independent gates and documentation/astparser checks: 47 gates total.
All 16 corpus commands meet their expected outcomes; six semantic reports match
P6-39. The legacy P5 projection diagnostic retains expected status 1 and is not
reported as full preservation success. Frozen source hashes bind the results to
the committed implementation. No C++ changes or push.

Commands, runtime identity and artifact checksums are in
[P6-40-validation.json](P6-40-validation.json); local diagnostic artifacts are in
`/tmp/xml-mime-representations/`. The [62-check audit](audits/P6-40-mime-representations.md)
records 18 Pass / 44 N/A / zero Fail. Durable design is in
[HTTP/MIME design](../../design/wsdl-http-mime.md).

This increment covers direct HTTP MIME alternatives. Mixed/nested multipart
layouts and attachment contract replay remain P6 work; detailed attachment and
SOAP-encoding acceptance remain P8. Complete HTTP URI execution still needs the
Qore request-local target API described in
`/tmp/xml-http-base-resolution/QORE-REQUEST-URL.md`. P6 is not accepted and P7–P9
have not been started prematurely.
