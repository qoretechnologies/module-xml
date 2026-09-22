# P8-01 independent encoding sources

Copyright (C) 2026 Qore Technologies, s.r.o.

P8-01 pins the independent sources that the SOAP encoding increments are measured against, and proves that
they run offline and reproduce. It adds no production code.

## Apache Axis 1.4 peer

`axis-peer/` pins the six-JAR Maven Central closure of `axis:axis:1.4` and the Axis 1.4 source release files it
needs: LICENSE, NOTICE and the SOAPBuilders round 2 interop service from `samples/echo`. The source release was
verified with its detached signature (good signature, key `C212662E12F3E1DD` in Apache's Axis KEYS file) and
its published MD5. The published `.sha` file does not match the archive; `manifest.json` records the discrepancy
and pins SHA-256 instead. Every JAR matched Maven's own `.sha1` sidecar.

Axis 1.4 runs on the installed Java 25 when compiled for `--release 17`. The gate generates the interop client
classes with Axis's own `WSDL2Java`, using the options in the pinned `build.xml`, and compiles Axis's sources
unchanged. Axis's own `TestClient` then performs all 31 round 2 operations against Axis's own implementation.
Axis's own comparisons report **31 verified, 0 failures**. The server starts from Axis's default configuration
held in memory and stops when the gate closes its standard input, so no sleeps or polling are involved. The only
local Java code, `AxisPeer.java`, compiles with `-Xlint:all -Werror` and no diagnostics.

## Corpora

- `encoded-corpus/axis-round2.json` holds the 31 captured exchanges in raw and canonical form. Axis reorders
  struct members and multi-reference blocks between runs, which SOAP 1.1 section 5 permits, so the gate compares
  canonical forms: references resolved, structs and maps compared by accessor name, array order kept, and
  `xsd:dateTime` masked because `echoDate` sends the current time. The raw messages exercise multi-reference
  values in 14 operations and `soapenc:Array` in 7, including two-dimensional and nested arrays.
- `encoded-corpus/w3c-soap12.json` holds the 66 tests of the pinned W3C SOAP 1.2 test collection whose messages
  use the SOAP 1.2 encoding or RPC namespaces: 150 messages, including the collection's SOAP 1.2 SOAPBuilders
  tests. Its SHA-256 matches the digest recorded for the P7 ledger. Seven messages are not well-formed in the
  published document. They are kept verbatim and recorded as errata.

## Validation

`test_axis_peer.py` passes 4 tests: pinned artifacts, warning-free harness, round 2 interop against the corpus,
and reproducible W3C extraction. It passed four consecutive times against fresh Axis runs, and three more after the server moved to the shared
`endpoint()` protocol (`READY<TAB>port`, `STOP`, silent output enforced). Two negative tests
confirm that it fails when a pinned JAR changes and when a corpus value changes (103.0 to 103.09 in
`echoStruct`). The assertion ledger verifier still passes after the collection entry in `normative/sources.json`
gained its path.

Neither corpus yet contains sparse or partially transmitted arrays (`soapenc:offset`, `soapenc:position`) or
`xsi:nil`. P8-02 adds independent fixtures for those, drawn from the SOAP 1.1 specification's own examples.
