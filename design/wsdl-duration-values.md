# WSDL duration values and restrictions

Copyright (C) 2026 Qore Technologies, s.r.o.

`XsdBaseType` validates `xs:duration` text before serialization or deserialization.
The grammar follows XSD 1.0 Second Edition §3.2.6.1: ASCII component digits,
ordered year/month/day and hour/minute/second fields, an optional single leading
minus, at least one component and at least one time component after `T`.
Fractional seconds require digits on both sides of the decimal point. XML
whitespace collapses before validation; other whitespace and trailing text reject.

The decoded value is always an XML string. Component sizes and fractional precision
are retained without native numeric conversion, rounding heuristics or tolerances.
For example, `PT1.00000000000000001S` and `PT1.00000000000000002S` remain distinct.
Original component spelling and zeros are preserved after whitespace normalization.

A native Qore relative date is accepted as an input convenience. Its year/month
components combine into months and its day/hour/minute/second components combine
into whole seconds, with microseconds kept separately. This avoids overflowing
64-bit arithmetic at the native 32-bit day limit. Within-group mixed signs normalize:
one day minus one hour becomes `PT23H`. A consistent negative duration gets one
leading minus sign, and microseconds retain up to six fractional digits.

Opposing nonzero month and second groups cannot be represented by an XSD duration
without a reference date and therefore reject. Absolute dates also reject. The
native formatter supports Qore relative-date forms beyond XSD's grammar, so the
XSD conversion builds and validates its own representation. The decoder applies the
same conversion to explicit native relative-date input; unrelated scalars and
containers are never coerced into duration strings.

`XsdDurationDataType` accepts string/date input and returns string output. Its
empty direct-acceptance map and unspecified native value type ensure enclosing
providers validate every value. Optional and reconstructed providers retain this
contract. Required omission raises `MISSING-VALUE-ERROR`; invalid provider input
raises `RUNTIME-TYPE-ERROR`. Wire serialization/deserialization use their existing
SOAP error categories. Scalar provider metadata is immutable after construction;
reconstruction validates optionality before assigning it. Numeric/calendar restrictions and
list metadata also recognize duration providers and reject incompatible builtin identities.

Duration restrictions use XSD 1.0 §3.2.6.2 and Appendix E. Each duration is added
separately to `1696-09-01`, `1697-02-01`, `1903-03-01` and `1903-07-01`, all at
midnight UTC. A relation exists only when all four comparisons agree; equality
requires four equal results. `P1M` and each of `P28D` through `P31D` are incomparable.
`P400Y` and `P146097D` compare equal under this prescribed relation.

Private arithmetic uses signed decimal integers with base-10^9 limbs. Each limb
calculation stays below 10^18. Month arithmetic uses Euclidean division into
4,800-month Gregorian cycles, each containing exactly 146,097 days, followed by
bounded residual-year calculations. Appendix E adds numeric years internally,
including intermediate zero; these arithmetic coordinates are separate from XSD
calendar lexical year labels. Fractions remain decimal digit strings. Negative
fractions normalize to a floor whole-second value plus a nonnegative fraction,
so comparisons never depend on floating-point precision or formatting heuristics.
Parsing, limb arithmetic and rendering are linear in input length; there is no
loop proportional to the number of elapsed years or days.

`XsdDurationFacetInfo` contains the declared name, `duration` builtin, patterns,
bounds and enumeration text. `XsdDurationRestrictionDataType` validates metadata
before assignment and retains its base provider for inherited validation and
optionality. Bounds reject incomparable values. Contradictory or weakened bounds,
changed fixed bounds, invalid facet spellings and incompatible builtin providers
reject when the schema or detached provider is constructed. Repeated inherited
exclusive endpoints follow the XSD declaration rule. Patterns apply to collapsed
lexical text at each derivation step; equivalent duration spellings can therefore
have different pattern results.

`XsdDurationDataField` retains display text but compares finite choices by all four
reference-date results. Choice updates validate completely before replacing state.
Atomic/repeated field choices, fixed attributes, list enumerations and union item
identities use the same relation. A duration selected from a union stays distinct
from a string containing the same characters.

Example generation first checks a supplied value and inherited enumeration choices.
It then validates endpoints, nearby month/second candidates and pattern candidates.
The decimal grid has one more place than every endpoint's fractional precision,
so tiny open intervals are not rounded away. Anchor-relative seconds also provide
candidates where the single-sign duration grammar excludes a nearby mixed-sign
month/second spelling. Every candidate passes all inherited facets before return;
if the bounded candidate search cannot find a valid example, `XSD-SAMPLE-ERROR`
asks the caller to supply one.

```qore
%modern
%requires WSDL

XsdDurationDataType processing_interval();
@assert(processing_interval.acceptsValue(microseconds(-1)) == "-PT0.000001S");
@assert(processing_interval.acceptsValue(days(1) + hours(-1)) == "PT23H");
@assert(processing_interval.acceptsValue("PT0.00000000000000001S") == "PT0.00000000000000001S");

XsdDurationRestrictionDataType short_delay(<XsdDurationFacetInfo>{
    "name": "ShortDelay", "base_name": "duration",
    "bounds": {"minExclusive": "PT0S", "maxInclusive": "PT0.00000000000000001S"},
}, processing_interval);
@assert(short_delay.acceptsValue("PT0.000000000000000005S") == "PT0.000000000000000005S");
```

[Normative grammar](https://www.w3.org/TR/xmlschema-2/#duration-lexical-representation)
and [independent validator evidence](../test/wsdl-interop/duration-values-evidence.md)
explain the lexical boundaries. Tests cover native limits, 1,000-digit components
and fractions, provider reconstruction/cancellation/recovery and actual SOAP
bindings with independent exact-value assertions and local HTTP exchanges.

See [duration facet validator evidence](../test/wsdl-interop/duration-facets-evidence.md)
for exact independent arithmetic and classified libxml2/Xerces disagreements.
