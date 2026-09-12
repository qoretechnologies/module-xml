# Generic XML value evidence (P5-15)

Copyright (C) 2026 Qore Technologies, s.r.o.

The implementation follows XSD 1.0 [ur-type definitions](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#ur-type-itself),
[simple ur-type](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#simple-ur-type-itself)
and [local type validity](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-type).
The original generic decoder extracted only scalar text, rejected empty values,
and did not assess known content under anyType. Its ordinary provider accepted
invalid XML-data records without assessing the receiving type. The reduction in
`/tmp/wsdl-p5-15-preparation/` reproduces these positive and negative failures.

| Requirement | Implementation and regression evidence |
| --- | --- |
| Generic empty/scalar/structured values | `XsdGenericValueHelper` retains XML-data text, attributes and ordered children. `wsdl-generic-values.qtest` covers empty text, mixed content, CDATA, attributes and repeated child names. |
| Lax assessment | Known global attributes, child declarations and descendants under unknown wrappers are checked. Invalid numeric content, missing required attributes, abstract/unknown/unbound selected types reject with the intended error category. |
| Simple generic content | anySimpleType admits lexical text, namespace declarations and instance metadata, and rejects ordinary attributes or child elements. Native scalar projection and complete XML carrier APIs retain their documented distinct contracts. |
| Namespace identity | Inherited/rebound prefixes and originally unbound QName-like text survive detached XML, every mixed text/CDATA fragment, generated namespaces and both SOAP envelopes. Expanded child identity, original lexical values and order are asserted. |
| Selected types and precision | Explicit native wrappers and retained selected types keep their receiving registry. Arbitrary-precision numbers infer decimal and reuse exact decimal output; nonfinite numeric values infer double and reuse IEEE conversion. |
| Provider contract | `XsdGenericDataType` validates ordinary/native/saved/soft values, mandatory/optional variants, list/field consumers and detached declaration registries; malformed component state rejects reconstruction. |
| HTTP and cleanup | `wsdl-generic-http.qtest` uses actual SOAP 1.1/1.2 bindings with SoapClient, SoapHandler and SoapDataProvider, native and XML carriers, saved providers, both directions, synchronized concurrent calls and cancellation/recovery. |
| Recursive assessment | Declared anyType owns descendant assessment; wildcard dispatch and complete XML validation avoid repeating it. A 32-level valid tree and invalid known leaf are covered. |

`test_generic_values.py` generates four independent schema models and 112 input
documents. It checks native decoding/emission, direct XML-data emission, ordinary
providers and saved complete XML carriers. Native DOM/reader, lxml and pinned
Xerces assess the applicable inputs/outputs; comparisons include typed values,
expanded names, namespace bindings and order. The independent wildcard matrix
is also rerun because it shares declared-anyType assessment.

The final 135-suite gate has 1,319 cases and 65,233 reported assertions, including
three historically intentional caught negative SOAP assertions. Both new suites
pass Valgrind with zero errors and zero definitely/indirectly/possibly lost bytes.
The HTTP run retains the known system libnss_sss fstat(-1) warning, already traced
and assigned to P9; it is not suppressed. No C++ source or native artifact changed.
See [the validation inventory](P5-15-validation.json) and
[the full audit](audits/P5-15-generic-values.md) for exact commands and hashes.

The both-version diagnostic survey improves six input rows and adds six valid
output rows. Strict coverage improves twelve request/response directions for
AnyTypeElement and GlobalElementAbstract. Valid-input directions requiring fixes
fall from 40 to 28, broader failure records from 56 to 44; all 144 selected
WSDLs/1,388 directions continue to pass. Keyed comparison finds no regression.
Original fixtures, source adjudication and historical findings are unchanged.

Remaining findings retain explicit ownership:

- **P5-16:** element nil/default/fixed semantics. The separate 12-schema/756-document
  specification-derived diagnostic agrees with Xerces, and still exposes 415 WSDL
  verdict mismatches and 18 native DOM/reader false rejections involving empty CDATA.
  Native text-event handling clears the empty-content flag and checks nilled
  content before discarding zero-length character events. The correction belongs
  in libxml2 event handling. No input rewriting or validation bypass is proposed.
- **P9 runtime:** the existing 128-level QName consumer exceeds the normal stack
  limit with default AOT compilation. The exact previous committed XML source
  reproduces the same failure, independent of P5-15. The separate reproducer and
  native frame measurements are in `/tmp/wsdl-p5-15-aot-stack/`; full optimization
  also fails and is not a fix. Source AST/IR/JIT/tiered checks pass. The failing AOT
  result remains a failure and must be resolved before final runtime acceptance.
- Complete P5 mixed/identity semantics and every P6-P9 requirement remain in scope.

Routing these independent findings follows the execution prompt; it neither
waives an acceptance criterion nor claims complete P5 or P9 acceptance.
