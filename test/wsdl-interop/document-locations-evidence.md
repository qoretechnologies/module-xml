# P6-06 containing-document URI evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

Directory-only state cannot resolve a reference such as `?version=2` because the
containing filename has already been discarded. Non-file URL loaders now pass
the complete document URI through WSDL construction and nested XSD parsing, using
the [RFC 3986 section 5.2](https://www.rfc-editor.org/rfc/rfc3986#section-5.2)
resolver introduced in P6-05. `SoapClient` has its own raw-WSDL construction path
and is included explicitly. Fragment variants share retrieval keys while queries
remain distinct. Per-source URI and directory state are retained for serialization.

The focused suite `test/wsdl-document-locations.qtest` passes 9 cases / 97
assertions. It checks all three real HTTP loading paths, exact request targets,
fragment deduplication, typed values and invalid values, offline reconstruction,
identical source text under two document URIs, query cycles, missing dependencies,
failures inside nested documents, successful retries and local-file additions.
It also exercises the older source-record shape without a URI and dependencies
stored under fragment-bearing keys.

Two findings were fixed before the gate: full-URI cycle identity must ignore an
unused fallback directory, and service reconstruction must restore saved active
defaults after rebuilding the original WSDL and subsequently added schemas.
The test asserts both active URI and directory defaults after reconstruction.

See [validation](P6-06-validation.json), [audit](audits/P6-06-document-locations.md)
and [durable design](../../design/wsdl-location-resolution.md).
Bare filesystem and legacy file-URL loading retain their existing directory
interface. WSDL import catalog integration, canonical file-URI handling and the
remaining P6 binding matrix are still required. No P6 phase boundary is claimed.
