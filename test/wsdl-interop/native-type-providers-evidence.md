# Native selected-type providers

Copyright (C) 2026 Qore Technologies, s.r.o.

The original W3C TypeSubstitutionUsingXsiType message decoded with capture
contains a Part2 wrapper around its number and description. Passing it to the
ordinary Part provider treated the wrapper as a record and reported the
required number field missing. The new explicit factories describe and validate
both forms: `XsdSchema::getNativeDataProviderType()` and
`WSMessage::getDataProviderType(True)`. Default factories keep their field shapes.

The provider resolves the selected name in the receiving schema, checks
substitution rules, converts the selected native fields, and applies existing
XML instance validation. It preserves the wrapper and derived fields. It does
not encode and decode XML to perform conversion. Its graph is completed before
publication; reconstructed component indexes are rebuilt in one pass. Anonymous
declarations retain their component identity instead of inventing a QName.
Finite choices use the existing scalar comparators, with QName lexical context
retained. Callback exceptions and cancellation restore scoped state.

The [implemented contract](../../design/wsdl-native-type-values.md) explains
ownership, metadata, variants and examples. This API implements Qore's chosen
native representation over XSD 1.0 [Element Locally Valid](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#cvc-elt)
and [QName identity](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#QName).
The wrapper is an API representation, not additional wire syntax.

Run with the environment recorded in [P5-05-validation.json](P5-05-validation.json):

```sh
qore -b --enable-debug test/wsdl-native-type-providers.qtest
qore -b --enable-debug test/wsdl-native-provider-http.qtest
QORE_EXEC_MODE=jit python3 test/wsdl-interop/test_native_type_providers.py -v
```

The unit suite passes 15 cases/521 assertions and the HTTP suite 1 case/64
assertions. Both run in AST, IR, JIT, tiered and AOT. HTTP coverage includes
actual SOAP 1.1/1.2 bindings, document/RPC parts, reconstructed providers on both
sides, and compatibility with capture disabled. The 105-case independent matrix
has 63 valid/42 invalid cases, 840 binding/direction/copy rows, 336 required
rejecting rows per conversion path and 1008 independently valid outputs per mode.
It verifies saved providers as well as saved values and schemas. The original
W3C case separately validates two original inputs and 24 outputs with exact
part numbers, derived description and Part2 identity; the SOAP 1.2 derivative
changes only the WSDL binding extension namespace and verifies the selected binding.

The final full gate passes 118 suites/1203 cases/58850 reported assertions,
including Cargo, CDA and SOAP consumers. Compiled Cargo/CDA tests use complete
temporary module packages with the original bundled assets. Module builds,
WSDL docs, the invoice example and supplementary matrices pass without warnings.
All 62 audit items are recorded as 27 Pass/35 N/A/0 Fail.

The default diagnostic survey and strict coverage preserve all earlier counts
and rows except the WSDL digest. Its 68 broader failures remain visible; explicit
provider capture is separately tested. P5 element substitution/final controls,
wildcard/mixed/generic content, complete nil/default/fixed and document identity
requirements remain. P6 owns binding/part-aware SoapDataProvider integration and
the operation lifetime finding; P6-P9 retain their complete plan scope.
