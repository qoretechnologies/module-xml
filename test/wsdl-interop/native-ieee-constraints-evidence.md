# P5-18e native IEEE conversion and canonical constraints

Copyright (C) 2026 Qore Technologies, s.r.o.

Native float/double canonical formatting used 14 fractional digits with lowercase
`e`, losing binary64 precision and emitting non-XML special values. The lexical
scan did not require exponent digits: invalid `1e`/`1e+` passed when no computed
value was requested. Computed conversion used locale- and rounding-sensitive
`sscanf`. The reproducible baseline and pinned Xerces canonical outputs are under
`/tmp/wsdl-p5-18e-ieee/`.

The correction validates complete XML syntax, converts directly to the selected
IEEE precision, and formats a shortest round-trip significand with XSD 1.0
syntax. The private C++17 helper preserves rounding mode, flags and enabled
traps; a focused test established that bare `from_chars` leaves an inexact flag.
Native computed values are published only after conversion succeeds. The
existing canonical declaration checker now includes selected IEEE members.
See [implemented design and primary sources](../../design/native-ieee-constraints.md).

Coverage includes:

- 300 declaration schemas: 156 valid and 144 expected syntax rejections, with
  both constraint kinds, six declaration locations, lists/unions and controls.
- 90 lexical cases through native conversion, DOM and reader validation. The
  native unit suite passes two cases and 970 assertions.
- 1,314 integer-rational reference inputs, including both sides of exact
  midpoints, tie parities, subnormal/normal transitions, finite limits, seeded
  values, 5,000-digit significands and huge exponents. Every input is checked in
  all four rounding modes against exact selected bits and independently derived
  canonical text, with caller floating-point flags preserved. C and German
  numeric locales each account for 5,256 records.
- Pinned Xerces validation of 302 schemas and 390 documents. All 90 lexical
  expectations agree. Forty-eight declaration differences remain explicit:
  24 use Xerces's incorrect `0.0E1` zero spelling, and 24 use its different
  precision policy for the smallest subnormal values. Native schema expectations
  remain enforced; neither disagreement is converted to a passing oracle result.
- Configure selection against real fixed and defective shared libraries,
  static linking from a C-only parent, repeated configuration, and allocation
  failure/recovery in datatype and canonical declaration paths.

The final [validation inventory](P5-18e-validation.json) records full suites,
native allocation sweeps, Valgrind, corpus comparisons, source hashes and exact
commands. The [audit](audits/P5-18e-native-ieee-constraints.md) covers every skill
check. Reproduction commands are in the [interop README](README.md#native-ieee-constraints-p5-18e).

Two build integration failures were root-caused before final acceptance: C++
must be enabled before creating libxml2's CMake directory, and the standalone
floating-point environment probe must link libm explicitly on Unix when testing
a shared installed dependency. Earlier failed provider runs remain separate from
final evidence.

No main-Qore change, installation or push. WSDL's corresponding IEEE canonical
capture, calendar canonical declarations, empty-element default PSVI, remaining
P5 criteria and P6–P9 remain required work.
