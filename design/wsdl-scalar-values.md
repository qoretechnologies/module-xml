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

Boolean strings accept exactly `true`, `false`, `1` and `0` after XML whitespace
collapse. Native booleans and numeric zero/one are accepted, including negative
zero. Other numbers, missing text, null, binary/structured values and invalid
spellings are rejected before conversion. Serialization emits `true` or `false`;
deserialization returns native booleans. This is an XML binding input contract;
it does not use the wider numeric truth conversion defined for XPath casts.
List decoding collapses XML whitespace before splitting items, so TAB, LF and CR
are separators just as SPACE is. Empty and whitespace-only lexical lists are empty
lists; non-XML separators remain part of the item for its validator to reject.
Scalar decoding joins ordered `^value^` and `^cdata^` fragments before lexical
validation, ignoring comments and rejecting child elements. Splitting `false`
between text and CDATA must still return `False`; appending `tail` must fail.
A single native `^value^` wrapper retains its native type. Retained XML carriers
keep the original XML nodes; this text projection is used only for validation.

`XsdBooleanDataType` shares this validation and returns `NOTHING` from
`getValueType()` so enclosing list providers cannot first turn every nonempty
string into `True`. Its native base category remains `NT_BOOLEAN`/`bool`.
Optional and mandatory copies retain validation after Serializable reconstruction;
only optional providers accept `NOTHING`, while null is always invalid. Invalid
provider values raise `RUNTIME-TYPE-ERROR`; required omissions raise
`MISSING-VALUE-ERROR`. For example, a list `("false", "1")` produces `(False, True)`,
whereas `("false", "yes")` is rejected.

`test/wsdl-boolean-lexical.qtest` checks lexical boundaries, native numeric values,
provider lists/optionality, reconstruction, attributes, simple content and unions.
`test_boolean_lexical.py` independently validates both directions of actual SOAP
1.1/1.2 bindings, boolean lists/unions, native provider values and generated examples
with libxml2 and Xerces, and compares the resulting boolean values.

Decimal strings use the XSD 1.0 decimal lexical space: an optional sign, ASCII
digits with an optional decimal point, and at least one digit. XML whitespace
is collapsed before validation. Exponents, nonfinite values, trailing data,
non-ASCII digits and other native value categories are rejected with the
corresponding SOAP or provider error. Native finite integers, floats and numbers
are accepted; boolean/null/binary/container values are not decimals.

Serialization preserves validated decimal text. Native float/number input uses
Qore 3.0 `toStringRoundTrip()`, which selects the shortest significand that
reconstructs the source binary value at its original precision and expands its
exponent into plain decimal notation. For example, `123.45n` emits `123.45`,
while `number("1.00000000000000000001")` retains its meaningful final digits.
This is a numeric binding policy; it does not apply the display heuristic or
round a value merely to satisfy a schema facet.

Deserialization retains the familiar native float result only when that float's
round-trip spelling reproduces the normalized input text exactly. Otherwise the
result is a string. Thus `"123.45"` returns a float, but `"+001.2300"`,
`"12345678901234567890.123456789"`, values beyond binary64's range and nonzero
values below its range remain exact strings. This prevents both precision loss
and loss of authored spellings needed by patterns. In particular, `9898.00` stays
valid through decoding and reserialization. Signed zero is retained on the wire;
all decimal zero spellings still denote the same XSD value.

`XsdDecimalDataType` applies the same rules before provider/list conversion and
reports float/string output alternatives (`NT_ALL`). Its conversion type is
`NOTHING`, so enclosing lists cannot coerce strings first. Optional providers
also accept/return `NOTHING`, while mandatory omission raises
`MISSING-VALUE-ERROR`. Null and invalid decimal input raise `RUNTIME-TYPE-ERROR`.
Serializable reconstruction and optional/mandatory copies retain these rules.

```qore
%modern
%requires WSDL
WSDL::XsdDecimalDataType amount();
auto exact = amount.acceptsValue("12345678901234567890.123456789");
@assert(exact == "12345678901234567890.123456789");
```

`test/wsdl-decimal-lexical.qtest` covers lexical boundaries, precision/range,
native inputs, provider lists/optionality, reconstruction and attributed simple
content. `test_decimal_lexical.py` checks 784 documents across real SOAP 1.1/1.2
bindings, both directions, lists/unions, CDATA, providers and examples. Xerces
and Python Decimal comparisons remain mandatory for all valid documents. Older
libxml2 versions have the already adjudicated 24-digit decimal pre-parser limit;
those rejections are recorded explicitly, including fractional leading/trailing
zeros, while newer libxml2 versions may accept every valid case.

The binding follows [XSD decimal](https://www.w3.org/TR/xmlschema-2/#decimal).
Its native-number policy is consistent with the canonical-spelling approach of
[BigDecimal.valueOf(double)](https://docs.oracle.com/en/java/javase/24/docs/api/java.base/java/math/BigDecimal.html#valueOf(double));
it is separate from XPath's float-to-decimal casting contract. Qore's MPFR-backed
number type is binary floating point, so original decimal text remains the
representation for exact decimal source values. WSDL requires Qore 3.0 for the
new formatter.

Decimal and integer restrictions validate normalized lexical input at each
derivation step. Numeric bounds and enumeration use canonical decimal value
keys: sign, integer length, integer digits and fractional digits determine order
without a floating point cast. Canonical keys are used only for comparison;
the caller's lexical spelling remains available for pattern validation and output.
For example, `1.00000000000000000000` fails a minimum of
`1.00000000000000000001`; `1.23` belongs to an enumeration declared as `+001.2300`.

Digit facets follow XSD 1.0 Second Edition sections 4.3.11–12. Integer leading
zeros and fractional trailing zeros do not count. Fractional leading zeros do:
`0.0012` needs four total digits and four fractional digits under that edition's
`i * 10^-n` rule, which bounds both the coefficient and `n`. Zero has one total
digit and no fractional digits. Native values are checked using the same exact
round-trip spelling used for serialization; display rounding cannot make an
out-of-range value satisfy a bound or digit limit.

`XsdNumericRestrictionDataType` carries a scalar `XsdNumericFacetInfo` snapshot
and its base provider. It retains no transient namespace graph, and both survive
Serializable reconstruction. Each provider in the derivation chain checks its
own restrictions before conversion. A step with a pattern returns a string and
reports that string output category; inherited patterned values also remain
strings. Scalar/list inputs reach validation before any soft conversion.

`XsdNumericDataField` gives fields the same numeric enumeration semantics.
Generic DataProvider string-key equality cannot express equivalent XML numeric
spellings. The numeric field retains declared `AllowedValueInfo` spellings and
uses exact canonical keys for comparison, independently of its provider's type
facets. It also checks numeric fixed attributes and choices for repeated elements.
Omission is accepted only through the provider's optional/default rules. Declared
numeric enumeration spellings are value-space metadata: an additional pattern
may require the caller to use a different lexical spelling of that same value.

Numeric samples first validate the proposed value and pattern/enum candidates.
Otherwise they find the interval nearest zero, including inherited and builtin
bounds, and construct an exact decimal grid value subject to digit limits.
Every result passes full serialization validation. Empty integer intervals and
pattern/enumeration intersections the generator cannot construct raise
`XSD-SAMPLE-ERROR`; they never produce a knowingly invalid example. List example
generation constructs a list from a valid item example.

The focused numeric facet suite covers exact boundaries, 2000-digit integers,
underflow, negative/zero values, native precision, patterns, inherited constraints,
provider/field reconstruction, optionality, repeated choices and fixed attributes.
`test_numeric_facets.py` checks both actual SOAP bindings and both directions
with libxml2 and Xerces, asserting exact Decimal values and expanded names.
Its 864 lexical input/output documents and 576 reconstructed provider/example
outputs form a 1,440-document independent matrix, with negative provider errors
checked separately.

References: [numeric bounds](https://www.w3.org/TR/xmlschema-2/#rf-minInclusive),
[enumeration](https://www.w3.org/TR/xmlschema-2/#rf-enumeration),
[totalDigits](https://www.w3.org/TR/xmlschema-2/#rf-totalDigits),
[fractionDigits](https://www.w3.org/TR/xmlschema-2/#rf-fractionDigits).

Restriction providers keep private configuration fixed after construction or
reconstruction. As with `QoreDataField`, callers configure numeric field choices
before sharing a field between threads; acceptance itself does not mutate the
field. Choice setters validate and construct replacement maps before publishing
them, so a failed update retains the previous choices.

Numeric restriction declarations are validated during dependency finalization,
before publishing a schema or provider. A restriction cannot widen inherited
digit counts or numeric bounds, change a fixed facet through any ancestor,
weaken numeric whitespace collapse, or introduce length facets. Integer-derived
types retain fractionDigits fixed at zero. Bound and enumeration literals must
map through the base datatype, including inherited patterns. The current step's
own pattern need not match the enumeration's declared spelling: enumeration
constrains values, and a different spelling of that value can satisfy the pattern.

XSD 1.0 permits a repeated inherited exclusive endpoint even though that endpoint
is outside the base value space. The declaration still needs a valid lexical
mapping; base enumeration/digit constraints do not invalidate this exception.
Opposite bounds must satisfy the edition's explicit inclusive/exclusive ordering
rules, including inherited and builtin endpoints. Equal exclusive endpoints in
one restriction are permitted; their empty value space causes sample generation
to raise `XSD-SAMPLE-ERROR`. An own-step enumeration/digit intersection may also
be empty without making the declarations themselves invalid.

`XsdFacetCount` retains `totalDigits` and `fractionDigits` as an `int`, or a
canonical decimal `string` beyond the native integer range. For example,
`<xs:totalDigits value="9223372036854775808"/>` is legal and retains that exact
string in `XsdSimpleType.totalDigits` and the provider's scalar metadata.
Comparisons use exact integer text. Example generation converts a count to an
integer only after proving it is smaller than the bounded candidate size.

The existing streaming schema grammar pass now checks simple derivation/facet
expanded names, annotation position and multiplicity, and facet attributes and
content before grouped XML hashes erase namespace/order information. Foreign
namespace facet attributes remain permitted. Facet values and `fixed` attributes
are validated before conversion; `whiteSpace`'s NMTOKEN value uses whitespace
collapse. The grammar stack uses memory proportional to XML depth and is local
to each parse. Annotation application content remains opaque.

`wsdl-facet-declarations.qtest` verifies these rules, large-count metadata,
provider reconstruction, examples and failed-addition rollback. The independent
`test_facet_declarations.py` matrix checks atomic and simple-content restrictions
through both actual SOAP bindings and both directions, comparing exact Decimal
values and expanded names. Its specification adjudication records compiler
disagreements separately from production acceptance. Other scalar families retain
their remaining P3 acceptance work.
