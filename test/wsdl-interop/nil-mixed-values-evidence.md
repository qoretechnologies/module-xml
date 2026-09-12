# P5-16c nil and ordered mixed values

Copyright (C) 2026 Qore Technologies, s.r.o.

Nil assessment previously bypassed receiving-element rules, allowed missing
required occurrences and discarded attributes. Inline complex types could inherit
nillability from a child. Mixed serialization skipped the ordered particle path,
and decoding collected text before children, losing their relative positions.
Ordinary record providers could not retain interleaved child segments.

Receiving `XsdElement` declarations now own nil assessment and occurrence checks.
`XsdNilValue` retains explicit presence and native attributes, using the same
attribute converters as ordinary complex values. Ordered mixed conversion first
attributes the complete child sequence with the existing bounded particle matcher,
then converts each item at its original position. Providers apply declared field
conversions without rearranging content. Samples retain the selected schedule.

| Requirement | Implementation and executable evidence |
| --- | --- |
| P5.N1: Receiving nil permission and lexical validity | `assessNil()` checks expanded `xsi:nil`, all four boolean spellings and XML whitespace; a non-nillable declaration rejects even false. Unit and independent matrix include child/parent independence, selected types and unknown attributes. |
| P5.N2: Nilled content and attributes | True nil rejects character/element content and fixed constraints. Comments/empty CDATA contribute no characters. Shared converters enforce required, prohibited, fixed, defaulted, typed and wildcard attributes, including QName identity. |
| P5.N3: Occurrence presence | Required absence, zero maximum, insufficient/extra occurrences and empty occurrence lists fail. Explicit carriers and portable type wrappers preserve optional presence; legacy omission and the single empty-complex record alias retain their contracts. |
| P5.N4: Native and provider values | Immutable nil carriers retain copy-on-write data and validate reconstruction. Ordinary/native providers retain finite choices, effective optionality, fields and list metadata. Invalid carrier/provider graphs and cancellation have exact exception checks. |
| P5.M1: Ordered mixed content | Text, CDATA, comments and declared/wildcard children retain order through complete particle attribution. Wrong order, missing children, invalid metadata and occurrence limits fail. |
| P5.M2: Repeated values | Adjacent scalar child occurrences may share a list; interleaved occurrences use numbered segments. Each list-valued child segment remains one occurrence, including an empty XSD list. Repeated groups and choices keep their complete schedule. |
| P5.M3: Namespace and selected identity | Scoped text retains lexical bindings; QName children, same-local-name collisions, selected types and substitution members retain identity. Generated redundant namespace declarations are omitted; explicit declarations remain. |
| P5.M4: Providers and samples | Ordered providers retain field conversion, soft values, finite choices, attributes, custom required groups, saved graphs and bounded examples. Mandatory native examples do not inherit optional omission from an inner provider. |
| P5.NM5: Consumer integration and cleanup | Native and retained schema values, actual SOAP 1.1/1.2 request/response bindings, saved service/message providers and real client/handler/SoapDataProvider exchanges pass. Queue/Counter barriers exercise concurrent namespace isolation; cancellation preserves caller values and restores scoped state. |

The normative sources are XSD 1.0 [Element Locally Valid](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-elt),
[complex content validation](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-complex-type)
and the XML Infoset's ordered [element children](https://www.w3.org/TR/xml-infoset/#infoitem.element).
The designs describe the explicit capture and legacy projection contracts:
[nil values](../../design/wsdl-element-nil.md) and
[mixed content](../../design/wsdl-mixed-content.md).

The nil matrix contains 20 schemas and 1,264 documents: 168 valid and 1,096 invalid,
with 5,056 actual SOAP directions and 1,062 independently valid outputs. The mixed
matrix contains 12 schemas and 480 documents: 72 valid and 408 invalid, with
1,920 actual SOAP directions and 852 independently valid outputs. Pinned Xerces
2.12.2 supplies schema/input/output verdicts; the mixed matrix also requires lxml
agreement. Independent comparisons check text/order, expanded names, nil meaning,
native numeric/QName attributes and child/list values. Missing, duplicate or failed
rows cannot improve counts. Both matrices remain strict in every execution mode.

The four new Qore suites have 29 cases and 721 assertions. Their unit and HTTP
coverage includes positive, negative, boundary, reconstruction, caller-isolation
and interruption cases. The SOAP test helper now compares namespace-normalized
XML values and has positive local-binding/shadowing cases plus negative namespace,
attribute and QName-value cases. Its wildcard assertion checks meaningful XML
instead of assuming namespace-bearing XML data must have the scalar data shape.

Full-gate totals, mode/AOT results, corpus comparison, fixture hashes, documentation
examples, memory checks and the complete 62-item audit are recorded in
[P5-16c-validation.json](P5-16c-validation.json) and
[the audit](audits/P5-16c-nil-mixed-values.md). Exact scripts and logs are under
`/tmp/wsdl-p5-16-values-validation/`; initial and intermediate failures remain
recorded. No C++ or main-Qore source was changed or installed.

The mixed prerequisite is reproduced on unchanged parent `c587d09` in
`/tmp/wsdl-p5-16-mixed-output/`: twelve of 21 valid non-nilled mixed cases failed
native output before this change. The nil matrix has no exception for those
cases. The older full nil/default diagnostic remains available separately; fixed
non-nilled empty/default assessment is explicitly owned by the next value
increment, rather than reported as passing here.

The current corpus closes twenty request/response direction failures for
MixedComplexContent and MixedContentType, while preserving previously passing
stages. All 144 selected WSDLs/1,388 directions pass. Eight valid-input directions
and 24 broader failure records remain. The independently reproduced default-AOT
QName stack-limit failure remains a P9 runtime failure; it is retained as a failed
supplement. Instance defaults/fixed values, identity constraints and all P6–P9
acceptance criteria remain required. This increment makes no complete SOAP or
WS-I conformance claim.
