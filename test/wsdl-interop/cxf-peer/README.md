# Offline CXF binding peer

Copyright (C) 2026 Qore Technologies, s.r.o.

This peer uses Apache CXF 4.1.3, JAXB and Jetty to check the module's WSDL binding
behavior independently. `CxfPeer.java` implements Java interfaces generated from
five pinned contracts: bare document/literal, RPC/literal, SOAP 1.2, RPC headers,
and the explicitly corrected document-header derivative. Its typed client and
server check the same 19 operations and values. CXF XML/JMS ports remain metadata
only; this peer selects supported SOAP ports.

Run from the repository root with Java 17 or later (JDK, including `javac`),
Python 3 and the local Qore module build:

```sh
QORE_MODULE_DIR=build-debug:qlib python3 -B test/wsdl-interop/test_cxf_peer.py -v
QORE_MODULE_DIR=build-debug:qlib qore -b --enable-debug test/wsdl-cxf-replay.qtest
```

No Maven download or public service is used by the tests. The dependency JARs are
unmodified Maven Central artifacts pinned by SHA-256 and size in `manifest.json`.
`pom.xml` records the dependency roots used to assemble them; Maven dependency
plugin 3.8.1's `copy-dependencies` goal assembled the closure. New versions require
an explicit manifest and interoperability update. Embedded licenses/notices remain
inside each JAR; missing notices are supplied in `notices/` or the existing
`../oracle/` WSDL4J distribution. Manifest entries identify every notice source.
These are test dependencies and are not installed with module-xml.

The test generates interfaces and JAXB classes in an owned temporary directory,
using CXF's `WSDLToJava`, `-suppress-generated-date`, `-faultSerialVersionUID 1`, and
`serializable.xjb`. The JAXB binding makes generated checked faults' detail beans
serializable too, so compilation passes `javac --release 17 -Xlint:all -Werror`.
Generated Java is not patched. The handwritten peer compiles with the same checks.

`golden.json` contains the complete request and response bodies captured from
CXF-to-CXF HTTP exchanges, with application values written independently from the
Java endpoint contract. Only end-to-end request headers and the response content
type/status are retained; connection-specific headers and dates are not fixtures.
The test replays those requests against the CXF server and checks its responses.
It also compares Qore-produced expanded names, attributes, element order and values
against the captures, treating the declared `xs:float` ticker price as a number.
String whitespace remains significant. Every case runs through Qore source and
saved services; Qore's replay suite additionally covers detached operations,
native capture, retained document XML, providers and sample generation.

Both live directions are required: Qore SoapClient to the CXF server, and the
CXF typed client to Qore SoapHandler. Listeners bind an ephemeral loopback port;
readiness is a pipe event. STOP and request completion drive teardown, with bounded
startup, call and shutdown deadlines and unconditional process reaping. No sleep
or readiness polling is used. Unexpected compiler/runtime diagnostics fail tests.

References: [CXF WSDL-to-Java options](https://cxf.apache.org/docs/wsdl-to-java.html)
and [CXF 4.1 Java baseline](https://cxf.apache.org/docs/41-migration-guide.html).
This binding matrix does not claim complete SOAP protocol, attachment or legacy
encoding acceptance; those have separate gates in the XML plan.
