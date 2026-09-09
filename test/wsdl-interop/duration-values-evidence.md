# Duration lexical and native conversion evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

This increment implements strict duration lexical/native conversion and its scalar
provider contract, including rejection of incompatible builtin provider metadata. Duration bounds, enumeration/fixed/choice identity, derived
provider facets and collection value identity remain explicit following P3 work.
The implemented representation is described in [the design](../../design/wsdl-duration-values.md).

## Normative requirements and root causes

[XSD 1.0 Second Edition §3.2.6.1](https://www.w3.org/TR/xmlschema-2/#duration-lexical-representation)
requires ordered ASCII components, at least one component, and a time component
whenever `T` appears. Seconds may carry arbitrarily many fractional digits, with
at least one digit before and after a decimal point. Whitespace collapses as
specified for non-string primitive types.

The former WSDL regex allowed `T` with no following component (`P1DT`). Native
serialization omitted microseconds, placed minus signs inside components and
accepted absolute dates. Deserialization converted unrelated native categories
to strings. The generic soft-string provider bypassed duration validation entirely.
The new helper validates text directly and normalizes native relative components
into XSD's one-sign representation while retaining microseconds. Opposing month
and second group signs reject because no XSD lexical value represents them without
a reference date. Qore's native relative-date representation has broader semantics;
its `IF` formatter is therefore not used as an XSD lexical validator.

The independent Python reference converts authored input and output into exact
integer months and rational seconds. These component assertions check lossless
conversion, including fractions beyond binary floating-point precision. They are
not used as an implementation of XSD's four-anchor duration equality or ordering.
The Qore tests cover arbitrary 1,000-digit components, tiny fractions and all native
year/day limits without depending on a validator's bounded numeric representation.

## Pinned validator discrepancies

`duration-validator-defects.json` records three exact scalar reproductions:

| Lexical input | XSD 1.0 | libxml2 2.12.10 | Private libxml2 2.15.4 | Xerces-J 2.12.2 |
| --- | --- | --- | --- | --- |
| `PT.5S` | Invalid | Accepts | Accepts | Accepts |
| `PT1.S` | Invalid | Accepts | Accepts | Rejects |
| `P1D` surrounded by XML whitespace | Valid | Rejects | Accepts | Accepts |

The old libxml2 duration parser trims leading whitespace but its component loop
tries to parse trailing whitespace as another component. Private 2.15.4 explicitly
consumes trailing whitespace and checks for end-of-input. Both versions use one
`has_digits` flag for the integral and fractional parts together, so either part
can be empty even when a decimal point occurs. Xerces `DurationDV.parseSecond()` delegates to
`Double.parseDouble()` after its own character/trailing-dot checks, permitting a
leading decimal point. Sources:
[libxml2 2.12.10](https://github.com/GNOME/libxml2/blob/v2.12.10/xmlschemastypes.c),
[libxml2 2.15.4](https://gitlab.gnome.org/GNOME/libxml2/-/blob/v2.15.4/xmlschemastypes.c),
[pinned Xerces source archive](https://repo.maven.apache.org/maven2/xerces/xercesImpl/2.12.2/xercesImpl-2.12.2-sources.jar).
The digit-before/after rule was clarified by first-edition erratum E2-23 and is
incorporated into the second edition. A later XSD 1.1 BNF change is discussed in
[this W3C grammar report](https://lists.w3.org/Archives/Public/www-xml-schema-comments/2023JulSep/0000.html);
it does not change this project's XSD 1.0 target.

The binding input/output matrix requires the exact three recorded discrepancies:
36 libxml2 and 12 Xerces incorrect verdicts over atomic elements, attributed simple
content and repeated elements in both versions and directions. All generated and
reconstructed outputs have zero oracle disagreements. Every Qore acceptance,
rejection category and exact component assertion remains mandatory. Original W3C
fixtures and historical findings remain intact.

The generic manifest accepted by the existing native diagnostic also reproduces
these duration verdicts:

```sh
qore -b --enable-debug test/wsdl-interop/calendar-validator.qr \
  test/wsdl-interop/duration-validator-defects.json
```

The diagnostic's status reports successful execution, not conformance; compare
its individual verdicts with the recorded private-libxml2 column.
