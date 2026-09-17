# XML schema resource URI identity

Copyright (C) 2026 Qore Technologies, s.r.o.

Schema locations identify resources after XSD 1.0 anyURI whitespace normalization
and the XLink 1.0 UTF-8 escaping procedure. Raw Unicode and spaces in a schema's
`schemaLocation` are accepted without rewriting the schema. Existing percent
escapes retain their meaning: `a%2Fb.xsd` and `a/b.xsd` can identify different HTTP
resources. URI resolution also preserves literal path colons, query delimiters
and empty path segments such as `a//b.xsd`.

The native resolver keeps URI components in their raw form during resolution and
serialization. RFC 3986 dot-segment removal runs in place in linear time; encoded
dots and slashes remain encoded. Existing public decoded URI parsing retains its
decoded component values. Filesystem base paths retain libxml2's separate path
semantics, including actual Unicode/percent-containing directory names and
clamping parent traversal at an absolute root.

XML Base values are LEIRIs, so the base accessor returns raw Unicode and spaces
while preserving already encoded octets. It uses the native extended URI parser,
with an explicit string-terminator check, and shares the resolver's raw component
handling. No attribute text changes. XSD whitespace collapse applies to schema
location values, not to an XML Base path.

Includes, imports, redefines and runtime schema hints use the same anyURI mapping.
`xsi:noNamespaceSchemaLocation` is one anyURI; `xsi:schemaLocation` contains
namespace/location pairs. Both attributes can contribute schemas on one element.
Streaming readers obtain an available document URI from their locator when the
validation context has no parser context. Absolute hints also work without a
document base.

## Dependency selection

CMake's behavior probe covers namespace/QName identity and 142 URI checks:
106 direct URI/XML Base cases, 12 include/import/redefine cases and 24 runtime
hint cases. Hint tests include DOM and streaming validation, absolute/relative
locations, whitespace normalization, combined attributes and invalid typed values.
All probe resource callbacks are offline and reject unknown locations.

`AUTO` uses an installed library only when this complete probe passes; otherwise
it builds the checksum-pinned private libxml2. `SYSTEM` fails if the probe fails.
The package version is not an eligibility rule: a fixed distribution backport
remains supported. The private 2.15.4 build compiles checksum-verified copies of
`uri.c`, `tree.c` and the already QName-corrected `xmlschemas.c` through
`QoreXmlLibXml2UriFix.cmake`. The downloaded source tree and archive remain intact.
The existing hidden-symbol, offline-source and notice-installation rules apply.

## Qore resource loading

HTTP loading maps a direct raw location with Qore `qore_resolve_url()` using
`QRU_RELATIVE_BASE | QRU_ENCODE | QRU_NO_FRAGMENT` and uses HTTPClient's
pre-encoded URL option. This preserves existing URI escapes and correctly transmits UTF-8
paths as ASCII percent escapes. The response's `effective-url` metadata provides
the schema base, including after redirects; module-xml does not reconstruct
redirect chains.
The existing filesystem/network policies, TLS verification, cancellation and
callback ownership described in [schema attachment](xml-reader-schemas.md) apply.
Optional schema warnings use detailed debug logging; caught diagnostics do not
write to application stdout in ordinary Debug execution.

For example, an existing schema package can contain this unescaped source:

```xml
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:include schemaLocation="café 中文.xsd"/>
</xs:schema>
```

Load the package with `reader.schemaValidate("/opt/contracts/catalog.xsd")`;
the included resource resolves beside that file. An HTTP package with the same
source requests `caf%C3%A9%20%E4%B8%AD%E6%96%87.xsd` beside the final package URI.

## Independent verification

The offline Xerces worker maps raw anyURI references at its resolver boundary,
uses URI identity for catalog keys and rejects duplicate aliases. It implements
RFC 3986 resolution because Java's legacy URI resolver changes empty path
segments, query-only references and excess parent segments. Schema/document
bytes remain unchanged and unknown resources never fall back to external I/O.

Pinned Xerces 2.12.2 ignores XML Base during schema composition: its
`XSDHandler.doc2SystemId()` uses the document URI. Six exact false negatives remain
recorded separately; all twelve original component schemas pass the native loader
and reject invalid integer content. This oracle limitation is not a native
conformance waiver. The original URI finding remains preserved as historical
evidence and has an executable regression using its exact source bytes.

The standalone allocation test fails each URI/XML Base allocation and then checks
recovery. Resource and oracle regressions live in `test/wsdl-interop`; CMake's
provider tests cover a QName-correct but URI-broken library, fixed backports,
source integrity, provider switching, offline builds and cross-compilation.

Normative references: [XSD anyURI](https://www.w3.org/TR/xmlschema-2/#anyURI),
[XLink 1.0 escaping](https://www.w3.org/TR/2001/REC-xlink-20010627/#link-locators),
[XML Base Second Edition](https://www.w3.org/TR/xmlbase/) and
[RFC 3986](https://www.rfc-editor.org/rfc/rfc3986).
