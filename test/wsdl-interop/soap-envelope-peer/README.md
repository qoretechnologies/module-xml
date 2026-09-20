# SOAP envelope peers

Copyright (C) 2026 Qore Technologies, s.r.o.

`contract.wsdl` supplies actual SOAP 1.1 and 1.2 bindings for an invoice reference.
`peer.qr` runs a bounded loopback handler or a persistent client per test group.
Python's HTTP implementation sends malformed requests and controlled responses;
lxml independently resolves names and validates every emitted envelope/fault
against the pinned W3C schemas in `schemas.json`. Source/saved/data graphs,
protocol failures, callback exclusion and recovery are covered in both directions.

The three upstream schema files are unmodified and retain their original notices;
`schemas.json` records retrieval URLs and byte hashes. Schema imports are resolved
offline and unexpected resources reject. These envelope checks supplement the
pinned CXF implementation gate; they do not claim complete SOAP profile coverage.
