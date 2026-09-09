# WSDL calendar values

Copyright (C) 2026 Qore Technologies, s.r.o.

`XsdBaseType` and derived restrictions validate `date`, `gYear`, `gYearMonth`,
`gMonthDay`, `gMonth` and `gDay` before native conversion. Input strings retain
their spelling after XML whitespace collapse. Grammar, Gregorian field limits,
signed extended years and timezone bounds are checked independently of the host
calendar parser. XSD 1.0 excludes year zero and extra leading zeros in extended
years. A native absolute date projects the requested fields and retains its
offset; relative dates and offsets outside whole minutes in ±14 hours reject.

## Public representation

| Input | Decoded value |
| --- | --- |
| `date` with an explicit timezone and a year in the native signed 32-bit range | Native Qore `date`, preserving calendar fields and offset |
| `date` without a timezone or beyond that year range | Validated XML `string` |
| Any of the five partial calendar primitives | Validated XML `string` |
| A derived restriction whose pattern requires a particular spelling | Validated XML `string` retaining that spelling |

This corrects the former conversion of an unzoned XML date into a native date
with an implicit program timezone. Consumers that assumed every `xs:date`
decoded to a native date must handle the documented string alternative.
`XsdCalendarDataType` reports both alternatives for `date`; partial calendar
providers report string output. Its native value type is unspecified and its
direct-acceptance map is empty, ensuring nested fields and lists also validate.
The legacy `getDataProviderBaseType()` API still reports the closest native type;
`getDataProviderType()` supplies the complete validated conversion contract.

This is the same lossless scalar fallback principle used by decimal values.
`XsdXmlValue` remains available when a caller needs the entire XML element and
its namespace/content context. A calendar string does not retain that context.
The native Qore calendar uses astronomical year zero; WSDL validates XSD year
labels before invoking it and never uses native epoch arithmetic for XSD facets.

## Comparisons, restrictions and collections

Calendar keys contain timezone presence and the normalized start of the period.
Missing calendar fields use year 2000, month 1 and day 1. Complete years remain
decimal strings, including during carry and borrow; Gregorian leap divisibility
requires only the final four digits. Timezone normalization shifts at most one
calendar day and skips year zero. A suffix scan performs year carry/borrow in
linear time instead of repeatedly indexing a large UTF-8 string.

Two values with the same timezone-presence state have an exact ordering. A
missing timezone spans the inclusive ±14-hour uncertainty interval when compared
with an explicitly zoned value. Overlap or a touching endpoint is incomparable.
Bounds reject incomparable values. Enumeration and fixed values use exact
identity, including timezone presence; no rounding heuristic or tolerance is used.

Patterns constrain normalized lexical text at each restriction step. Enumeration,
bounds, inherited/fixed endpoints and finite field choices use calendar values.
Provider reconstruction checks the builtin, facet metadata and known base-provider
identity before assigning state. Choice setters validate a complete replacement
before publishing it. Metadata is immutable after construction, except for field
setters that retain the existing caller-synchronization contract.

Lists compare ordered calendar items. Unions retain the selected primitive family,
so a string alternative cannot satisfy an enumeration of calendar values merely
because its text resembles a date. Mandatory/optional providers, reconstructed
schemas, elements, simple content, attributes and message providers use the same
conversion rules. Cancellation exceptions propagate without being remapped to
lexical errors; recovery does not retain partially converted state.

## Examples

```qore
%modern
%requires WSDL

XsdCalendarDataType delivery_day("date");
@assert(delivery_day.acceptsValue("2026-09-09") == "2026-09-09");
date zoned = delivery_day.acceptsValue("2026-09-09+05:30");
@assert(zoned.getUtcOffset() == 19800);
XsdCalendarDataType anniversary("gMonthDay");
@assert(anniversary.acceptsValue("--02-29") == "--02-29");
```

`WSMessageHelper` starts with valid samples for all six primitives. Restrictions
validate the supplied default, enumeration candidates, endpoints, nearby calendar
and timezone values, pattern candidates and a builtin sample. Every returned
candidate must satisfy the full derivation chain. This bounded construction does
not enumerate an unbounded calendar domain; failure raises `XSD-SAMPLE-ERROR`.

The normative definitions are [XSD 1.0 calendar datatypes](https://www.w3.org/TR/xmlschema-2/#date)
and its [partial ordering](https://www.w3.org/TR/xmlschema-2/#dateTime-order).
The independent reference uses arbitrary-precision ordinal-day arithmetic,
separate from the production tuple/carry algorithm. Regressions cover exact
values through actual SOAP 1.1/1.2 bindings, both directions, detached providers,
generated examples and local HTTP client/handler exchanges.
[Validator evidence](../test/wsdl-interop/calendar-values-evidence.md) records
upstream discrepancies without changing the expected XSD result.
