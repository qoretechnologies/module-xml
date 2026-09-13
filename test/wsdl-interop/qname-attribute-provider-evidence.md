# QName attribute provider evidence (P5-19c)

Copyright (C) 2026 Qore Technologies, s.r.o.

An existing defect discovered while testing NOTATION records prevented construction
of providers for enumerated or fixed QName attributes. `addAttributeFields()`
wraps a scalar provider in `XsdAttributeDataType`, but `XsdQNameDataField` looked
only for a direct QName provider or its collection item. An atomic attribute has
no item provider, so construction raised `XSD-SIMPLETYPE-ERROR` before any value
could be checked. The baseline reproducer and log are retained in
`/tmp/wsdl-p5-19c-notation-values/qname-attribute-baseline.qr` and `.log`.

The wrapper now exposes its scalar validator with `getWrappedType()`. Choice
resolution uses it while ordinary conversion keeps the original attribute
presence check. Collection-item semantics and saved formats are unchanged.
There is no fallback or weakened validation. See the implemented
[QName design](../../design/wsdl-qname-values.md).

Focused coverage includes optional/required copies, saved wrappers and fields,
atomic/repeated choices, alias identity, invalid namespaces and unbound prefixes,
atomic failed choice updates, local/referenced/group attributes, defaults, fixed
unrestricted QName attributes and simple content. Ordinary and native providers
are tested before and after serialization; native XSD validation checks output.
Both actual SOAP HTTP bindings exercise request and response providers, saved
services/providers and successful recovery after rejected values.

Acceptance: all 38 affected Qore suites and six supplements pass, including all
four execution modes and Python survey/QName declaration tests. The focused suites
pass 437 unit assertions and 468 HTTP assertions. Both-version surveys and strict
coverage in legacy/native modes retain all parent results; only the expected WSDL
source hash changes. WSDL docs and metadata generation pass without warnings.
No native code changed, so no additional Valgrind run is required.

See the [validation inventory](P5-19c-validation.json) and
[full 62-item audit](audits/P5-19c-qname-attributes.md): 20 Pass, 42 N/A, zero Fail.
Frozen inputs, commands and logs are retained under
`/tmp/wsdl-p5-19c-qname-attributes/`. The installed Qore library still matches
verified runtime `8c0c22c15`. No main-Qore mutation, installation or push.
NOTATION integration remains the next increment, followed by identity constraints
and typed accounting. This prerequisite does not close P5 or P6–P9.
