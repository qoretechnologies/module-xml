# P5-14 element wildcard values and consumers

Copyright (C) 2026 Qore Technologies, s.r.o.

Parent: `8101f81`. The element wildcard decoder previously returned raw values
without assessing declarations or instance types. A 684-document diagnostic
accepted 184 invalid documents. The serializer used a legacy raw-member branch,
and the sample generator could not supply assessable strict wildcard values.

The implemented [representation and validation contract](../../design/wsdl-element-wildcards.md)
uses resolved global elements/types and complete particle attribution. Namespace
constraints apply in all processing modes; strict/lax assess declarations and
available instance types, including known descendants under unassessed wrappers.
Skip retains the subtree without schema assessment. Conversion retains lexical
XML data, while explicit XML values preserve comments, CDATA, mixed order and
namespace context. Declared fields keep their existing native conversion.

Global declaration/type registries are shared by completed namespace contexts,
detached components and providers. Failed additions restore earlier registries.
Serializable graph reconstruction validates metadata before typed assignment.
The core prerequisite `783ecefc0` corrects Qore's shared-container cycle scanner
and stale recursive-reference snapshots. It is deployed locally; module-xml
requires no ownership workaround. Original failing and reduced logs remain in
`/tmp/wsdl-wildcard-registry-leak/`, with root cause and resolved controls in
`RESOLUTION.md`; verification on the deployed runtime is separate under
`/tmp/wsdl-p5-14-qore-fixed/`.

## Requirements and checks

| Requirement | Regression evidence |
| --- | --- |
| XSD 1.0 cvc-wildcard namespace and processing constraints; cvc-assess-elt declaration/type assessment | `wsdl-wildcard-elements.qtest` processing, nested and ordered cases; `test_wildcard_elements.py` 36 schemas/684 documents |
| Preserve expanded names, namespace scope and lexical values | Structured namespace, inherited/rebound QName, inferred-hash and qualified lexical-child regressions; independent output infoset comparisons |
| Complete occurrence order with declared and wildcard positions | Ordered native field scheduling, repetitions, duplicate aliases, namespace failures and retained fragments |
| Lossless explicit XML carriers | `wsdl-wildcard-element-values.qtest`: comments, CDATA, text/child interleaving, inherited XML attributes, absent namespace bindings, conflicting contexts, invalid roots and prohibited document constructs |
| Detached schema/component lifetime and safe reconstruction | Registry publication/addition/rollback, detached roots/providers, malformed map/type metadata and full wildcard attribute consumers |
| Ordinary, native, saved and soft providers | Native field validation and portable builtin/complex type wrappers; wrong types, namespaces and content reject with the correct error category |
| Bounded valid samples | Namespace/process matrices, required occurrences, global-name collisions, max_items/max_elements bounds, detached type and provider examples |
| Actual SOAP 1.1/1.2 request/response consumers | `wsdl-wildcard-element-http.qtest`: SoapClient, SoapHandler, SoapDataProvider, saved components, four concurrent workers, cancellation and recovery |

The independent matrix checks all 684 decoder, direct serializer and ordinary
provider verdicts. Every successful emission receives native DOM/reader checks
and pinned Xerces-J 2.12.2 validation; expanded names, type/QName identities,
lexical values and child order are compared separately. AST, IR, JIT, tiered and
rebuilt AOT workers exercise the same matrix. Pinned lxml 6.1.1/libxml2 2.12.10
retains its previously adjudicated strict-instance-type discrepancy; no Qore or
Xerces failure is waived.

## Verification and scope

The [validation inventory](P5-14-validation.json) records final source/runtime
hashes, commands, corpus comparison and Valgrind results. The full
[62-item audit](audits/P5-14-element-wildcards.md) records every check. Focused
units cover 11 cases/530 assertions, retained values 4/26, and actual HTTP 4/157.
The acceptance gate passes 133 suites (1,305 cases/64,748 reported assertions)
and all 27 execution-mode/AOT/independent supplements on installed Qore `783ecefc0`.
Documentation and the original default/AST reproducer plus all four affected
full Valgrind suites pass. The HTTP test first exceeded its 30-second completion
deadline under competing heavy test load; the unchanged test passes when run
alone. Original failing evidence remains separate. No deadline was increased.

The both-version corpus has 2,453 diagnostic rows, 144 selected WSDLs/1,388
message directions with no selected failures, and 56 broader failure records.
Compared with P5-13, only the two invalid ExtendedSequenceStrictOther inputs
change to the required rejection, making their output rows unreachable. Forty
valid-input directions still require later P5 work; historical source fixtures,
adjudications and findings remain unchanged. The Qore deployment changes only
version metadata compared with the preceding P5-14 diagnostic results.

The HTTP Valgrind fstat(-1) warning is traced by a fresh syscall stack to system
libnss_sss during c-ares service lookup. It matches the environment finding
already assigned to P9 in P3-36; no suppression or clean-environment claim is
made. This is separate from Qore's resolved shared-container memory defect.

Declared xs:anyType conversion and anySimpleType provider validation remain the
next P5 generic-value increment, with positive and negative failing diagnostics
under `/tmp/wsdl-p5-15-preparation/`. Mixed/generic content, complete
nil/default/fixed and identity semantics, followed by every P6-P9 binding,
protocol, attachment, platform and CI requirement, remain in scope. No complete
P5 acceptance or SOAP/WS-I conformance claim is made here.
