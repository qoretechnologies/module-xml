# P3 acceptance: scalar correctness and shared XML values

Copyright (C) 2026 Qore Technologies, s.r.o.

P3 is complete through `defff2c`, after 46 implementation increments and their
49 XML audit records. P1/P2 remain complete; P4-P9 remain open. The
[machine-readable register](P3-acceptance.json) maps each criterion to executable
tests, implemented designs, audit commits, exact source/runtime hashes and the
final test inventory. This acceptance does not claim full SOAP or WS-I conformance.

## Acceptance criteria

| Criterion | Evidence |
| --- | --- |
| Validate lexical forms before conversion | Integer, decimal, boolean, IEEE, calendar, duration, binary and name validators reject malformed/empty/trailing input with the intended SOAP or provider error. XML whitespace, CDATA/text joining and empty list/string distinctions have dedicated tests. |
| Separate lexical facets from value facets | Restrictions retain derivation-local pattern spellings while bounds, digit counts, enumeration and fixed values compare the appropriate exact primitive values. Tests include inherited/fixed facets, empty intersections and invalid schema declarations. |
| Preserve integer and decimal values | All thirteen integer builtins, signed/unsigned limits, arbitrary magnitudes, non-exponent decimal output and native round-trip formatting pass exact integer/Decimal assertions. The display rounding heuristic is not used to make schema values fit. |
| Respect IEEE target precision | Binary32 and binary64 conversion, ties, overflow/underflow, subnormals, signed zero, infinity/NaN, facets and union identity are compared with independent rational arithmetic. Native conversion also passes 1,380 C++ checks. |
| Preserve temporal semantics | Extended/negative years, absent/explicit/bounded timezones, calendar limits, partial dates including gMonth, arbitrary fractions, durations and partial ordering pass exact value assertions. The approved leap-second interpretation and validator disagreements remain documented. |
| Preserve collection and QName identities | Lists, nested unions, union-valued list items, inherited restrictions and reconstructed providers retain primitive-family/item-order/expanded-name identity. Name grammar, binary octets and selected ENTITY context have separate negative and integration tests. |
| Implement XSD patterns and valid examples | Unicode categories/name ranges, subtraction, repetitions, invalid grammar and adversarial expressions pass independent checks. Sample generation returns a fully validated value or XSD-SAMPLE-ERROR; structural matching avoids backend whole-expression limits. |
| Exercise all scalar consumers | Elements, attributes, simple content, field/message providers, Serializable reconstruction, examples and actual SOAP 1.1/1.2 client/server HTTP requests/responses are covered. Error and interruption recovery, immutable caller values and concurrent conversions have dedicated checks. |

The durable contracts are [scalar values](../../design/wsdl-scalar-values.md),
[IEEE facets](../../design/wsdl-ieee-facets.md),
[calendar values](../../design/wsdl-calendar-values.md),
[time/dateTime](../../design/wsdl-time-output.md),
[durations](../../design/wsdl-duration-values.md),
[binary values](../../design/wsdl-binary-values.md),
[QName values](../../design/wsdl-qname-values.md),
[union composition](../../design/xsd-union-composition.md),
[message providers](../../design/wsdl-message-providers.md), and
[checked examples](../../design/wsdl-sample-instances.md).
The corresponding increment evidence preserves independent implementation versions,
normative references, exact reductions and committed fixtures. Validator agreement
is never a substitute for the required exact value checks.

## Final verification

The local Debug runtime uses prefix `/usr`, the isolated tested Qore prerequisite
through `38e8e0e52`, and the local XML module. All executions use debugging; the
final Python matrix launches Qore with `-b` through its invocation wrapper. No
installation or push was performed. The module and core hashes are in the register,
so the isolated runtime's older embedded Git label is not mistaken for its source.

| Gate | Result |
| --- | --- |
| Affected Qore suites plus native IEEE suite | 99 suites / 1,006 successful cases / 40,743 reported assertions |
| Standalone native IEEE tests | 1,380 checks pass |
| Complete Python inventory | 69 files / 249 methods; only the four explicitly assigned diagnostic files below fail |
| New literal/HTTP consumer matrix | Three Qore cases / 1,336 assertions and 52 independent documents in AST/IR/JIT/tiered |
| Required W3C Qore suite | 10 cases / 238 assertions, included in the Qore total |
| Required survey harness | 15 methods pass, included in the Python inventory |
| Strict adjudicated corpus | 130 WSDLs / 1,260 message directions, zero selected failures; all 43 original P3 families included |
| Broad both-version survey and both-direction coverage | All 2,411 survey rows, counts, stage accounting and 144 diagnostic failure identities unchanged |
| Documentation | WSDL Doxygen and all three extracted scalar/IEEE examples pass without diagnostics |
| Native memory checks | Clean affected Valgrind runs are recorded per C++ increment, including the final XML-RPC/native HTTP prerequisite; no C++ changed after those checks |

`soap.qtest` has three intentionally caught comparator-negative assertions in its
nested accounting; all 20 cases pass. The initial parallel regex-consumer run
exceeded its unchanged 90-second worker deadline. The complete regex suite then
passed alone in 101.591 seconds total. The final schedule uses that isolated run
and executes the remaining inventory concurrently; it does not alter the test,
extend its deadline, skip it or accept its timeout as success.

The diagnostic Python failures remain failures:

- P4: `test_compositor_context.py`, four nested-choice exclusivity failures.
- P5: `test_xml_consumers.py`, one aggregate wildcard-example failure covering
  16 invalid examples and their 16 rejected conversions.
- P6: `test_coverage.py`, two selected-binding/version failures.
- P6: `test_soap_container_whitespace.py`, 26 failure records for header/body-part
  and single RPC argument processing, including its aggregate count assertions.

All 33 diagnostic failure records match the preceding inventory exactly; no new
error, warning, omission or skip is accepted. The corpus's eight originally
P2-labelled runtime anyType/mixed-content failures retain their documented P5 owner
from P2 acceptance; the other corpus failures are 76 P4 and 60 P5 records. P6-P8
also retain their broader requirements outside the payload corpus. In particular,
SOAP 1.2 envelope variants in the W3C archive are not counted as SOAP 1.2 binding
coverage; the authored actual-binding and HTTP matrices provide that coverage.

The reports alongside this file contain the final source fingerprint. The original
archive, findings and adjudication history remain unchanged. The next phase is P4:
ordered particles and complete group occurrence/matching behavior.
