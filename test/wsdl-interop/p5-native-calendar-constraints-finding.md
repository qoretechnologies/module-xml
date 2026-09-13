# Native calendar constraints and formatting: resolved in P5-18h

Copyright (C) 2026 Qore Technologies, s.r.o.

The baseline observations below are retained as historical evidence. P5-18h
resolves the exact calendar representation, declaration checks and independent
reference endpoint issue; see [accepted evidence](native-calendar-constraints-evidence.md)
and [validation inventory](P5-18h-validation.json). At P5-18g, these native
failures remained independently reproducible after the WSDL correction.

The committed 306-schema calendar matrix contains 162 valid and 144 invalid
declarations. The P5-18g native conversion, DOM and reader paths accepted every
one: 432 invalid schema acceptances across 918 stage records. The native
canonical-default selector excludes calendar values. Diagnostic source, exact
results and stderr are under `/tmp/wsdl-p5-18g-calendar-constraints/` as
`native-constraints.qr`, `native-constraints.jsonl` and `native-constraints.err`.

Calling the native canonical API directly also exposes these root causes in
`xmlschemastypes.c`; `native-baseline.c` and `.tsv` retain eight examples:

| Input | Native result | Required result |
| --- | --- | --- |
| dateTime `2000-01-01T00:00:00.100+01:00` | `1999-12-31T23:00:0.099999999999909Z` | `1999-12-31T23:00:00.1Z` |
| time `24:00:00` | `24:00:00` | `00:00:00` |
| date `2002-10-10+13:00` | `2002-10-09Z` | `2002-10-09-11:00` |
| date `-0001-01-01Z` | `-001-01-01Z` | `-0001-01-01Z` |

The formatter's `%02.14g` does not pad the integer seconds correctly and loses
decimal precision. Timezone normalization adds double seconds, introducing
cancellation error. Its zero-offset branch retains hour 24; signed year padding
counts the sign among the four required digits. Date formatting normalizes the
first instant to UTC and discards the recoverable offset, changing the interval.
Native `date.sec` stores a double, so exact fractional ownership must be resolved
before extending canonical checks. A decimal rounding heuristic cannot repair
lost digits or the interval/offset error.

The normative requirements are XSD 1.0 Part 2
[dateTime](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#dateTime),
[time](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#time) and
[date](https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#date), plus Part 1
[element](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#e-props-correct)
and [attribute](https://www.w3.org/TR/2004/REC-xmlschema-1-20041028/#a-props-correct)
constraint validity. The target remains XSD 1.0; canonical rules from 1.1 must
not be silently applied to duration or partial calendar types.

The native fix requires configure/provider probes, direct canonical and copied
value tests, every declaration path, allocation-failure recovery and Valgrind.
Valid XML and original selected values must remain intact. The corrected WSDL
path uses existing exact calendar arithmetic independently; it does not wrap
or suppress the defective native results. Main Qore changes are not indicated.

The expanded native prototype also identifies a missing case in the independent
`temporal_reference.py` uncertainty calculation. For unzoned `09:39:60.22`
versus `09:39:60.22-14:00`, the interval includes the zoned value at its upper
endpoint, so the result is indeterminate. WSDL already gives that result. The
reference shifts minutes without normalizing the inappropriate leap second at
the assumed endpoint and incorrectly reports less. Correcting that reference
and adding explicit reversed endpoint regressions belongs to the native increment;
see `/tmp/wsdl-p5-18h-native-calendar/uncertainty-reference-finding.md`. This
additional independent finding does not change the WSDL declaration verdicts.
