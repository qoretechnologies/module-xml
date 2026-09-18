# Independent SOAP attachment peer

Copyright (C) 2026 Qore Technologies, s.r.o.

This peer uses Apache CXF 4.1.3 and the pinned artifacts/notices in `../cxf-peer/`.
`golden.json` contains complete HTTP request/response body captures, headers and
independently chosen values for `echoData`, `echoDataWithHeader`, and
`echoAllAttachmentTypes`. The captures came from CXF client/server exchanges; Qore
was not involved. Random boundaries/Content-IDs are retained in the capture but
comparisons use the selected root XML infoset and each public part's media type and
exact decoded bytes. JPEG/GIF bytes remain binary; CXF's image encoders may choose
different lossless GIF compression when reading and re-emitting an image.

The peer WSDL is a separately named derivative of the original pinned
`cxf/swa-mime.wsdl`. Its only semantic edit removes `xmime:expectedContentTypes`
from the `DataRef` element whose type is `wsi:swaRef` (derived from `xs:anyURI`).
The [W3C media-content note](https://www.w3.org/TR/2005/NOTE-xml-media-types-20050504/#expectedContentTypes)
restricts that annotation to binary element content. The original is unchanged;
a test checks the exact derivative edit, with trailing whitespace removed. Removing this invalid annotation resolves
the CXF schema warning without changing message parts, bindings or wire types.
The `echoDataRef` reference protocol belongs to the separate attachment-reference
acceptance; this suite tests the three explicit `mime:content` operations.

Code generation explicitly enables MIME mappings for those operations with
`-mimeMethods`; otherwise CXF generates ordinary body parameters for attachments.
The generated `DataStruct` contains a non-serializable `DataHandler`, so this peer
does not request Java Serializable generation. Compilation uses `-Xlint:all -Werror`.

Run `python3 -B test/wsdl-interop/test_swa_parts.py -v` from the repository root.
The runner verifies pinned dependencies, generates and compiles the peer, checks
captures in both directions and runs 24 live CXF/Qore calls across source/saved
services and native/retained XML consumers. Sixty further exchanges test missing,
duplicate and incompatible parts in both directions, with successful recovery. Listeners report readiness and accept
a STOP event; teardown reaps processes with bounded completion deadlines.
