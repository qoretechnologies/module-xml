# Native IEEE conversion and canonical declarations

Copyright (C) 2026 Qore Technologies, s.r.o.

The private libxml2 provider validates complete XSD float/double lexical forms
whether or not the caller requests a computed value. The exponent must contain
digits; XML whitespace is accepted only at the permitted normalization stage.
Special values use exactly `INF`, `-INF` and `NaN`.

Finite decimals convert directly to binary32 or binary64 with nearest,
ties-to-even rounding. The C++17 `from_chars` helper uses no locale-dependent
conversion and preserves the caller's entire floating-point environment,
including rounding direction, status flags and enabled traps. Overflow maps to
signed infinity and underflow to signed zero. Classification uses the decimal
order and saturating exponent arithmetic, so long significands and exponent
cancellation do not overflow an integer counter.

Canonical text uses the shortest decimal significand that maps back to the
selected IEEE value, choosing the closest candidate with ties to even. The
`to_chars` scientific overload supplies those digits at the actual precision;
promoting binary32 to binary64 before formatting would choose different digits.
Formatting then applies XSD 1.0's required decimal point, uppercase `E`, normalized
exponent and unsigned `0.0E0`. Specials retain their XML spellings. Stack buffers
are bounded; only the returned libxml2-owned string allocates memory.

XSD 1.0 specifies the scientific syntax but does not uniquely select a decimal
precision. Shortest round-trip formatting is the explicit policy here, consistent
with the later XSD canonical-mapping guidance while retaining XSD 1.0 zero
semantics. For the least binary32 value, the result is `1.0E-45`; the least
binary64 value uses `5.0E-324`. These preserve the exact selected IEEE values.
Pinned Xerces instead chooses `1.4E-45` and `4.9E-324`; precision-sensitive pattern
differences are recorded separately. Its `0.0E1` zero spelling is an independent
violation of the XSD 1.0 rule.

Element, attribute and attribute-use default/fixed checks reuse the selected
value's canonical spelling, including list/union members. The second assessment
checks validity and retains the original computed value and source XML. For
example, `default="+017"` on a float restriction with pattern `\+017` is invalid;
the pattern `\+017|1\.7E1` admits both required spellings.

Configure-time behavior tests reject an installed library with these defects.
The private correction adds a C++17 conversion unit with a private C interface;
libxml2's public ABI stays unchanged. CMake carries the C++ runtime linkage to
static consumers. After all build-tree C source replacements, the provider adds
libxml2's source root only to the final C translation units. C++ include lookup
excludes that root because upstream `VERSION` aliases the standard `<version>`
header on case-insensitive filesystems. Instrumented C test drivers request the
private include explicitly. The provider regression builds a copied source tree
with a colliding header and checks both successful compilation and a negative
control that restores the target-wide include.

Allocation failures preserve negative internal-error status,
null outputs and cleanup. Tests compare 1,314 inputs with an integer-rational
oracle in all four rounding modes, exercise native conversion/DOM/reader APIs,
and keep canonical precision disagreements visible.

References:

- [XSD 1.0 float lexical and canonical rules](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#float)
- [XSD 1.0 declaration constraints](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#e-props-correct)
- [W3C discussion of the precision omission](https://lists.w3.org/Archives/Public/www-xml-schema-comments/2009JanMar/0043.html)
- [XSD 1.1 canonical-mapping guidance](https://www.w3.org/TR/xmlschema11-2/#f-floatCanmap)
- [C++ elementary string conversion specification](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2016/p0067r5.html)
