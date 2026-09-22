# Independent SOAP-encoded message corpora

Copyright (C) 2026 Qore Technologies, s.r.o.

The corpora are produced by implementations or authors independent of this module and are reproducible by
`../encoded_corpus.py`. `../test_axis_peer.py` verifies them.

- `w3c-soap12.json` holds every test in the W3C "SOAP Version 1.2 Specification Assertions and Test Collection"
  whose messages use the SOAP 1.2 encoding or RPC namespaces: 66 tests with 150 messages. That includes the
  collection's own SOAPBuilders round 1 and 2 tests in SOAP 1.2 form (`SBR1-*`, `SBR2-*`). The source is
  `../normative/soap12-testcollection.html`, whose SHA-256 matches `../normative/sources.json`. Messages are
  kept verbatim. HTTP-framed examples keep their start line and headers separately.
- `axis-round2.json` holds the 31 SOAPBuilders round 2 exchanges that Apache Axis 1.4's interop client performs
  against Axis's own service (`../axis-peer/`), as raw wire messages and in canonical form.
- `soap11-note.json` holds the 34 section 5 examples of the SOAP 1.1 W3C Note
  (<https://www.w3.org/TR/2000/NOTE-SOAP-20000508/>), rendered as the Note displays them. Each well-formed
  example also lists its top-level elements verbatim, so a test can place accessors and independent elements.
  The Note carries its submitters' copyright without redistribution terms, so the document itself is not kept:
  `../normative/sources.json` records its SHA-256, and `encoded_corpus.py --write-note NOTE.html` regenerates
  this file from a copy that matches it. Offline, the gate recomputes each example's well-formedness and element
  split from the quoted text.
- `soap11-note.wsdl` declares rpc/encoded operations for the Note's instance examples. The Note's schema
  fragments use the 1999 XML Schema draft syntax; the WSDL declares their XML Schema 1.0 equivalents, and the
  types the Note leaves undeclared follow its instances. `../../soap11-note-examples.qtest` binds the examples'
  `xsd` and `xsi` prefixes to XML Schema 1.0 and replaces the draft names `ur-type` and `uriReference` in
  examples 25 and 26 with `anyType` and `anyURI`.

Seven messages in the published collection are not well-formed XML. They are recorded verbatim with
`well_formed: false` and the parser's diagnostic, never corrected:

| Test | Message | Erratum |
| --- | --- | --- |
| T76 | both Node C responses | `test:echoStringResponse` closed by `</test:echoString>` |
| SBR1-echoBase64, SBR1-echoDate | Node A | prefix `sb` used without a declaration |
| XMLP-9 | Node C | `env:Value` closed by `</env:value>` |
| XMLP-14 | Node C | `inputString` closed by `</sb:echoString>` |
| XMLP-15 | Node A | `inputString` closed by `</sb:echoString>` |

Two of the Note's examples are not well-formed as published: example 17 closes `<element name="Book">` with
`</e:Book>`, and example 37 omits the closing quote of `SOAP-ENC:arrayType="xsd:string[10,10]`. Example 28 is
well-formed but declares `array-1` as `xsd:string[2]` with three members; the test expects its rejection.

Regenerate with `python3 -B test/wsdl-interop/encoded_corpus.py --write-w3c`, or
`--write-axis CAPTURE.jsonl` from an `AxisPeer` capture. Without options, the script checks that the W3C corpus
still reproduces from the pinned collection.
