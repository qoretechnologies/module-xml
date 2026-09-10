# WSDL IEEE scalar conversion

Copyright (C) 2026 Qore Technologies, s.r.o.

`XsdBaseType` converts `xs:float` and `xs:double` through the XML module's
`convert_xsd_float()` API. Both return Qore's native binary64 float; a value
returned for `xs:float` has already been rounded to binary32 and is represented
exactly by that carrier. The [native conversion design](xml-ieee-conversion.md)
describes direct nearest, ties-to-even rounding, gradual underflow, overflow,
signed zero and floating-point environment restoration.

XML text must be a complete decimal/scientific spelling or exactly `INF`,
`-INF` or `NaN`, after XML whitespace collapse. Empty input, trailing text,
missing exponent digits, hexadecimal syntax, non-ASCII digits and other native
categories fail before permissive Qore conversion can change their meaning.
The WSDL adapter translates only lexical rejection to
`SOAP-SERIALIZATION-ERROR`, `SOAP-DESERIALIZATION-ERROR` or `RUNTIME-TYPE-ERROR`.
Cancellation and infrastructure exceptions retain their original categories.

Serialization returns validated lexical text. String callers retain their
normalized spelling; native numeric callers receive a round-trip-safe spelling
of the rounded target value. Native values reach conversion before formatting:
formatting an arbitrary-precision number or a binary64 midpoint as approximate
decimal text first could change binary32 rounding. The intermediate result of
`XsdBaseType.serializeValue()` is therefore a string for both IEEE types.
Decoded public values remain native floats. Negative zero retains its sign on
the wire even though XSD 1.0 has one zero in its schema value space.

`XsdIeeeDataType` is the scalar provider for the two builtins. It validates
string/int/float/number inputs directly and returns a native float. Its native
value type is unspecified and its direct-acceptance map is empty, so lists and
fields cannot bypass lexical validation or target-precision rounding. Mandatory
and optional copies retain the builtin precision. Serializable reconstruction
requires an exact builtin name and a boolean optionality flag before replacing
members. Instance metadata is immutable after construction; optionality changes
create a separate copy.

For example:

```qore
%modern
%requires WSDL
XsdIeeeDataType sensor("float");
XsdIeeeDataType precise_sensor("double");
printf("%Y\n", sensor.acceptsValue("16777217"));         # 16777216.0
printf("%Y\n", precise_sensor.acceptsValue("16777217")); # 16777217.0
```

`WSMessageHelper` supplies a numeric sample for both builtins. This also gives
unrestricted derived types and lists a valid starting value. The scalar paths
apply to elements, attributes, simple content, list items and individual union
alternatives. [IEEE restriction facets and union identity](wsdl-ieee-facets.md)
describe comparisons after target-precision conversion.

`test/wsdl-ieee-scalars.qtest` covers direct APIs, requiredness, invalid metadata,
reconstruction, native input boundaries and builtin type annotations. The
independent `test_ieee_scalars.py` matrix uses the rational reference from the
native tests to check decoded, encoded and original/reconstructed provider
values. Actual SOAP 1.1/1.2 contracts cover both message directions, repeated
elements, simple content, attributes, native lists and examples. The
[validator evidence](../test/wsdl-interop/ieee-scalars-evidence.md) records an
independent libxml2 grammar defect without changing or omitting invalid inputs.
