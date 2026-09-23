# Independent MTOM/XOP peer

Copyright (C) 2026 Qore Technologies, s.r.o.

This peer uses Apache CXF 4.1.3 and the pinned artifacts and notices in `../cxf-peer/`. The contract is the
unmodified CXF test resource `../cxf/mtom_xop.wsdl`, verified against its digest in `../cxf/catalog.json`.

`MtomPeer.java` implements both operations as a server with MTOM enabled, and calls them as a client with MTOM
enabled or disabled. An interceptor records each received message's Content-Type and the number of binary parts
that its `xop:Include` elements referenced, so each side checks the other's wire form, not only the values:

- A request name `xop:<size>` or `inline:<size>` tells the CXF server whether the Qore client must have sent the
  value as a binary part. Qore sends an MTOM request only with its `mtom` option. Values of at least
  `MTOM_THRESHOLD` (1024) octets are then extracted, so the sizes 0, 1, 1023, 1024, 70000 and 1 MiB cross the boundary and cover a large part.
- The CXF client checks that the Qore `SoapHandler` answers MTOM requests with MTOM responses, with binary parts
  from 1024 octets, and ordinary requests with ordinary responses.

`testXop` carries octets through a `DataHandler`. For `testXopString`, whose `base64Binary` element declares
`xmime:expectedContentTypes="text/plain; charset=utf-8"`, CXF generates a `String` that holds the element's
base64 lexical form: the characters of inline content, or the base64 encoding of an `xop:Include`'s octets. JAXB
never optimizes it on output, so the peer writes the base64 encoding of the UTF-8 text.

Compilation uses `-Xlint:all -Werror`. Run `python3 -B test/wsdl-interop/test_mtom_xop.py -v` from the repository
root. The runner verifies the pinned dependencies and contract, generates and compiles the peer, and makes 12 live
runs of seven calls each: Qore's `SoapClient` and `SoapClientIo`, with and without MTOM, call CXF, and CXF's MTOM
and ordinary clients call the Qore handler, from both source and saved WSDL graphs. Listeners report readiness
and accept a STOP event, and the Qore server checks that every expected call arrived.
