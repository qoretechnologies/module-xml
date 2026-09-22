# Offline Apache Axis 1.4 rpc/encoded peer

Copyright (C) 2026 Qore Technologies, s.r.o.

This peer is the independent SOAP 1.1 section 5 (rpc/encoded) implementation for P8. JAX-WS and therefore
CXF do not support `use="encoded"`. Axis 1.4 is the reference rpc/encoded implementation of its time, and the
SOAPBuilders interop tests it ships exercise arrays, multi-reference values, structs, maps and the XSD
scalar types.

Run from the repository root with Java 17 or later (JDK, including `javac`) and Python 3 with lxml:

```sh
QORE_MODULE_DIR=build-debug:qlib python3 -B test/wsdl-interop/test_axis_peer.py -v
```

No network access is needed. `jars/` holds the unmodified Maven Central closure of `axis:axis:1.4`, which
`pom.xml` records and `maven-dependency-plugin` 3.8.1 `copy-dependencies` assembled. `axis-jaxrpc` and
`axis-saaj` are Maven relocations to the `org.apache.axis` group. `manifest.json` pins every JAR by size and
SHA-256, and each JAR also matched Maven's own `.sha1` sidecar when it was pinned.

The Axis JARs embed no license or notice files. `notices/` holds the LICENSE and NOTICE of the Axis 1.4 source
release, `axis-src-1_4.tar.gz` from `archive.apache.org`, which is also the source of the pinned sample files in
`contracts/`. That release was verified with its detached signature (good signature from David Blevins,
fingerprint `B757 4789 F501 8690 043E 6DD9 C212 662E 12F3 E1DD`, key in Apache's Axis KEYS file) and its
published MD5. The published `.sha` file does not match the archive; the manifest records both values.
`axis-wsdl4j` is IBM WSDL4J under the Common Public License, covered by `../oracle/wsdl4j-license.html`.
commons-discovery and commons-logging embed their licenses.

`contracts/` holds the SOAPBuilders round 2 interop service from Axis's `samples/echo`, unchanged:
`InteropTest.wsdl` (31 rpc/encoded operations), Axis's implementation `InteropTestSoapBindingImpl.java`, its
header handlers, its deployment descriptor `deploy.wsdd`, its interop client `TestClient.java`, and
`build.xml`, which records the stub generation options. The test generates client classes with Axis's
`WSDL2Java` using those options (`-T 1.1`, both interop namespaces mapped to `samples.echo`) and compiles the
generated and sample sources unchanged.

`AxisPeer.java` is the only local Java code, compiled with `javac --release 17 -Xlint:all -Werror`:

- `server DEPLOY.wsdd` deploys the pinned descriptor into Axis's default server configuration held in memory,
  prints `READY<TAB>port`, and stops on `STOP` or end of input, following the shared `endpoint()` protocol of
  `../test_cxf_peer.py`. No administration state is written to disk.
- `client URL` runs Axis's own `TestClient.executeAll()` and reports the outcome of Axis's own comparisons.
- `RecordingHandler`, configured in the client's response flow, appends each exchange's request and response
  SOAP parts to the JSON-lines file named by `-Dqore.axis.capture`.

The gate routes Axis's commons-logging output to its no-op implementation. Both processes then stay silent, so
any output on standard error fails the gate. Failures still surface through the client's `VERIFIED`/`FAIL` lines
and exit status.

Axis orders struct members and multi-reference blocks differently from run to run, which SOAP 1.1 section 5
allows because struct accessors are distinguished by name. `../encoded_corpus.py` therefore compares exchanges
in a canonical form: references resolved, struct and map members compared by name, array order kept, and
`xsd:dateTime` text masked because `echoDate` sends the current time.

These are test dependencies and are not installed with module-xml.
