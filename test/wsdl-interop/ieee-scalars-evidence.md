# IEEE scalar integration and validator evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

P3-22 integrates the native conversion prerequisite into WSDL builtin scalars,
providers and example generation. Before this change, `xs:float` decoded
`16777217` as binary64 `16777217.0`, and both WSDL decoding and the soft provider
accepted `1tail` as `1.0`. The prior WSDL source at `aa3751f` reproduces all three
results using the same core and native XML binaries as the fixed implementation.
Evidence is `/tmp/wsdl-p3-22-baseline/{WSDL.qm,probe.qr,result.log}`.

[XSD 1.0 sections 3.2.4 and 3.2.5](https://www.w3.org/TR/xmlschema-2/#float)
require direct mapping to the target value space with nearest, ties-to-even
rounding. A mantissa optionally followed by `e`/`E` and an integer exponent is
valid; an exponent sign without digits is not an integer. The native design
records [W3C R-214's double exponent correction](https://www.w3.org/Bugs/Public/show_bug.cgi?id=2206).
The implementation uses these value rules, without applying display-rounding
heuristics to schema conversions.

## libxml2 missing exponent digits

Both lxml 6.1.1's libxml2 2.12.10 and the XML module's private libxml2 2.15.4
accept all six combinations of `xs:float`/`xs:double` with `1e`, `1e+`, and
`1e-`. Pinned Xerces-J 2.12.2 rejects them, agreeing with the normative grammar.
This is a validator defect, not a valid alternate spelling.

The cause is in `xmlSchemaValPredefTypeNode`, in
[libxml2 2.15.4 xmlschemastypes.c](https://gitlab.gnome.org/GNOME/libxml2/-/blob/v2.15.4/xmlschemastypes.c):
the exponent branch consumes `e`/`E`, an optional sign, and zero or more digits.
It checks for trailing characters but does not require a digit in that branch.
The later `sscanf` conversion can report a converted mantissa for the incomplete
exponent. No production parser or dependency source is patched for this finding.
WSDL's own lexical validator enforces the full grammar.

Minimal schema and invalid document:

```xml
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="value" type="xs:float"/>
</xs:schema>
```

```xml
<value>1e+</value>
```

The private native validator reproducer is
`/tmp/wsdl-p3-22-libxml-exponent.qr`, with results in the adjacent `.log`.
The committed Python matrix retains all invalid documents and requires exact
Xerces rejections. It records exactly 72 libxml2 false positives over the two
builtins, three lexical strings, three models, two SOAP versions and two
directions. Every such acceptance must have one of those exact invalid strings,
a failed independent complete-grammar match and no libxml2 diagnostic. Every
other schema/document verdict remains mandatory. No input is skipped, rewritten
or counted as conforming because libxml2 accepted it.

## Independent coverage

The seven Python methods exercise 24 actual SOAP binding contracts. They assess
1,248 incoming messages: 648 valid and 600 invalid, with all 648 valid outputs
checked for target IEEE values and schema validity. Atomic/simple-content/
attribute/repeated and list contracts are covered in both directions.

The provider matrix checks 6,848 results through element/message providers,
original/reconstructed services and requests/responses: 3,200 required
rejections and 3,648 valid outputs, including 192 generated examples.
Across binding and provider checks, 5,544 document verdicts are assessed by
both validators; the 72 libxml2 false positives remain explicit disagreements.

Three inherited rational-reference methods exercise 3,144 source values through
four conversion paths: direct decode, serialize/decode and original/reconstructed
providers, totaling 12,576 exact binary64-carrier comparisons. The reference
rounds rational significands using integer arithmetic; it does not ask libc,
MPFR, Qore or a validator to choose expected floating-point values. All 1,248
string-source cases also require exact lexical preservation during serialization.

The example failures found by this matrix were caused by missing float/double
entries in `WSMessageHelper::getTypeInfo(XsdBaseType)`. They formerly supplied
an `unknown type` text placeholder, which permissive numeric conversion hid.
Both now use a correctly rounded numeric sample, including inside native lists.

IEEE enumeration/bounds/fixed-value identity, patterned restrictions and
cross-member union identity remain the next P3 increment. This scalar coverage
does not close the full P3 or SOAP protocol acceptance criteria.
