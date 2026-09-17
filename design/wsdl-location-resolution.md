# WSDL resource location resolution

Copyright (C) 2026 Qore Technologies, s.r.o.

`WSDLLib::resolveDocumentLocation(reference, document_location)` delegates to
Qore 3.0 `resolve_url(document_location, reference, RESOLVE_URL_STRICT)` for
[RFC 3986 section 5.2](https://www.rfc-editor.org/rfc/rfc3986#section-5.2).
The base includes the containing document's filename and query. For example,
resolving `?revision=2` against
`https://partner.example/contracts/orders.wsdl?revision=1` keeps the filename and
replaces the query.

The private typed URI record distinguishes an absent authority, query or fragment
from an explicitly empty component. Resolution preserves escaped octets, repeated
path separators and query/fragment text; only literal path dot segments are
removed. Qore owns component merging and dot-segment removal; module-xml retains only
component access needed by file interpretation, directory adapters and request
target construction. All state is local to the call. An absent base scheme,
unescaped ASCII spaces/control characters, malformed percent escapes, or a colon
in a relative first path segment raises `WSDL-LOCATION-ERROR`. Only Qore's
`RESOLVE-URL-ERROR` is translated; cancellation and other exceptions propagate.
Scheme-specific address validation belongs to retrieval.

The existing `getLocationBase()` and `resolveLocation()` interface uses a directory
base. URL directory extraction discards the query and fragment before removing
the filename. Resolution handles root-relative paths using the URL authority and
network-path references using the base scheme. Repeated separators retain their
meaning. Bare filesystem paths still use filesystem directory and normalization
rules, including literal spaces in filenames. Calls without a base return the
location unchanged. A directory base does not retain a document filename; callers
requiring query-only or fragment-only document references must use the complete
URI interface.

Synchronous and asynchronous HTTP document retrieval construct the request target
from the URI path and query, excluding the fragment. An empty path becomes `/`.
The asynchronous root WSDL fetch records its HTTP directory so nested schema
references use the containing document's directory. Existing schema dependency
storage retains retrieved bytes and directory bases for offline saved-service
reconstruction.

File and URL loaders (`WSDLLib`, `SoapClient` and `WsdlPollOperation`) retain the
complete source URI in `XsdSchema::document_location`. Callers supplying XML
strings can set the `document_location` construction option explicitly. It takes
precedence over `def_path` for reference resolution. `getUriDocumentLocation()`
extracts this URI from a loader source, converting bare and legacy file paths to
absolute escaped file URIs. Inline XML has no inferred document URI.

Each external schema temporarily installs its own containing URI and restores
the caller's context on every exit. Resource keys omit fragments and retain
queries. Namespace checks still apply to every distinct reference, even when
bytes are reused. Previously stored fragment-bearing dependency/cache keys are
accepted when the canonical key is absent.

`XsdSourceInfo::location` retains the URI for each explicitly added source. Saved
schemas rebuild each source with its original URI and directory; saved services
first rebuild their original WSDL, then added sources, then restore their saved
active defaults. Local `addSchemaFile()` temporarily installs the file's URI and directory,
restoring the caller's URI even on failure. Older
saved source records without `location` use their retained directory.

Active schema identity consists of namespace, source bytes and the full URI when
available. A fallback directory does not affect that identity because it does
not participate in resolution. Sources supplied without a URI use their directory
instead; this also preserves cycle recognition for roots supplied as raw XML.

Local file retrieval uses FileLocationHandler 3.0
`AbstractFileLocationHandler::getPathFromFileUri()` and `getFileUri()` for the
absolute and `localhost` forms of
[RFC 8089 sections 2–4](https://www.rfc-editor.org/rfc/rfc8089#section-2):
`file:/srv/contracts/orders.wsdl`, `file:///srv/contracts/orders.wsdl` and
`file://localhost/srv/contracts/orders.wsdl` identify the same file. Scheme and
`localhost` matching are case insensitive; filename case is retained. The URI
is split before path octets are decoded once. A fragment is excluded from
retrieval and resource identity. Queries, malformed percent escapes, NUL octets
and missing absolute paths raise `WSDL-LOCATION-ERROR` before I/O. The WSDL adapter preserves its error category, strict character
policy and legacy literal path handling. Encoded spaces,
UTF-8 bytes, percent signs, hashes, question marks and plus signs name literal
filesystem characters; plus is not interpreted as a form-encoded space.

Bare paths and the existing `file://relative/path` interface use literal path
semantics and environment expansion. Other nonempty file authorities retain
that legacy relative-directory interpretation, rather than selecting a remote
host. Absolute URI paths do not expand environment variables. Resource keys
are absolute escaped file URIs without `localhost` or fragments; URI spelling
aliases share dependency bytes and cycle detection. Bare filenames containing
`#`, `?` or `%` are escaped when constructing the document URI, not parsed as
URI delimiters or decoded. For example, `/srv/contracts/order #1.wsdl` becomes
`file:///srv/contracts/order%20%231.wsdl`; an import of `types%20%231.xsd` then
loads the sibling `types #1.xsd`.

The synchronous loaders use the decoded local path directly. The asynchronous
loader translates its canonical file URI to the literal path interface of
`FileLocationHandler` only at the I/O boundary; its cache key remains a URI.
Local `try_import` callbacks receive the original unschemed reference even when
the resolved resource now has a canonical file URI. WSDL roots supplied inline
compare normalized containing directories when recognizing a root cycle.
All resource state is owned by the construction call; no process working-directory
change or shared cache is introduced.
