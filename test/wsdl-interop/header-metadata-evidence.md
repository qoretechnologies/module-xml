# Concrete SOAP header metadata (P6-19)

Copyright (C) 2026 Qore Technologies, s.r.o.

The reduced fixture binds a type-based token with encoded use, an explicit
`urn:header-wire` namespace and SOAP encoding URI while its normal body is literal.
Before this change, the descriptor discarded namespace/encodingStyle and emitted
an unqualified token without block encoding metadata. The reproducer and logs
are recorded in the validation manifest; the committed regression constructs the
same source from the reduced fault-binding fixture.

[WSDL 1.1 section 3.7](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_soap:header)
applies independent body-style use, namespace and encoding metadata to headers,
with document style regardless of the operation. The pinned WSDL4J observer
confirms these header attributes in both SOAP versions. This is metadata evidence,
not full SOAP protocol or encoding conformance.

Descriptors now preserve and validate their own namespace/style. Encoded parts
must reference types, and unsupported explicit codecs reject. Accessor names use
the declared namespace; decoding matches that identity, validates block-local
SOAP encodingStyle and consumes it before schema validation. Literal element
names remain controlled by their schema. The codec URI is the existing
SOAP_ENCODING URI; absent style selects it as before.

Eight regression cases / 352 assertions pass, covering document/RPC, both versions
and directions, source/manual/saved/imported graphs, literal hints, namespace
scopes, invalid descriptions and attributes, complex values and real consumers.
Unknown part checks now report WSDL-ERROR instead of putting the description in
the exception code. Two golden header blocks now require their encodingStyle.
The ownership fixture had used nonexistent auth parts; it now declares real
parts while retaining exact destructor and cancellation assertions.

The affected gate passes 24 suites / 489 cases / 9,405 reported assertions. All
16 corpus commands meet expected outcomes; the six semantic reports are unchanged
apart from versions. Doxygen and astparser pass; all 62 audit checks are recorded
as 18 Pass / 44 N/A / zero Fail. No C++ or DGC implementation changed.

See [validation](P6-19-validation.json), [audit](audits/P6-19-header-metadata.md)
and [durable header design](../../design/wsdl-soap-header-values.md).

P6 remains open for headerfault handling, typed fault consumption, full binding
grammar, HTTP/MIME and pinned CXF replay. P7 must still address namespace-qualified
header enforcement, including the inherited unqualified accessor convention when
an encoded binding omits its namespace, and inherited protocol metadata. Complete
encoding/reference/array behavior remains P8. No phase boundary is claimed.
