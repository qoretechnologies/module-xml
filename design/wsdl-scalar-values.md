# WSDL scalar lexical validation

Copyright (C) 2026 Qore Technologies, s.r.o.

`XsdBaseType` validates integer XML lexical forms before native conversion in
both serialization directions. All thirteen integer builtins require ASCII
digits; signed integer types permit one leading sign, while XSD 1.0 unsigned
types require digits alone. Empty or absent text, fractions, exponents, trailing
data and non-ASCII digits raise `SOAP-SERIALIZATION-ERROR` or
`SOAP-DESERIALIZATION-ERROR` at the corresponding API boundary. Boolean, null,
binary and structured values cannot masquerade as native integers.

Whitespace normalization replaces TAB, LF and CR with SPACE. Collapse additionally
merges SPACE runs and removes leading/trailing SPACE. Other characters remain
available for lexical validation to reject; generic language whitespace trimming
is unsuitable. `normalizedString` uses replacement and `token` uses collapse.
For example, an integer field containing `" \t001\r\n "` has the value one;
`"1.0"`, `"1tail"` and `"1\x00tail"` are invalid integer lexical forms.

Integer bounds are compared as canonical decimal strings: sign first, then digit
count and lexical order, with the ordering reversed for negative values. No
bounded numeric conversion precedes validation. All eight bounded types enforce
their exact minimum/maximum, and the four sign-constrained unbounded types enforce
their sign. Values within signed 64-bit range become native integers. Larger
values remain strings, as do noncanonical spellings of `xs:integer` retained by
its existing API. For example, `xs:unsignedLong` returns `18446744073709551615`
as a string; `18446744073709551616` is rejected instead of clamped.

Native integer, float and number inputs must denote finite integral values.
Float formatting uses zero fractional digits and no grouping; number formatting
uses `NF_Raw`, preserving the exact stored MPFR integer. These paths preserve
the supplied numeric value, including precision already chosen by the caller.
Use decimal strings when the originating value must not first undergo floating
point rounding. Native negative zero is integer zero, which is valid for unsigned
types; an unsigned XML string containing a sign is still invalid.

`XsdIntegerDataType` applies these same rules before provider conversion, including
inside lists and after Serializable reconstruction. `getValueType()` returns
`NOTHING` to prevent enclosing list providers from coercing lexical strings first.
The output type hash reports `int`, plus `string` where large or retained lexical
values require it. Bounded integer providers retain the `NT_INT` base category;
mixed int/string providers report `NT_ALL`. Optional providers additionally accept
and return `NOTHING`; null remains invalid. Invalid values raise
`RUNTIME-TYPE-ERROR`, and absent required values raise `MISSING-VALUE-ERROR`.

```qore
%modern
%requires WSDL
WSDL::XsdIntegerDataType orderNumber("unsignedLong");
auto value = orderNumber.acceptsValue("18446744073709551615");
@assert(value == "18446744073709551615");
```

Integer examples use negative values for negative/nonpositive types. General
facets and the other scalar requirements retain their phase ownership in the
interoperability execution plan. Retained XML values continue to use the additive
public contract documented in `wsdl-xml-values.md`.

`test/wsdl-integer-lexical.qtest` covers all integer builtins, invalid value types,
attributes/simple content, reconstruction, lists/unions and whitespace. The
independent `test/wsdl-interop/test_integer_lexical.py` exercises actual SOAP 1.1
and 1.2 bindings in both directions, validates 936 input/output documents with
libxml2 and Xerces, and compares exact small integer values and expanded names.

`test/wsdl-integer-range.qtest` adds all thirteen builtin bounds, arbitrary-size
values, native numeric inputs, provider metadata and reconstruction. Independent
`test_integer_range.py` checks 1,200 documents across actual SOAP 1.1/1.2 bindings,
both directions, attributes/simple content, provider conversion and generated
examples. Exact Python integers and Xerces acceptance govern value fidelity;
96 libxml2 rejections of valid arbitrary-size input integers are explicitly
recorded as the retained P1 oracle disagreement.
