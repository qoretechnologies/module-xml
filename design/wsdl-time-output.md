# Lossless XSD dateTime and time values

Copyright (C) 2026 Qore Technologies, s.r.o.

`xs:dateTime` and `xs:time` use the same lexical and value validation boundary as
the other calendar primitives. XML text is checked before native conversion.
Whitespace collapses according to XSD; ASCII field widths, Gregorian dates,
nonzero year labels, extended-year leading zeros, clock ranges and timezone
syntax are enforced. An XML timezone has whole minutes within minus fourteen
through plus fourteen hours, with `14:00` as either endpoint.

An explicitly zoned value becomes a native Qore date only when its calendar
year and fraction fit the native representation and its second is below 60.
Otherwise it remains validated XML text. Missing timezones, arbitrary fractions,
arbitrary years and leap-second spellings therefore survive conversion without
acquiring a program timezone or losing precision. This extends the existing
calendar provider contract: callers must accept either `date` or `string` for
complete calendar values. The provider reports both return categories and
validates all input rather than allowing soft-date conversion to run first.
A native `time` retains the historical `1970-01-01` anchor; that day is not part
of the XML clock value.

Absolute native inputs project their fields into the requested XSD datatype.
Native `time` output has all six microsecond digits and an explicit offset;
`dateTime` retains Qore's ISO formatting. The offset comes from the represented
instant, including regional daylight-saving time. Relative dates and offsets
that cannot be expressed as an XSD timezone raise the appropriate serialization
or provider error. There is no rounding, tolerance or clipping.

```qore
Namespaces namespaces({});
XsdBaseType clock = namespaces.getBaseType("time");
date departure = new TimeZone(19800).date("2026-09-10T23:59:59.123456");
@assert(clock.serializeValue(namespaces, departure, True) == "23:59:59.123456+05:30");
auto appointment = clock.deserializeValue("appointment", {}, NOTHING, "09:30:00.0000001");
@assert(appointment == "09:30:00.0000001");
@assert(clock.serializeValue(namespaces, appointment, True) == appointment);
```

Exact comparison keeps calendar year labels and decimal fractions as strings.
Trailing fractional zeros do not affect identity. Timezone normalization moves
whole minutes and days, skipping year zero at the BCE/CE boundary. Midnight
`24:00:00` maps to `00:00:00` on the next date for dateTime, or the same recurring
midnight for time. Daily clock identity discards the normalized calendar date.
Bounds use the calendar partial order: a missing timezone introduces the XSD
fourteen-hour uncertainty and touching endpoints are indeterminate. Restrictions
reject a value whose relation to a bound is indeterminate.

Leap-second normalization preserves second 60 at a possible UTC quarter end,
including equivalent offset spellings. For example,
`1998-12-31T23:59:60Z` and `1999-01-01T05:29:60+05:30` identify the same value,
which differs from `1999-01-01T00:00:00Z`. Inappropriate leap dates map to the
following minute under XSD 1.0 Appendix D.1. For a missing timezone, the helper
checks whether an allowed offset could place the local value at a quarter end.
No historical leap-second table is required by this interpretation. The published
Appendix-E-based ordering algorithm contradicts the stated leap-second value
model for equivalent offsets; this implementation preserves value identity.

Patterns apply to lexical text while enumerations and bounds compare values.
A patterned restriction retains its accepted spelling as text, including zeros,
midnight notation and timezone aliases. The shared path covers elements,
attributes, simple content, lists, ordered unions, defaults/fixed values and
reconstructed providers. Example generation considers enumerations, bounds,
adjacent decimal fractions and fixed builtin prefixes for unconstrained leading
pattern fields. Every candidate passes the complete restriction chain; a
pattern intersection without a constructed candidate raises `XSD-SAMPLE-ERROR`.
The longest builtin prefix seed is twenty ASCII characters, so prefix synthesis
has a fixed candidate bound independent of input size.

The requirements are [XSD 1.0 dateTime](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#dateTime),
[time](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#time) and
[Appendix D.1](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#isoformats).
The [published leap-second contradiction](https://lists.w3.org/Archives/Public/www-xml-schema-comments/2002AprJun/0043.html)
explains the approved interpretation. Unit and real HTTP regressions are in
`test/wsdl-temporal-values.qtest` and `test/wsdl-time-output.qtest`; independent
matrices and validator reductions are beside the interoperability plan.

Both pinned schema validators store seconds in binary64 and can equate distinct
long fractions. Their exact false-positive reductions remain separately recorded
in `temporal-validator-defects.json`, with mandatory rational-value assertions.
The independent Java XMLGregorianCalendar value API uses decimal precision and
checks those distinctions separately from Xerces schema validation. Partial clock
ordering supplies the specification's common arbitrary date so day carries survive
timezone normalization; a retained direct-time API reduction records its limitation. Agreement
between schema validators is not a substitute for preserved-value checks.
