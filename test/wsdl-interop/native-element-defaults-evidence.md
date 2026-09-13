# Native canonical element-default evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

P5-18i builds on `ebaf11a`. The user approved the canonical-actual-type PSVI
interpretation on 2026-09-13. The [decision record](default-identity-investigation.md)
and [implemented native design](../../design/native-element-defaults.md) explain
the value/lexical distinction and declaration namespace scope.

## Root causes

The native end-element validator used `decl->value` directly and explicitly
claimed canonical spelling was irrelevant. Its ordinary instance namespace
lookup also reinterpreted default QNames using the instance's bindings. Replacing
that path with canonical assessment and scoped declaration lookup fixes validity
and the instance values used by identity constraints without changing original
XML or declaration metadata.

The QName parser, value factory callers and `xsi:type` expansion had unchecked
allocations. Failures could become a different expanded name or a successful
conversion with incomplete data. Deep-copy branches for QName, NOTATION, strings,
integer/decimal and binary data likewise returned partial values after a failed
string allocation. Checked ownership and explicit lookup status resolve these
paths, with single-failure and persistent-failure sweeps and recovery tests.

## Reproducible cases and independent comparison

`test_element_defaults.py` reproduces `fixtures/element-defaults.json`: 68 schemas
and 263 instance documents. Forty schemas/200 documents distinguish source-only
and canonical-only restrictions for ten atomic families, default/fixed constraints,
empty content, comments, empty CDATA and explicit text. Seven documents distinguish
string, boolean and QName instance identity. Forty-eight documents cover declaration
prefixes, default/no namespaces, implicit `xml`, QName lists and mixed lists.
Eight NOTATION documents compare empty defaults, explicit expanded names and
incorrect namespaces. Native rejection categories and unchanged parsed/DOM input
are asserted on each relevant path.

Pinned Xerces 2.12.2 is checked independently with exactly 15 recorded differences:

- Nine existing time/date canonicalization differences: midnight's day anchor and
  omitted recoverable date offsets.
- Four explicit PSVI interpretation differences: Xerces retains the declaration's
  boolean value where the approved interpretation assesses canonical `true` as the
  actual string or QName type.
- Two NOTATION defaults: Xerces reassesses unprefixed `item` using the instance's
  empty default namespace and rejects the declaration's `{urn:part}item` value.
  Explicit `t:item` passes. The implementation preserves declaration namespace
  identity, consistent with its QName/default contract. QName and NOTATION value
  spaces are described in [XSD Part 2](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#QName).

No upstream corpus fixture or historical result is rewritten. The original
40-schema diagnostic and both prior native prototypes remain under
`/tmp/wsdl-p5-18i-default-assessment/`. The WSDL decoder still has 66 valid-input
rejections in that initial reduction and requires the corresponding default
application and retained-value integration. This increment covers native
validation; WSDL defaults, key/unique/keyref and full typed accounting remain
P5 work, followed by P6–P9.

## Acceptance

All 163 Qore suites, 63 real-provider checks and 11 supplements pass on unchanged
source. The new Qore suite has 911 assertions and passes AST, IR, JIT and tiered
execution. Four direct-ELF/native-C Valgrind runs have zero errors and no lost
memory; the C suite covers 204 injected failures. Both SOAP-version surveys and
strict reports exactly match the parent semantic records in legacy and native
preservation modes. Doxygen builds without warnings.

Final artifacts are retained under `/tmp/wsdl-p5-18i-default-assessment/final/`.
The [inventory](P5-18i-validation.json) includes source/runtime fingerprints,
commands and outcomes; the [full audit](audits/P5-18i-native-element-defaults.md)
records 19 Pass, 43 N/A and zero Fail. No main-Qore changes, installation or push.
