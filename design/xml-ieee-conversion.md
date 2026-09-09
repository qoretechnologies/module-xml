# Native XML Schema IEEE conversion

Copyright (C) 2026 Qore Technologies, s.r.o.

`Qore::Xml::convert_xsd_float(value, double_precision = False)` validates and
rounds scalar input to binary32, or binary64 when `double_precision` is true.
Both results use Qore's native binary64 `float`; every binary32 result is exactly
representable in that carrier. Supported native inputs are `int`, `float` and
`number`, plus XSD lexical strings. Booleans, missing/null values and containers
are rejected with `XSD-FLOAT-LEXICAL-ERROR`.

```qore
%modern
%requires xml
float measurement = convert_xsd_float("16777217");       # 16777216
float precise = convert_xsd_float("16777217", True);     # 16777217
float rounded = convert_xsd_float("1.00000005960464477539062500000000001");
@assert(rounded == 1.0000001192092896);
```

## Lexical input

A length-aware state machine accepts the XSD decimal/scientific grammar, with
optional sign, decimal point and decimal exponent. Only XML's four whitespace
characters may surround the value; none may occur inside it. Embedded NUL,
non-ASCII digits, hexadecimal syntax, numeric prefixes with trailing garbage,
missing exponent digits and empty values are rejected before numeric conversion.
The special spellings are exactly `INF`, `-INF` and `NaN`, with the same surrounding
whitespace rule. Encoding conversion precedes byte validation, so UTF-16 strings
are treated by their characters rather than rejected for their encoding bytes.

Validated finite text is extracted directly into `float` or `double` using a
classic-locale C++ stream. The `num_get` contract selects `strtof` for `float` and
`strtod` for `double`; there is no intermediate binary64 rounding for binary32
text. The converter accounts for stream overflow reporting as infinity or as
the largest finite value with `failbit`. Underflow retains zero or subnormal
results. A complete parse is required, even after lexical validation.

A stack guard saves the thread's floating-point environment, disables traps,
selects nearest rounding and restores the original rounding direction and flags
on every exit. Environment setup/restoration failures produce
`XSD-FLOAT-CONVERSION-ERROR`. C++ allocation exceptions unwind owned temporaries
and the environment guard normally. The process locale is never changed.

## Native values

Binary64 input already denotes an exact native value. For a binary64 target it
is returned directly. Native integers use an exact Qore number carrier, and
arbitrary-precision numbers use Qore's MPFR-backed nearest binary64 conversion.

For a binary32 target, an ordered search compares the original native value
with exact binary32 rounding boundaries. A binary32 midpoint has at most 25
significant binary digits and lies within the finite binary64 range, including
the zero/subnormal midpoint `2^-150` and the overflow midpoint. Each boundary is
therefore represented exactly in binary64. Native float input is compared
directly; integer and number input uses Qore's exact number-versus-double
comparison API. Equality at a boundary selects the even significand. The search
performs at most 31 comparisons and never narrows the source before the final
choice. Endpoint construction uses exact powers of two, without byte-order
assumptions or a rounding-mode-dependent native float cast.

This also avoids using Qore's float-to-number conversion, which intentionally
constructs a decimal approximation, for native binary64 input. Display rounding
heuristics and shortest decimal spellings preserve different contracts: a
spelling that reconstructs a source at its own precision can cross a midpoint
at a different target precision. Neither is used to choose the binary32 value.
The original number object and its precision remain unchanged.

Overflow produces signed infinity, gradual underflow produces subnormals or
signed zero, and NaN stays NaN. Signed zero is retained so callers can preserve
lexical requirements. XSD value equality, enumeration and facets are separate
from this conversion API's native IEEE result.

## Ownership and cancellation

Production state is local to each call. Qore node references use reference
holders; strings, streams and floating-point environment state have automatic
ownership. No new shared mutable cache, filesystem access or network operation
is introduced. Input scans check cooperative cancellation every 100 bytes.
The bounded native search needs fewer than 100 iterations. Cancellation is also
checked before conversion and after the standard-library decimal conversion.

The implementation retains the existing C++11 minimum for older Qore headers,
uses the project's configured C++ standard, and introduces no third-party
dependency. Compile-time checks require the actual IEEE binary32/binary64
precision and exponent ranges used by the algorithm.

## Verification and references

`test/xsd-float.qtest` exercises public lexical, native, boundary, encoding,
special-value and concurrent calls. `qore-xml-float-test`, built from
`test/xsd-float.cpp`, verifies bit patterns, all four standard rounding modes,
pre-existing floating-point flags, comma-decimal C++ locale, deterministic
cancellation and recovery. `test/wsdl-interop/test_ieee_conversion.py` compares
3,144 conversions with an independent integer-rational rounding oracle;
its reference quantizes an exact rational to an integer significand and does
not use libc or MPFR to choose an expected result.

The requirements are XSD 1.0 Part 2 [float](https://www.w3.org/TR/xmlschema-2/#float)
and [double](https://www.w3.org/TR/xmlschema-2/#double), including nearest-value
rounding with ties to even. The published double exponent-range typo is
adjudicated by [W3C R-214 / issue 2206](https://www.w3.org/Bugs/Public/show_bug.cgi?id=2206):
the working group classified it as an error and adopted `-1074..971` for the
integer-significand representation. The code and oracle use those IEEE bounds.
The native parsing contract is specified by
[C++ num_get, stage 3](https://eel.is/c++draft/facet.num.get.virtuals);
number conversion uses [MPFR conversion functions](https://www.mpfr.org/mpfr-current/mpfr.html#Conversion-Functions).
