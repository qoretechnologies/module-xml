# WSDL ENTITY instance validation evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

## Requirement and reduction

The datatype/document distinction and normative references are in
[the implemented contract](../../design/wsdl-entity-values.md).
The native XML increment `abd5785` preserves declared entities in standalone XML;
this increment applies the selected type's requirement at WSDL instance boundaries.
No SOAP DTD policy is relaxed.

The initial reduction `/tmp/wsdl-p3-41-preflight.py` exercised 48 contracts and
768 consumer outcomes. Pinned Xerces rejected 336 emitted payloads, including
examples, while 192 conversions rejected datatype-invalid inputs and 240 emitted
valid payloads. WSDL retained ENTITY's primitive string identity but discarded its
selected document requirement. Rejecting at the initial lexical check would be
incorrect: an earlier member's failed datatype facet must still allow the next
union member. A document failure after selection cannot do so.

An immutable copy of the previous module and the initial six-case regression
suite is under `/tmp/wsdl-p3-41-before`. Its run records five failed cases,
including missing ENTITY rejections and an undeclared `xsi` prefix on standalone
nil output. The fixed suite additionally tests callbacks, cancellation,
concurrency and declaration namespace defaults.

## Implementation

The selected atomic/list identity retains an independent ordered list of entity
names. Target-specific captures preserve the actual union selection without
calling a member again. An element, attribute, array item or WSDL type-based part
checks the captured requirement after its complete datatype conversion. Detached
simple-type values, provider acceptance, enumeration compilation and primitive
value comparison remain datatype operations; provider-fed serialization is checked.

The nil branch now registers the instance namespace before emitting its attribute.
An audit reduction also showed why a default cannot be reparsed in the instance's
namespace scope. `getInstanceDefaultValue()` checks its compiled value using a
private output registry and returns that original typed value. QName and
QName/string defaults retain declaration identity after reconstruction and when
an instance rebinds their prefix. Neither change weakens ENTITY rejection.

## Verification inventory

- `wsdl-entity-values.qtest`: nine cases / 185 assertions, including exact
  error categories, union ordering/facets, list positions, defaults, absent/nil,
  retained XML/DTD rejection, reconstruction, callback counts, nested rejection,
  actual sandbox interruption, cancellation recovery and four synchronized threads.
- `wsdl-entity-consumers.qtest`: two cases / 64 assertions. Actual SOAP 1.1/1.2
  local HTTP traffic through SoapClient and SoapHandler covers valid records,
  invalid element/attribute/list/simple-content requests, invalid callback output
  and recovery. Type-based RPC/literal parts check both directions and reconstruction.
- `test_entity_wsdl.py`: 72 actual binding contracts, twelve datatype forms,
  three schema layouts and nine lexical/native variants. Outbound processing
  produces 2,880 outcomes and 888 independently valid documents. Inbound decoding
  plus seven consumers produces 9,216 outcomes and 7,392 independent document
  verdicts: 6,528 valid and 864 invalid. Every source schema and oracle diagnostic
  is checked. Counts, uniqueness and expected reachable stages are mandatory.
- The 92-suite gate passes 948 cases / 36,146 reported assertions. The new
  nine-case suite also passes in AST, IR, JIT and tiered modes. No C++ changed;
  the user instruction therefore does not require another Valgrind run.
- The executed documentation example and Doxygen build pass. Survey tests pass
  fifteen methods. Coverage tests retain the two explicitly recorded P6 binding
  version assertions; ENTITY's strict rejection and all other checks pass.

The worker's native/provider/retained outputs preserve exact lexical content and
attributes for accepted inputs. Failed decoding makes downstream consumers
unreachable; it is counted explicitly and cannot become a missing/skipped success.
Examples whose string-first member is valid must succeed. Other generated
candidates either validate independently or fail with the precise serialization
or sample-generation category.

## Corpus and remaining work

The strict selection adds `ENTITYElement`, `ENTITYAttribute`, `ENTITIESElement`
and `ENTITIESAttribute`: 126 descriptions / 1,172 message directions. All sixteen
new direction checks require `SOAP-DESERIALIZATION-ERROR`, no serialization, and
no failed requirement. All 1,060 exact-value checks remain successful.

The complete diagnostic coverage has 144 failure signatures, sixteen fewer.
The raw survey now has 110 decoding failures, 1,004 successful decodes,
1,002 serializations and 34 rejected outputs. Those changed counts are exclusively
the eight invalid ENTITY/ENTITIES inputs no longer being accepted. The four
valid-input invalid outputs and two serialization failures remain tracked for
their assigned phases. Original corpus hashes and every non-ENTITY case are
compared with the previous reports; none is removed or reclassified.

P3 remains active. Detached message-provider validation and native sample
selection are separate remaining integration criteria; the dateTime/time
leap-second decision remains pending. These are not counted as completed by the
provider-fed serialization tests. P4–P9 remain required.

The HTTP negative-response test also provides a concrete P7 reproducer: an invalid
server callback result is classified as Sender/Client by
`SoapHandler::makeSoapFaultResponse()` because it always passes `SoapFaultSender`
to `makeSoapFaultResponseWithCode()`. That generic classification predates this
increment and requires the P7 sender/receiver fault work. The P3 test asserts
that the result is rejected as `SOAP-SERVER-FAULT-RESPONSE` and that the connection
recovers; it makes no claim that the fault code/status is conformant. Both versions are reproduced in `/tmp/wsdl-p3-41-fault-reduction.log`;
SOAP 1.1 returns `soapenv:Client`, and SOAP 1.2 returns `soapenv:Sender`. The
same call remains executable in the final HTTP suite.
