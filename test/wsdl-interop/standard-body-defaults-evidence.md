# Standard SOAP body defaults and binding patterns (P6-16)

Copyright (C) 2026 Qore Technologies, s.r.o.

The approved WSDL 1.1 default is implemented: omitted `soap:body parts` selects
all message parts, including header-bound parts. Explicit lists are the partitioning
mechanism. [WSDL 1.1 section 3.5](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_soap:body)
is the normative reference; the pinned WSDL4J part-selection oracle remains unchanged.

The previous implicit exclusion caused missing body data. Correcting it exposed
native merge collisions and serializer message-container precedence that could
replace the body value with the header value. Decoding now uses separate `^body^`
and `^headers^` maps for overlapping parts. Serialization accepts these maps,
validates their shape and rejects conflicting header sources. Literal serialization
also rejects missing selected body parts. Ordinary disjoint merge shapes remain.

Standard SOAP/HTTP bindings reject notification and solicit-response, while
abstract operation discovery retains all four patterns. Manual registration and
saved graphs apply the same rule. The distinction follows
[WSDL 1.1 section 2.4](https://www.w3.org/TR/2001/NOTE-wsdl-20010315#_porttypes).
Legacy test notifications now remain abstract; the two HTTP response fixtures
have empty request messages and URL-encoded input, preserving their response tests.

The corrected HTTP fixture exposed an internal overload diagnostic for malformed
URL arguments and a Qore Mime empty-form return-type defect. URL argument types
are now checked before conversion. Qore/develop commit `ac5cfb171` fixes the empty
form at its source, with 26 passing Mime cases / 231 assertions and its own
62-check audit. It was not pushed. This gate selects the rebuilt local Mime module;
publication/CI must include that prerequisite. No installed modules were changed.

Validation:
- `wsdl-standard-body-parts.qtest`: 7 cases / 362 assertions. Both SOAP versions,
  styles and directions, source/saved/detached operations, explicit partitions,
  missing parts, nil/empty records, malformed maps, independent values and actual
  client/handler/provider exchanges. Schema-invalid bodies and headers reject.
- `wsdl-binding-patterns.qtest`: 7 cases / 138 assertions. Abstract discovery,
  four standard protocols, imported definitions, manual registration, saved and
  old standalone graphs, and live one-way/request-response calls.
- Full final-source Qore gate: 164 suites / 1,647 cases /
  82,855 reported assertions. All cases pass without warnings;
  the seven deliberately caught comparator assertions in soap.qtest remain accounted for.
- All 14 corpus/oracle commands produce expected outcomes. Six corpus reports
  differ from P6-15 only in versions: 2,096 native valid directions, 2,084 legacy
  valid directions, 12 approved legacy projection losses, 176 invalid source
  directions rejected.
- WSDL and SoapDataProvider Doxygen builds and the WSDL astparser check pass.
- Audit: 27 Pass / 35 N/A / zero Fail across all 62 skill checks. No C++ changes;
  Valgrind is not required.

Early regression attempts were superseded after fixing the HTTP/Mime defects
and preserving the ordinary provider validation-error contract. None of their
partial results replaces a final-source gate result.

See [validation](P6-16-validation.json), [audit](audits/P6-16-standard-body-defaults.md),
[selection design](../../design/wsdl-body-parts.md),
[header values](../../design/wsdl-soap-header-values.md) and
[binding patterns](../../design/wsdl-binding-patterns.md).

P6 remains open for concrete fault/headerfault rules, the remaining binding
and HTTP/MIME matrix and pinned CXF replay. P7–P9 remain open. An isolated next-step
fault prototype under `/tmp/xml-p6-fault-binding` is not part of this increment.
