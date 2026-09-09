# Exact duration facet evidence

Copyright (C) 2026 Qore Technologies, s.r.o.

P3-26 implements exact duration restriction semantics on top of P3-25 lexical
validation. Previously, generic numeric comparisons coerced duration strings,
enumerations/fixed choices compared authored text, detached providers lost facets,
and list/union identities did not recognize duration's value space. These causes
are addressed by the shared exact duration relation, restriction providers and
finite-choice field; see [the implemented contract](../../design/wsdl-duration-values.md).

## Normative relation and independent arithmetic

[XSD 1.0 §3.2.6.2](https://www.w3.org/TR/xmlschema-2/#duration) specifies four
reference dates and requires the same relation at every date. Its
[Appendix E](https://www.w3.org/TR/xmlschema-2/#adding-durations-to-dateTimes)
adds numeric year/month components, then day/time components. The four dates are
1696-09-01, 1697-02-01, 1903-03-01 and 1903-07-01 at midnight UTC. The independent
Python reference uses unbounded integer years and `Fraction` seconds; production
uses decimal limbs, 400-year cycles and separate exact fractional strings.
Neither uses a native date formatter, binary floating-point tolerance or display
rounding heuristic to decide equality or a facet boundary.

The 1,376-row matrix includes all ordered pairs of 30 duration spellings, seeded
large mixed components and independent normalized aliases, 9/18/19/100/1,000-digit
boundaries, subnormal-size fractions, negative values, every reference date shifted
across arithmetic year zero and Gregorian century boundaries. Each row checks
serialization, decoding, reconstructed providers, all four bounds and enumeration.
`P400Y` equals `P146097D` at every reference date, including negative 400-year and
2,000-year comparisons. `P1M` is incomparable with each of 28 through 31 days.

## Pinned validator defects

`duration-facet-validator-defects.json` records 16 exact builtin/facet/value triples
in 11 groups. Both libxml2 2.12.10 and private 2.15.4 disagree on all 16; Xerces-J
2.12.2 disagrees on the eight fractional-second triples. The other eight are
libxml2 Gregorian comparison defects. Every row records its normative result and
each pinned implementation's actual result. No blanket validator exception applies.

The libxml2 `xmlSchemaCompareDurations()` function computes year/day ranges using
four-year cycles and explicitly omits century/400-year exceptions. For example,
it rejects 146,097 and 146,098 days against an inclusive 400-year minimum. It also
stores seconds as `double`, collapsing distinct decimal fractions. Xerces uses
`Double.parseDouble()` and a `double` second field, so it likewise cannot distinguish
`PT1S`, `PT1.000000000000000009S`, `PT1.00000000000000001S` and
`PT1.00000000000000002S` in these facets. Exact ordered fractions prove the verdicts;
validator agreement does not override that arithmetic.

Sources: [libxml2 2.12.10](https://github.com/GNOME/libxml2/blob/v2.12.10/xmlschemastypes.c),
[libxml2 2.15.4](https://gitlab.gnome.org/GNOME/libxml2/-/blob/v2.15.4/xmlschemastypes.c),
[pinned Xerces source archive](https://repo.maven.apache.org/maven2/xerces/xercesImpl/2.12.2/xercesImpl-2.12.2-sources.jar).
The private libxml2 reproductions use the generic existing manifest diagnostic:

```sh
qore -b --enable-debug test/wsdl-interop/calendar-validator.qr \
  test/wsdl-interop/duration-facet-validator-defects.json
```

The actual-binding matrix includes atomic elements, attributed simple content and
repeated elements across both versions and directions, reconstructed services,
detached providers and examples. All Qore value results and error categories remain
mandatory. A generated `PT1.000000000000000009S` is correctly below the exclusive
`PT1.00000000000000001S` bound; the fixture records the validators' rejection without
changing that valid example or relaxing its exact value check.

Original W3C sources and historical findings remain unchanged. `DurationElement`
and `DurationAttribute` enter the strict selection with independent four-reference-date
value checks. These duration checks do not close the remaining P3 dateTime/time
work or the later ordered-content, binding and protocol phases.
