# Concrete SOAP fault descriptions (P6-17)

Copyright (C) 2026 Qore Technologies, s.r.o.

The previous binding compiler discarded concrete fault metadata. Named faults
therefore reused ordinary output settings, and scalar literal detail failed for
RPC operations even though WSDL requires document-style fault detail. Reduced
baseline evidence also shows acceptance of invalid use, mismatched names, missing
fault extensions and multi-part fault messages.

Concrete descriptions now retain independent use, namespace and encodingStyle.
Compilation validates fault membership, the SOAP extension version, names, single
part count, encoded type-part requirements, allowed unqualified attributes and
empty extension content. One-way and notification operations cannot declare
faults. Manual registration and saved graphs validate compatible operation/fault
metadata before use. The existing SOAP 1.1 encoding codec is explicit; unknown
selected codec URIs reject instead of producing incorrectly labeled output.

Named serialization selects the actual binding's fault description, uses document
style, and keeps ordinary output MIME/body selection out of the detail path.
Encoded detail uses the fault namespace and carries encodingStyle on application
detail. Generic faults have no declared detail and can be emitted for a one-way
operation. Legacy standalone bindings without fault metadata require source
reload for named faults. Normal output headers remain available without mutation
of shared binding descriptions. Payload identity checks remain independent per
schema root; a header cannot donate an ID binding to fault detail.

Two existing local fixtures contained SOAP 1.1 fault extensions inside SOAP 1.2
bindings, with differently capitalized fault names. They now use matching SOAP
1.2 extensions and names; dedicated negative tests preserve rejection coverage.
Pinned external contracts and corpus inputs were not rewritten.

Validation:
- `wsdl-fault-bindings.qtest`: 9 cases / 272 assertions. Literal/encoded selection,
  both SOAP versions and operation styles, source/saved/detached/imported graphs,
  namespace scopes, literal hints, malformed metadata, manual registration,
  generic and one-way faults, schema/identity failures and live client/handler calls.
- Final affected gate: 22 suites / 473 cases /
  8,872 reported assertions; every case passes without warnings.
  Seven deliberately caught comparator assertions in soap.qtest remain accounted for.
- Two Python tests observe eight fault descriptions through checksum-pinned
  WSDL4J 1.6.3, independently confirming use/namespace/encoding metadata across
  SOAP versions and operation styles. This is declaration observation, not a
  complete SOAP protocol conformance claim.
- All 15 corpus/oracle commands produce their expected outcomes. Six reports
  differ from P6-16 only in versions: 2,096 native valid directions, 2,084 legacy
  valid directions, 12 approved legacy projection losses, 176 invalid source
  directions rejected.
- WSDL Doxygen and astparser checks pass. The audit records 18 Pass / 44 N/A /
  zero Fail across all 62 checks. No C++ changes; Valgrind is not required.

See [validation](P6-17-validation.json), [audit](audits/P6-17-fault-bindings.md),
[implemented design](../../design/wsdl-fault-bindings.md) and
[WSDL 1.1 section 3.6](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_soap:fault).

This increment does not complete P6. Headerfault metadata and handling, typed
fault consumption, the remaining HTTP/MIME matrix and pinned CXF replay remain.
The existing decoder continues to raise its raw fault exception; full fault
codes/reasons/roles/status rules belong to the remaining P7 work. Complete SOAP
encoding/attachment interoperability remains P8, followed by P9 CI acceptance.
