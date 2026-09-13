# Exact native XSD 1.0 calendar values and constraints

Copyright (C) 2026 Qore Technologies, s.r.o.

The private libxml2 provider represents dateTime, time, date and the five partial
calendar primitives using exclusively owned year and fractional-second strings.
Other calendar fields and timezone offsets are bounded integers. Parsing,
comparison and formatting never convert those strings to floating-point seconds
or bounded native years. `xmlSchemaVal` is opaque to public callers; the change
does not expose or alter an XML module API layout.

The calendar parser validates the complete XML lexical form and collapsible
boundary whitespace. It rejects year zero, extended leading zeros, invalid
Gregorian dates, invalid clock components and offsets outside +/-14 hours.
Year magnitudes contain at least four digits, independently of their sign.
Fraction strings omit trailing zeros. Midnight advances dateTime to the next
day, skips year zero and preserves arbitrary year magnitude. A time value repeats
daily, so its lexical midnight uses the same common-date anchor as hour zero.

Timezone normalization shifts integer minutes and at most one calendar day.
A carry at a year boundary allocates a replacement year before releasing the
previous buffer. Gregorian leap divisibility depends only on the final four
magnitude digits. Fractions remain untouched by timezone arithmetic.

Comparisons use exact year/field tuples and decimal fraction ordering. Partial
calendar periods use the previously defined common anchors: leap year 2000,
January and day one for absent components. Values with equal timezone presence
are totally ordered within a primitive. Unknown-zone comparisons attach the
permitted extreme offsets before normalizing; touching interval endpoints are
indeterminate. Distinct primitive calendar types are not equal.

Leap-second handling follows the existing [WSDL temporal contract](wsdl-time-output.md).
It preserves timezone-equivalent leap values and normalizes inappropriate leap
dates to the following minute. An unzoned value retains a leap second whenever
a permitted offset can place it at a valid quarter end. Each assumed timezone
endpoint is normalized separately, retaining common-date day carries for times.

Canonical dateTime/time values use UTC when a timezone exists, preserve timezone
absence, render two integer-second digits and retain every nonzero fractional
digit. Dates retain their recoverable offset in the interval (-12h,+12h]. For
example, `2002-10-10+13:00` becomes `2002-10-09-11:00`; replacing its zone with
`Z` would change the represented day interval. XSD 1.0 defines no canonical
representation for partial calendars; the native formatting API retains their
components and offsets instead of dropping the offset or shifting the period.

Schema construction includes complete calendar members in the existing
[canonical declaration checker](native-numeric-defaults.md). The source and
canonical spellings must both validate for element defaults/fixed values,
attribute declarations and attribute uses, including selected list/union members.
This assessment does not replace the original selected value or lexical scope.
WSDL's [corresponding declaration path](wsdl-canonical-constraints.md) uses its
own exact calendar arithmetic under the same contract.

The native free and copy operations own both variable-length components.
Copy failure releases only newly allocated storage. Canonical formatting and
comparison operate on local copies, release them on every failure path and
publish output only after success. No shared mutable calendar state is added.
The obsolete floating-point date parser, addition, normalization and comparison
paths are replaced together; duration representation and operations are separate.

`QoreXmlLibXml2CalendarFix.cmake` applies the correction only to hash-verified
predecessor sources and checks the complete generated result. Reconfiguration
preserves unchanged output timestamps. The provider's behavior probe checks
exact formatting/copied values and declaration enforcement independently. AUTO
selects the pinned private provider when either check fails; SYSTEM requires
both to pass, along with the existing dependency checks.

Verification includes direct native exact values, complete calendar boundaries,
all declaration paths, saved WSDL providers and SOAP bindings, allocation failure
recovery and Valgrind. The independent reference uses ordinal days and rational
seconds, and the historical external-validator discrepancies remain preserved.
See [native calendar evidence](../test/wsdl-interop/native-calendar-constraints-evidence.md).
