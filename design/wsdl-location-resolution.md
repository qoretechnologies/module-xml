# WSDL resource location resolution

Copyright (C) 2026 Qore Technologies, s.r.o.

`WSDLLib::resolveDocumentLocation(reference, document_location)` implements the
component transformation and dot-segment removal in
[RFC 3986 section 5.2](https://www.rfc-editor.org/rfc/rfc3986#section-5.2).
The base includes the containing document's filename and query. For example,
resolving `?revision=2` against
`https://partner.example/contracts/orders.wsdl?revision=1` keeps the filename and
replaces the query.

The private typed URI record distinguishes an absent authority, query or fragment
from an explicitly empty component. Resolution preserves escaped octets, repeated
path separators and query/fragment text; only literal path dot segments are
removed. The algorithm consumes the path using an advancing offset and a segment
stack. It does not repeatedly copy the remaining input. All state is local to the
call. An absent base scheme, unescaped ASCII spaces/control characters, or a
colon in a relative first path segment raises `WSDL-LOCATION-ERROR`. This resolver
splits URI components; scheme-specific address validation belongs to retrieval.

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

Non-file URL loaders (`WSDLLib`, `SoapClient` and `WsdlPollOperation`) retain the
complete source URI in `XsdSchema::document_location`. Callers supplying XML
strings can set the `document_location` construction option explicitly. It takes
precedence over `def_path` for reference resolution. `getUriDocumentLocation()`
extracts this URI from a loader source; bare paths and legacy file URLs continue
to use the directory interface.

Each external schema temporarily installs its own containing URI and restores
the caller's context on every exit. Resource keys omit fragments and retain
queries. Namespace checks still apply to every distinct reference, even when
bytes are reused. Previously stored fragment-bearing dependency/cache keys are
accepted when the canonical key is absent.

`XsdSourceInfo::location` retains the URI for each explicitly added source. Saved
schemas rebuild each source with its original URI and directory; saved services
first rebuild their original WSDL, then added sources, then restore their saved
active defaults. Local `addSchemaFile()` temporarily clears the URI context and
uses that file's directory, restoring the caller's URI even on failure. Older
saved source records without `location` use their retained directory.

Active schema identity consists of namespace, source bytes and the full URI when
available. A fallback directory does not affect that identity because it does
not participate in resolution. Sources supplied without a URI use their directory
instead; this also preserves cycle recognition for roots supplied as raw XML.
