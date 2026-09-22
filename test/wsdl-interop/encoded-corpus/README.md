# Independent SOAP-encoded message corpora

Copyright (C) 2026 Qore Technologies, s.r.o.

Both corpora are produced by implementations or authors independent of this module, and both are
reproducible from pinned inputs by `../encoded_corpus.py`. `../test_axis_peer.py` verifies them.

- `w3c-soap12.json` holds every test in the W3C "SOAP Version 1.2 Specification Assertions and Test Collection"
  whose messages use the SOAP 1.2 encoding or RPC namespaces: 66 tests with 150 messages. That includes the
  collection's own SOAPBuilders round 1 and 2 tests in SOAP 1.2 form (`SBR1-*`, `SBR2-*`). The source is
  `../normative/soap12-testcollection.html`, whose SHA-256 matches `../normative/sources.json`. Messages are
  kept verbatim. HTTP-framed examples keep their start line and headers separately.
- `axis-round2.json` holds the 31 SOAPBuilders round 2 exchanges that Apache Axis 1.4's interop client performs
  against Axis's own service (`../axis-peer/`), as raw wire messages and in canonical form.

Seven messages in the published collection are not well-formed XML. They are recorded verbatim with
`well_formed: false` and the parser's diagnostic, never corrected:

| Test | Message | Erratum |
| --- | --- | --- |
| T76 | both Node C responses | `test:echoStringResponse` closed by `</test:echoString>` |
| SBR1-echoBase64, SBR1-echoDate | Node A | prefix `sb` used without a declaration |
| XMLP-9 | Node C | `env:Value` closed by `</env:value>` |
| XMLP-14 | Node C | `inputString` closed by `</sb:echoString>` |
| XMLP-15 | Node A | `inputString` closed by `</sb:echoString>` |

Regenerate with `python3 -B test/wsdl-interop/encoded_corpus.py --write-w3c`, or
`--write-axis CAPTURE.jsonl` from an `AxisPeer` capture. Without options, the script checks that the W3C corpus
still reproduces from the pinned collection.
